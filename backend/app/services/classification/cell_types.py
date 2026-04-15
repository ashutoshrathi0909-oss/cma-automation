"""Loader for DOCS/cma_cell_types.json.

Single source of truth for cell-type metadata used by agent prompts, the
output validator, and excel_generator. Loads once at first access and
caches thereafter.
"""
from __future__ import annotations

import json
from pathlib import Path

_CELL_TYPES_PATH = Path(__file__).resolve().parents[4] / "DOCS" / "cma_cell_types.json"

_cache: dict | None = None


def load() -> dict:
    """Return the full cell_types structure. Cached after first call."""
    global _cache
    if _cache is None:
        if not _CELL_TYPES_PATH.exists():
            raise FileNotFoundError(
                f"cma_cell_types.json not found at {_CELL_TYPES_PATH}. "
                "Run: python scripts/derive_cma_cell_types.py"
            )
        _cache = json.loads(_CELL_TYPES_PATH.read_text(encoding="utf-8"))
    return _cache


def _reset_cache() -> None:
    """Test helper — clears the module cache."""
    global _cache
    _cache = None


def get_agent_context(agent_key: str) -> dict:
    data = load()
    agents = data.get("agents", {})
    if agent_key not in agents:
        raise KeyError(f"Unknown agent key '{agent_key}'. Known: {list(agents.keys())}")
    return agents[agent_key]


def is_valid_target(agent_key: str, row: int) -> bool:
    try:
        ctx = get_agent_context(agent_key)
    except KeyError:
        return False
    return row in ctx["valid_rows"]


def valid_rows_csv(agent_key: str) -> str:
    ctx = get_agent_context(agent_key)
    return ", ".join(str(r) for r in ctx["valid_rows"])


def section_tree(agent_key: str) -> str:
    return get_agent_context(agent_key)["section_tree"]


_SHARED_NOTES_PRIMARY_PATH = (
    Path(__file__).parent / "agents" / "prompts" / "_shared_notes_primary.md"
)


def shared_notes_primary() -> str:
    """Return the shared Notes-Primary rule block, read fresh each call.

    Kept uncached so the prompt can be edited without restarting the worker
    during development. Cost is a single small file read per agent init.
    """
    return _SHARED_NOTES_PRIMARY_PATH.read_text(encoding="utf-8")
