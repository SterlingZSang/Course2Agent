---
name: course2mcp
description: Build and verify a local MCP server that searches course materials, reads stable chunks, reports coverage, and assembles citation-ready study context.
---

# Course2MCP

Use the Course2Agent builder instead of inventing a separate retrieval format. The server must remain deterministic and must not require an LLM or network access at runtime.

Required tools:

- `get_course_overview`: return source inventory and coverage.
- `search_course`: return ranked excerpts with stable IDs and citations.
- `read_course_chunk`: return the complete stored text for a stable chunk ID.
- `build_study_context`: assemble a bounded, citation-ready evidence packet.

Preserve source snapshots and SHA-256 hashes in the manifest. A citation must identify the source and the best available locator: PDF page, PowerPoint slide, notebook cell, document paragraph range, or text line range.

Before delivery, run the package self-test and make at least one query whose answer is known to occur in the supplied material. Inspect that the top result contains the expected source and locator. Record extraction limits; do not claim that successful text search verifies image-only content.

