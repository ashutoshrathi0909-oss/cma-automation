"""Tests for run_excel_generation ARQ task."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.mark.asyncio
async def test_excel_task_calls_generator():
    """run_excel_generation calls ExcelGenerator.generate() with the report_id."""
    with patch("app.workers.excel_tasks.ExcelGenerator") as MockGen:
        instance = MagicMock()
        instance.generate.return_value = "cma_reports/rep-aaa/output.xlsm"
        MockGen.return_value = instance

        with patch("app.workers.excel_tasks.get_service_client") as mock_svc:
            mock_service = MagicMock()
            mock_service.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock(data=[{}])
            mock_svc.return_value = mock_service

            from app.workers.excel_tasks import run_excel_generation

            result = await run_excel_generation({}, "rep-aaa")

    instance.generate.assert_called_once_with(report_id="rep-aaa", user_id="system")
    assert result["status"] == "complete"


@pytest.mark.asyncio
async def test_excel_task_updates_report_status_on_success():
    """On success, report status is updated to 'complete' with output_path."""
    with patch("app.workers.excel_tasks.ExcelGenerator") as MockGen:
        instance = MagicMock()
        instance.generate.return_value = "cma_reports/rep-aaa/output.xlsm"
        MockGen.return_value = instance

        with patch("app.workers.excel_tasks.get_service_client") as mock_svc:
            mock_service = MagicMock()
            update_chain = MagicMock()
            mock_service.table.return_value.update.return_value = update_chain
            update_chain.eq.return_value.execute.return_value = MagicMock(data=[{}])
            mock_svc.return_value = mock_service

            from app.workers.excel_tasks import run_excel_generation

            await run_excel_generation({}, "rep-aaa")

    update_call_args = mock_service.table.return_value.update.call_args[0][0]
    assert update_call_args["status"] == "complete"
    assert "output_path" in update_call_args


@pytest.mark.asyncio
async def test_excel_task_updates_report_status_on_failure():
    """On failure, report status is updated to 'failed' and the exception re-raised."""
    with patch("app.workers.excel_tasks.ExcelGenerator") as MockGen:
        instance = MagicMock()
        instance.generate.side_effect = RuntimeError("template missing")
        MockGen.return_value = instance

        with patch("app.workers.excel_tasks.get_service_client") as mock_svc:
            mock_service = MagicMock()
            update_chain = MagicMock()
            mock_service.table.return_value.update.return_value = update_chain
            update_chain.eq.return_value.execute.return_value = MagicMock(data=[{}])
            mock_svc.return_value = mock_service

            from app.workers.excel_tasks import run_excel_generation

            with pytest.raises(RuntimeError, match="template missing"):
                await run_excel_generation({}, "rep-aaa")

    update_call_args = mock_service.table.return_value.update.call_args[0][0]
    assert update_call_args["status"] == "failed"
