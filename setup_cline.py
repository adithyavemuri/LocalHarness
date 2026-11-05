#!/usr/bin/env python3
"""Compatibility entry point for the shared skills module's Cline setup."""
from local_skills import install as install_shared
from local_skills.__main__ import main


def install(workspace, dry_run=False):
    return install_shared(workspace, dry_run=dry_run, client="cline")


if __name__ == "__main__":
    main(default_client="cline")
