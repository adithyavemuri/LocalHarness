# Shared skills and agent clients

OpenCode is the default agent client. Cline remains supported. Both use the
same `local_skills` module and instruction bundles for Graphify, Context7,
Karpathy guidelines and Ian/Xiaohei illustrations. Selecting Qwen, Gemma or Phi
changes the inference model, not the skill files.

## Automatic OpenCode setup and launch

From this repository, select an installed model and an existing project:

```bash
python3 manage_models.py --start qwen3.5-4b --workspace /absolute/path/to/project
```

The launcher installs the pinned OpenCode binary locally when missing, sets up
workspace skills, starts the selected model, and opens OpenCode's web interface.
Choose the intended project in OpenCode's project selector. The client receives
the local endpoint, selected model ID and allocated context automatically. All
four instruction files are loaded before inference. The owned model server is
stopped when OpenCode exits or the launcher receives Ctrl+C.

For an interactive terminal or one request with JSON event output:

```bash
python3 manage_models.py --start gemma4-e2b --workspace /path/to/project --interface terminal
python3 manage_models.py --start phi4-mini --workspace /path/to/project --prompt "Review the project README"
```

Change `--start` to `qwen3.8-27b` to use the larger model with the same module.
Its memory and inference costs still apply. `--browser` instead of `--start`
enables the installed-model router; OpenCode gets those model IDs and one model
is loaded at a time. Title generation uses the selected local model too.

Linux `start_localharness.sh` and Windows `start_localharness.ps1` also default to OpenCode.
The low-level `run_server.py` defaults to server-only operation for API clients;
pass `--client opencode` to use its managed client lifecycle. On Windows use
`python` for Python commands, or `-Client`, `-Workspace`, `-Interface` and
`-Prompt` with the PowerShell launcher. Windows runtime validation remains
deferred. Add `--dry-run` to preview without writing or downloading anything.

Setup without launching a model:

```bash
python3 setup_opencode.py --workspace /path/to/project
python3 -m local_skills --workspace /path/to/project
```

OpenCode 1.19.5 is pinned in [integrations/opencode-release.json](integrations/opencode-release.json)
to official Linux/Windows x64 baseline archives, sizes and SHA-256 hashes.
Archives go under `downloads/`; binaries, client state, cache and config go
under `runtime/opencode/`. First setup and client bootstrap require network
access; no global npm install, Node installation, root access or shell-profile
edit is performed by these scripts. OpenCode is separate upstream software;
see its [release and license](https://github.com/anomalyco/opencode/tree/v1.19.5).

Workspace setup adds `.agents/skills/` and `.opencode/local-models.json`.
Different existing files or symlinked destinations are rejected before copying.
The managed launch supplies current settings through the child process's
`OPENCODE_CONFIG_CONTENT`; no existing `opencode.json` or global Cline settings
are overwritten. Inference is restricted to the configured local provider.
OpenCode's tool permissions still apply; this is not an OS sandbox.

## Cline remains available

```bash
python3 manage_models.py --start qwen3.5-4b --client cline --workspace /path/to/project
python3 setup_cline.py --workspace /path/to/project
```

The first command starts the inference server and prepares Cline's skills/rules;
continue in the Cline IDE panel. It does not install or run OpenCode. The second
only installs the Cline integration. Existing Cline MCP configuration and IDE
provider settings remain intact. Follow the [Cline guide](integrations/cline/README.md)
to select the model ID/context and connect tools. Both client setups can coexist
in one workspace and share identical skill files.

For the previous plain llama.cpp chat, use `manage_models.py --start PRESET
--client browser`, or `start_localharness.sh --client server`. This mode has no agent
tools. The package leaves llama.cpp's built-in agent mode and UI MCP proxy
disabled; OpenCode supplies the agent/browser runtime instead.

## Tool availability and required skills

The managed OpenCode configuration registers Context7's remote MCP endpoint.
Documentation retrieval needs connectivity; inference remains local. For a
Context7 API key or other settings, add the appropriate private MCP configuration
to the project's OpenCode config rather than committing credentials.

Graphify is connected automatically when `graphify-mcp` is on the launcher's
PATH and `graphify-out/graph.json` exists in this workspace. Otherwise, install
Graphify/build the graph explicitly or configure its executable and graph path
in OpenCode's project MCP settings. The setup does not copy another project's
graph, install Graphify dependencies or build a graph silently.

Ian/Xiaohei planning produces shot lists and prompts. Image generation/editing
requires a separate connected image backend; a text model does not supply it.
Karpathy guidelines are behavioral instructions, not a correctness validator.

OpenCode's `instructions` configuration forces the four files to load. It does
not guarantee model compliance or required tool execution. A hard requirement
needs a host-side action or a check of actual tool events. Phi's currently
installed template did not produce native calls in the API probe; preloading
instructions works independently of that limitation. Treat tool use by each
model as a separately verified capability, not a consequence of a successful
text reply.

## Reuse the module elsewhere

```bash
python3 -m local_skills --list
python3 -m local_skills --prompt karpathy-guidelines graphify
python3 -m local_skills --workspace /path/to/project --client generic
```

Generic setup copies only `.agents/skills/` for other compatible agent clients.
`--prompt` prints instructions for a wrapper to supply before inference. In
Python, `from local_skills import instructions` and
`instructions(["karpathy-guidelines", "graphify"])` load the same bundled files;
unknown names fail before inference. Tool execution remains the host's job.
The inference-only `llama-cli` can accept prompt instructions but does not
become an MCP agent merely by loading them.

## Verification

Offline checks: `python3 -m unittest discover -s tests -v`.

Managed client with installed models:

```bash
python3 examples/smoke_test_opencode.py --backend vulkan
```

It starts one server at a time, checks that OpenCode can identify the four
preloaded skills, and checks server shutdown. Formatting-marker adherence is
reported separately. Results go to `logs/opencode-smoke-test.json`. This does
not establish native tool compliance, external MCP operation or browser clicks.

Locally checked on 2026-11-05: OpenCode delivered all four instruction files to
Qwen3.5-4B, Gemma 4 E2B, Phi-4-mini and Qwen3.8-27B through the installed Vulkan
runtime, using 16384 context tokens and one model at a time. Phi initially
omitted the formatting marker while naming the skills; the focused rerun passed
both checks. Its separate native-tool limitation remains. The OpenCode web
server also passed HTTP health, HTML and local-provider/instruction-configuration
checks; GUI clicking and Windows end-to-end operation were not tested.

For native tool round-trips against a running server use
`examples/smoke_test_skills.py --model MODEL_ID`. The pinned runtime accepts
`tool_choice: "required"`; a named-function object is treated as `auto` by this
pin. The probe rejects prose claims without an actual call. The router variant
is `examples/smoke_test_router.py --skills --models PRESET ...`, with 4096 tokens
per model. Neither API probe establishes the quality of skill outputs.
