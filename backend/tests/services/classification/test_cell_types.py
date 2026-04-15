"""Tests for backend/app/services/classification/cell_types.py."""
from __future__ import annotations
import pytest
from app.services.classification import cell_types


@pytest.fixture(autouse=True)
def _reset_module_cache():
    cell_types._reset_cache()
    yield
    cell_types._reset_cache()


def test_load_returns_dict():
    data = cell_types.load()
    assert isinstance(data, dict)
    assert "rows" in data
    assert "agents" in data


def test_get_agent_context_pl_income():
    ctx = cell_types.get_agent_context("pl_income")
    assert "section_tree" in ctx
    assert "valid_rows" in ctx
    assert 22 in ctx["valid_rows"]
    assert 21 not in ctx["valid_rows"]


def test_get_agent_context_unknown_raises():
    with pytest.raises(KeyError):
        cell_types.get_agent_context("bogus_agent")


def test_is_valid_target_for_agent():
    assert cell_types.is_valid_target("pl_income", 22) is True
    assert cell_types.is_valid_target("pl_income", 21) is False  # header
    assert cell_types.is_valid_target("pl_income", 24) is False  # formula


def test_valid_rows_csv_for_prompt():
    csv = cell_types.valid_rows_csv("pl_income")
    assert "22" in csv
    assert "23" in csv
    assert "," in csv


def test_cache_is_hit_on_second_call():
    cell_types._reset_cache()
    a = cell_types.load()
    b = cell_types.load()
    assert a is b


def test_section_tree_returns_str():
    tree = cell_types.section_tree("pl_income")
    assert isinstance(tree, str)
    assert "R22" in tree
    assert "Domestic" in tree
