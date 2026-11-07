# Copyright 2025-2026 hingebase

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied. See the License for the specific language governing
# permissions and limitations under the License.

"""Type checking and linting."""

import runpy
import subprocess  # ruff: ignore[suspicious-subprocess-import]
import sys

import pytest


def test_basedpyright(monkeypatch: pytest.MonkeyPatch) -> None:
    """Type checking with basedpyright.

    Raises:
        subprocess.CalledProcessError: type checking fails.

    """
    argv = ["basedpyright", "--pythonpath", sys.executable]
    monkeypatch.setattr(sys, "argv", argv)
    try:
        runpy.run_module("basedpyright", run_name="__main__")
    except SystemExit as e:
        returncode = e.code
        assert isinstance(returncode, int)
        if returncode:
            raise subprocess.CalledProcessError(returncode, argv) from None


@pytest.mark.skipif(sys.platform == "darwin", reason="pyrefly is unavailable")
def test_pyrefly() -> None:
    """Type checking with pyrefly."""
    _run(["pyrefly", "check"])


@pytest.mark.skipif(sys.platform == "darwin", reason="pyrefly is unavailable")
def test_pyrefly_coverage() -> None:
    """Type coverage checking with pyrefly."""
    _run(["pyrefly", "coverage", "check", "--strict"])


def test_ruff() -> None:
    """Linting with Ruff."""
    _run(["ruff", "check", "--ignore", "FIX002"])


def test_tombi() -> None:
    """Linting with Tombi."""
    _run(["tombi", "lint"])


def test_ty() -> None:
    """Type checking with ty."""
    argv = ["ty", "check", "--python", sys.executable]
    if sys.platform == "darwin":
        argv += ("--ignore", "unresolved-attribute")
    _run(argv)


def _run(args: list[str]) -> None:
    subprocess.run(args, check=True)  # ruff: ignore[subprocess-without-shell-equals-true]
