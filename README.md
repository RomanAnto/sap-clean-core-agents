# SAP Clean Core — Kiro Agents & Copilot Skills

A **production-ready** agent-driven toolkit for SAP Clean Core compliance analysis, ABAP/S4 code quality review, and automated fix implementation planning. Built on Kiro CLI agents, GitHub Copilot Skills, and a Python FastMCP server that bridges the agents to SAP via ADT REST APIs.

**Key Features:**
- ✅ **6 specialized agents** — model-agnostic via Portkey AI gateway
- ✅ **Portkey integration** for provider-independent LLM routing (Anthropic, OpenAI, Azure, Bedrock, …)
- ✅ **4 Copilot skills** for IDE integration in VS Code
- ✅ **Python FastMCP server** with 8 SAP ADT tools (async httpx client)
- ✅ **All 7 security fixes** from Clean Core analysis applied (S-01 through S-07)
- ✅ **New `abap-fix-planner` agent** that transforms ATC findings into implementation plans
- ✅ **Complete CI/CD** with GitHub Actions, Dependabot, security scanning (bandit, safety)
- ✅ **Test suite** for settings, security, and tool handlers (pytest)

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Developer Machine                           │
│                                                                  │
│  ┌───────────────────────────┐   HTTP   ┌──────────────────┐   │
│  │    Kiro CLI Agents (6)    │ ◄──────► │   MCP Server     │   │
│  │                           │  :8001   │  (Python/FastMCP)│   │
│  │  - sap-atc-checker        │          │  Port 8001       │   │
│  │  - sap-custom-code-       │          │  Reads:          │   │
│  │    documenter             │          │  - mcp/sap.env   │   │
│  │  - sap-unused-code-       │          │  - secrets/      │   │
│  │    discovery              │          │    sap_password  │   │
│  │  - business-function-     │          └────────┬─────────┘   │
│  │    mapper                 │                   │ ADT/HTTPS   │
│  │  - abap-accelerator       │                   ▼             │
│  │  - abap-fix-planner  ←NEW │          ┌─────────────────┐   │
│  └───────────────────────────┘          │   SAP System    │   │
│                                         │  S/4HANA / ECC  │   │
│  ┌───────────────────────────┐          │  ADT REST API   │   │
│  │  GitHub Copilot Skills    │          └─────────────────┘   │
│  │  (VS Code integration)    │                                  │
│  │  - sap-atc-analysis       │                                  │
│  │  - abap-code-review       │                                  │
│  │  - clean-core-compliance  │                                  │
│  │  - fix-implementation-    │                                  │
│  │    planning          ←NEW │                                  │
│  └───────────────────────────┘                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Repository Structure

```
sap-clean-core-agents/
├── .kiro/agents/               ← Kiro CLI agent definitions (JSON)
├── .github/workflows/          ← CI/CD pipeline
├── agents/                     ← Agent instructions (Markdown)
│   ├── atc-checker/
│   ├── documenter/
│   ├── unused-code/
│   ├── business-function-mapper/
│   ├── abap-accelerator/
│   └── abap-fix-planner/       ← NEW: fix implementation planner
├── skills/                     ← GitHub Copilot Skill definitions
│   ├── sap-atc-analysis/
│   ├── abap-code-review/
│   ├── clean-core-compliance/
│   └── fix-implementation-planning/   ← NEW
├── mcp/
│   ├── mcp-launcher.sh
│   └── sap.env.example
├── secrets/                    ← Git-ignored; holds sap_password file
├── input/                      ← SAP API classification CSVs (from SAP/abap-atc-cr-cv-s4hc)
├── reports/                    ← Git-ignored agent output
│   ├── atc/
│   ├── docs/
│   ├── unused/
│   ├── fix-plans/              ← NEW: ABAP fix implementation plans
│   └── executive/
├── src/aws_abap_accelerator/   ← Python MCP server
├── tests/                      ← Test suite
├── check-setup.sh
└── AGENTS.md
```

---

## Agents

