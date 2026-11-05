---
name: karpathy-guidelines
description: Apply Karpathy-inspired coding guidelines when implementing, reviewing or refactoring code, with explicit assumptions, small changes and verifiable outcomes.
---

# Karpathy-inspired coding workflow

Local-model adaptation of https://github.com/multica-ai/andrej-karpathy-skills.
These are behavioral instructions, not trained capabilities or an executable
validator. Use judgment for trivial changes.

1. Before editing, state consequential assumptions and resolve ambiguities that
   would change the implementation. Explain meaningful tradeoffs.
2. Choose the smallest implementation that satisfies the request. Avoid extra
   features, speculative configuration and abstractions used only once.
3. Keep the diff tied to the task. Match existing conventions, preserve unrelated
   work, and remove only unused code created by your changes.
4. Define observable success criteria. For a bug, reproduce it; implement the
   fix and run the relevant checks. For a larger task, give a short plan with a
   verification step for each part. Report results and remaining limitations.

Do not claim that reading these guidelines proves compliance. Show the diff
and verification evidence that support the result.
