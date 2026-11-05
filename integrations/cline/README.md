# Cline with local models and skills

OpenCode is the package default; this Cline integration remains fully available.
Use `manage_models.py --start PRESET --client cline --workspace PATH`, or the
setup-only commands below. Cline setup does not install OpenCode.

Use Cline as the agent client and the existing llama.cpp server for inference.
The server's browser remains text chat. Cline supplies file, terminal and MCP
tools under its own approval settings; no server agent flag needs changing.

The pack contains compact local-model adapters for Graphify, Context7,
Karpathy-inspired coding guidelines and Ian/Xiaohei illustration planning.
The adapters are supplied by the model-independent [local_skills module](../../SKILLS.md),
so Qwen, Gemma and Phi share the same skills when switching models.
These are maintained adapters, not full copies of the upstream Claude/Codex
plugins. They do not install runtimes, credentials, MCP connections or an image
model. Source projects:

- https://github.com/Graphify-Labs/graphify
- https://github.com/upstash/context7
- https://github.com/multica-ai/andrej-karpathy-skills
- https://github.com/tojileon/ian-xiaohei-illustrations-en

## Install in the workspace Cline actually opens

From this repository, with Python 3.10+:

```bash
python3 setup_cline.py --workspace /absolute/path/to/your/project --dry-run
python3 setup_cline.py --workspace /absolute/path/to/your/project
```

Windows: use `python` and a Windows workspace path. No pip dependencies or
network requests are needed. The workspace must exist. The installer checks
all destinations first and refuses conflicting files or symlinked destinations;
identical files are kept on rerun. If `.clinerules` is an existing file, merge
the bundled rule into it and copy the other files manually. It never edits
`AGENTS.md`, `CLAUDE.md`, VS Code settings or Cline's global MCP settings.

Files installed:

```text
.agents/skills/{graphify,context7,karpathy-guidelines,ian-xiaohei-illustrations}/
.clinerules/10-local-skills.md
.cline/local-models.mcp.example.json
```

