"""
SAP ABAP Accelerator MCP Server — settings.py

Security fixes applied (from repo analysis):
  S-02: CORS disabled by default; wildcard '*' origin rejected when enabled
  S-03: SSL_VERIFY separate from SAP_SECURE; both default true
  S-04: SAP_PASSWORD via env var emits warning; missing password raises clearly
  B-03: CORS default code matches documented default (False)
  B-04: Empty password raises ValueError with actionable message

Portkey integration:
  PortkeySettings reads PORTKEY_* env vars to configure the AI gateway.
  When PORTKEY_API_KEY is set, the MCP server uses Portkey for all LLM calls,
  enabling model-agnostic routing via virtual keys (Anthropic, OpenAI, etc.).
"""
from __future__ import annotations

import os
import logging
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# SAP Connection Settings
# ---------------------------------------------------------------------------

class SAPSettings(BaseSettings):
    """SAP system connection configuration."""

    host: str = Field(..., description="SAP system hostname or IP")
    client: str = Field(..., description="SAP client number (e.g. '100')")
    username: str = Field(..., description="SAP ABAP username with ADT authorizations")
    instance: str = Field("00", description="SAP instance number (two digits)")
    secure: bool = Field(True, description="Use HTTPS instead of HTTP")
    ssl_verify: bool = Field(True, description="Validate TLS certificate. Must be true in production.")

    model_config = SettingsConfigDict(env_prefix="SAP_", case_sensitive=False)

    @field_validator("host")
    @classmethod
    def validate_sap_host(cls, v: str) -> str:
        """Reject obviously invalid hostnames."""
        v = v.strip()
        if not v:
            raise ValueError("SAP_HOST must not be empty.")
        if ";" in v or "&" in v or "|" in v:
            raise ValueError(
                f"SAP_HOST contains invalid characters: {v!r}"
            )
        return v

    @field_validator("instance")
    @classmethod
    def validate_instance(cls, v: str) -> str:
        """SAP instance numbers are 00–99."""
        if not v.isdigit() or not (0 <= int(v) <= 99):
            raise ValueError("SAP_INSTANCE must be a two-digit number between 00 and 99.")
        return v.zfill(2)

    @field_validator("client")
    @classmethod
    def validate_client(cls, v: str) -> str:
        if not v.isdigit() or not (1 <= int(v) <= 999):
            raise ValueError("SAP_CLIENT must be a number between 1 and 999.")
        return v.zfill(3)


# ---------------------------------------------------------------------------
# Server Settings
# ---------------------------------------------------------------------------

class ServerSettings(BaseSettings):
    """MCP server runtime configuration."""

    host: str = Field("127.0.0.1", description="Bind address (default: loopback only)")
    port: int = Field(8001, description="Listen port")
    log_level: str = Field("INFO", description="Logging level")
    stateless_http: bool = Field(True, description="Run FastMCP in stateless HTTP mode")

    model_config = SettingsConfigDict(env_prefix="SERVER_", case_sensitive=False)

    @field_validator("port")
    @classmethod
    def validate_port(cls, v: int) -> int:
        if not (1024 <= v <= 65535):
            raise ValueError("SERVER_PORT must be between 1024 and 65535.")
        return v


# ---------------------------------------------------------------------------
# CORS Settings
# ---------------------------------------------------------------------------

class CORSSettings(BaseSettings):
    """CORS configuration.

    SECURITY: CORS is disabled by default.
    When enabled, CORS_ALLOWED_ORIGINS must be set to an explicit comma-separated
    list of allowed origins. The wildcard '*' is explicitly rejected to prevent
    cross-origin attacks on the locally running MCP server.
    """

    cors_enabled: bool = Field(False, description="Enable CORS (default: disabled)")
    allowed_origins: str = Field(
        "",
        description=(
            "Comma-separated list of allowed origins. "
            "Required when cors_enabled=True. Wildcard '*' is not permitted."
        ),
    )

    model_config = SettingsConfigDict(env_prefix="CORS_", case_sensitive=False)

    @field_validator("allowed_origins")
    @classmethod
    def validate_origins(cls, v: str, info) -> str:
        cors_on = info.data.get("cors_enabled", False)
        if cors_on:
            stripped = v.strip()
            if not stripped or stripped == "*":
                raise ValueError(
                    "CORS_ALLOWED_ORIGINS must be set to explicit origins (not wildcard '*') "
                    "when CORS_ENABLED=true. Example: CORS_ALLOWED_ORIGINS=http://localhost:3000"
                )
        return v

    def get_origins_list(self) -> List[str]:
        """Return allowed origins as a list."""
        if not self.allowed_origins.strip():
            return []
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]


# ---------------------------------------------------------------------------
# Portkey AI Gateway Settings
# ---------------------------------------------------------------------------

