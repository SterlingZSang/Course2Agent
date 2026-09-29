# Course2Agent output contract

## Required files

- `skill/<slug>-course/SKILL.md`: teaching and grounding behavior.
- `skill/<slug>-course/references/index.md`: source inventory.
- `skill/<slug>-course/references/course-map.md`: source roles and course structure.
- `mcp/server.py`: standalone standard-library stdio MCP server.
- `knowledge/manifest.json`: package metadata, hashes, formats, roles, and limits.
- `knowledge/chunks.jsonl`: stable citation-bearing evidence chunks.
- `sources/`: immutable snapshots used to build the package.
- `USAGE.md`: startup, connection, provenance, and limitations.

## Delivery checks

1. The manifest counts match the stored sources and chunks.
2. Every chunk names an existing source ID and has a non-empty locator and citation.
3. `python3 mcp/server.py --self-test` exits successfully.
4. One representative search returns the expected evidence and locator.
5. No absolute source paths, credentials, or hidden temporary files appear in the package.

## Evidence boundary

The package verifies extraction and retrieval, not instructional correctness of the original material. It does not certify that all visual, audio, or handwritten information was captured. State those limits in the delivery report.

