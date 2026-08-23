"""Shared cross-package vocabulary for PrimeGraph generated Python packages.

The module is deliberately named ``primegraph_core`` and not ``runtime``: a
generic top-level name collides as soon as two distributions are installed into
one environment, and every generated package of a graph shares that
environment.

``PRIMEGRAPH_CORE`` is a placeholder public surface so the distribution builds
before the shared vocabulary is migrated here.
"""

PRIMEGRAPH_CORE: str = "primegraph-core"

__all__ = ["PRIMEGRAPH_CORE"]
