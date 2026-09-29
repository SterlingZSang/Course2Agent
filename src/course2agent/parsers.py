from __future__ import annotations

import hashlib
import html
import json
import re
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from xml.etree import ElementTree


TEXT_SUFFIXES = {
    ".md",
    ".markdown",
    ".txt",
    ".rst",
    ".py",
    ".java",
    ".r",
    ".csv",
    ".tsv",
    ".json",
    ".yaml",
    ".yml",
}
SUPPORTED_SUFFIXES = TEXT_SUFFIXES | {".pdf", ".pptx", ".docx", ".ipynb", ".html", ".htm"}


@dataclass(frozen=True)
class Unit:
    locator: str
    text: str
    ordinal: int


def slugify(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return value or "course"


def source_id(path: Path) -> str:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()[:8]
    return f"{slugify(path.stem)}-{digest}"


def source_role(path: Path) -> str:
    if path.suffix.lower() == ".ipynb":
        return "notebook"
    name = path.name.lower()
    routes = (
        ("syllabus", ("syllabus", "outline", "module-guide")),
        ("assessment", ("assignment", "assessment", "coursework", "exam", "rubric", "marking")),
        ("lecture", ("lecture", "lesson", "week", "slide", "class")),
        ("lab", ("lab", "practical", "workshop")),
        ("exercise", ("exercise", "problem", "quiz", "tutorial")),
        ("reading", ("reading", "chapter", "textbook", "paper")),
    )
    for role, hints in routes:
        if any(hint in name for hint in hints):
            return role
    return "material"


def discover_sources(inputs: Iterable[str | Path]) -> list[Path]:
    found: list[Path] = []
    for raw in inputs:
        path = Path(raw).expanduser().resolve()
        if not path.exists():
            raise FileNotFoundError(f"Course source does not exist: {path}")
        if path.is_dir():
            found.extend(
                candidate
                for candidate in sorted(path.rglob("*"))
                if candidate.is_file()
                and candidate.suffix.lower() in SUPPORTED_SUFFIXES
                and not any(part.startswith(".") for part in candidate.relative_to(path).parts)
            )
        elif path.suffix.lower() in SUPPORTED_SUFFIXES:
            found.append(path)
        else:
            raise ValueError(f"Unsupported course source: {path.name}")
    unique = {str(path): path for path in found}
    return [unique[key] for key in sorted(unique)]


def parse_source(path: Path) -> list[Unit]:
    suffix = path.suffix.lower()
    if suffix in TEXT_SUFFIXES:
        return _parse_text(path)
    if suffix == ".pdf":
        return _parse_pdf(path)
    if suffix == ".pptx":
        return _parse_pptx(path)
    if suffix == ".docx":
        return _parse_docx(path)
    if suffix == ".ipynb":
        return _parse_notebook(path)
    if suffix in {".html", ".htm"}:
        return _parse_html(path)
    raise ValueError(f"Unsupported source type: {suffix}")


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace").replace("\x00", "")


def _parse_text(path: Path) -> list[Unit]:
    lines = _read_text(path).splitlines()
    if not lines:
        return []
    units: list[Unit] = []
    window, overlap = 80, 10
    start = 0
    ordinal = 1
    while start < len(lines):
        end = min(start + window, len(lines))
        text = "\n".join(lines[start:end]).strip()
        if text:
            units.append(Unit(f"lines {start + 1}-{end}", text, ordinal))
            ordinal += 1
        if end == len(lines):
            break
        start = end - overlap
    return units


def _parse_pdf(path: Path) -> list[Unit]:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError(
            "PDF input requires pypdf. Install it with: pip install 'course2agent[pdf]'"
        ) from exc
    reader = PdfReader(str(path))
    units: list[Unit] = []
    for index, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()
        if text:
            units.append(Unit(f"page {index}", text, index))
    return units


def _numeric_suffix(name: str) -> int:
    match = re.search(r"(\d+)(?=\D*$)", name)
    return int(match.group(1)) if match else 0


def _parse_pptx(path: Path) -> list[Unit]:
    units: list[Unit] = []
    with zipfile.ZipFile(path) as archive:
        slides = sorted(
            (name for name in archive.namelist() if re.fullmatch(r"ppt/slides/slide\d+\.xml", name)),
            key=_numeric_suffix,
        )
        for index, name in enumerate(slides, start=1):
            root = ElementTree.fromstring(archive.read(name))
            text = "\n".join(
                node.text.strip()
                for node in root.iter()
                if node.tag.endswith("}t") and node.text and node.text.strip()
            )
            if text:
                units.append(Unit(f"slide {index}", text, index))
    return units


def _parse_docx(path: Path) -> list[Unit]:
    with zipfile.ZipFile(path) as archive:
        root = ElementTree.fromstring(archive.read("word/document.xml"))
    paragraphs: list[str] = []
    for paragraph in (node for node in root.iter() if node.tag.endswith("}p")):
        text = "".join(
            node.text or "" for node in paragraph.iter() if node.tag.endswith("}t")
        ).strip()
        if text:
            paragraphs.append(text)
    units: list[Unit] = []
    for start in range(0, len(paragraphs), 30):
        end = min(start + 30, len(paragraphs))
        units.append(
            Unit(
                f"paragraphs {start + 1}-{end}",
                "\n\n".join(paragraphs[start:end]),
                len(units) + 1,
            )
        )
    return units


def _parse_notebook(path: Path) -> list[Unit]:
    notebook = json.loads(_read_text(path))
    units: list[Unit] = []
    for index, cell in enumerate(notebook.get("cells", []), start=1):
        source = cell.get("source", [])
        text = "".join(source) if isinstance(source, list) else str(source)
        text = text.strip()
        if text:
            kind = cell.get("cell_type", "cell")
            units.append(Unit(f"{kind} cell {index}", text, index))
    return units


def _parse_html(path: Path) -> list[Unit]:
    raw = _read_text(path)
    raw = re.sub(r"<(script|style)\b[^>]*>.*?</\1>", " ", raw, flags=re.I | re.S)
    raw = re.sub(r"</(p|div|li|h[1-6]|tr)>", "\n", raw, flags=re.I)
    text = html.unescape(re.sub(r"<[^>]+>", " ", raw))
    lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
    clean = "\n".join(line for line in lines if line)
    temp_lines = clean.splitlines()
    return [
        Unit(
            f"text block {start // 80 + 1}",
            "\n".join(temp_lines[start : start + 80]),
            start // 80 + 1,
        )
        for start in range(0, len(temp_lines), 80)
        if temp_lines[start : start + 80]
    ]
