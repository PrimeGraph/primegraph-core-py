"""The import surface: exact export names, and no top-level ``runtime``."""

from __future__ import annotations

import importlib
import tomllib
from pathlib import Path

import pytest

import primegraph_core
from primegraph_core import runtime

EXPECTED = [
    "DSL_ERROR_MESSAGES",
    "TRANSPORT_ERROR_CODES",
    "DslError",
    "DslErrorView",
    "File",
    "HttpResponse",
    "coerce_error",
    "default_error_message",
    "error_matches",
    "error_view",
    "transport_error_code",
]


def test_the_exported_names_are_exactly_the_ones_the_emitter_will_reference() -> None:
    assert sorted(primegraph_core.__all__) == sorted(EXPECTED)
    for name in EXPECTED:
        assert hasattr(primegraph_core, name), name


def test_the_runtime_qualifier_is_a_submodule_not_a_top_level_package() -> None:
    # `from primegraph_core import runtime` binds the qualifier emitted code
    # already writes, without any distribution claiming the top-level name.
    assert runtime.__name__ == "primegraph_core.runtime"


def test_the_runtime_qualifier_exposes_the_very_same_objects() -> None:
    for name in EXPECTED:
        assert getattr(runtime, name) is getattr(primegraph_core, name), name


def test_the_submodules_expose_the_same_objects_as_the_package() -> None:
    errors = importlib.import_module("primegraph_core.errors")
    files = importlib.import_module("primegraph_core.files")
    http = importlib.import_module("primegraph_core.http")

    assert errors.DslError is primegraph_core.DslError
    assert files.File is primegraph_core.File
    assert http.HttpResponse is primegraph_core.HttpResponse


def test_the_manifest_ships_one_package_and_it_is_not_generic() -> None:
    manifest = Path(__file__).resolve().parent.parent / "pyproject.toml"
    if not manifest.is_file():  # pragma: no cover - installed-only run
        pytest.skip("the manifest is not part of an installed distribution")

    packages = tomllib.loads(manifest.read_text())["tool"]["poetry"]["packages"]

    assert [p["include"] for p in packages] == ["primegraph_core"]


def test_the_pep_561_marker_sits_next_to_the_module() -> None:
    assert primegraph_core.__file__ is not None

    assert (Path(primegraph_core.__file__).parent / "py.typed").is_file()
