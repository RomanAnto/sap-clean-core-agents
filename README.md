# SAP Clean Core — Kiro Agents & Copilot Skills

A complete agent-driven toolkit for SAP Clean Core compliance analysis, ABAP/S4 code quality
review, and automated fix implementation planning. Built on Kiro CLI agents, GitHub Copilot
Skills, and a Python FastMCP server that bridges the agents to SAP via ADT REST APIs.

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

| Agent | Model | Purpose |
|-------|-------|---------|
| `sap-atc-checker` | `claude-sonnet-4-5` | Run SAP ATC checks; classify Clean Core violations |
| `sap-custom-code-documenter` | `claude-sonnet-4-5` | Document ABAP custom code objects |
| `sap-unused-code-discovery` | `claude-haiku-3-5` | Identify unused ABAP programs and classes |
| `business-function-mapper` | `claude-sonnet-4-5` | Map custom code to standard SAP business functions |
| `abap-accelerator` | `claude-opus-4-5` | General-purpose SAP operations (full tool access) |
| `abap-fix-planner` | `claude-opus-4-5` | **NEW**: Create fix implementation plans from ATC findings |

### Model Selection Rationale
- **`claude-opus-4-5`** — Complex reasoning, multi-step planning, ambiguous SAP business logic
- **`claude-sonnet-4-5`** — Analysis, documentation, classification (best speed/quality balance)
- **`claude-haiku-3-5`** — High-volume pattern matching, simple structural queries

---

## Quick Start

### 1. Clone this repository
```bash
git clone https://github.com/your-org/sap-clean-core-agents.git
cd sap-clean-core-agents
```

### 2. Clone the MCP server (ABAP Accelerator)
```bash
git clone https://github.com/aws-solutions-library-samples/guidance-for-deploying-sap-abap-accelerator-for-amazon-q-developer.git \
  aws-abap-accelerator-http
```

### 3. Configure SAP connection
```bash
cp mcp/sap.env.example mcp/sap.env
# Edit mcp/sap.env with your SAP host, client, username
nano mcp/sap.env

# Store password securely (600 = owner read/write only)
echo -n "your_sap_password" > secrets/sap_password
chmod 600 secrets/sap_password
```

### 4. Download SAP API classification data
```bash
# Download from the official SAP repository
git clone --depth=1 https://github.com/SAP/abap-atc-cr-cv-s4hc.git /tmp/sap-atc-data
cp /tmp/sap-atc-data/src/data/*.csv input/
cp /tmp/sap-atc-data/src/data/*.xml input/

# Generate integrity checksums
cd input && sha256sum *.csv *.xml > SHA256SUMS && cd ..
```

### 5. Validate setup
```bash
bash check-setup.sh
```

### 6. Start the MCP server
```bash
bash mcp/mcp-launcher.sh
```

### 7. Run an agent
```bash
# Check ATC violations in package ZFINANCE
kiro run sap-atc-checker --package ZFINANCE

# Generate fix implementation plan from last ATC report
kiro run abap-fix-planner --input reports/atc/latest.json
```

---

## Configuration Reference

### `mcp/sap.env` variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SAP_HOST` | Yes | — | SAP system hostname or IP |
| `SAP_CLIENT` | Yes | — | SAP client number (e.g., `100`) |
| `SAP_USERNAME` | Yes | — | ABAP user with ADT authorizations |
| `SAP_INSTANCE` | No | `00` | SAP instance number |
| `SAP_SECURE` | No | `true` | Use HTTPS (`true`/`false`) |
| `SSL_VERIFY` | No | `true` | Validate TLS certificate (`true`/`false`) |
| `CORS_ENABLED` | No | `false` | Enable CORS on MCP server |
| `CORS_ALLOWED_ORIGINS` | Cond. | — | Required if `CORS_ENABLED=true`. Specific origins only — no wildcard |

---

## Security Notes

> **Never commit** `mcp/sap.env` or `secrets/sap_password`. Both are git-ignored.
> The `reports/` directory may contain SAP source code — also git-ignored.

- SSL certificate verification is **enabled by default**
- CORS is **disabled by default**; explicit origin list required to enable
- SAP password is read from a `600`-permission file, not env vars
- All agents include prompt-injection warnings for SAP tool responses

---

## License

MIT-0
