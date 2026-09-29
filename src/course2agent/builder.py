from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from .parsers import Unit, discover_sources, parse_source, slugify, source_id, source_role


def _safe_title(path: Path) -> str:
    return path.stem.replace("_", " ").replace("-", " ").strip().title()


def _chunk_id(source: str, unit: Unit) -> str:
    digest = hashlib.sha256(f"{source}\0{unit.locator}\0{unit.text}".encode("utf-8")).hexdigest()[:10]
    return f"{source}-{unit.ordinal:04d}-{digest}"


def _json_dump(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_skill(skill_dir: Path, title: str, slug: str) -> None:
    content = f"""---
name: {slug}-course
description: Teach, explain, review, and quiz from the indexed {title} course materials with source citations and assessment-integrity boundaries.
---

# {title} Course Agent

Use the connected Course2Agent MCP tools for every course-specific answer.

1. Start with `get_course_overview` when scope or available materials are unclear.
2. Use `search_course` or `build_study_context` before explaining a topic.
3. Cite factual course claims using the returned source citation, such as `[Lecture 1, slide 4]`.
4. Distinguish three layers when useful: **course material**, **general background**, and **your inference**. Never present the latter two as course requirements.
5. Teach from definitions to a worked example, then check understanding. Match notation and terminology used by the supplied course.
6. For a quiz, derive questions from retrieved evidence, keep answers separate, and cite the answer key.
7. For assessed work, explain concepts, interpret rubrics, and give feedback. Do not fabricate results or misrepresent work as the learner's own.

Read [references/index.md](references/index.md) for source coverage and [references/course-map.md](references/course-map.md) for the material map. If retrieval finds no support, say that the indexed course materials do not establish the answer.
"""
    (skill_dir / "SKILL.md").write_text(content, encoding="utf-8")


def _write_usage(root: Path, title: str, slug: str) -> None:
    content = f"""# Use {title} Agent

This package contains a course skill, a local MCP retrieval server, indexed knowledge, and source snapshots.

## Start the MCP server

```bash
python3 mcp/server.py --self-test
python3 mcp/server.py
```

The server uses stdio and implements four tools: `get_course_overview`, `search_course`, `read_course_chunk`, and `build_study_context`.

Register `python3` with the absolute path to `mcp/server.py` in any MCP-compatible client, then install `skill/{slug}-course` as a skill for that client. No network access or API key is required at runtime.

## Provenance

Course-specific claims should cite the locators returned by the MCP tools. `knowledge/manifest.json` records source hashes, roles, formats, and extraction coverage. Source files are snapshotted under `sources/`.

## Limits

- Text extraction does not recover diagrams or equations that are image-only.
- PDF support during building requires `pypdf`; the delivered server itself uses only Python's standard library.
- Retrieval is lexical BM25-style search, not semantic embedding search.
"""
    (root / "USAGE.md").write_text(content, encoding="utf-8")


def build_course(
    inputs: Iterable[str | Path],
    output: str | Path,
    title: str | None = None,
    slug: str | None = None,
) -> Path:
    sources = discover_sources(inputs)
    if not sources:
        raise ValueError("No supported course materials were found")

    output = Path(output).expanduser().resolve()
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f"Output directory is not empty: {output}")
    output.mkdir(parents=True, exist_ok=True)

    title = title or _safe_title(sources[0].parent)
    slug = slugify(slug or title)
    skill_dir = output / "skill" / f"{slug}-course"
    references_dir = skill_dir / "references"
    knowledge_dir = output / "knowledge"
    source_dir = output / "sources"
    mcp_dir = output / "mcp"
    for directory in (references_dir, knowledge_dir, source_dir, mcp_dir):
        directory.mkdir(parents=True, exist_ok=True)

    chunks: list[dict[str, Any]] = []
    source_records: list[dict[str, Any]] = []
    copied_names: set[str] = set()
    for path in sources:
        identifier = source_id(path)
        role = source_role(path)
        units = parse_source(path)
        if not units:
            continue
        destination_name = path.name
        if destination_name in copied_names:
            destination_name = f"{identifier}-{path.name}"
        copied_names.add(destination_name)
        shutil.copy2(path, source_dir / destination_name)
        sha256 = hashlib.sha256(path.read_bytes()).hexdigest()
        record = {
            "source_id": identifier,
            "title": _safe_title(path),
            "role": role,
            "format": path.suffix.lower().lstrip("."),
            "snapshot": f"sources/{destination_name}",
            "sha256": sha256,
            "unit_count": len(units),
        }
        source_records.append(record)
        for unit in units:
            chunks.append(
                {
                    "chunk_id": _chunk_id(identifier, unit),
                    "source_id": identifier,
                    "source_title": record["title"],
                    "role": role,
                    "locator": unit.locator,
                    "citation": f"[{record['title']}, {unit.locator}]",
                    "text": unit.text,
                }
            )

    if not chunks:
        raise ValueError("The supplied files contained no extractable text")

    manifest = {
        "schema_version": 1,
        "generator": "course2agent 0.1.0",
        "title": title,
        "course_slug": slug,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_count": len(source_records),
        "chunk_count": len(chunks),
        "sources": source_records,
        "known_limitations": [
            "Image-only content is not transcribed.",
            "Lexical retrieval may miss conceptual synonyms absent from the query.",
        ],
    }
    _json_dump(knowledge_dir / "manifest.json", manifest)
    (knowledge_dir / "chunks.jsonl").write_text(
        "".join(json.dumps(chunk, ensure_ascii=False) + "\n" for chunk in chunks),
        encoding="utf-8",
    )

    index_lines = [f"# {title} source index", ""]
    map_lines = [f"# {title} course map", ""]
    for record in source_records:
        index_lines.append(
            f"- **{record['title']}** (`{record['source_id']}`): "
            f"{record['role']}, {record['format']}, {record['unit_count']} indexed units; "
            f"snapshot `{record['snapshot']}`."
        )
    for role in sorted({record["role"] for record in source_records}):
        map_lines.extend([f"## {role.title()}", ""])
        for record in source_records:
            if record["role"] == role:
                map_lines.append(f"- {record['title']}: {record['unit_count']} units")
        map_lines.append("")
    (references_dir / "index.md").write_text("\n".join(index_lines) + "\n", encoding="utf-8")
    (references_dir / "course-map.md").write_text("\n".join(map_lines), encoding="utf-8")
    _write_skill(skill_dir, title, slug)

    runtime_source = Path(__file__).with_name("runtime.py").read_text(encoding="utf-8")
    server_path = mcp_dir / "server.py"
    server_path.write_text("#!/usr/bin/env python3\n" + runtime_source, encoding="utf-8")
    server_path.chmod(0o755)
    _write_usage(output, title, slug)
    return output

