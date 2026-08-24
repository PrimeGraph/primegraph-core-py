# primegraph-core-py

`primegraph-core` — the shared cross-package vocabulary for PrimeGraph generated Python packages.

## Why this distribution exists

The PrimeGraph compiler generates one package per graph bucket. Each generated package used to carry
its own private copy of a runtime, so a type declared in that runtime existed once per package. When
one generated package handed a value to another — a model field, a raised error — the two copies were
different nominal types and the code broke: it failed to compile in Go and Swift, and in Kotlin a
`catch` silently failed to match.

This distribution holds the vocabulary that crosses package boundaries, so a graph has exactly one
nominal type per concept no matter how many generated packages it spans.

Per-bundle machinery — Firebase, HTTP transport, server helpers — stays inside the generated packages
and does **not** belong here.

There are five of these, one per target language:
`primegraph-core-ts`, `primegraph-core-go`, `primegraph-core-swift`, `primegraph-core-py`,
`primegraph-core-kt`.

## What is here

Only the declarations that must be one object per process, plus the ones that are pure declaration
and were repeated verbatim everywhere. Everything else the compiler emits — the expression helpers,
`validate_schema`, `fetch`, `parse_response`, the HTTP and Firebase transport — stays inside the
generated packages.

| Name | Why it is shared |
| --- | --- |
| `File` | pydantic validates a `BaseModel`-typed field by `isinstance` and offers no `from_attributes` fallback, so a second copy of the class makes a model in one package reject a file built by another with a `ValidationError`. |
| `DslError` | Every boundary recognises a DSL error by `isinstance(e, DslError)`. Two copies make that test `False`, so a raised error silently degrades to `INTERNAL_ERROR` and drops its typed payload. |
| `DslErrorView` | The `{code, payload}` carrier a catch binding holds and an HTTP handler annotates. |
| `coerce_error`, `error_matches`, `error_view` | The three entry points that reach `isinstance(e, DslError)`. |
| `default_error_message`, `DSL_ERROR_MESSAGES` | The text a coerced error is given when its payload leaves the slot empty. |
| `HttpResponse` | Not by identity: it is pure declaration. Every generated package that emits an HTTP step repeated the same three members and none of them ever differed. The `fetch` that fills it stays generated. |
| `transport_error_code`, `TRANSPORT_ERROR_CODES` | The SDK status → DSL code mapping the coercion consults. Both SDK imports are guarded, so this adds no dependency on `firebase-admin` or `google-api-core`. |

`validate_schema`, `fetch` and `parse_response` *raise* `DslError` but nothing tests their identity, so
they stay per-package and import `DslError` from here.

## The importable module is `primegraph_core`, not `runtime`

Distribution name: `primegraph-core`. Import name: `primegraph_core`.

The top-level module must never be called `runtime` or anything else generic. Every generated package
of a graph is installed into one environment; a generic top-level name collides between two
distributions there, and the loser is decided by `sys.path` order rather than by anything the compiler
controls.

Emitted code qualifies every shared reference — `runtime.File`, `runtime.DslErrorView[...]`,
`runtime.error_matches(...)`. To keep that qualifier without claiming the top-level name, the
distribution ships `primegraph_core/runtime.py`, so a generated module writes:

```python
from primegraph_core import runtime
```

`runtime` is then a locally bound name for `primegraph_core.runtime`, not a top-level package, and
every existing `runtime.<name>` reference site is unchanged.

## Typing

The distribution is PEP 561 typed. `src/primegraph_core/py.typed` is the marker, and it is declared in
`pyproject.toml` under `include` with `format = ["sdist", "wheel"]` — poetry ships only `*.py`
otherwise, and a wheel without the marker makes consumers see the whole package as untyped.

## Layout

```
pyproject.toml                    poetry manifest, python >=3.11
src/primegraph_core/__init__.py   public surface
src/primegraph_core/errors.py     DslError, DslErrorView and the coercion cluster
src/primegraph_core/files.py      File
src/primegraph_core/http.py       HttpResponse
src/primegraph_core/runtime.py    the same surface under the `runtime` qualifier
src/primegraph_core/py.typed      PEP 561 marker
tests/                            pytest suite
.githooks/                        Conventional Commits hook, dependency-free POSIX shell
scripts/setup.sh                  one-time clone setup
scripts/release.sh                the release procedure
```

## Setup

A fresh clone has to be pointed at the repository's own hooks once:

```sh
git config core.hooksPath .githooks
```

`sh scripts/setup.sh` does that for you.

The hook rejects any commit message that is not a Conventional Commit: `type(scope)!: subject`, one of
`build chore ci docs feat fix perf refactor revert style test`, header at most 100 characters, no
trailing period.

## Build and check

```sh
poetry install
poetry check
poetry build
poetry run pytest
poetry run mypy
```

`mypy` runs `--strict` over `src` and `tests`; the settings live in `pyproject.toml`.

## Releasing

```sh
sh scripts/release.sh 1.4.0
```

The argument is a bare semver — no leading `v`; the tag gets one. The script refuses to run on a dirty
tree, off the default branch, or when the tag already exists, and it does all of those checks before it
changes anything. It then bumps `pyproject.toml`, builds, commits `chore(release): v1.4.0`, tags and
pushes the branch and the tag.

There is no PyPI in this pipeline, so there is no upload step. Consumers install from the tag:

```toml
primegraph-core = { git = "https://github.com/PrimeGraph/primegraph-core-py.git", tag = "v1.4.0" }
```
