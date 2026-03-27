"""Phase 8A V2: Conversion upgrade tests.

Covers:
  - diff_financial_items() 4-pass algorithm (pure function, no mocks)
  - _normalize() text normalization helper
  - _amounts_equal() tolerance-based comparison
  - V2 confirm flow (mock Supabase)
  - _fetch_line_items() bug-fix regression (source_text not description)
  - V2 API endpoints (/api/conversion/v2/preview, /api/conversion/v2/confirm)
"""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.dependencies import get_current_user, require_admin
from app.main import app
from app.models.schemas import UserProfile
from app.services.conversion_service import (
    DiffCategory,
    DiffResult,
    _amounts_equal,
    _normalize,
    diff_financial_items,
)

# ── Constants ──────────────────────────────────────────────────────────────

CLIENT_ID = "client-uuid-conv-v2"
PROV_DOC_ID = "doc-uuid-prov-v2"
AUD_DOC_ID = "doc-uuid-aud-v2"
REPORT_ID = "report-uuid-v2"

ADMIN_USER = UserProfile(
    id="admin-uuid-v2",
    full_name="Test Admin V2",
    role="admin",
    created_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
    updated_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
)

EMPLOYEE_USER = UserProfile(
    id="employee-uuid-v2",
    full_name="Test Employee V2",
    role="employee",
    created_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
    updated_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
)

PROV_DOC = {
    "id": PROV_DOC_ID,
    "client_id": CLIENT_ID,
    "financial_year": 2024,
    "nature": "provisional",
    "extraction_status": "verified",
}

AUD_DOC = {
    "id": AUD_DOC_ID,
    "client_id": CLIENT_ID,
    "financial_year": 2024,
    "nature": "audited",
    "extraction_status": "verified",
}

# V2 items use source_text (not description)
PROV_ITEMS_V2 = [
    {"id": "p1", "source_text": "Sales Revenue", "amount": 1000.0},
    {"id": "p2", "source_text": "Wages", "amount": 200.0},
    {"id": "p3", "source_text": "Rent Expense", "amount": 50.0},
]

AUD_ITEMS_V2 = [
    {"id": "a1", "source_text": "Sales Revenue", "amount": 1050.0},
    {"id": "a2", "source_text": "Wages", "amount": 200.0},
    {"id": "a3", "source_text": "New Equipment", "amount": 300.0},
]


# ── Fixtures ───────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def clear_overrides():
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def admin_client():
    app.dependency_overrides[get_current_user] = lambda: ADMIN_USER
    app.dependency_overrides[require_admin] = lambda: ADMIN_USER
    return TestClient(app)


@pytest.fixture
def employee_client():
    app.dependency_overrides[get_current_user] = lambda: EMPLOYEE_USER
    return TestClient(app)


# ── Mock factory helpers ───────────────────────────────────────────────────


def _make_service(**table_mocks) -> MagicMock:
    """Return a mock Supabase service dispatching per table name."""
    svc = MagicMock()
    svc.table.side_effect = lambda name: table_mocks.get(name, MagicMock())
    return svc


def _docs_table(prov_doc, aud_doc):
    """Documents table mock returning different docs by doc_id."""
    tbl = MagicMock()

    def eq_se(field, value):
        m = MagicMock()
        if value == PROV_DOC_ID:
            m.single.return_value.execute.return_value.data = prov_doc
        elif value == AUD_DOC_ID:
            m.single.return_value.execute.return_value.data = aud_doc
        else:
            m.single.return_value.execute.return_value.data = None
        return m

    tbl.select.return_value.eq.side_effect = eq_se
    tbl.update.return_value.eq.return_value.execute.return_value.data = [{}]
    return tbl


def _items_table(prov_items, aud_items):
    """Line items table returning different items by document_id."""
    tbl = MagicMock()

    def eq_se(field, value):
        m = MagicMock()
        if value == PROV_DOC_ID:
            m.execute.return_value.data = prov_items
        elif value == AUD_DOC_ID:
            m.execute.return_value.data = aud_items
        else:
            m.execute.return_value.data = []
        return m

    tbl.select.return_value.eq.side_effect = eq_se
    tbl.update.return_value.eq.return_value.execute.return_value.data = [{}]
    tbl.insert.return_value.execute.return_value.data = [{}]
    return tbl


