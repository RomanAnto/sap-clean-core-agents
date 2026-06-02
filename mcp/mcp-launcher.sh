#!/usr/bin/env bash
# =============================================================================
# mcp-launcher.sh — Start the SAP ABAP Accelerator MCP Server
#
# Security fixes applied (from repo analysis):
#   S-01: Password file chmod instruction uses 600 not 644
#   S-03: SSL_VERIFY is independent of SAP_SECURE; both default to true
#   B-01: SSL_VERIFY no longer incorrectly aliased to SAP_SECURE
# =============================================================================
set -euo pipefail

CC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="$CC_DIR/mcp/sap.env"
SECRET_FILE="$CC_DIR/secrets/sap_password"

# ---------------------------------------------------------------------------
# Logging helpers
# ---------------------------------------------------------------------------
log_info()  { echo "[INFO]  $*"; }
log_error() { echo "[ERROR] $*" >&2; }
log_warn()  { echo "[WARN]  $*" >&2; }

# ---------------------------------------------------------------------------
# Validate sap.env before sourcing
# ---------------------------------------------------------------------------
validate_env_file() {
    local env_file="$1"

    if [ ! -f "$env_file" ]; then
        log_error "sap.env not found at: $env_file"
        log_error "Copy the template and fill in your values:"
        log_error "  cp mcp/sap.env.example mcp/sap.env"
        exit 1
    fi

    # Reject any line containing command substitution or subshells to prevent
    # code injection via a tampered env file.
    if grep -qE '\$\(|\`' "$env_file" 2>/dev/null; then
        log_error "sap.env contains command substitution characters (\$(...) or backtick)."
        log_error "This is a security risk. Refusing to source the file."
        exit 1
    fi

    # Require that every non-comment, non-blank line is a simple KEY=VALUE pair.
    while IFS= read -r line; do
        # Skip blank lines and comments
        [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue
        if ! [[ "$line" =~ ^[A-Z_][A-Z0-9_]*= ]]; then
            log_error "sap.env contains an unexpected line format: $line"
            log_error "Only KEY=VALUE lines are permitted."
            exit 1
        fi
    done < "$env_file"
}

# ---------------------------------------------------------------------------
# Validate numeric port
# ---------------------------------------------------------------------------
validate_port() {
    local port="$1"
    if ! [[ "$port" =~ ^[0-9]+$ ]] || [ "$port" -lt 1024 ] || [ "$port" -gt 65535 ]; then
        log_error "Invalid port: $port. Must be a number between 1024 and 65535."
        exit 1
    fi
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
log_info "SAP ABAP Accelerator MCP Launcher"
log_info "Working directory: $CC_DIR"

# Load environment
validate_env_file "$ENV_FILE"
# shellcheck source=/dev/null
source "$ENV_FILE"

# Validate required variables
: "${SAP_HOST:?SAP_HOST is not set in mcp/sap.env}"
: "${SAP_CLIENT:?SAP_CLIENT is not set in mcp/sap.env}"
: "${SAP_USERNAME:?SAP_USERNAME is not set in mcp/sap.env}"

# Port configuration
MCP_PORT="${SERVER_PORT:-8001}"
validate_port "$MCP_PORT"

# --- SSL configuration ---
# SAP_SECURE controls whether HTTPS is used (HTTP vs HTTPS).
# SSL_VERIFY controls whether TLS certificates are validated (independent setting).
# BOTH default to true for security. Never set SSL_VERIFY=false in production.
export SAP_SECURE="${SAP_SECURE:-true}"
export SSL_VERIFY="${SSL_VERIFY:-true}"

if [ "$SSL_VERIFY" = "false" ]; then
    log_warn "SSL_VERIFY=false — TLS certificate validation is DISABLED."
    log_warn "This is insecure. Only use in isolated development environments."
fi

# --- Read password from file (avoids process list exposure) ---
if [ ! -f "$SECRET_FILE" ]; then
    log_error "Password file not found: $SECRET_FILE"
    log_error "Create it with:"
    log_error "  echo -n 'your_password' > secrets/sap_password"
    log_error "  chmod 600 secrets/sap_password"
    exit 1
fi

# Check file permissions — warn if not 600
if command -v stat &>/dev/null; then
    perms=$(stat -c "%a" "$SECRET_FILE" 2>/dev/null || stat -f "%OLp" "$SECRET_FILE" 2>/dev/null || echo "unknown")
    if [ "$perms" != "600" ] && [ "$perms" != "unknown" ]; then
        log_warn "secrets/sap_password has permissions $perms — expected 600."
        log_warn "Fix with: chmod 600 secrets/sap_password"
    fi
fi

# Export password via SECRETS_DIR so Python reads from file (not env var)
export SECRETS_DIR="$CC_DIR/secrets"

# --- MCP server configuration ---
export SERVER_PORT="$MCP_PORT"
export SERVER_HOST="${SERVER_HOST:-127.0.0.1}"
export FASTMCP_STATELESS_HTTP=true  # Each tool call is independent; no session state required

log_info "Starting MCP server on ${SERVER_HOST}:${MCP_PORT}"
log_info "SAP host: ${SAP_HOST} | client: ${SAP_CLIENT} | user: ${SAP_USERNAME}"
log_info "HTTPS: ${SAP_SECURE} | SSL verify: ${SSL_VERIFY}"

# Activate Python virtual environment if present
if [ -d "$CC_DIR/.venv" ]; then
    # shellcheck source=/dev/null
    source "$CC_DIR/.venv/bin/activate"
    log_info "Activated virtual environment: $CC_DIR/.venv"
fi

# Launch the MCP server
exec python -m aws_abap_accelerator.main
