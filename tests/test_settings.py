"""Tests for configuration settings module."""
from __future__ import annotations
import os
import pytest
from unittest.mock import patch, mock_open


class TestSAPSettings:
    """Tests for SAPSettings validation."""

    def test_ssl_verify_defaults_true(self, tmp_path):
        """S-03: SSL_VERIFY must default to True (independent of SAP_SECURE)."""
        with patch.dict(os.environ, {"SAP_HOST": "myhost", "SAP_CLIENT": "100",
                                      "SAP_USERNAME": "user", "SAP_PASSWORD": "pass"},
                        clear=False):
            from aws_abap_accelerator.config.settings import SAPSettings
            s = SAPSettings(host="myhost", client="100", username="user", password="pass")
            assert s.ssl_verify is True

    def test_ssl_verify_independent_of_sap_secure(self, tmp_path):
        """S-03/B-01: ssl_verify must not be sourced from SAP_SECURE."""
        with patch.dict(os.environ, {"SAP_SECURE": "false"}, clear=False):
            from aws_abap_accelerator.config.settings import SAPSettings
            s = SAPSettings(host="h", client="100", username="u", password="p", secure=False)
            # ssl_verify should still be True regardless of SAP_SECURE
            assert s.ssl_verify is True


class TestCORSSettings:
    """Tests for CORSSettings validation."""

    def test_cors_disabled_by_default(self):
        """S-02: CORS must be disabled by default."""
        from aws_abap_accelerator.config.settings import CORSSettings
        c = CORSSettings()
        assert c.cors_enabled is False

    def test_cors_wildcard_rejected(self):
        """S-02: Wildcard origin must be rejected when CORS is enabled."""
        from aws_abap_accelerator.config.settings import CORSSettings
        with pytest.raises(ValueError, match="wildcard"):
            CORSSettings(cors_enabled=True, allowed_origins="*")

    def test_cors_specific_origin_accepted(self):
        """Specific origin must be accepted when CORS is enabled."""
        from aws_abap_accelerator.config.settings import CORSSettings
        c = CORSSettings(cors_enabled=True, allowed_origins="http://localhost:3000")
        assert c.cors_enabled is True


class TestSecretReader:
    """Tests for SecretReader password loading."""

    def test_password_from_file(self, tmp_path):
        """S-04/B-04: Password should be read from file when available."""
        secret_file = tmp_path / "sap_password"
        secret_file.write_text("my_secret_password")
        secret_file.chmod(0o600)

        from aws_abap_accelerator.config.settings import SecretReader
        with patch("aws_abap_accelerator.config.settings.SECRETS_DIR", str(tmp_path)):
            pwd = SecretReader.get_secret_or_env("SAP_PASSWORD", "sap_password")
        assert pwd == "my_secret_password"

    def test_empty_password_raises_error(self):
        """S-04/B-04: Empty password must raise ValueError with actionable message."""
        from aws_abap_accelerator.config.settings import SecretReader
        with patch.dict(os.environ, {"SAP_PASSWORD": ""}, clear=False):
            with patch("os.path.exists", return_value=False):
                with pytest.raises(ValueError, match="SAP_PASSWORD"):
                    SecretReader.get_secret_or_env("SAP_PASSWORD", "sap_password")