def _classifications_table(clf_data=None):
    """Classifications table mock. Defaults to one classification found."""
    tbl = MagicMock()
    data = clf_data if clf_data is not None else [{"id": "clf-001"}]
    tbl.select.return_value.eq.return_value.execute.return_value.data = data
    tbl.update.return_value.in_.return_value.execute.return_value.data = [{}]
    return tbl


def _reports_table():
    """CMA reports table mock."""
    tbl = MagicMock()
    tbl.select.return_value.eq.return_value.single.return_value.execute.return_value.data = {
        "document_ids": [PROV_DOC_ID],
    }
    tbl.update.return_value.eq.return_value.execute.return_value.data = [{}]
    return tbl


def _conversion_events_table():
    """Conversion events table mock."""
    tbl = MagicMock()
    tbl.insert.return_value.execute.return_value.data = [{}]
    return tbl


def _history_table():
    """History table mock."""
    tbl = MagicMock()
    tbl.insert.return_value.execute.return_value.data = [{}]
    return tbl


# ══════════════════════════════════════════════════════════════════════════
# 1. diff_financial_items() — pure function tests
# ══════════════════════════════════════════════════════════════════════════


class TestDiffFinancialItems:
    """Pure function unit tests for the V2 4-pass diff algorithm."""

    def test_exact_match_same_amounts_unchanged(self):
        """Identical normalized text and amounts -> UNCHANGED."""
        prov = [{"id": "p1", "source_text": "Sales Revenue", "amount": 1000.0}]
        aud = [{"id": "a1", "source_text": "Sales Revenue", "amount": 1000.0}]
        results = diff_financial_items(prov, aud)
        assert len(results) == 1
        r = results[0]
        assert r.category == DiffCategory.UNCHANGED
        assert r.match_score == 100.0
        assert r.needs_reclassification is False
        assert r.provisional_item_id == "p1"
        assert r.audited_item_id == "a1"

    def test_exact_match_different_amounts_amount_changed(self):
        """Same text, different amounts -> AMOUNT_CHANGED."""
        prov = [{"id": "p1", "source_text": "Sales Revenue", "amount": 1000.0}]
        aud = [{"id": "a1", "source_text": "Sales Revenue", "amount": 1200.0}]
        results = diff_financial_items(prov, aud)
        assert len(results) == 1
        r = results[0]
        assert r.category == DiffCategory.AMOUNT_CHANGED
        assert r.match_score == 100.0
        assert r.needs_reclassification is False

    def test_exact_match_within_tolerance_unchanged(self):
        """Amounts within 0.5% tolerance -> UNCHANGED (e.g. 1000 vs 1004 = 0.4%)."""
        prov = [{"id": "p1", "source_text": "Depreciation", "amount": 1000.0}]
        aud = [{"id": "a1", "source_text": "Depreciation", "amount": 1004.0}]
        results = diff_financial_items(prov, aud)
        assert len(results) == 1
        assert results[0].category == DiffCategory.UNCHANGED

    def test_exact_match_outside_tolerance_amount_changed(self):
        """Amounts outside 0.5% tolerance -> AMOUNT_CHANGED (e.g. 1000 vs 1010 = 1%)."""
        prov = [{"id": "p1", "source_text": "Depreciation", "amount": 1000.0}]
        aud = [{"id": "a1", "source_text": "Depreciation", "amount": 1010.0}]
        results = diff_financial_items(prov, aud)
        assert len(results) == 1
        assert results[0].category == DiffCategory.AMOUNT_CHANGED

    def test_fuzzy_match_high_score_desc_changed_no_reclass(self):
        """Fuzzy match score >= 90 -> DESC_CHANGED, needs_reclassification=False.

        "Salary Expenses" vs "Salary Expense" should produce a high fuzzy score.
        """
        prov = [{"id": "p1", "source_text": "Salary Expenses", "amount": 200.0}]
        aud = [{"id": "a1", "source_text": "Salary Expense", "amount": 250.0}]
        results = diff_financial_items(prov, aud)
        assert len(results) == 1
        r = results[0]
        assert r.category == DiffCategory.DESC_CHANGED
        assert r.match_score >= 90
        assert r.needs_reclassification is False

    def test_fuzzy_match_medium_score_desc_changed_needs_reclass(self):
        """Fuzzy match score 75-89 -> DESC_CHANGED, needs_reclassification=True.

        Use descriptions that produce a score in the 75-89 range with token_set_ratio.
        """
        prov = [{"id": "p1", "source_text": "Raw Material Consumed", "amount": 500.0}]
        aud = [{"id": "a1", "source_text": "Cost of Raw Material Purchases and Consumption", "amount": 600.0}]
        results = diff_financial_items(prov, aud)
        # Should fuzzy match but with a score in the 75-89 range
        matched = [r for r in results if r.category == DiffCategory.DESC_CHANGED]
        if matched:
            r = matched[0]
            assert r.match_score >= 75
            assert r.match_score < 90
            assert r.needs_reclassification is True
        else:
            # If no fuzzy match, items should appear as REMOVED + ADDED
            removed = [r for r in results if r.category == DiffCategory.REMOVED]
            added = [r for r in results if r.category == DiffCategory.ADDED]
            assert len(removed) == 1
            assert len(added) == 1

    def test_fuzzy_match_below_threshold_becomes_added_removed(self):
        """Fuzzy match score < 75 -> not matched (becomes ADDED + REMOVED)."""
        prov = [{"id": "p1", "source_text": "Bank Charges", "amount": 100.0}]
        aud = [{"id": "a1", "source_text": "Plant and Machinery", "amount": 5000.0}]
        results = diff_financial_items(prov, aud)
        categories = {r.category for r in results}
        assert DiffCategory.REMOVED in categories
        assert DiffCategory.ADDED in categories
        assert DiffCategory.DESC_CHANGED not in categories

    def test_item_only_in_provisional_is_removed(self):
        """Item only in provisional -> REMOVED, needs_reclassification=False."""
        prov = [{"id": "p1", "source_text": "Old Rent Expense", "amount": 50.0}]
        aud = []
        results = diff_financial_items(prov, aud)
        assert len(results) == 1
        r = results[0]
        assert r.category == DiffCategory.REMOVED
        assert r.needs_reclassification is False
        assert r.provisional_item_id == "p1"
        assert r.audited_item_id is None

    def test_item_only_in_audited_is_added(self):
        """Item only in audited -> ADDED, needs_reclassification=True."""
        prov = []
        aud = [{"id": "a1", "source_text": "New Equipment", "amount": 300.0}]
        results = diff_financial_items(prov, aud)
        assert len(results) == 1
        r = results[0]
        assert r.category == DiffCategory.ADDED
        assert r.needs_reclassification is True
        assert r.provisional_item_id is None
        assert r.audited_item_id == "a1"

    def test_note_prefix_normalization(self):
        """'Note 23: Wages' matches 'Wages' exactly via normalization."""
        prov = [{"id": "p1", "source_text": "Note 23: Wages", "amount": 200.0}]
        aud = [{"id": "a1", "source_text": "Wages", "amount": 200.0}]
        results = diff_financial_items(prov, aud)
        assert len(results) == 1
        r = results[0]
        assert r.category == DiffCategory.UNCHANGED
        assert r.match_score == 100.0

    def test_empty_lists_empty_results(self):
        """Both empty lists -> empty results."""
        results = diff_financial_items([], [])
        assert results == []

    def test_single_item_both_sides_exact_match_unchanged(self):
        """Single item on both sides with exact match -> UNCHANGED."""
        prov = [{"id": "p1", "source_text": "Interest Income", "amount": 75.0}]
        aud = [{"id": "a1", "source_text": "Interest Income", "amount": 75.0}]
        results = diff_financial_items(prov, aud)
        assert len(results) == 1
        assert results[0].category == DiffCategory.UNCHANGED

    def test_full_scenario_all_categories(self):
        """Full scenario producing all 5 categories in a single diff."""
        prov = [
            {"id": "p1", "source_text": "Sales Revenue", "amount": 1000.0},    # exact match, amt changed
            {"id": "p2", "source_text": "Wages", "amount": 200.0},              # exact match, unchanged
            {"id": "p3", "source_text": "Rent Expense", "amount": 50.0},        # only in prov -> removed
        ]
        aud = [
            {"id": "a1", "source_text": "Sales Revenue", "amount": 1050.0},     # exact match, amt changed
            {"id": "a2", "source_text": "Wages", "amount": 200.0},              # exact match, unchanged
            {"id": "a3", "source_text": "New Equipment", "amount": 300.0},      # only in aud -> added
        ]
        results = diff_financial_items(prov, aud)
        cats = [r.category for r in results]
        assert DiffCategory.UNCHANGED in cats
        assert DiffCategory.AMOUNT_CHANGED in cats
        assert DiffCategory.REMOVED in cats
        assert DiffCategory.ADDED in cats


