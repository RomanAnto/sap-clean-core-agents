#!/usr/bin/env bash
# =============================================================================
# check-setup.sh — Validate SAP Clean Core Agent environment
#
# Security fixes applied (from repo analysis):
#   B-06: This script acts as a safety net alongside the .gitignore
#   S-07: Added SHA-256 integrity check for input/ classification data
#   S-01: Checks secret file permission (must be 600)
# =============================================================================
set -euo pipefail

CC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PASS=0
WARN=0
FAIL=0
JSON_MODE=false

# ---------------------------------------------------------------------------
# CLI argument parsing
# ---------------------------------------------------------------------------
for arg in "$@"; do
    case "$arg" in
        --json) JSON_MODE=true ;;
        --help|-h)
            echo "Usage: $0 [--json]"
            echo "  --json    Output results as JSON (for CI)"
            exit 0
            ;;
    esac
done

# ---------------------------------------------------------------------------
# Logging helpers
# ---------------------------------------------------------------------------
_results=()

log_check_pass() {
    PASS=$((PASS+1))
    if [ "$JSON_MODE" = false ]; then
        echo "  [PASS] $*"
    fi
    _results+=("{\"status\":\"pass\",\"message\":$(printf '%s' "$*" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))')}")
}

log_check_warn() {
    WARN=$((WARN+1))
    if [ "$JSON_MODE" = false ]; then
        echo "  [WARN] $*" >&2
    fi
    _results+=("{\"status\":\"warn\",\"message\":$(printf '%s' "$*" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))')}")
}

log_check_fail() {
    FAIL=$((FAIL+1))
    if [ "$JSON_MODE" = false ]; then
        echo "  [FAIL] $*" >&2
    fi
    _results+=("{\"status\":\"fail\",\"message\":$(printf '%s' "$*" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))')}")
}

log_section() {
    [ "$JSON_MODE" = false ] && echo "" && echo "=== $* ==="
}

# ---------------------------------------------------------------------------
# Check: sap.env exists and is not git-tracked
# ---------------------------------------------------------------------------
check_env_file() {
    log_section "SAP Environment File"
    local env_file="$CC_DIR/mcp/sap.env"

    if [ -f "$env_file" ]; then
        log_check_pass "mcp/sap.env exists"

        # Warn if git-tracked
        if git -C "$CC_DIR" ls-files --error-unmatch "$env_file" &>/dev/null 2>&1; then
            log_check_fail "mcp/sap.env is tracked by git — this file contains credentials. Run: git rm --cached mcp/sap.env"
        else
            log_check_pass "mcp/sap.env is NOT git-tracked (correct)"
        fi

        # Check for required keys
        for key in SAP_HOST SAP_CLIENT SAP_USERNAME; do
            if grep -q "^${key}=" "$env_file" 2>/dev/null; then
                log_check_pass "mcp/sap.env: ${key} is set"
            else
                log_check_fail "mcp/sap.env: ${key} is missing"
            fi
        done
    else
        log_check_fail "mcp/sap.env not found. Copy template: cp mcp/sap.env.example mcp/sap.env"
    fi
}

# ---------------------------------------------------------------------------
# Check: password file exists, has correct permissions, is not git-tracked
# ---------------------------------------------------------------------------
check_secret_file() {
    log_section "SAP Password File"
    local secret_file="$CC_DIR/secrets/sap_password"

    if [ -f "$secret_file" ]; then
        log_check_pass "secrets/sap_password exists"

        # Permission check (must be 600)
        if command -v stat &>/dev/null; then
            perms=$(stat -c "%a" "$secret_file" 2>/dev/null || stat -f "%OLp" "$secret_file" 2>/dev/null || echo "unknown")
            if [ "$perms" = "600" ]; then
                log_check_pass "secrets/sap_password permissions: 600 (correct)"
            elif [ "$perms" = "unknown" ]; then
                log_check_warn "secrets/sap_password: could not determine permissions"
            else
                log_check_fail "secrets/sap_password permissions: $perms (expected 600). Fix: chmod 600 secrets/sap_password"
            fi
        fi

        # Warn if git-tracked
        if git -C "$CC_DIR" ls-files --error-unmatch "$secret_file" &>/dev/null 2>&1; then
            log_check_fail "secrets/sap_password is tracked by git. Run: git rm --cached secrets/sap_password"
        else
            log_check_pass "secrets/sap_password is NOT git-tracked (correct)"
        fi

        # Check not empty
        if [ ! -s "$secret_file" ]; then
            log_check_fail "secrets/sap_password is empty"
        else
            log_check_pass "secrets/sap_password is non-empty"
        fi
    else
        log_check_fail "secrets/sap_password not found. Create it:"
        log_check_fail "  echo -n 'password' > secrets/sap_password && chmod 600 secrets/sap_password"
    fi
}

