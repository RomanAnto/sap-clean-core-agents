"""Tests for MCP tool handler stubs."""
from __future__ import annotations
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture
def mock_sap_client():
    client = AsyncMock()
    client.get_connection_status.return_value = {"status": "connected", "statusCode": 200}
    client.get_objects.return_value = {"objects": []}
    client.get_source_code.return_value = {"objectName": "ZCL_TEST", "source": "CLASS zcl_test."}
    client.run_atc_check.return_value = {"findings": []}
    client.get_where_used.return_value = {"usages": []}
    client.search_objects.return_value = {"objects": []}
    client.activate_objects.return_value = {"activated": True}
    client.create_transport.return_value = {"transportNumber": "DEVK123456"}
    return client


class TestConnectionStatusHandler:
    """Tests for connection_status tool handler."""

    @pytest.mark.asyncio
    async def test_returns_json_string(self, mock_sap_client):
        from aws_abap_accelerator.server.tool_handlers import ToolHandlers
        handlers = ToolHandlers(mock_sap_client)
        result = await handlers.connection_status()
        parsed = json.loads(result)
        assert parsed["status"] == "connected"

    @pytest.mark.asyncio
    async def test_client_called_once(self, mock_sap_client):
        from aws_abap_accelerator.server.tool_handlers import ToolHandlers
        handlers = ToolHandlers(mock_sap_client)
        await handlers.connection_status()
        mock_sap_client.get_connection_status.assert_called_once()


class TestGetObjectsHandler:
    """Tests for get_objects tool handler."""

    @pytest.mark.asyncio
    async def test_returns_json_string(self, mock_sap_client):
        from aws_abap_accelerator.server.tool_handlers import ToolHandlers
        handlers = ToolHandlers(mock_sap_client)
        result = await handlers.get_objects(package="ZMYPACKAGE", object_type="CLAS")
        parsed = json.loads(result)
        assert "objects" in parsed

    @pytest.mark.asyncio
    async def test_invalid_package_raises(self, mock_sap_client):
        from aws_abap_accelerator.server.tool_handlers import ToolHandlers
        handlers = ToolHandlers(mock_sap_client)
        with pytest.raises(ValueError):
            await handlers.get_objects(package="<script>", object_type="CLAS")


class TestRunAtcCheckHandler:
    """Tests for run_atc_check tool handler."""

    @pytest.mark.asyncio
    async def test_returns_findings_json(self, mock_sap_client):
        from aws_abap_accelerator.server.tool_handlers import ToolHandlers
        handlers = ToolHandlers(mock_sap_client)
        result = await handlers.run_atc_check(
            object_name="ZCL_TEST", object_type="CLAS", variant=None
        )
        parsed = json.loads(result)
        assert "findings" in parsed

    @pytest.mark.asyncio
    async def test_object_name_too_long_raises(self, mock_sap_client):
        from aws_abap_accelerator.server.tool_handlers import ToolHandlers
        handlers = ToolHandlers(mock_sap_client)
        with pytest.raises(ValueError):
            await handlers.run_atc_check(
                object_name="Z" * 100, object_type="CLAS", variant=None
            )