| Agent | Model Tier | Purpose |
|-------|------------|---------|
| `sap-atc-checker` | `STANDARD` | Run SAP ATC checks; classify Clean Core violations |
| `sap-custom-code-documenter` | `STANDARD` | Document ABAP custom code objects |
| `sap-unused-code-discovery` | `FAST` | Identify unused ABAP programs and classes |
| `business-function-mapper` | `STANDARD` | Map custom code to standard SAP business functions |
| `abap-accelerator` | `HIGH` | General-purpose SAP operations (full tool access) |
| `abap-fix-planner` | `HIGH` | **NEW**: Create fix implementation plans from ATC findings |

Model tiers resolve at runtime via Portkey env vars (`AGENT_MODEL_HIGH`, `AGENT_MODEL_STANDARD`,
`AGENT_MODEL_FAST`). Defaults: `claude-opus-4-5` / `claude-sonnet-4-5` / `claude-haiku-3-5`.

### Model Selection Rationale
- **`HIGH`** — Complex reasoning, multi-step planning, ambiguous SAP business logic
- **`STANDARD`** — Analysis, documentation, classification (best speed/quality balance)
- **`FAST`** — High-volume pattern matching, simple structural queries

---

## Quick Start

### Prerequisites
- Python 3.11+
- Git
- A SAP S/4HANA or SAP ECC system with ADT enabled
- Kiro CLI installed (`npm install -g @kiro/cli`)

### 1. Clone and setup
```bash
git clone https://github.com/RomanAnto/sap-clean-core-agents.git
cd sap-clean-core-agents
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Configure SAP connection
```bash
# Copy the template
cp mcp/sap.env.example mcp/sap.env

# Edit with your SAP system details
# - SAP_HOST: your S/4HANA hostname
# - SAP_CLIENT: client number (e.g., 100)
# - SAP_USERNAME: ABAP user with ADT authorization
# Required authorizations: S_ADT_RES, S_DEVELOP (display), S_CTS_ADMI
nano mcp/sap.env

# Create password file (600 permissions = owner read/write only)
mkdir -p secrets
echo -n "your_sap_password" > secrets/sap_password
chmod 600 secrets/sap_password
```

### 3. Configure Portkey (model-agnostic LLM gateway)
```bash
# Copy the Portkey template
cp mcp/portkey.env.example mcp/portkey.env

# Edit mcp/portkey.env:
#   1. Set PORTKEY_API_KEY  (get from https://app.portkey.ai/api-keys)
#   2. Create virtual keys for your preferred LLM provider in the Portkey
#      dashboard (https://app.portkey.ai/virtual-keys) and paste the slugs
#      into PORTKEY_VIRTUAL_KEY_HIGH / _STANDARD / _FAST
#   3. Optionally override AGENT_MODEL_* to switch from Claude to GPT-4o etc.
nano mcp/portkey.env