# ---------------------------------------------------------------------------
# Check: input/ API classification data and SHA-256 integrity
# ---------------------------------------------------------------------------
check_input_data() {
    log_section "SAP API Classification Data"
    local input_dir="$CC_DIR/input"

    if [ ! -d "$input_dir" ]; then
        log_check_fail "input/ directory not found. Download from SAP/abap-atc-cr-cv-s4hc."
        return
    fi

    # Check for CSV and XML files
    csv_count=$(find "$input_dir" -maxdepth 1 -name "*.csv" | wc -l)
    xml_count=$(find "$input_dir" -maxdepth 1 -name "*.xml" | wc -l)

    if [ "$csv_count" -gt 0 ]; then
        log_check_pass "input/: found $csv_count CSV file(s)"
    else
        log_check_fail "input/: no CSV files found. Download from SAP/abap-atc-cr-cv-s4hc."
    fi

    if [ "$xml_count" -gt 0 ]; then
        log_check_pass "input/: found $xml_count XML file(s)"
    else
        log_check_warn "input/: no XML ATC variant files found."
    fi

    # SHA-256 integrity check (S-07 fix)
    local sha_file="$input_dir/SHA256SUMS"
    if [ -f "$sha_file" ]; then
        if command -v sha256sum &>/dev/null; then
            if (cd "$input_dir" && sha256sum --check SHA256SUMS --quiet 2>/dev/null); then
                log_check_pass "input/: SHA-256 integrity verified"
            else
                log_check_fail "input/: checksum mismatch — re-download files from SAP/abap-atc-cr-cv-s4hc"
            fi
        elif command -v shasum &>/dev/null; then
            # macOS fallback
            if (cd "$input_dir" && shasum -a 256 --check SHA256SUMS --quiet 2>/dev/null); then
                log_check_pass "input/: SHA-256 integrity verified (shasum)"
            else
                log_check_fail "input/: checksum mismatch — re-download files from SAP/abap-atc-cr-cv-s4hc"
            fi
        else
            log_check_warn "input/: sha256sum/shasum not available — cannot verify integrity"
        fi
    else
        log_check_warn "input/: no SHA256SUMS file — integrity cannot be verified"
        log_check_warn "  Generate with: cd input && sha256sum *.csv *.xml > SHA256SUMS"
    fi
}

# ---------------------------------------------------------------------------
# Check: Python environment and dependencies
# ---------------------------------------------------------------------------
check_python() {
    log_section "Python Environment"

    if command -v python3 &>/dev/null; then
        pyver=$(python3 --version 2>&1)
        log_check_pass "python3: $pyver"
    else
        log_check_fail "python3 not found"
        return
    fi

    if [ -d "$CC_DIR/.venv" ]; then
        log_check_pass ".venv virtual environment exists"
    else
        log_check_warn ".venv not found. Create with: python3 -m venv .venv && .venv/bin/pip install -r requirements.txt"
    fi

    # Check key packages
    for pkg in fastmcp pydantic httpx pydantic_settings; do
        if python3 -c "import $pkg" 2>/dev/null; then
            log_check_pass "Python package: $pkg"
        else
            log_check_warn "Python package not installed: $pkg"
        fi
    done
}

# ---------------------------------------------------------------------------
# Check: reports/ directory structure
# ---------------------------------------------------------------------------
check_reports_dir() {
    log_section "Reports Directory"

    for subdir in atc docs unused fix-plans executive; do
        if [ -d "$CC_DIR/reports/$subdir" ]; then
            log_check_pass "reports/$subdir/ exists"
        else
            log_check_warn "reports/$subdir/ not found — will be created by agents on first run"
        fi
    done

    # Warn if reports/ is git-tracked
    if git -C "$CC_DIR" ls-files --error-unmatch "$CC_DIR/reports/" &>/dev/null 2>&1; then
        log_check_warn "reports/ directory has git-tracked files — may contain SAP source code"
    fi
}

# ---------------------------------------------------------------------------
# Check: .gitignore covers credentials and reports
# ---------------------------------------------------------------------------
check_gitignore() {
    log_section ".gitignore"
    local gi="$CC_DIR/.gitignore"

    if [ ! -f "$gi" ]; then
        log_check_fail ".gitignore not found — credentials and reports could be accidentally committed"
        return
    fi

    for pattern in "mcp/sap.env" "secrets/sap_password" "reports/"; do
        if grep -q "$pattern" "$gi" 2>/dev/null; then
            log_check_pass ".gitignore covers: $pattern"
        else
            log_check_fail ".gitignore missing entry for: $pattern"
        fi
    done
}

# ---------------------------------------------------------------------------
# Run all checks
# ---------------------------------------------------------------------------
[ "$JSON_MODE" = false ] && echo "SAP Clean Core Agent — Setup Validation"
[ "$JSON_MODE" = false ] && echo "========================================"

check_env_file
check_secret_file
check_input_data
check_python
check_reports_dir
check_gitignore

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
if [ "$JSON_MODE" = true ]; then
    # Build JSON array from _results
    joined=$(IFS=,; echo "${_results[*]:-}")
    python3 -c "
import json, sys
results_json = '[${joined}]'
results = json.loads(results_json)
summary = {
    'pass': sum(1 for r in results if r['status'] == 'pass'),
    'warn': sum(1 for r in results if r['status'] == 'warn'),
    'fail': sum(1 for r in results if r['status'] == 'fail'),
    'results': results
}
print(json.dumps(summary, indent=2))
"
else
    echo ""
    echo "========================================"
    echo "Results: PASS=$PASS  WARN=$WARN  FAIL=$FAIL"
    if [ "$FAIL" -gt 0 ]; then
        echo "Status: FAILED — fix the FAIL items above before running agents"
        exit 1
    elif [ "$WARN" -gt 0 ]; then
        echo "Status: WARNINGS — review the WARN items above"
        exit 0
    else
        echo "Status: ALL CHECKS PASSED — ready to run agents"
        exit 0
    fi
fi
