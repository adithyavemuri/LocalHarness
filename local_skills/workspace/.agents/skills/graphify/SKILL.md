---
name: graphify
description: Use an existing workspace knowledge graph for codebase architecture, dependencies and change impact, or build a local code graph when requested.
---

# Graphify with a local model

Integration adapter for https://github.com/Graphify-Labs/graphify. The Graphify
runtime and a graph are separate prerequisites; installing this skill installs
neither. This adapter is community maintained and not affiliated with Graphify Labs.

Prefer the connected Graphify MCP tools when available. Read their schemas
instead of guessing tool names. Confirm the graph belongs to the requested
workspace; pass its absolute project path when the tool supports it. A server
connected to another project's graph is not evidence about this project.

For architecture questions, make a scoped query with a small output budget,
then inspect the returned source files to verify important relationships. Use
neighbors or paths for focused follow-ups. Graph absence, empty results and
stale sources are limitations to report, not permission to invent edges.

If using the local CLI instead, run from the target workspace:

```bash
graphify query "the specific architecture question" --budget 2000
```

When the user requests graph creation, an installed Graphify supports local
code extraction with `graphify extract . --code-only`. Run with
`GRAPHIFY_BACKEND=none` in the child environment to prevent cloud semantic or
labeling calls. Read the installed CLI help if its options differ. Graph creation
writes `graphify-out/`; it does not install hooks or modify agent configuration.

If Graphify is optional and unavailable, report that fact and use scoped source
searches. If it is explicitly required, stop the graph-dependent work and state
which runtime, connection or graph is missing.