# Skip this step if you want to use Kiro's built-in Claude defaults directly.
```

### 4. Download SAP API classification data (optional but recommended)
```bash
# The input/ directory holds SAP API Clean Core classification CSVs
# Download from the official repo:
git clone --depth=1 https://github.com/SAP/abap-atc-cr-cv-s4hc.git /tmp/sap-atc-data
cp /tmp/sap-atc-data/src/data/*.csv input/ 2>/dev/null || true
cp /tmp/sap-atc-data/src/data/*.xml input/ 2>/dev/null || true

# Generate SHA-256 integrity checksums
cd input && sha256sum *.csv *.xml > SHA256SUMS 2>/dev/null || true; cd ..
```

### 5. Validate environment
```bash
bash check-setup.sh
# Output: "Status: ALL CHECKS PASSED — ready to run agents"
```

### 6. Start the MCP server
```bash
bash mcp/mcp-launcher.sh
# Output: [INFO] Starting MCP server on 127.0.0.1:8001
# Output: [INFO] Portkey configuration loaded from mcp/portkey.env   ← if portkey.env exists
```

### 7. Run an agent
In a new terminal:
```bash
# Run ATC checker on a specific package
kiro run sap-atc-checker --package ZFINANCE

# Generate ABAP fix implementation plan
kiro run abap-fix-planner --input reports/atc/latest.json
```

---

## MCP Server Architecture

The `src/aws_abap_accelerator/` directory contains a **stateless FastMCP server** that exposes **8 SAP ADT tools** over HTTP:

### Tools Available
1. **`connection_status`** — Verify SAP connection
2. **`get_objects`** — Query ABAP objects by package/type
3. **`get_source_code`** — Retrieve source code for a program/class
4. **`run_atc_check`** — Execute ATC checks on an object
5. **`get_where_used`** — Find where an object is referenced
6. **`search_objects`** — Full-text search in repository
7. **`activate_objects`** — Activate ABAP objects
8. **`create_transport`** — Create CTS transport requests

### Configuration
- **Port:** 8001 (default, configurable via `SERVER_PORT`)
- **Host:** 127.0.0.1 (localhost only; set to 0.0.0.0 for remote access)
- **Timeout:** 60 seconds per tool call (configurable)
- **Authentication:** SAP Basic Auth (username/password from `secrets/sap_password`)
- **SSL/TLS:** Configurable via `SAP_SECURE` and `SSL_VERIFY`

### Input Validation (Security Fix S-05)
All tool parameters are validated for:
- **Length limits:** Object names ≤40 chars, package names ≤40 chars, queries ≤200 chars
- **Character restrictions:** No `<`, `>`, `(`, `)`, quote characters
- **Source code:** ≤5 MB per file

### Code Organization
```
src/aws_abap_accelerator/
├── config/settings.py         # Pydantic settings with validators
├── server/fastmcp_server.py   # FastMCP server setup
├── server/tool_handlers.py    # Tool handler stubs
├── sap/sap_client.py          # Async httpx client for ADT REST API
├── utils/security.py          # Input validation functions
└── main.py                    # Entry point
```

---

## Agent Details

### `sap-atc-checker` (claude-sonnet-4-5)
**Purpose:** Run SAP ATC (ABAP Test Cockpit) compliance checks and classify findings by severity.

**Input:** Package name or list of object names  
**Output:** `reports/atc/atc-report-<timestamp>.json` + `reports/atc/atc-report-<timestamp>.md`

**Features:**
- Batch execution (3 objects per request to respect 60s timeout)
- Crash recovery via checkpoints
- Classification into: CRITICAL, HIGH, MEDIUM, LOW
- Detailed JSON + Markdown output

**Example:**
```bash
kiro run sap-atc-checker --package ZFINANCE --variant ABAP_CLOUD_READINESS_CHECK
```

---

### `abap-fix-planner` (claude-opus-4-5) — **NEW**
**Purpose:** Transform ATC findings into detailed ABAP fix implementation plans.

**Input:** ATC report JSON (from sap-atc-checker)  
**Output:** `reports/fix-plans/fix-plan-<timestamp>.md` + `reports/fix-plans/fix-plan-<timestamp>.json`

**Features:**
- Phase 1: Load ATC report, triage by severity (HIGH → MEDIUM → LOW)
- Phase 2: Retrieve source code (batches of 2)
- Phase 3: Fix planning with category decision table (NOT_RELEASED, DEPRECATED, STABLE)
- Phase 4: Generate implementation plan with:
  - Root cause analysis for each violation
  - Fix steps with code snippets
  - Transport strategy
  - Effort estimates: S (<4h), M (4-8h), L (1-3d), XL (>3d)
  - Dependency map
  - Rollback plan
  - RAP migration patterns as primary fix strategy

**Example:**
```bash
kiro run abap-fix-planner --input reports/atc/atc-report-latest.json
```

---

### Other Agents

- **`sap-custom-code-documenter`** (claude-sonnet-4-5): Generate Markdown docs for custom ABAP objects
- **`sap-unused-code-discovery`** (claude-haiku-3-5): Score decommission candidates (HIGH/MEDIUM/LOW)
- **`business-function-mapper`** (claude-sonnet-4-5): Map custom code to standard S/4HANA equivalents
- **`abap-accelerator`** (claude-opus-4-5): Full-access agent for complex ABAP tasks

---

## GitHub Copilot Skills

Four skills are available for VS Code integration:

| Skill | Model | Purpose |
|-------|-------|---------|
| `sap-atc-analysis` | sonnet-4-5 | Understand ATC check findings |
| `abap-code-review` | sonnet-4-5 | Review ABAP code against Clean Core + security checklist |
| `clean-core-compliance` | sonnet-4-5 | Explain Clean Core principles and extensibility tiers |
| `fix-implementation-planning` | opus-4-5 | Plan ABAP fixes with effort estimates and patterns |

**Usage in VS Code:**
1. Open a file containing ABAP code or ATC findings
2. Ask Copilot: "@sap-atc-analysis Explain this ATC error"
3. Copilot uses the skill to provide contextual guidance

---

## Report Outputs

After running agents, check these directories:

| Directory | Agent | Output |
|-----------|-------|--------|
| `reports/atc/` | sap-atc-checker | JSON + Markdown ATC findings |
| `reports/fix-plans/` | abap-fix-planner | JSON + Markdown implementation plans |
| `reports/docs/` | sap-custom-code-documenter | Markdown documentation |
| `reports/unused/` | sap-unused-code-discovery | Decommission candidate reports |
| `reports/executive/` | business-function-mapper | Executive summary mappings |

All reports are **git-ignored** to prevent accidentally committing SAP source code.

---

## Testing

### Run all tests
```bash
pytest tests/ -v
```

### Test categories
- **`test_settings.py`** — Config validation, SSL/CORS defaults, password handling
- **`test_security.py`** — Input length validation, SAP object name rules
- **`test_tool_handlers.py`** — Tool handler stubs, mock SAP client

### Test with coverage
```bash
pytest tests/ --cov=src/aws_abap_accelerator --cov-report=html
# Open htmlcov/index.html in browser
```

CI/CD requires ≥60% coverage.

---

## File Permissions & Secrets

**Files that must be git-ignored:**
- `mcp/sap.env` — SAP system connection details
- `secrets/sap_password` — Must have `600` permissions (owner read/write only)
- `reports/` — May contain SAP source code
- `input/*.csv`, `input/*.xml` — API classification data (only `input/SHA256SUMS` is tracked)

**Checked by:** `check-setup.sh` validates permissions and git-ignored status on each run.

---

## Configuration Reference

### `mcp/sap.env` Variables

**Required:**

| Variable | Type | Example | Description |
|----------|------|---------|-------------|
| `SAP_HOST` | string | `s4h-prod.acme.com` | SAP system hostname or IP address |
| `SAP_CLIENT` | string | `100` | SAP client number (3 digits) |
| `SAP_USERNAME` | string | `ABAP_USER` | ABAP username with ADT authorizations |

**Optional (with defaults):**

| Variable | Default | Type | Description |
|----------|---------|------|-------------|
| `SAP_INSTANCE` | `00` | string | SAP instance number (typically `00`, `01`, etc.) |
| `SAP_SECURE` | `true` | bool | Use HTTPS (`true`) or HTTP (`false`) |
| `SSL_VERIFY` | `true` | bool | Validate TLS certificates (`true`/`false`) |
| `SERVER_HOST` | `127.0.0.1` | string | MCP server bind address (localhost only by default) |
| `SERVER_PORT` | `8001` | int | MCP server TCP port |
| `CORS_ENABLED` | `false` | bool | Enable CORS support (disabled by default) |
| `CORS_ALLOWED_ORIGINS` | (empty) | string | Comma-separated list of allowed origins (e.g., `http://localhost:3000,https://myapp.example.com`) |
| `SERVER_LOG_LEVEL` | `INFO` | string | Logging level: `DEBUG`, `INFO`, `WARNING`, `ERROR` |

**Required Authorization Objects for ABAP User:**
- `S_ADT_RES` — Access to ADT development objects
- `S_DEVELOP` — Display/modify ABAP source code
- `S_CTS_ADMI` — Create/manage transport requests

### Example `mcp/sap.env`
```bash
# SAP Connection
SAP_HOST=s4h-prod.acme.com
SAP_CLIENT=100
SAP_USERNAME=ZBOT_USER
SAP_INSTANCE=00

# Security (defaults: both true)
SAP_SECURE=true
SSL_VERIFY=true

# MCP Server
SERVER_HOST=127.0.0.1
SERVER_PORT=8001
SERVER_LOG_LEVEL=INFO

# CORS (disabled by default)
CORS_ENABLED=false
CORS_ALLOWED_ORIGINS=
```

### Environment Variable Precedence

The system checks for secrets in this order:
1. **File:** `secrets/sap_password` (recommended)
2. **Environment:** `SAP_PASSWORD` env var (fallback, logged as WARNING)
3. **Missing:** Raises `ValueError` with actionable help message

---

## Dependencies

### Production (`requirements.txt`)
```
fastmcp==0.4.1                 # MCP server framework
pydantic==2.9.2                # Config validation
pydantic-settings==2.6.1       # Settings management
httpx==0.28.0                  # Async HTTP client
uvicorn==0.32.1                # ASGI server
cryptography==43.0.3           # SSL/TLS utilities
jsonschema==4.23.0             # JSON schema validation
```

### Development (`requirements-dev.txt`)
```
pytest==8.3.4                  # Test framework
pytest-asyncio==0.24.0         # Async test support
black==24.10.0                 # Code formatter
mypy==1.13.0                   # Type checker
bandit==1.8.0                  # Security linter (OWASP)
safety==3.2.9                  # Dependency vulnerability scan
```

---

## Security Fixes Applied

This repository implements **all 7 security fixes** from the SAP Clean Core analysis:

| Fix | Issue | Resolution |
|-----|-------|-----------|
| **S-01** | Password file permissions | `chmod 600` enforced in `mcp/sap.env.example` and `check-setup.sh` |
| **S-02** | CORS wildcard allowed | Wildcard rejected in `settings.py`; `CORSSettings` validator prevents `*` |
| **S-03** | SSL_VERIFY confused with SAP_SECURE | Separate fields in `settings.py`; both default to `true` |
| **S-04** | Empty password silently fails | `SecretReader.get_secret_or_env()` raises `ValueError` with 3-option help message |
| **S-05** | Unbounded input | Input length validators in `utils/security.py` for all 8 tool parameters |
| **S-06** | Prompt injection | `PROMPT_INJECTION_NOTICE` in FastMCP `instructions`; all agent docs include warnings |
| **S-07** | No integrity check | `check_input_integrity()` in `check-setup.sh` with SHA-256 verification |

---

## Security Notes

> **Never commit** `mcp/sap.env` or `secrets/sap_password`. Both are git-ignored.
> The `reports/` directory may contain SAP source code — also git-ignored.

**Default Security Posture:**
- ✅ SSL certificate verification **enabled by default**
- ✅ CORS **disabled by default**; explicit origin list required to enable
- ✅ SAP password read from `600`-permission file, not env vars
- ✅ All agents include prompt-injection warnings for SAP tool responses
- ✅ Input validation on all tool parameters (length bounds, SAP identifier rules)
- ✅ CI/CD scans with `bandit` (OWASP) and `safety` (dependencies)

---

## Developer Workflow

### 1. Add a new agent
```bash
# Create agent config in .kiro/agents/
# Create instructions in agents/<agent-name>/instructions.md
# Test locally: kiro run <agent-name> --help
```

### 2. Run tests
```bash
pytest tests/ --cov=src/aws_abap_accelerator --cov-report=term-missing
```

### 3. Run security scans
```bash
bandit -r src/ -ll
safety check -r requirements.txt --full-report
```

### 4. Push to GitHub
```bash
git add .
git commit -m "feat: [description]"
git push origin main
```

GitHub Actions CI will automatically:
- Run bandit (security static analysis)
- Run safety (dependency vulnerability scan)
- Run black (code format check)
- Run mypy (type check)
- Run pytest with coverage (≥60% threshold)

---

## Troubleshooting

### `ValueError: SAP_PASSWORD is empty`
**Cause:** Password file missing or empty.  
**Fix:**
```bash
echo -n "your_password" > secrets/sap_password
chmod 600 secrets/sap_password
```

### `SSL: CERTIFICATE_VERIFY_FAILED`
**Cause:** SAP system uses self-signed certificate.  
**Fix:** Set `SSL_VERIFY=false` in `mcp/sap.env` (dev only; not for production).

### MCP server won't start
**Fix:** Run `bash check-setup.sh` to diagnose missing dependencies or config issues.

### Agent can't connect to MCP server
**Ensure:**
- MCP server is running: `bash mcp/mcp-launcher.sh`
- MCP server is on `127.0.0.1:8001` (default)
- Firewall allows localhost:8001

---

## License

MIT-0

---

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit changes with clear messages
4. Push to your fork
5. Open a Pull Request with description of changes

All PRs must pass CI/CD checks (bandit, safety, black, mypy, pytest).
