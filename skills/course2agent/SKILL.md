---
name: course2agent
description: Convert course materials such as syllabi, lecture notes, slides, PDFs, notebooks, exercises, and rubrics into a cited course skill and tested retrieval MCP server. Use to create or refresh a grounded teaching agent for a course; not for answering from a single file without building an agent.
---

# Course2Agent

Turn supplied course materials into two coordinated components:

- Follow [Course2Skill](course2skill/SKILL.md) to preserve course structure, citations, teaching behavior, and evidence boundaries.
- Follow [Course2MCP](course2mcp/SKILL.md) to build and verify deterministic retrieval tools over those materials.

Use the project CLI as the supported builder:

```bash
course2agent build <FILES_OR_DIRECTORIES...> --title '<COURSE TITLE>' --output '<OUTPUT_DIR>'
course2agent verify '<OUTPUT_DIR>'
```

Read [the output contract](references/output-contract.md) before delivery. Keep source files immutable and build into a new or empty output directory. Never place credentials, answer keys from restricted systems, student records, or private feedback into a deliverable unless the user explicitly supplied and authorized those materials for this purpose.

The combined output is:

```text
<course>-agent/
├── skill/<course>-course/
├── mcp/server.py
├── knowledge/
├── sources/
└── USAGE.md
```

Report the package path, indexed formats and coverage, verification result, and material limitations. Treat successful extraction as text coverage only; image-only diagrams, handwritten annotations, audio, and video require separate review or transcription.
