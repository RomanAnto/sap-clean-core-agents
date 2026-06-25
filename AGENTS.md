# AGENTS.md — SAP Clean Core Agent Registry

This file describes all agents in this repository, their purposes, tool scopes,
and model tiers. Models are resolved at runtime via **Portkey** (AI gateway),
making every agent model-agnostic — swap providers by changing env vars, no
code edits required.

See [mcp/portkey.env.example](mcp/portkey.env.example) for gateway setup.

---

## Agent Catalogue

### 1. `sap-atc-checker`

| Property | Value |
|----------|-------|
| **Config** | `.kiro/agents/sap-atc-checker.json` |
| **Instructions** | `agents/atc-checker/instructions.md` |
| **Model tier** | `STANDARD` → `${AGENT_MODEL_STANDARD:-claude-sonnet-4-5}` |
| **Access Level** | Read + Write reports |

**Purpose**: Connects to the SAP system via MCP, runs ABAP Test Cockpit (ATC) checks against
one or more packages, classifies each finding against the SAP Clean Core API classification
data in `input/`, and writes a structured JSON + Markdown report to `reports/atc/`.

**Tools granted**:
- `read`, `write`, `todo`, `introspect`, `knowledge`
- `@sap-abap-accelerator/aws_abap_cb_connection_status`
- `@sap-abap-accelerator/aws_abap_cb_get_objects`
- `@sap-abap-accelerator/aws_abap_cb_run_atc_check`

---

### 2. `sap-custom-code-documenter`

| Property | Value |
|----------|-------|
| **Config** | `.kiro/agents/sap-custom-code-documenter.json` |
| **Instructions** | `agents/documenter/instructions.md` |
| **Model tier** | `STANDARD` → `${AGENT_MODEL_STANDARD:-claude-sonnet-4-5}` |
| **Access Level** | Read-only SAP access |

**Purpose**: Reads ABAP class, function module, and program source code from SAP via ADT,
generates structured documentation (purpose, inputs, outputs, dependencies), and writes
Markdown documentation to `reports/docs/`.

**Tools granted**:
- `read`, `write`, `todo`, `knowledge`
- `@sap-abap-accelerator/aws_abap_cb_connection_status`
- `@sap-abap-accelerator/aws_abap_cb_get_objects`
- `@sap-abap-accelerator/aws_abap_cb_get_source_code`

---

### 3. `sap-unused-code-discovery`

| Property | Value |
|----------|-------|
| **Config** | `.kiro/agents/sap-unused-code-discovery.json` |
| **Instructions** | `agents/unused-code/instructions.md` |
| **Model tier** | `FAST` → `${AGENT_MODEL_FAST:-claude-haiku-3-5}` |
| **Access Level** | Read-only SAP access |

**Purpose**: Identifies ABAP programs, function groups, and classes that have had no runtime
usage in the configured period (default: 6 months). Uses ATC usage statistics variant and
SAP Where-Used lists. Outputs a prioritised list to `reports/unused/`.

**Tools granted**:
- `read`, `write`, `todo`
- `@sap-abap-accelerator/aws_abap_cb_connection_status`
- `@sap-abap-accelerator/aws_abap_cb_get_objects`
- `@sap-abap-accelerator/aws_abap_cb_run_atc_check`
- `@sap-abap-accelerator/aws_abap_cb_get_where_used`

---

### 4. `business-function-mapper`

| Property | Value |
|----------|-------|
| **Config** | `.kiro/agents/business-function-mapper.json` |
| **Instructions** | `agents/business-function-mapper/instructions.md` |
| **Model tier** | `STANDARD` → `${AGENT_MODEL_STANDARD:-claude-sonnet-4-5}` |
| **Access Level** | Read-only SAP access + knowledge base |

**Purpose**: Reads custom ABAP code, analyses its business logic, and maps each custom
object to the standard SAP business function it replaces or enhances. Outputs a mapping
table with standard S/4HANA API alternatives where applicable.

**Tools granted**:
- `read`, `write`, `todo`, `introspect`, `knowledge`
- `@sap-abap-accelerator/aws_abap_cb_connection_status`
- `@sap-abap-accelerator/aws_abap_cb_get_objects`
- `@sap-abap-accelerator/aws_abap_cb_get_source_code`

---

### 5. `abap-accelerator`

