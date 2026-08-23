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

## Status

Scaffolding only. No shared declarations have been migrated yet; `src/primegraph_core/__init__.py`
holds a single placeholder so the distribution has something to build.

## The importable module is `primegraph_core`, not `runtime`

Distribution name: `primegraph-core`. Import name: `primegraph_core`.

The top-level module must never be called `runtime` or anything else generic. Every generated package
of a graph is installed into one environment; a generic top-level name collides between two
distributions there, and the loser is decided by `sys.path` order rather than by anything the compiler
controls.

## Typing

The distribution is PEP 561 typed. `src/primegraph_core/py.typed` is the marker, and it is declared in
`pyproject.toml` under `include` with `format = ["sdist", "wheel"]` — poetry ships only `*.py`
otherwise, and a wheel without the marker makes consumers see the whole package as untyped.

## Layout

```
pyproject.toml                    poetry manifest, python >=3.11
src/primegraph_core/__init__.py   public surface
src/primegraph_core/py.typed      PEP 561 marker
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

## Build

```sh
poetry check
poetry build
```

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
