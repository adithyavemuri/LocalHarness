"""Shared skill instructions and workspace setup, independent of model selection."""
from __future__ import annotations

from pathlib import Path

PACK = Path(__file__).resolve().parent / "workspace"
SKILLS = PACK / ".agents/skills"
CLINE_PACK = Path(__file__).resolve().parents[1] / "integrations/cline/workspace"
OPENCODE_PACK = Path(__file__).resolve().parents[1] / "integrations/opencode/workspace"


def skill_names() -> tuple[str, ...]:
    return tuple(sorted(path.parent.name for path in SKILLS.glob("*/SKILL.md")))


def read_skill(name: str) -> str:
    if name not in skill_names():
        raise ValueError(f"Unknown skill {name!r}; choose from {', '.join(skill_names())}")
    return (SKILLS / name / "SKILL.md").read_text(encoding="utf-8")


def instructions(names: list[str]) -> str:
    """Load requested skills before inference, for a host's system/user message."""
    return "\n\n".join(read_skill(name) for name in names)


def install(workspace: Path, dry_run: bool = False, client: str = "opencode") -> list[Path]:
    if client not in ("opencode", "cline", "generic"):
        raise ValueError("Client must be opencode, cline or generic.")
    workspace = workspace.expanduser().resolve()
    if not workspace.is_dir():
        raise ValueError(f"Workspace must be an existing directory: {workspace}")
    pending = []
    # Check the entire plan before creating files, including parent conflicts.
    packs = [PACK]
    if client != "generic":
        packs.append(CLINE_PACK if client == "cline" else OPENCODE_PACK)
    sources = [(source, workspace / source.relative_to(pack))
               for pack in packs for source in sorted(pack.rglob("*")) if source.is_file()]
    for source, destination in sources:
        for path in (destination, *destination.parents):
            if path == workspace:
                break
            if path.is_symlink():
                raise ValueError(f"Refusing to write through a symlink: {path}")
            if path != destination and path.exists() and not path.is_dir():
                raise ValueError(f"Expected a directory: {path}; merge the pack manually.")
        if destination.exists():
            if not destination.is_file() or destination.read_bytes() != source.read_bytes():
                raise ValueError(f"Existing file differs: {destination}; merge the pack manually.")
        else:
            pending.append((source, destination))
    for source, destination in pending:
        if not dry_run:
            destination.parent.mkdir(parents=True, exist_ok=True)
            with destination.open("xb") as stream:
                stream.write(source.read_bytes())
    return [destination for _, destination in pending]
