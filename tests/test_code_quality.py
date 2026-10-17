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

import contextlib
import importlib.metadata
import os
import pathlib
import runpy
import subprocess  # ruff: ignore[suspicious-subprocess-import]
import sys
import sysconfig
from typing import TYPE_CHECKING, NoReturn

import pytest

if TYPE_CHECKING:
    from collections.abc import Generator

if sys.platform == "win32":
    from contextlib import (
        nullcontext as _astral_context,
    )
else:
    @contextlib.contextmanager
    def _astral_context(monkeypatch: pytest.MonkeyPatch) -> Generator[object]:
        def execvp(executable: str, args: list[str]) -> NoReturn:
            nonlocal patched
            patched = True
            sys.exit(subprocess.call(args, executable=executable))  # ruff: ignore[subprocess-without-shell-equals-true]
        patched = False
        monkeypatch.setattr(os, "execvp", execvp)
        try:
            yield
        finally:
            assert patched


def test_basedpyright(monkeypatch: pytest.MonkeyPatch) -> None:
    """Type checking with basedpyright."""
    argv = ["basedpyright", "--pythonpath", sys.executable]
    monkeypatch.setattr(sys, "argv", argv)
    _run_module("basedpyright")


@pytest.mark.skipif(sys.platform == "darwin", reason="pyrefly is unavailable")
def test_pyrefly(monkeypatch: pytest.MonkeyPatch) -> None:
    """Type checking with pyrefly."""
    _run_module_or_executable(["pyrefly", "check"], monkeypatch)


@pytest.mark.skipif(sys.platform == "darwin", reason="pyrefly is unavailable")
def test_pyrefly_coverage(monkeypatch: pytest.MonkeyPatch) -> None:
    """Type coverage checking with pyrefly."""
    argv = ["pyrefly", "coverage", "check", "--strict"]
    _run_module_or_executable(argv, monkeypatch)


def test_ruff(monkeypatch: pytest.MonkeyPatch) -> None:
    """Linting with Ruff."""
    argv = ["ruff", "check", "--ignore", "FIX002"]
    _run_module_or_executable(argv, monkeypatch)


def test_tombi() -> None:
    """Linting with Tombi."""
    tombi = "tombi" + sysconfig.get_config_var("EXE")
    try:
        dist = importlib.metadata.distribution("tombi")
    except ModuleNotFoundError:
        pass
    else:
        if paths := dist.files:
            for p in paths:
                if os.path.normcase(p.name) == tombi:
                    match dist.locate_file(p):
                        case pathlib.Path() as tombi:
                            break
                        case _:
                            break
    subprocess.run([tombi, "lint"], check=True)  # ruff: ignore[subprocess-without-shell-equals-true]


def test_ty(monkeypatch: pytest.MonkeyPatch) -> None:
    """Type checking with ty."""
    argv = ["ty", "check", "--python", sys.executable]
    _run_module_or_executable(argv, monkeypatch)


def _run_module(module_name: str) -> None:
    try:
        runpy.run_module(module_name, run_name="__main__")
    except SystemExit as e:
        code = e.code
    else:
        return
    assert code == 0


def _run_module_or_executable(
    args: list[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module_name = args[0]
    try:
        importlib.metadata.distribution(module_name)
    except ModuleNotFoundError:
        subprocess.run(args, check=True)  # ruff: ignore[subprocess-without-shell-equals-true]
    else:
        monkeypatch.setattr(sys, "argv", args)
        if module_name == "pyrefly":
            _run_module("pyrefly")
        else:
            with _astral_context(monkeypatch):
                _run_module(module_name)