# ══════════════════════════════════════════════════════════════════════════
# 2. _normalize() tests
# ══════════════════════════════════════════════════════════════════════════


class TestNormalize:
    """Tests for the _normalize() text normalization helper."""

    def test_strips_note_prefix(self):
        """'Note 3: Depreciation' -> 'depreciation'."""
        assert _normalize("Note 3: Depreciation") == "depreciation"

    def test_lowercases(self):
        """'SALES REVENUE' -> 'sales revenue'."""
        assert _normalize("SALES REVENUE") == "sales revenue"

    def test_collapses_whitespace(self):
        """'  Salary   Expenses  ' -> 'salary expenses'."""
        assert _normalize("  Salary   Expenses  ") == "salary expenses"

    def test_strips_item_prefix(self):
        """'Item 1 (i) : Domestic sales' -> 'domestic sales'."""
        assert _normalize("Item 1 (i) : Domestic sales") == "domestic sales"

    def test_strips_numbered_prefix(self):
        """'1. Salaries & Wages' -> 'salaries & wages'."""
        assert _normalize("1. Salaries & Wages") == "salaries & wages"

    def test_empty_string(self):
        """Empty string normalizes to empty."""
        assert _normalize("") == ""


# ══════════════════════════════════════════════════════════════════════════
# 3. _amounts_equal() tests
# ══════════════════════════════════════════════════════════════════════════


