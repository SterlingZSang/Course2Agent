from __future__ import annotations

import argparse
import json
import math
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any


TOKEN_RE = re.compile(r"[\w]+", re.UNICODE)
CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]+")


def tokenize(text: str) -> list[str]:
    tokens: list[str] = []
    for raw in TOKEN_RE.findall(text.lower()):
        non_cjk = CJK_RE.sub(" ", raw)
        tokens.extend(part for part in non_cjk.split() if len(part) > 1)
        for segment in CJK_RE.findall(raw):
            if len(segment) == 1:
                tokens.append(segment)
            else:
                tokens.extend(segment[index : index + 2] for index in range(len(segment) - 1))
    return tokens


class CourseIndex:
    def __init__(self, root: str | Path):
        self.root = Path(root).resolve()
        manifest_path = self.root / "knowledge" / "manifest.json"
        chunks_path = self.root / "knowledge" / "chunks.jsonl"
        self.manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.chunks = [
            json.loads(line)
            for line in chunks_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        self.by_id = {chunk["chunk_id"]: chunk for chunk in self.chunks}
        self.term_counts = [Counter(tokenize(chunk["text"])) for chunk in self.chunks]
        self.lengths = [sum(counts.values()) for counts in self.term_counts]
        self.avg_length = sum(self.lengths) / max(len(self.lengths), 1)
        self.document_frequency: Counter[str] = Counter()
        for counts in self.term_counts:
            self.document_frequency.update(counts.keys())

    def overview(self) -> dict[str, Any]:
        return {
            "title": self.manifest["title"],
            "course_slug": self.manifest["course_slug"],
            "source_count": len(self.manifest["sources"]),
            "chunk_count": len(self.chunks),
            "sources": self.manifest["sources"],
        }

    def search(self, query: str, limit: int = 5, role: str | None = None) -> list[dict[str, Any]]:
        query_terms = tokenize(query)
        if not query_terms:
            return []
        n_docs = len(self.chunks)
        scores: list[tuple[float, int]] = []
        k1, b = 1.5, 0.75
        for index, (chunk, counts, length) in enumerate(zip(self.chunks, self.term_counts, self.lengths)):
            if role and chunk["role"] != role:
                continue
            score = 0.0
            for term in query_terms:
                frequency = counts.get(term, 0)
                if not frequency:
                    continue
                df = self.document_frequency[term]
                inverse = math.log(1 + (n_docs - df + 0.5) / (df + 0.5))
                denominator = frequency + k1 * (1 - b + b * length / max(self.avg_length, 1))
                score += inverse * frequency * (k1 + 1) / denominator
            if score > 0:
                scores.append((score, index))
        scores.sort(key=lambda item: (-item[0], self.chunks[item[1]]["chunk_id"]))
        results = []
        for score, index in scores[: max(1, min(limit, 20))]:
            chunk = self.chunks[index]
            results.append(
                {
                    "chunk_id": chunk["chunk_id"],
                    "score": round(score, 4),
                    "citation": chunk["citation"],
                    "role": chunk["role"],
                    "text": chunk["text"][:1600],
                }
            )
        return results

    def read_chunk(self, chunk_id: str) -> dict[str, Any]:
        if chunk_id not in self.by_id:
            raise KeyError(f"Unknown chunk_id: {chunk_id}")
        return self.by_id[chunk_id]

    def study_context(self, topic: str, max_chars: int = 6000) -> dict[str, Any]:
        results = self.search(topic, limit=12)
        selected: list[dict[str, Any]] = []
        used = 0
        budget = max(500, min(max_chars, 20000))
        for result in results:
            chunk = self.by_id[result["chunk_id"]]
            cost = len(chunk["text"])
            if selected and used + cost > budget:
                break
            if not selected and cost > budget:
                shortened = dict(chunk)
                shortened["text"] = chunk["text"][:budget]
                shortened["truncated"] = True
                selected.append(shortened)
                used = budget
                break
            selected.append(chunk)
            used += cost
        return {
            "topic": topic,
            "evidence": selected,
            "instruction": "Use only this evidence for course-specific claims; cite each claim with the supplied citation.",
        }


TOOLS = [
    {
        "name": "get_course_overview",
        "description": "List the course title, indexed materials, source roles, and coverage.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "search_course",
        "description": "Search indexed course materials and return ranked excerpts with citations.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "limit": {"type": "integer", "minimum": 1, "maximum": 20, "default": 5},
                "role": {"type": "string"},
            },
            "required": ["query"],
            "additionalProperties": False,
        },
    },
    {
        "name": "read_course_chunk",
        "description": "Read one complete indexed chunk by its stable chunk ID.",
        "inputSchema": {
            "type": "object",
            "properties": {"chunk_id": {"type": "string"}},
            "required": ["chunk_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "build_study_context",
        "description": "Assemble a citation-ready evidence packet for explaining or revising a topic.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "topic": {"type": "string"},
                "max_chars": {"type": "integer", "minimum": 500, "maximum": 20000, "default": 6000},
            },
            "required": ["topic"],
            "additionalProperties": False,
        },
    },
]