class PortkeySettings(BaseSettings):
    """Portkey AI gateway configuration for model-agnostic LLM routing.

    When PORTKEY_API_KEY is set, the MCP server uses Portkey as the LLM
    gateway. Virtual keys (set in the Portkey dashboard) abstract the actual
    provider so agents can switch between Anthropic, OpenAI, Azure, etc.
    without code changes.

    See mcp/portkey.env.example for setup instructions.
    """

    api_key: Optional[str] = Field(
        None,
        description="Portkey API key (from https://app.portkey.ai/api-keys)",
    )
    base_url: str = Field(
        "https://api.portkey.ai/v1",
        description="Portkey gateway base URL (override for self-hosted deployments)",
    )
    virtual_key_high: Optional[str] = Field(
        None,
        description="Virtual key for high-capability tier (Opus-class models)",
    )
    virtual_key_standard: Optional[str] = Field(
        None,
        description="Virtual key for standard tier (Sonnet-class models)",
    )
    virtual_key_fast: Optional[str] = Field(
        None,
        description="Virtual key for fast/high-volume tier (Haiku-class models)",
    )
    # Model tier overrides (mirror AGENT_MODEL_* used by Kiro agent JSON env vars)
    model_high: str = Field(
        "claude-opus-4-5",
        description="Model name for HIGH tier agents (AGENT_MODEL_HIGH)",
    )
    model_standard: str = Field(
        "claude-sonnet-4-5",
        description="Model name for STANDARD tier agents (AGENT_MODEL_STANDARD)",
    )
    model_fast: str = Field(
        "claude-haiku-3-5",
        description="Model name for FAST tier agents (AGENT_MODEL_FAST)",
    )

    model_config = SettingsConfigDict(env_prefix="PORTKEY_", case_sensitive=False)

    @property
    def enabled(self) -> bool:
        """Return True when a Portkey API key is configured."""
        return bool(self.api_key)

    def get_headers(self, tier: str = "standard") -> dict:
        """Return HTTP headers required for Portkey-routed requests.

        Args:
            tier: One of "high", "standard", or "fast".

        Returns:
            Dict of headers to include in every LLM API call.
        """
        if not self.enabled:
            return {}

        headers: dict = {"x-portkey-api-key": self.api_key}

        virtual_key_map = {
            "high": self.virtual_key_high,
            "standard": self.virtual_key_standard,
            "fast": self.virtual_key_fast,
        }
        virtual_key = virtual_key_map.get(tier)
        if virtual_key:
            headers["x-portkey-virtual-key"] = virtual_key

        return headers

    def get_model(self, tier: str = "standard") -> str:
        """Return the configured model name for the given tier."""
        model_map = {
            "high": self.model_high,
            "standard": self.model_standard,
            "fast": self.model_fast,
        }
        return model_map.get(tier, self.model_standard)


# ---------------------------------------------------------------------------
# Credential / Secret Loading
# ---------------------------------------------------------------------------

class SecretReader:
    """Reads secrets from files or environment variables.

    File-based secrets are preferred. Environment variable usage emits a
    security warning because env vars can appear in process listings, container
    inspection output, and log aggregators.
    """

    @staticmethod
    def read_secret_file(name: str) -> Optional[str]:
        """Read a secret from the `secrets/<name>` file next to this project."""
        secrets_dir = os.environ.get(
            "SECRETS_DIR",
            os.path.join(os.path.dirname(__file__), "..", "..", "..", "secrets"),
        )
        path = os.path.join(secrets_dir, name)
        try:
            with open(path, "r", encoding="utf-8") as fh:
                return fh.read().strip()
        except FileNotFoundError:
            return None
        except PermissionError:
            logger.error(
                "Permission denied reading secret file '%s'. "
                "Ensure the file has mode 600 and is owned by this process's user.",
                path,
            )
            return None

    @staticmethod
    def get_secret_or_env(secret_file_name: str, env_var_name: str) -> Optional[str]:
        """Return secret from file (preferred) or environment variable (fallback)."""
        # Prefer file-based secrets
        value = SecretReader.read_secret_file(secret_file_name)
        if value:
            return value

        # Fall back to env var with warning
        env_value = os.environ.get(env_var_name)
        if env_value:
            logger.warning(
                "%s set via environment variable '%s'. "
                "For better security, use a secret file 'secrets/%s' with mode 600.",
                secret_file_name,
                env_var_name,
                secret_file_name,
            )
            return env_value

        return None


# ---------------------------------------------------------------------------
# Top-level Config Loader
# ---------------------------------------------------------------------------

def load_config() -> dict:
    """Load and validate all configuration. Raises ValueError on misconfiguration."""
    sap = SAPSettings()  # type: ignore[call-arg]  # reads from env
    server = ServerSettings()
    cors = CORSSettings()
    portkey = PortkeySettings()

    # --- SAP password ---
    password = SecretReader.get_secret_or_env("sap_password", "SAP_PASSWORD")
    if not password:
        raise ValueError(
            "SAP password not found. Provide it via one of:\n"
            "  1. Secret file:    echo -n 'password' > secrets/sap_password && chmod 600 secrets/sap_password\n"
            "  2. Environment:    SAP_PASSWORD=your_password (less secure — avoid in production)\n"
        )

    return {
        "sap": sap,
        "server": server,
        "cors": cors,
        "sap_password": password,
        "portkey": portkey,
    }


def sanitize_for_logging(value: str, mask: str = "***") -> str:
    """Replace a secret value with a mask for safe logging."""
    return mask if value else "<empty>"