| Property | Value |
|----------|-------|
| **Config** | `.kiro/agents/abap-accelerator.json` |
| **Instructions** | `agents/abap-accelerator/instructions.md` |
| **Model tier** | `HIGH` → `${AGENT_MODEL_HIGH:-claude-opus-4-5}` |
| **Access Level** | Full (read + write + shell + all SAP tools) |

**Purpose**: General-purpose ABAP development assistant. Can read, analyse, and produce
ABAP code, trigger SAP transports, and co-ordinate across other agents. Use sparingly —
this agent has the highest tool access level.

**Tools granted**:
- `read`, `write`, `shell`, `todo`, `introspect`, `knowledge`
- All `@sap-abap-accelerator/*` tools

---

### 6. `abap-fix-planner` *(NEW)*

| Property | Value |
|----------|-------|
| **Config** | `.kiro/agents/abap-fix-planner.json` |
| **Instructions** | `agents/abap-fix-planner/instructions.md` |
| **Model tier** | `HIGH` → `${AGENT_MODEL_HIGH:-claude-opus-4-5}` |
| **Access Level** | Read reports + Read SAP (no write to SAP) |

**Purpose**: Consumes ATC check results (from `reports/atc/`) and the Clean Core API
classification data to produce a detailed, prioritised **ABAP/S4 Fix Implementation Plan**.
The plan specifies:
- Which custom code objects violate Clean Core
- The exact violation category (Released API, Stable API, Not Released, etc.)
- The recommended clean-core migration pattern (BAdI, RAP, OData, etc.)
- Step-by-step implementation instructions for each fix
- Effort estimates and priority ranking
- Transport strategy and test approach

The plan is written to `reports/fix-plans/` in both Markdown and JSON formats.

**Tools granted**:
- `read`, `write`, `todo`, `introspect`, `knowledge`
- `@sap-abap-accelerator/aws_abap_cb_connection_status`
- `@sap-abap-accelerator/aws_abap_cb_get_objects`
- `@sap-abap-accelerator/aws_abap_cb_get_source_code`

---

## Model Tiers & Portkey Gateway

Agents are **model-agnostic**: each agent is assigned a capability *tier*, not a
specific model. The actual model is resolved at runtime via environment variables
routed through the [Portkey AI gateway](https://portkey.ai).

### Capability Tiers

| Tier | Env var | Default | Suitable replacements |
|------|---------|---------|----------------------|
| `HIGH` | `AGENT_MODEL_HIGH` | `claude-opus-4-5` | `gpt-4o`, `gemini-1.5-pro` |
| `STANDARD` | `AGENT_MODEL_STANDARD` | `claude-sonnet-4-5` | `gpt-4o-mini`, `claude-3-5-sonnet` |
| `FAST` | `AGENT_MODEL_FAST` | `claude-haiku-3-5` | `gpt-4o-mini`, `gemini-flash` |

All models must support **tool-use / function calling** — the MCP tool calls will
fail silently with models that do not.

### Switching Providers with Portkey

1. Create virtual keys in the [Portkey dashboard](https://app.portkey.ai/virtual-keys)
   pointing to your preferred provider (Anthropic, OpenAI, Azure, AWS Bedrock, etc.).
2. Copy and fill `mcp/portkey.env.example` → `mcp/portkey.env`:
   ```bash
   cp mcp/portkey.env.example mcp/portkey.env
   # Set PORTKEY_API_KEY, PORTKEY_VIRTUAL_KEY_*, and AGENT_MODEL_* as needed
   ```
3. Start the MCP server — the launcher picks up `portkey.env` automatically.

If no `portkey.env` exists the agents fall back to their hardcoded defaults
(`claude-opus-4-5` / `claude-sonnet-4-5` / `claude-haiku-3-5`).

---

## Agent Execution Order (Recommended)

For a full Clean Core assessment and fix cycle:

```
1. sap-atc-checker          → reports/atc/
2. sap-unused-code-discovery → reports/unused/
3. business-function-mapper  → reports/docs/   (optional, enrich context)
4. sap-custom-code-documenter → reports/docs/
5. abap-fix-planner          → reports/fix-plans/   ← REQUIRES step 1
```

`abap-accelerator` is used on-demand for ad-hoc ABAP work, not as part of the batch pipeline.