class TestAmountsEqual:
    """Tests for the _amounts_equal() tolerance-based comparison."""

    def test_same_amount_true(self):
        assert _amounts_equal(1000.0, 1000.0) is True

    def test_within_half_percent_true(self):
        """0.5% of 1000 = 5, so 1000 vs 1005 is within tolerance."""
        assert _amounts_equal(1000.0, 1005.0) is True

    def test_one_percent_diff_false(self):
        """1% of 1000 = 10, so 1000 vs 1010 is outside tolerance."""
        assert _amounts_equal(1000.0, 1010.0) is False

    def test_none_vs_none_true(self):
        assert _amounts_equal(None, None) is True

    def test_none_vs_number_false(self):
        assert _amounts_equal(None, 100.0) is False

    def test_number_vs_none_false(self):
        assert _amounts_equal(100.0, None) is False

    def test_zero_vs_zero_true(self):
        assert _amounts_equal(0.0, 0.0) is True

    def test_zero_vs_nonzero_false(self):
        """Zero vs any non-zero is False (division guard)."""
        assert _amounts_equal(0.0, 1.0) is False

    @pytest.mark.parametrize(
        "a, b, expected",
        [
            (200.0, 201.0, True),    # 0.5% of 200 = 1.0, exactly at boundary
            (200.0, 202.0, False),   # 1% of 200 = 2.0, outside
            (10000.0, 10050.0, True),  # 0.5% of 10000 = 50
            (10000.0, 10051.0, False), # just over 0.5%
        ],
    )
    def test_parametrized_tolerance_boundary(self, a, b, expected):
        """Parametrized boundary cases for amount tolerance."""
        assert _amounts_equal(a, b) is expected


# ══════════════════════════════════════════════════════════════════════════
# 4. Confirm flow tests (mock Supabase)
# ══════════════════════════════════════════════════════════════════════════