Cline discovers workspace skills in `.agents/skills/`. Open its Skills tab
(under the rules/workflows control) and enable the four skills. Start a fresh
task after installation; reload the VS Code window if discovery has not refreshed.
Check for same-name skills in other supported directories: Cline may prefer
those over this pack. Keep one intended version enabled. The installed Cline
4.1.26 bundle was checked for discovery support; a full Cline UI run has not
been automated here. See [Cline skills](https://docs.cline.bot/customization/skills).

## Connect the model server

Start one installed model from this repository:

```bash
./start_localharness.sh --client cline --preset qwen3.5-4b --thinking off
```

Windows: `.\start_localharness.ps1 -Client cline -ModelPreset qwen3.5-4b -Thinking off`.
Router mode also works, using an installed catalog preset as the request model;
validate each model separately because tool calling depends on its chat template
and instruction-following ability.

In Cline, select **OpenAI Compatible** and set:

| Setting | Value |
| --- | --- |
| Base URL | `http://127.0.0.1:8080/v1` |
| Model ID | The ID returned by `GET http://127.0.0.1:8080/v1/models`; router mode uses the catalog preset |
| API key, if the UI requires one | A dummy value such as `local`; default server authentication is not configured |
| Context window | The selected model's allocated context from the startup report |
| Images | Off for this text-only setup |
| Tool calling, if exposed by your version | Enable, then verify with a real task |

Set both Plan and Act configurations if Cline uses separate providers. A client
context setting cannot resize the server. Avoid auto-approval changes during
setup. See [Cline's provider guide](https://docs.cline.bot/provider-config/openai-compatible).

## Connect Graphify and Context7

The copied `.cline/local-models.mcp.example.json` is a template, **not an
automatically loaded workspace configuration**. In Cline, open MCP Servers →
Configure → Configure MCP Servers. Merge the desired entries into its existing
`mcpServers` object; preserve unrelated entries and existing credentials.

- **Graphify:** use an already installed `graphify-mcp` executable, with an
  absolute path to this project's `graphify-out/graph.json`. Replace both
  template paths, then set `disabled` to `false`. A virtual environment path
  works on Linux or Windows; JSON paths on Windows can use forward slashes.
  This repo does not install Graphify's separate dependencies. For an offline
  code graph, run `graphify extract . --code-only` from the target project with
  `GRAPHIFY_BACKEND=none` in the process environment. Existing graph creation
  should be an explicit action, not a side effect of launching chat.
- **Context7:** set `disabled` to `false` to connect to the hosted documentation
  service. For higher rate limits, add an `Authorization: Bearer YOUR_API_KEY`
  header in your private Cline settings, following the
  [upstream setup](https://github.com/upstash/context7). Keep credentials out of
  this example and version control. Documentation queries leave the machine
  even though inference is local.

Both entries start disabled and have an empty `autoApprove` list. Confirm that
each enabled server connects and advertises its tools in Cline. This chat's MCP
connections do not automatically become Cline connections. See
[Cline MCP configuration](https://docs.cline.bot/mcp/mcp-overview).

## Automatic selection and explicit requirements

With skills enabled, Cline exposes their metadata and the model can select
relevant workflows. The installed rule also asks for Karpathy guidelines during
coding, graph queries for architecture questions and Context7 for library APIs.

Use a skill slash command for explicit selection, for example `/graphify` or
`/ian-xiaohei-illustrations`, from Cline's command suggestions. This loads the
instructions without waiting for automatic selection. If your version does not
offer skill commands, explicitly ask it to load the named SKILL.md.

For an explicit tool requirement, use a prompt such as:

> Load graphify and karpathy-guidelines. Before changing code, query this
> project's graph. If the graph or tool is missing, stop and report it. Include
> the actual tool result in your explanation.

These requirements are instructions to Cline and the model, **not a hard
execution gate**. Slash selection loads a skill; it does not guarantee tool use,
correctness or compliance with every instruction. Verify the tool events and
results in Cline's transcript. Enforcing arbitrary required tools regardless of
model behavior would require a separate controller or validated Cline hooks,
which this integration does not add.

Claude/Codex `SKILL.md` bundles containing portable instructions can also be
copied into `.agents/skills/<name>/`, keeping their supporting files and license.
Host-specific tools, hooks, permissions and image services still need adapters.
Do not expect copying a skill to provide those capabilities.

## Illustrations

Try `/ian-xiaohei-illustrations` followed by a short article and a request for
two scene ideas. The local text model can create the shot list and image prompts.
Actual image generation/editing needs a separately connected image tool. This
pack supplies no image backend and never treats prompts as rendered PNGs. The
full upstream skill assumes Codex's `image_gen`, which Cline does not acquire
by loading the file. Existing scientific plots should use plotting tools when
numerical accuracy matters.

## Verify the setup

First run the bounded API probe with the server already running:

```bash
python3 examples/smoke_test_skills.py --model YOUR_ADVERTISED_MODEL_ID
```

It checks automatic tool selection and a forced function call, reads only the
bundled Karpathy skill, supplies the result to the model, and requires a final
answer. Its JSON report goes to `logs/skills-smoke-test.json`. It does not execute
commands or call external services. A passing API probe does not establish
Cline compatibility, general coding quality or model compliance.

The original Qwen probe's named-function selection was treated as automatic by
the pinned runtime. The probe now uses its supported `"required"` string and has
a regression check for this contract. Live Cline UI activation, external MCP
calls and image generation require separate validation.

Then verify in a fresh Cline task:

1. Use `/karpathy-guidelines` for a small code review. Confirm skill loading.
2. Ask a scoped architecture question with `/graphify`. Confirm a real query
   against this workspace's graph and inspect the cited source.
3. Use `/context7` for an API question. Confirm resolution and documentation
   calls, not merely a statement that documentation was consulted.
4. Request an illustration plan. Without an image tool, expect prompts and an
   explicit generation limitation rather than claimed image files.

Model or template failures must be reported for the tested preset. Do not infer
that a successful text-chat smoke test establishes tool support for all models.