def call_tool(index: CourseIndex, name: str, arguments: dict[str, Any]) -> Any:
    if name == "get_course_overview":
        return index.overview()
    if name == "search_course":
        return index.search(arguments["query"], arguments.get("limit", 5), arguments.get("role"))
    if name == "read_course_chunk":
        return index.read_chunk(arguments["chunk_id"])
    if name == "build_study_context":
        return index.study_context(arguments["topic"], arguments.get("max_chars", 6000))
    raise KeyError(f"Unknown tool: {name}")


def _response(request_id: Any, result: Any = None, error: dict[str, Any] | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {"jsonrpc": "2.0", "id": request_id}
    payload["error" if error else "result"] = error if error else result
    return payload


def serve(root: str | Path) -> None:
    index = CourseIndex(root)
    for line in sys.stdin:
        try:
            request = json.loads(line)
            method = request.get("method")
            request_id = request.get("id")
            if method == "notifications/initialized":
                continue
            if method == "initialize":
                result = {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {"listChanged": False}},
                    "serverInfo": {"name": "course2agent", "version": "0.1.0"},
                }
            elif method == "ping":
                result = {}
            elif method == "tools/list":
                result = {"tools": TOOLS}
            elif method == "tools/call":
                params = request.get("params", {})
                value = call_tool(index, params.get("name", ""), params.get("arguments", {}))
                result = {
                    "content": [{"type": "text", "text": json.dumps(value, ensure_ascii=False, indent=2)}],
                    "structuredContent": {"result": value},
                    "isError": False,
                }
            else:
                raise KeyError(f"Unsupported method: {method}")
            if request_id is not None:
                print(json.dumps(_response(request_id, result=result), ensure_ascii=False), flush=True)
        except Exception as exc:
            request_id = request.get("id") if "request" in locals() else None
            if request_id is not None:
                error = {"code": -32603, "message": str(exc)}
                print(json.dumps(_response(request_id, error=error), ensure_ascii=False), flush=True)


def self_test(root: str | Path) -> dict[str, Any]:
    index = CourseIndex(root)
    overview = index.overview()
    first_text = index.chunks[0]["text"] if index.chunks else ""
    first_terms = tokenize(first_text)
    results = index.search(first_terms[0] if first_terms else "course")
    return {
        "ok": bool(index.chunks and results),
        "source_count": overview["source_count"],
        "chunk_count": overview["chunk_count"],
        "search_result_count": len(results),
    }


def main(default_root: str | Path | None = None) -> None:
    parser = argparse.ArgumentParser(description="Course2Agent MCP server")
    parser.add_argument("--root", default=str(default_root) if default_root else None)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if not args.root:
        parser.error("--root is required")
    if args.self_test:
        report = self_test(args.root)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        raise SystemExit(0 if report["ok"] else 1)
    serve(args.root)


if __name__ == "__main__":
    main(Path(__file__).resolve().parents[1])
