"""Tests for scripts/derive_cma_cell_types.py."""
from __future__ import annotations
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
SCRIPT = REPO / "scripts" / "derive_cma_cell_types.py"


def test_script_exists():
    assert SCRIPT.exists(), f"Script missing: {SCRIPT}"


def test_script_produces_output(tmp_path):
    out_file = tmp_path / "out.json"
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--output", str(out_file)],
        cwd=str(REPO), capture_output=True, text=True,
    )
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    assert out_file.exists()
    data = json.loads(out_file.read_text())
    assert isinstance(data, dict)
    assert "rows" in data
    assert "agents" in data


def test_known_headers_classified_correctly(tmp_path):
    out_file = tmp_path / "out.json"
    subprocess.run(
        [sys.executable, str(SCRIPT), "--output", str(out_file)],
        cwd=str(REPO), check=True,
    )
    data = json.loads(out_file.read_text())
    rows = data["rows"]
    assert rows["21"]["type"] == "WHITE_HEADER"   # "Sales"
    assert rows["22"]["type"] == "BLUE"           # Domestic Sales
    assert rows["24"]["type"] == "YELLOW"         # Sub Total formula
    assert rows["133"]["type"] == "NOTE_ROW"      # parenthetical note
    assert rows["18"]["type"] == "BLANK"          # spacer
    assert rows["11"]["type"] == "META"           # FY ending


def test_agent_section_trees_present(tmp_path):
    out_file = tmp_path / "out.json"
    subprocess.run(
        [sys.executable, str(SCRIPT), "--output", str(out_file)],
        cwd=str(REPO), check=True,
    )
    data = json.loads(out_file.read_text())
    agents = data["agents"]
    assert set(agents.keys()) >= {"pl_income", "pl_expense", "bs_liability", "bs_asset"}
    for agent_key, agent_data in agents.items():
        assert "section_tree" in agent_data
        assert "valid_rows" in agent_data
        assert isinstance(agent_data["valid_rows"], list)
        assert all(isinstance(r, int) for r in agent_data["valid_rows"])
        if agent_key == "pl_income":
            assert 22 in agent_data["valid_rows"]
            assert 23 in agent_data["valid_rows"]
            assert 21 not in agent_data["valid_rows"]  # header
            assert 24 not in agent_data["valid_rows"]  # formula


def test_section_tree_renders_hierarchy(tmp_path):
    out_file = tmp_path / "out.json"
    subprocess.run(
        [sys.executable, str(SCRIPT), "--output", str(out_file)],
        cwd=str(REPO), check=True,
    )
    data = json.loads(out_file.read_text())
    tree = data["agents"]["pl_income"]["section_tree"]
    assert "R22" in tree and "Domestic" in tree
    assert "R21" in tree and "Sales" in tree
    assert "HEADER" in tree
    assert "TARGET" in tree
    assert "FORMULA" in tree
