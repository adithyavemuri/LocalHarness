"""Install shared skills or print their instructions without starting a model."""
import argparse
from pathlib import Path
import subprocess

from . import install, instructions, skill_names


def main(default_client: str = "opencode"):
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument("--workspace", type=Path, help="Install into an existing project")
    actions.add_argument("--list", action="store_true", help="List bundled skills")
    actions.add_argument("--prompt", nargs="+", choices=skill_names(), metavar="SKILL",
                         help="Print full instructions for a CLI/browser host to load before inference")
    parser.add_argument("--client", choices=("opencode", "cline", "generic"), default=default_client,
                        help="Default: managed OpenCode; Cline adds its rules, generic copies only skills")
    parser.add_argument("--dry-run", action="store_true", help="Show new files without writing anything")
    args = parser.parse_args()
    if args.dry_run and not args.workspace:
        parser.error("--dry-run requires --workspace")
    if args.list:
        print("\n".join(skill_names()))
        return
    if args.prompt:
        print(instructions(args.prompt))
        return
    try:
        if args.client == "opencode":
            import opencode_client
            install(args.workspace, dry_run=True, client=args.client)
            opencode_client.ensure(dry_run=args.dry_run)
        paths = install(args.workspace, args.dry_run, client=args.client)
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        parser.exit(1, f"{exc}\n")
    for path in paths:
        print(f"{'Would copy' if args.dry_run else 'Copied'}: {path}")
    print(f"{len(paths)} new workspace files. Identical files are kept. No global IDE settings changes.")
    if args.client == "cline":
        print("MCP configuration is an example only; see integrations/cline/README.md.")
    elif args.client == "opencode":
        print("OpenCode setup preview." if args.dry_run else
              "OpenCode ready. Launch a model with manage_models.py --start PRESET --workspace PATH.")


if __name__ == "__main__":
    main()
