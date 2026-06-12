"""Validate setuptools packaging metadata files are UTF-8 readable.

CI runs this before ``pip install -e`` so UTF-16/BOM README regressions fail fast.
"""

from __future__ import annotations

import sys
import tomllib
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _readme_path_from_pyproject(root: Path) -> Path | None:
    pyproject = root / "pyproject.toml"
    if not pyproject.is_file():
        return None
    data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    readme = data.get("project", {}).get("readme")
    if isinstance(readme, str):
        return root / readme
    if isinstance(readme, dict):
        file_name = readme.get("file")
        if isinstance(file_name, str):
            return root / file_name
    return None


def validate_packaging_utf8(root: Path | None = None) -> list[str]:
    """Return violation messages; empty list means pass."""
    project_root = root or _repo_root()
    violations: list[str] = []

    pyproject = project_root / "pyproject.toml"
    if not pyproject.is_file():
        violations.append("missing pyproject.toml")
        return violations

    try:
        pyproject.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        violations.append(f"pyproject.toml is not valid UTF-8: {exc}")

    readme_path = _readme_path_from_pyproject(project_root)
    if readme_path is None:
        violations.append("could not resolve project.readme from pyproject.toml")
        return violations
    if not readme_path.is_file():
        violations.append(f"missing packaging readme file: {readme_path.relative_to(project_root)}")
        return violations

    raw = readme_path.read_bytes()
    if raw.startswith(b"\xff\xfe") or raw.startswith(b"\xfe\xff"):
        violations.append(
            f"{readme_path.relative_to(project_root)} uses UTF-16 BOM; setuptools reads UTF-8"
        )
    try:
        readme_path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        violations.append(
            f"{readme_path.relative_to(project_root)} is not valid UTF-8: {exc}"
        )

    return violations


def main(argv: list[str] | None = None) -> int:
    _ = argv
    violations = validate_packaging_utf8()
    if violations:
        for item in violations:
            print(item, file=sys.stderr)
        return 1
    print("packaging metadata UTF-8 validation: pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
