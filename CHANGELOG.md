# Changes

## LocalHarness rename — unreleased

- Renamed the project from qwen-local to LocalHarness, including repository URLs,
  setup examples and documentation.
- Added `setup_localharness.sh` / `.ps1` and `start_localharness.sh` / `.ps1`
  as the primary commands; existing Qwen-named commands forward to them.
- Kept existing checkout paths, model preset names and `QWEN_*` environment
  variables compatible. OpenCode remains the default, and Cline remains supported.

## Shared skills and OpenCode default — unreleased

- Added a model-independent `local_skills` module for Qwen, Gemma and Phi.
- Made OpenCode the model-manager and start-script default, with a pinned,
  checksum-verified Linux/Windows x64 installation below the package directory.
- Added automatic local-provider/context setup, preloaded skill instructions,
  web/terminal/one-shot interfaces, Context7 registration and local Graphify detection.
- Retained explicit Cline setup/launch and the original plain browser/API mode.
- Added offline integration checks and real installed-model client probes.
- Kept native model tool compliance separate from instruction loading; Phi's
  current GGUF template failed the native skill-call probe.

## 64K preferred context — unreleased

- Raised the preferred context to 65,536 tokens, with 32K/16K/8K fallbacks.
- Updated launch messages, model defaults and client-configuration guidance.
- Added regression checks for 64K selection, 32K fallback and cache scaling.
- No cache quantization, concurrency or custom offload algorithm was added.

## Automatic context preflight — unreleased

- Changed catalog preferred contexts from 4K to 32K.
- Added standard-library GGUF metadata reading and model-specific FP16 cache
  estimates, free-RAM/device probes, conservative margins and 16K/8K fallbacks.
- Reported full-GPU, CPU and partial-offload estimates separately; unsupported
  models cannot silently receive a claimed-safe automatic plan.
- Fixed router context overrides and added independent per-model contexts.
- Added `--context-report` (no downloads/model loading/config writes), retained
  explicit `--context` overrides and added offline analytical/regression tests.
- Documented formula sources, safety assumptions, IDE context matching and
  untested Windows hardware/runtime behavior. No driver changes are involved.

## Multi-model beta update — 2026-10-22

- Added selectable, pinned Qwen3.5-4B, Gemma 4 E2B and Phi-4-mini weights.
- Retained Qwen3.8-27B and Qwen3-30B-A3B catalog entries.
- Added a cross-platform terminal menu with explicit download consent, model
  notes, installed status, disk space and hardware cautions.
- Added native browser routing between installed models, with one model loaded
  at a time, offline mode and a project-local cache.
- Added optional rootless, checksum-pinned Linux Vulkan binaries; drivers and
  system libraries are not changed. CPU operation remains available.
- Pinned model sizes/hashes, runtime source commit, GPU archive and portable
  CMake archive. Upstream browser-asset provisioning remains an external dependency.
- Added offline regression tests, reusable real-model examples and Linux CI.
- Kept Windows x64 scripts and syntax checks; real Windows installation and
  runtime validation are explicitly deferred. Windows GPU setup is not provided.
- Kept the historical script names and QWEN_* variables for compatibility.

No autonomous agent framework, model collaboration controller, filesystem
tools or GitHub permissions are enabled by this update.