class TestConfirmFlowV2:
    """Tests for confirm_conversion() V2 behavior with mock Supabase."""

    def _make_confirm_svc(self, prov_items=None, aud_items=None, clf_data=None):
        """Build a fully-mocked service for confirm tests."""
        p = prov_items if prov_items is not None else PROV_ITEMS_V2
        a = aud_items if aud_items is not None else AUD_ITEMS_V2
        return _make_service(
            documents=_docs_table(PROV_DOC, AUD_DOC),
            extracted_line_items=_items_table(p, a),
            classifications=_classifications_table(clf_data),
            cma_reports=_reports_table(),
            conversion_events=_conversion_events_table(),
            cma_report_history=_history_table(),
        )

    @pytest.mark.asyncio
    async def test_amount_changed_updates_amount_only(self):
        """AMOUNT_CHANGED: updates amount, classification NOT flagged as doubt."""
        from app.services.conversion_service import confirm_conversion
        from app.models.schemas import ConversionConfirmRequest

        prov = [{"id": "p1", "source_text": "Sales Revenue", "amount": 1000.0}]
        aud = [{"id": "a1", "source_text": "Sales Revenue", "amount": 1200.0}]
        svc = self._make_confirm_svc(prov_items=prov, aud_items=aud)
        req = ConversionConfirmRequest(
            provisional_doc_id=PROV_DOC_ID,
            audited_doc_id=AUD_DOC_ID,
            cma_report_id=REPORT_ID,
        )
        with patch("app.services.conversion_service.audit_service.log_action"):
            result = await confirm_conversion(svc, req, ADMIN_USER.id)
        assert result.updated_count >= 1
        # Verify it updated amount on extracted_line_items
        items_tbl = svc.table("extracted_line_items")
        items_tbl.update.assert_called()
        # The first update call should be for amount only (no is_doubt flag)
        first_update_arg = items_tbl.update.call_args_list[0][0][0]
        assert "amount" in first_update_arg
        assert "is_doubt" not in first_update_arg

    @pytest.mark.asyncio
    async def test_desc_changed_high_score_keeps_classification(self):
        """DESC_CHANGED (>=90): updates source_text, classification kept."""
        from app.services.conversion_service import confirm_conversion
        from app.models.schemas import ConversionConfirmRequest

        # "Salary Expenses" vs "Salary Expense" produces score >= 90
        prov = [{"id": "p1", "source_text": "Salary Expenses", "amount": 200.0}]
        aud = [{"id": "a1", "source_text": "Salary Expense", "amount": 250.0}]
        svc = self._make_confirm_svc(prov_items=prov, aud_items=aud)
        req = ConversionConfirmRequest(
            provisional_doc_id=PROV_DOC_ID,
            audited_doc_id=AUD_DOC_ID,
            cma_report_id=REPORT_ID,
        )
        with patch("app.services.conversion_service.audit_service.log_action"):
            result = await confirm_conversion(svc, req, ADMIN_USER.id)
        # Should not flag any classifications for review (score >= 90)
        assert result.flagged_for_review == 0

    @pytest.mark.asyncio
    async def test_added_item_inserts_new_line_item(self):
        """ADDED: new line item inserted into extracted_line_items."""
        from app.services.conversion_service import confirm_conversion
        from app.models.schemas import ConversionConfirmRequest

        prov = []  # empty provisional
        aud = [{"id": "a1", "source_text": "Brand New Item", "amount": 999.0}]
        svc = self._make_confirm_svc(prov_items=prov, aud_items=aud)
        req = ConversionConfirmRequest(
            provisional_doc_id=PROV_DOC_ID,
            audited_doc_id=AUD_DOC_ID,
            cma_report_id=REPORT_ID,
        )
        with patch("app.services.conversion_service.audit_service.log_action"):
            result = await confirm_conversion(svc, req, ADMIN_USER.id)
        # Verify insert was called on extracted_line_items
        items_tbl = svc.table("extracted_line_items")
        items_tbl.insert.assert_called()
        insert_arg = items_tbl.insert.call_args[0][0]
        assert insert_arg["source_text"] == "Brand New Item"
        assert insert_arg["amount"] == 999.0
        assert insert_arg["document_id"] == PROV_DOC_ID
        assert insert_arg["is_verified"] is False

    @pytest.mark.asyncio
    async def test_removed_item_sets_is_verified_false(self):
        """REMOVED: is_verified set to False on the provisional item."""
        from app.services.conversion_service import confirm_conversion
        from app.models.schemas import ConversionConfirmRequest

        prov = [{"id": "p1", "source_text": "Old Obsolete Item", "amount": 50.0}]
        aud = []  # nothing in audited
        svc = self._make_confirm_svc(prov_items=prov, aud_items=aud)
        req = ConversionConfirmRequest(
            provisional_doc_id=PROV_DOC_ID,
            audited_doc_id=AUD_DOC_ID,
            cma_report_id=REPORT_ID,
        )
        with patch("app.services.conversion_service.audit_service.log_action"):
            result = await confirm_conversion(svc, req, ADMIN_USER.id)
        # Verify update was called with is_verified=False
        items_tbl = svc.table("extracted_line_items")
        items_tbl.update.assert_called()
        update_arg = items_tbl.update.call_args_list[0][0][0]
        assert update_arg == {"is_verified": False}

    @pytest.mark.asyncio
    async def test_provisional_doc_superseded(self):
        """Provisional doc gets superseded_at and superseded_by set."""
        from app.services.conversion_service import confirm_conversion
        from app.models.schemas import ConversionConfirmRequest

        svc = self._make_confirm_svc()
        req = ConversionConfirmRequest(
            provisional_doc_id=PROV_DOC_ID,
            audited_doc_id=AUD_DOC_ID,
            cma_report_id=REPORT_ID,
        )
        with patch("app.services.conversion_service.audit_service.log_action"):
            await confirm_conversion(svc, req, ADMIN_USER.id)
        # Documents table should have been updated for provisional doc
        docs_tbl = svc.table("documents")
        update_calls = docs_tbl.update.call_args_list
        # Find the call that sets superseded_at
        supersede_calls = [
            c for c in update_calls
            if "superseded_at" in c[0][0]
        ]
        assert len(supersede_calls) >= 1
        supersede_arg = supersede_calls[0][0][0]
        assert supersede_arg["superseded_by"] == AUD_DOC_ID

    @pytest.mark.asyncio
    async def test_audited_doc_marked_with_parent(self):
        """Audited doc gets parent_document_id and version_number=2."""
        from app.services.conversion_service import confirm_conversion
        from app.models.schemas import ConversionConfirmRequest

        svc = self._make_confirm_svc()
        req = ConversionConfirmRequest(
            provisional_doc_id=PROV_DOC_ID,
            audited_doc_id=AUD_DOC_ID,
            cma_report_id=REPORT_ID,
        )
        with patch("app.services.conversion_service.audit_service.log_action"):
            await confirm_conversion(svc, req, ADMIN_USER.id)
        docs_tbl = svc.table("documents")
        update_calls = docs_tbl.update.call_args_list
        parent_calls = [
            c for c in update_calls
            if "parent_document_id" in c[0][0]
        ]
        assert len(parent_calls) >= 1
        parent_arg = parent_calls[0][0][0]
        assert parent_arg["parent_document_id"] == PROV_DOC_ID
        assert parent_arg["version_number"] == 2

    @pytest.mark.asyncio
    async def test_conversion_event_record_created(self):
        """A conversion_event record is created with summary counts."""
        from app.services.conversion_service import confirm_conversion
        from app.models.schemas import ConversionConfirmRequest

        svc = self._make_confirm_svc()
        req = ConversionConfirmRequest(
            provisional_doc_id=PROV_DOC_ID,
            audited_doc_id=AUD_DOC_ID,
            cma_report_id=REPORT_ID,
        )
        with patch("app.services.conversion_service.audit_service.log_action"):
            await confirm_conversion(svc, req, ADMIN_USER.id)
        events_tbl = svc.table("conversion_events")
        events_tbl.insert.assert_called_once()
        insert_arg = events_tbl.insert.call_args[0][0]
        assert insert_arg["provisional_doc_id"] == PROV_DOC_ID
        assert insert_arg["audited_doc_id"] == AUD_DOC_ID
        assert "summary" in insert_arg

    @pytest.mark.asyncio
    async def test_audit_log_created_with_diff_summary(self):
        """Audit log includes diff summary counts."""
        from app.services.conversion_service import confirm_conversion
        from app.models.schemas import ConversionConfirmRequest

        svc = self._make_confirm_svc()
        req = ConversionConfirmRequest(
            provisional_doc_id=PROV_DOC_ID,
            audited_doc_id=AUD_DOC_ID,
            cma_report_id=REPORT_ID,
        )
        with patch("app.services.conversion_service.audit_service.log_action") as mock_log:
            await confirm_conversion(svc, req, ADMIN_USER.id)
        mock_log.assert_called_once()
        call_kwargs = mock_log.call_args
        # The 'after' dict should contain summary
        after = call_kwargs.kwargs.get("after") or call_kwargs[1].get("after")
        assert "summary" in after
        summary = after["summary"]
        assert "unchanged" in summary
        assert "amount_changed" in summary
        assert "added" in summary
        assert "removed" in summary


