# Course2Agent: Reimagining Courses as Interactive AI Tutors

## 📖 Overview

`Course2Agent` turns course materials into grounded, interactive AI tutors. It converts syllabi, lecture notes, slides, notebooks, exercises, readings, and rubrics into two coordinated components:

- **Course2Skill** defines how the tutor explains concepts, supports revision, generates formative quizzes, follows course terminology, and respects assessment-integrity boundaries.
- **Course2MCP** provides deterministic search, source retrieval, coverage reporting, and citation-ready study context.

Every indexed excerpt retains a source hash and a precise locator such as a PDF page, PowerPoint slide, notebook cell, document paragraph range, or text line range. Course-specific claims can therefore be traced back to the supplied teaching materials.

Course2Agent is inspired by [Paper2Agent](https://github.com/jmiao24/Paper2Agent), with the workflow redesigned around teaching, learning objectives, course authority, and educational evidence.

## 🚀 Quick Start

### Basic Usage with a Coding Agent

The simplest way to use Course2Agent is to ask a skill-compatible coding agent, such as Codex or Claude Code, to install the Course2Agent skill and convert your course materials.

```text
Read https://github.com/SterlingZSang/Course2Agent and install the course2agent
skill from skills/course2agent for this coding agent.

Use the course2agent skill to convert these course materials into a cited course
skill and tested local retrieval MCP server. Follow the skill instructions for
source handling, verification, and final delivery.

Course materials: <COURSE_FILES_OR_DIRECTORY>
Course title: <COURSE_TITLE>
Output directory: <OUTPUT_DIRECTORY>
```

If the skill does not appear after installation, restart the coding agent. See [Installation & Setup](#installation) for manual installation.

### Direct CLI Usage

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

The generated MCP server is local-first and does not require an API key, embedding service, or network connection at runtime.

## 💡 Examples

### Build a Cell Biology Course Agent

```text
Use the course2agent skill to convert the materials in ./BIO101 into a course
agent at ./dist/bio101-agent. Use the title "BIO101 Cell Biology".
```

### Build from a Notebook-Based Programming Course

```text
Use the course2agent skill to convert ./python-course, including all notebooks,
exercises, and the syllabus, into ./dist/python-course-agent.
```

### Focus Retrieval on a Source Role

```bash
course2agent search dist/cell101-agent \
  'active transport and ATP' \
  --role lecture \
  --limit 5
```

<a id="installation"></a>

## ⚙️ Installation & Setup

### Prerequisites

- Python 3.10 or newer
- Git
- A coding-agent host with skill support for the agent-first workflow
- `pypdf` when building from PDF files; it is included by the `pdf` optional dependency

### Install the Project

```bash
git clone https://github.com/SterlingZSang/Course2Agent.git
cd Course2Agent
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e '.[pdf]'
```

### Install the Skill

Copy the complete skill directory, including its nested components and references.

**Codex**

```bash
mkdir -p "$HOME/.agents/skills/course2agent"
cp -R skills/course2agent/. "$HOME/.agents/skills/course2agent/"
```

**Claude Code**

```bash
mkdir -p "$HOME/.claude/skills/course2agent"
cp -R skills/course2agent/. "$HOME/.claude/skills/course2agent/"
```

Start or restart the coding agent in the directory containing your course materials, then invoke the installed skill.

## 🤖 How to Create a Course Agent

Course2Agent builds a portable package containing a course-specific teaching skill, a local MCP server, the indexed knowledge, and immutable source snapshots.

```text
dist/<course>-agent/
├── skill/<course>-course/
│   ├── SKILL.md
│   └── references/
│       ├── index.md
│       └── course-map.md
├── mcp/
│   └── server.py
├── knowledge/
│   ├── manifest.json
│   └── chunks.jsonl
├── sources/
└── USAGE.md
```

The package separates teaching behavior from evidence retrieval:

```text
Course files
    │
    ├── extraction + stable source locators
    │           │
    │           ├── Course2Skill ── teaching, revision, quizzes, boundaries
    │           │
    │           └── Course2MCP ─── search, source reading, study context
    │
    └── manifest + source snapshots + SHA-256 provenance
```

### Connect the Generated Local MCP Server

Open the generated package and follow its `USAGE.md`. The server uses stdio and only requires Python's standard library after the package has been built.

To ask a coding agent to configure it:

```text
Connect the generated Course2Agent MCP server to this coding-agent client using
its USAGE.md, then verify the connection with a real course-material search.
```

You can also test the generated server directly:

```bash
python3 dist/<course>-agent/mcp/server.py --self-test
```

## 🧰 MCP Tools

| Tool | Purpose |
| --- | --- |
| `get_course_overview` | List indexed sources, source roles, formats, and coverage. |
| `search_course` | Return ranked course excerpts with stable IDs and citations. |
| `read_course_chunk` | Read the complete stored text for one stable chunk ID. |
| `build_study_context` | Assemble a bounded, citation-ready evidence packet for a topic. |

Retrieval is deterministic and local. Teaching responses are produced by the connected coding agent using the generated course skill and retrieved evidence.

## 📚 Supported Course Materials

| Format | Locator retained in citations |
| --- | --- |
| PDF (`.pdf`) | Page number |
| PowerPoint (`.pptx`) | Slide number |
| Word (`.docx`) | Paragraph range |
| Jupyter Notebook (`.ipynb`) | Markdown or code cell number |
| Markdown and plain text | Line range |
| Python, Java, and R source | Line range |
| CSV, TSV, JSON, and YAML | Line range |
| HTML | Extracted text block |

The retrieval tokenizer supports English terms and Chinese CJK bigrams, allowing mixed-language course materials and queries.

## ✅ Verification

Run the project tests:

```bash
python3 -m unittest discover -s tests -v
```

Validate the reusable skill:

```bash
python3 /path/to/skill-creator/scripts/quick_validate.py skills/course2agent
```

Verify a generated course package:

```bash
course2agent verify dist/<course>-agent
course2agent search dist/<course>-agent '<KNOWN_TOPIC_FROM_THE_COURSE>'
```

Verification checks extraction and retrieval behavior. It does not certify the correctness of the original teaching materials or prove that image-only content was captured.

## 🎓 Teaching and Evidence Boundaries

Course2Agent applies different authority levels to different sources:

- **Syllabi and rubrics** define course requirements, learning objectives, and assessment policy.
- **Lectures and readings** establish course content and terminology.
- **Exercises and tutorials** show practice style but do not automatically define grading policy.
- **General background knowledge** may supplement an explanation, but it must not be presented as if it came from the indexed course.

The generated skill can explain concepts, create worked examples, produce formative quizzes, interpret rubrics, and provide feedback. It should not fabricate experimental results, invent unsupported course requirements, or impersonate a learner in assessed work.

## ⚠️ Current Limitations

- Image-only diagrams, scanned pages, handwriting, audio, and video are not transcribed.
- PDF extraction requires `pypdf` during the build step.
- Retrieval is lexical BM25-style search rather than embedding-based semantic search.
- Source-role detection currently uses filenames and file types; unusual naming may require manual review.
- The package records source coverage, but instructors should still review high-stakes teaching and assessment behavior.

## 🗺️ Roadmap

- OCR and diagram-aware extraction
- Semantic and hybrid retrieval
- Prerequisite concept graphs and learner mastery state
- Separate instructor and student permission views
- Canvas and Moodle import/export
- Auditable incremental updates when course materials change

## 🙏 Acknowledgements

Course2Agent is inspired by the skill-and-MCP delivery pattern introduced by [Paper2Agent](https://github.com/jmiao24/Paper2Agent). Course2Agent is an independent implementation for educational use cases and does not copy Paper2Agent's conversion scripts.

## 📄 License

Course2Agent is released under the [MIT License](LICENSE).
