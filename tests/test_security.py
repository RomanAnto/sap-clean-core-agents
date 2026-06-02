"""Tests for input validation utilities."""
from __future__ import annotations
import pytest
from aws_abap_accelerator.utils.security import (
    validate_sap_object_name,
    validate_sap_package_name,
    validate_search_query,
    validate_source_code,
    SAP_IDENTIFIER_MAX_LEN,
    SAP_PACKAGE_MAX_LEN,
    SAP_SEARCH_QUERY_MAX_LEN,
    SAP_SOURCE_CODE_MAX_LEN,
)


class TestValidateSapObjectName:
    """Tests for SAP object name validation."""

    def test_valid_name_accepted(self):
        assert validate_sap_object_name("ZCL_MY_CLASS") == "ZCL_MY_CLASS"

    def test_empty_name_raises(self):
        with pytest.raises(ValueError, match="empty"):
            validate_sap_object_name("")

    def test_name_too_long_raises(self):
        long_name = "Z" * (SAP_IDENTIFIER_MAX_LEN + 1)
        with pytest.raises(ValueError, match="exceeds"):
            validate_sap_object_name(long_name)

    def test_name_at_max_length_accepted(self):
        name = "Z" * SAP_IDENTIFIER_MAX_LEN
        assert validate_sap_object_name(name) == name

    def test_invalid_characters_rejected(self):
        with pytest.raises(ValueError, match="invalid characters"):
            validate_sap_object_name("ZCL_<INJECTION>")


class TestValidateSapPackageName:
    """Tests for SAP package name validation."""

    def test_valid_package_accepted(self):
        assert validate_sap_package_name("ZPACKAGE_MYAPP") == "ZPACKAGE_MYAPP"

    def test_package_too_long_raises(self):
        long_pkg = "Z" * (SAP_PACKAGE_MAX_LEN + 1)
        with pytest.raises(ValueError, match="exceeds"):
            validate_sap_package_name(long_pkg)


class TestValidateSearchQuery:
    """Tests for search query validation."""

    def test_valid_query_accepted(self):
        assert validate_search_query("ZCL_*") == "ZCL_*"

    def test_query_too_long_raises(self):
        long_query = "A" * (SAP_SEARCH_QUERY_MAX_LEN + 1)
        with pytest.raises(ValueError, match="exceeds"):
            validate_search_query(long_query)


class TestValidateSourceCode:
    """Tests for source code validation."""

    def test_valid_source_accepted(self):
        code = "REPORT zmyreport.\nWRITE 'Hello'."
        assert validate_source_code(code) == code

    def test_source_too_large_raises(self):
        huge_code = "A" * (SAP_SOURCE_CODE_MAX_LEN + 1)
        with pytest.raises(ValueError, match="exceeds"):
            validate_source_code(huge_code)