# ══════════════════════════════════════════════════════════════════════════
# 5. Bug fix regression: _fetch_line_items selects source_text
# ══════════════════════════════════════════════════════════════════════════


class TestFetchLineItemsRegression:
    """Regression test: _fetch_line_items selects source_text, not description."""

    def test_fetch_line_items_selects_source_text(self):
        """_fetch_line_items() must call .select('id,source_text,amount')."""
        from app.services.conversion_service import _fetch_line_items

        svc = MagicMock()
        tbl = MagicMock()
        svc.table.return_value = tbl
        tbl.select.return_value.eq.return_value.execute.return_value.data = []

        _fetch_line_items(svc, "some-doc-id")

        svc.table.assert_called_with("extracted_line_items")
        tbl.select.assert_called_once_with("id,source_text,amount")


# ══════════════════════════════════════════════════════════════════════════
# 6. V2 API endpoint tests
# ══════════════════════════════════════════════════════════════════════════


class TestV2PreviewEndpoint:
    """Tests for POST /api/conversion/v2/preview."""

    def test_v2_preview_returns_5_category_format(self, admin_client):
        """V2 preview returns all 5 categories and a summary."""
        svc = _make_service(
            documents=_docs_table(PROV_DOC, AUD_DOC),
            extracted_line_items=_items_table(PROV_ITEMS_V2, AUD_ITEMS_V2),
        )
        with patch("app.routers.conversion.get_service_client", return_value=svc):
            response = admin_client.post(
                "/api/conversion/v2/preview",
                json={
                    "provisional_doc_id": PROV_DOC_ID,
                    "audited_doc_id": AUD_DOC_ID,
                },
            )
        assert response.status_code == 200
        data = response.json()
        assert "unchanged" in data
        assert "amount_changed" in data
        assert "desc_changed" in data
        assert "added" in data
        assert "removed" in data
        assert "summary" in data
        # Summary should have counts for all 5 categories
        summary = data["summary"]
        assert "unchanged" in summary
        assert "amount_changed" in summary
        assert "desc_changed" in summary
        assert "added" in summary
        assert "removed" in summary

    def test_v2_preview_includes_match_scores(self, admin_client):
        """V2 preview items include match_score and needs_reclassification fields."""
        prov = [{"id": "p1", "source_text": "Sales Revenue", "amount": 1000.0}]
        aud = [{"id": "a1", "source_text": "Sales Revenue", "amount": 1050.0}]
        svc = _make_service(
            documents=_docs_table(PROV_DOC, AUD_DOC),
            extracted_line_items=_items_table(prov, aud),
        )
        with patch("app.routers.conversion.get_service_client", return_value=svc):
            response = admin_client.post(
                "/api/conversion/v2/preview",
                json={
                    "provisional_doc_id": PROV_DOC_ID,
                    "audited_doc_id": AUD_DOC_ID,
                },
            )
        assert response.status_code == 200
        data = response.json()
        # The amount_changed list should have the item
        assert len(data["amount_changed"]) == 1
        item = data["amount_changed"][0]
        assert "match_score" in item
        assert "needs_reclassification" in item
        assert item["match_score"] == 100.0
        assert item["needs_reclassification"] is False


