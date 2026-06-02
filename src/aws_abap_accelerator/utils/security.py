"""
SAP ABAP Accelerator MCP Server — security.py

Input validation utilities used across all tool handlers.

Security fixes applied (from repo analysis):
  S-05: Input length validation prevents memory exhaustion / oversized ADT requests
"""
from __future__ import annotations

import re
import logging

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# SAP identifier length limits
# ---------------------------------------------------------------------------

SAP_IDENTIFIER_MAX_LEN = 40        # SAP standard: program/class/FM names
SAP_PACKAGE_MAX_LEN = 40           # SAP package names
SAP_SEARCH_QUERY_MAX_LEN = 200     # Search / filter strings
SAP_SOURCE_CODE_MAX_LEN = 5_000_000  # 5 MB cap for source uploads

# Allowed characters in SAP object names (alphanumeric + _ + /)
_SAP_NAME_RE = re.compile(r"^[A-Za-z0-9_/]+$")


# ---------------------------------------------------------------------------
# Validators
# ---------------------------------------------------------------------------

def validate_input_length(value: str, field_name: str, max_len: int) -> str:
    """
    Validate that a string input does not exceed the maximum allowed length.

    Raises:
        TypeError:  If value is not a string.
        ValueError: If value exceeds max_len.
    """
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string, got {type(value).__name__}.")
    if len(value) > max_len:
        raise ValueError(
            f"{field_name} exceeds maximum allowed length of {max_len} characters "
            f"(received {len(value)} characters)."
        )
    return value


def validate_sap_object_name(name: str, field_name: str = "object_name") -> str:
    """
    Validate a SAP object name:
    - Not empty
    - Max SAP_IDENTIFIER_MAX_LEN characters
    - Only alphanumeric, underscore, and slash characters
    """
    name = validate_input_length(name.strip(), field_name, SAP_IDENTIFIER_MAX_LEN)
    if not name:
        raise ValueError(f"{field_name} must not be empty.")
    if not _SAP_NAME_RE.match(name):
        raise ValueError(
            f"{field_name} contains invalid characters. "
            "Only letters, digits, underscores, and slashes are allowed."
        )
    return name.upper()


def validate_sap_package_name(package: str) -> str:
    """Validate a SAP package name (same rules as object names)."""
    return validate_sap_object_name(package, field_name="package_name")


def validate_search_query(query: str) -> str:
    """Validate a free-text search query string."""
    return validate_input_length(query.strip(), "search_query", SAP_SEARCH_QUERY_MAX_LEN)


def validate_source_code(source: str) -> str:
    """Validate source code size before uploading to SAP."""
    return validate_input_length(source, "source_code", SAP_SOURCE_CODE_MAX_LEN)


def sanitize_for_logging(value: str, visible_chars: int = 0) -> str:
    """
    Mask a sensitive value for logging.

    Args:
        value:         The sensitive string to mask.
        visible_chars: How many leading characters to show (0 = fully masked).
    """
    if not value:
        return "<empty>"
    if visible_chars > 0:
        return value[:visible_chars] + "***"
    return "***"
