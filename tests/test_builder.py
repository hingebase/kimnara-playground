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

"""Test `kimnara-playground-builder`."""

import io
import pathlib
import sys

import pydantic.alias_generators


def test_discovered_compilers() -> None:
    """Check the content of `discovered-compilers.json`."""
    compilers = {
        compiler.id: compiler.full_version
        for compiler in pydantic.TypeAdapter(
            list[_DiscoveredCompiler],
        ).validate_json(
            pathlib.Path("compiler-explorer", "discovered-compilers.json")
                .read_text("utf-8"),
        )
    }
    for id_ in "gcc", "cgcc", "clang", "cclang":
        assert id_ in compilers
    if sys.platform != "darwin":
        for id_ in "intel", "cintel":
            assert id_ in compilers
        if sys.platform == "win32":
            for id_ in "msvc", "cmsvc":
                assert id_ in compilers
    _library_states(
        compilers["nb057"],
        svml=not sys.platform.startswith("linux"),
    )
    for id_ in "nb058", "nb059", "nb060":
        _library_states(compilers[id_], svml=True)
    for id_ in "nb061", "nb062":
        _library_states(compilers[id_])
    if sys.platform != "darwin":
        for minor in range(63, 69):
            _library_states(compilers[f"nb0{minor}"])


class _DiscoveredCompiler(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(
        alias_generator=pydantic.alias_generators.to_camel,
        extra="ignore",
    )

    id: str
    full_version: str


def _library_states(full_version: str, *, svml: bool = False) -> None:
    svml_visited = [0, 0, 0, 0]
    tbb_visited = 0
    openmp_visited = 0
    with io.StringIO(full_version) as f:
        for line in f:
            if line.startswith("SVML State, config.USING_SVML"):
                svml_visited[0] += 1
                assert line.rstrip().endswith(": True" if svml else ": False")
            elif line.startswith("SVML Library Loaded"):
                svml_visited[1] += 1
                assert line.rstrip().endswith(": True" if svml else ": False")
            elif line.startswith("llvmlite Using SVML Patched LLVM"):
                svml_visited[2] += 1
                assert line.rstrip().endswith(": True" if svml else ": False")
            elif line.startswith("SVML Operational"):
                svml_visited[3] += 1
                assert line.rstrip().endswith(": True" if svml else ": False")
            elif line.startswith("TBB Threading Layer Available"):
                tbb_visited += 1
                assert line.rstrip().endswith(": True")
            elif line.startswith("OpenMP Threading Layer Available"):
                openmp_visited += 1
                assert line.rstrip().endswith(": True")
    assert svml_visited == [1, 1, 1, 1]
    assert tbb_visited == 1
    assert openmp_visited == 1