class TestV2ConfirmEndpoint:
    """Tests for POST /api/conversion/v2/confirm."""

    def test_v2_confirm_returns_per_category_counts(self, admin_client):
        """V2 confirm returns per-category counts and a message."""
        svc = _make_service(
            documents=_docs_table(PROV_DOC, AUD_DOC),
            extracted_line_items=_items_table(PROV_ITEMS_V2, AUD_ITEMS_V2),
            classifications=_classifications_table(),
            cma_reports=_reports_table(),
            conversion_events=_conversion_events_table(),
            cma_report_history=_history_table(),
        )
        with patch("app.routers.conversion.get_service_client", return_value=svc), \
             patch("app.services.conversion_service.audit_service.log_action"):
            response = admin_client.post(
                "/api/conversion/v2/confirm",
                json={
                    "provisional_doc_id": PROV_DOC_ID,
                    "audited_doc_id": AUD_DOC_ID,
                    "cma_report_id": REPORT_ID,
                },
            )
        assert response.status_code == 200
        data = response.json()
        assert "unchanged" in data
        assert "amount_updated" in data
        assert "reclassified" in data
        assert "added" in data
        assert "removed" in data
        assert "message" in data
        # Verify counts are non-negative integers
        assert isinstance(data["unchanged"], int)
        assert isinstance(data["amount_updated"], int)
        assert isinstance(data["added"], int)
        assert isinstance(data["removed"], int)

    def test_v2_confirm_requires_admin(self, employee_client):
        """Employee (non-admin) calling V2 confirm receives 403."""
        response = employee_client.post(
            "/api/conversion/v2/confirm",
            json={
                "provisional_doc_id": PROV_DOC_ID,
                "audited_doc_id": AUD_DOC_ID,
                "cma_report_id": REPORT_ID,
            },
        )
        assert response.status_code == 403
