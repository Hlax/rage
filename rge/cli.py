"""``research`` CLI entry point.

Phase 0 scaffold: subcommands exist, import cleanly, and show help, but the
pipeline behavior behind them is not implemented yet. Placeholders print a
machine-readable status and exit non-zero so nothing can mistake them for a
working pipeline.

Constraints honored here: no network calls, no database requirement, no live
Ollama requirement, and no public-data writes.
"""

from __future__ import annotations

import argparse
import json
import sys

from rge import __version__

_NOT_IMPLEMENTED_EXIT_CODE = 2


def _not_implemented(command: str, phase_hint: str) -> int:
    payload = {
        "status": "not_implemented",
        "command": command,
        "phase": "0",
        "detail": f"'{command}' is a Phase 0 placeholder. {phase_hint}",
    }
    print(json.dumps(payload, indent=2))
    return _NOT_IMPLEMENTED_EXIT_CODE


def _cmd_run(args: argparse.Namespace) -> int:
    return _not_implemented(
        "run",
        "Fixture-mode research runs arrive with the Phase 3 local research MVP "
        f"(requested topic={args.topic!r}, domain={args.domain!r}, "
        f"fixture_mode={args.fixture_mode}).",
    )


def _cmd_export_public(args: argparse.Namespace) -> int:
    return _not_implemented(
        "export-public",
        "Public-safe card export arrives with Phase 4 "
        f"(requested limit={args.limit}).",
    )


def _cmd_verify(_args: argparse.Namespace) -> int:
    return _not_implemented(
        "verify",
        "Deterministic verification suite arrives with later phases; "
        "use 'pytest tests/golden' for the current scaffold checks.",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="research",
        description=(
            "Research Graph Engine CLI. Local-first research infrastructure: "
            "sources -> scoped claims -> concept graph -> evidence graph -> "
            "reports/cards -> improvement tickets."
        ),
    )
    parser.add_argument("--version", action="version", version=f"research {__version__}")
    subparsers = parser.add_subparsers(dest="command")

    run_parser = subparsers.add_parser(
        "run",
        help="Run a research workflow for a topic (placeholder in Phase 0).",
        description="Run a research workflow for a topic. Placeholder in Phase 0.",
    )
    run_parser.add_argument("--topic", help="Root research topic.")
    run_parser.add_argument("--domain", help="Domain pack ID (e.g. creativity).")
    run_parser.add_argument(
        "--fixture-mode",
        action="store_true",
        help="Use deterministic fixture sources instead of live discovery.",
    )
    run_parser.set_defaults(func=_cmd_run)

    export_parser = subparsers.add_parser(
        "export-public",
        help="Export public-safe card JSON (placeholder in Phase 0).",
        description="Export public-safe card JSON. Placeholder in Phase 0.",
    )
    export_parser.add_argument(
        "--limit", type=int, default=100, help="Maximum records to export."
    )
    export_parser.set_defaults(func=_cmd_export_public)

    verify_parser = subparsers.add_parser(
        "verify",
        help="Run deterministic verification checks (placeholder in Phase 0).",
        description="Run deterministic verification checks. Placeholder in Phase 0.",
    )
    verify_parser.set_defaults(func=_cmd_verify)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "command", None):
        parser.print_help()
        return 0
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
