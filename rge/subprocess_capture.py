"""Safe subprocess output capture for operator and verify runners."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Mapping


def run_captured(
    argv: list[str],
    *,
    cwd: str | Path | None = None,
    env: Mapping[str, str] | None = None,
    check: bool = False,
) -> subprocess.CompletedProcess[str]:
    """Run a subprocess and capture stdout/stderr as UTF-8 text.

    Uses ``errors=\"replace\"`` so Windows npm/Next.js output that is not valid
    in the locale default encoding (cp1252) does not crash reader threads.
    """
    return subprocess.run(
        argv,
        cwd=cwd,
        env=env,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=check,
    )
