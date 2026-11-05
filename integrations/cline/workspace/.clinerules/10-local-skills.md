# Local model skills

Use the installed skills through Cline's skill loader, or read their SKILL.md
under `.agents/skills/` if the loader is unavailable. Load only relevant skills.

- Coding, review or refactoring: load `karpathy-guidelines` before editing.
- Codebase architecture or dependencies: load `graphify`; query a graph for
  this workspace before broad source searches when that graph is available.
- Library/API setup or usage: load `context7` and retrieve relevant docs before
  relying on remembered APIs.
- Explicit Ian/Xiaohei illustration requests: load `ian-xiaohei-illustrations`.
  This style is optional; do not apply it to unrelated image requests.

When the user explicitly requires a skill or tool, load the skill and execute
its applicable tool steps. If a required dependency is unavailable, identify it
and stop the dependent work. Do not substitute a claimed tool result. Optional
tools may fall back to source inspection or a clearly labeled plan.

Report which tools actually ran, which sources they returned, and any blocked
steps. A skill being loaded is not evidence that its tools ran. Keep normal
Cline approval settings; these instructions do not grant extra permissions.
