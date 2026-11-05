---
name: context7
description: Fetch current library or framework documentation with Context7 when coding depends on API syntax, setup, configuration or version-specific behavior.
---

# Context7 with a local model

Integration adapter for https://github.com/upstash/context7. Context7 is a
documentation service, accessed through MCP here. Running inference locally
does not make its documentation requests offline.

1. Identify the library, relevant version and one specific API question.
2. Use the connected Context7 library-resolution tool to obtain a library ID.
   If the user already supplies a valid Context7 library ID, use it directly.
3. Query documentation with that ID and a focused question. Use the tool names
   and parameters actually advertised by the connection; hosts may rename them.
4. Apply the returned version-appropriate guidance and cite its source links.
   Distinguish documentation evidence from your own inference.

Keep queries free of credentials, private source code and unnecessary project
details. Missing matches or connection errors do not establish API behavior.
If Context7 is required, report the missing dependency and stop the affected
implementation. Otherwise disclose the failure before using official docs or
local source as a fallback.
