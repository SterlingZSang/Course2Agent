# Course2Agent

Course2Agent turns a collection of course materials into a grounded teaching agent with traceable citations and deterministic retrieval. It is inspired by the dual-output architecture of [Paper2Agent](https://github.com/jmiao24/Paper2Agent), redesigned for educational content:

- **Course2Skill** defines how the agent explains concepts, supports revision, creates formative quizzes, respects course scope, and handles assessment integrity.
- **Course2MCP** provides deterministic search, source retrieval, coverage reporting, and citation-ready study context.

This is more than uploading a PDF to a chat interface. Every indexed piece of evidence retains a source hash and a precise locator such as a PDF page, PowerPoint slide, notebook cell, document paragraph range, or text line range.

## Current MVP

Course2Agent currently supports `.pdf`, `.pptx`, `.docx`, `.ipynb`, Markdown, plain text, source code, CSV/TSV, JSON/YAML, and HTML. The generated MCP server uses only the Python standard library. Building a package from PDF files additionally requires `pypdf`.

The generated MCP server exposes four tools:

- `get_course_overview`
- `search_course`
- `read_course_chunk`
- `build_study_context`

## Installation and Quick Start

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e '.[pdf]'

course2agent build examples/demo-course \
  --title 'CELL101 Foundations of Cell Biology' \
  --output dist/cell101-agent

course2agent verify dist/cell101-agent
course2agent search dist/cell101-agent 'cholesterol membrane fluidity'
```

The build command produces:

```text
dist/cell101-agent/
├── skill/cell101-foundations-of-cell-biology-course/
│   ├── SKILL.md
│   └── references/
├── mcp/server.py
├── knowledge/
│   ├── manifest.json
│   └── chunks.jsonl
├── sources/
└── USAGE.md
```

## Design Principles

1. **Course-grounded:** Course-specific claims must be retrieved from the indexed materials and accompanied by citations.
2. **Authority-aware:** Syllabi and rubrics define requirements; lectures and readings establish content; exercises indicate practice style but do not automatically define grading policy.
3. **Pedagogy-aware:** The teaching layer moves from definitions to worked examples and understanding checks instead of merely returning similar passages.
4. **Assessment-safe:** The agent can explain concepts, interpret rubrics, and provide feedback without fabricating results or impersonating the learner in assessed work.
5. **Local-first:** Building and retrieval run locally by default, without requiring an external API or embedding service.

## How It Differs from Paper2Agent

Paper2Agent primarily turns research code into scientific tools. Course2Agent turns heterogeneous educational materials into traceable evidence tools. Teaching behavior belongs in the skill, while retrieval and provenance remain deterministic. This separation allows the underlying language model to change without changing the course evidence boundary.

## Verification

```bash
python3 -m unittest discover -s tests -v
python3 /path/to/skill-creator/scripts/quick_validate.py skills/course2agent
```

The test suite covers package generation, citation-bearing search, generated-server self-testing, notebook locators, and Chinese CJK retrieval.

## Roadmap

- OCR and diagram-aware extraction
- Semantic and hybrid retrieval
- Prerequisite concept graphs and learner mastery state
- Separate instructor and student permission views
- Canvas/Moodle export and auditable update workflows

Course2Agent is an independent implementation of the architectural idea behind Paper2Agent for educational use cases. It does not copy Paper2Agent's conversion scripts.
