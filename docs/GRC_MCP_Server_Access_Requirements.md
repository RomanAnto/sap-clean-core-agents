# GRC Access Requirements — SAP Clean Core MCP Server

**Document type:** Access Provisioning Request  
**System:** SAP ABAP Accelerator MCP Server (`sap-clean-core-agents`)  
**Audience:** GRC team, SAP Basis, Network/Firewall team  
**Last updated:** 2026-06-25

---

## 1. Executive Summary

The SAP Clean Core MCP (Model Context Protocol) server is a locally-run Python service
that bridges AI agents (running on a developer workstation) to the SAP system's
**ABAP Development Tools (ADT) REST API**. It enables automated Clean Core compliance
analysis, ATC check execution, and code documentation without any direct GUI access to
the SAP system.

The GRC team must action the following to allow the server to function:

| # | Action | Owner |
|---|--------|-------|
| 1 | Create a dedicated SAP service user with least-privilege authorisations | SAP Basis |
| 2 | Assign the correct SAP authorisation objects per agent tier | SAP Basis / GRC |
| 3 | Open outbound network route from developer workstations to SAP ADT port | Network / Firewall |
| 4 | Issue or confirm a valid TLS certificate on the SAP application server | SAP Basis / PKI |
| 5 | Register the service user in your PAM / CyberArk (or equivalent) | GRC / Security |
| 6 | Schedule quarterly access reviews for the service user | GRC |

---

## 2. Architecture & Data Flow

```
Developer Workstation (localhost)
│
├── AI Agent (Kiro / Copilot)
│       │  calls tools via HTTP
│       ▼
├── MCP Server  [127.0.0.1:8001]   ← runs locally, never exposed to internet
│       │
│       │  HTTPS (port 443) or HTTP (port 8000)
│       │  SAP Basic Auth  (username + password)
│       ▼
└── SAP Application Server  [SAP_HOST:443]
        │
        └── ADT REST API  (/sap/bc/adt/…)
```

**Key facts for GRC:**

- The MCP server is bound to **127.0.0.1 (loopback only)** by default. It is not exposed
  on the network unless `SERVER_HOST=0.0.0.0` is explicitly set.
- All SAP communication uses **HTTPS with TLS certificate validation** (`SAP_SECURE=true`,
  `SSL_VERIFY=true` are the hardcoded defaults). Disabling either requires an explicit config
  change and is logged as a warning.
- Authentication is **SAP Basic Auth** over HTTPS; credentials are stored in a file with
  `chmod 600` (owner read/write only), not in environment variables or source code.
- The server is **stateless** — it holds no session state and logs are written to stdout
  only (no local database, no secret storage beyond the password file).

---

## 3. SAP User Account

### 3.1 Account Type

Create a **service user** (user type `S` in SU01) — not a dialog user — to prevent
interactive logon and reduce the attack surface.

| Field | Required value |
|-------|---------------|
| User type | `S` — Service user |
| Logon method | Password (Basic Auth over HTTPS) |
| Validity | Set to the project end date; review quarterly |
| Initial password | Set via PAM / CyberArk; rotate every 90 days |
| Multiple logon | Allowed (stateless server may open concurrent sessions) |
| Client | The specific client where analysis will run (e.g., `100`) |

### 3.2 Recommended Username Convention

```
Z_MCP_<SYSTEM>_<CLIENT>    e.g.  Z_MCP_S4D_100
```

---

## 4. SAP Authorisation Objects

The server uses two logical permission profiles depending on which agents are active:

### Profile A — Read-Only (5 of 6 agents)

Used by: `sap-atc-checker`, `sap-custom-code-documenter`, `sap-unused-code-discovery`,
`business-function-mapper`, `abap-fix-planner`

| Authorisation Object | Field | Value | Justification |
|---------------------|-------|-------|---------------|
| `S_ADT_RES` | `ACTVT` | `03` (Display) | Required for all ADT REST API access |
| `S_DEVELOP` | `ACTVT` | `03` (Display) | Read source code, object metadata |
| `S_DEVELOP` | `DEVCLASS` | `*` (all packages) or restrict to `Z*`, `Y*` | Scope to custom code packages only |
| `S_DEVELOP` | `OBJTYPE` | `PROG`, `CLAS`, `FUGR`, `INTF`, `DOMA`, `DTEL` | ABAP object types accessed |
| `S_DEVELOP` | `OBJNAME` | `*` or restrict to naming convention | Object name filter |
| `S_TABU_DIS` | `DICBERCLS` | `SS` | ATC check result display (via ADT) |

> **Restriction recommendation:** Limit `S_DEVELOP / DEVCLASS` to `Z*` and `Y*` packages
> only. This prevents the agent from reading SAP standard object source code.

### Profile B — Read + Activate + Transport (1 agent)

Used by: `abap-accelerator` only (full-access agent — **use with caution**)

Includes all objects from Profile A, plus:

| Authorisation Object | Field | Value | Justification |
|---------------------|-------|-------|---------------|
| `S_DEVELOP` | `ACTVT` | `01` (Create), `02` (Change), `03` (Display) | Activate ABAP objects |
| `S_CTS_ADMI` | `CTS_ADMFCT` | `TRBEG` (Create transport requests) | Create CTS transports |
| `S_TRANSPRT` | `ACTVT` | `01`, `02`, `03` | Transport request management |
| `S_TRANSPRT` | `TTYPE` | `TASK`, `WBOBJ` | Workbench transport types |

> **Risk note:** Profile B grants write access to the SAP development environment.
> The `abap-accelerator` agent **must require explicit user confirmation** before
> calling `activate_objects` or `create_transport` tools (this is enforced in the
> agent instructions). Consider assigning Profile B to a separate, more-privileged
> service user and restricting it to a non-production system only.

### 4.1 Suggested Role Design

```
Z_ROLE_MCP_READONLY       ← Profile A — assign to most agents
Z_ROLE_MCP_FULLACCESS     ← Profile B — assign only to abap-accelerator service user
```

Both roles should be documented in your GRC tool (e.g., SAP GRC Access Control) as
**"Technical / Service Account Roles"** with no human-usable transaction codes.

---

## 5. ADT Service Activation (SAP Basis Action)

The ADT REST API must be active and reachable. Verify with SAP Basis:

| Check | Transaction / Path | Expected state |
|-------|--------------------|---------------|
| ICM (Internet Communication Manager) running | `SMICM` | Active |
| ADT service group active | `SICF` → `/sap/bc/adt` | Activated (`Active`) |
| HTTPS service handler configured | `SMICM` → Services | HTTPS listener on port 443 |
| SAP Web Dispatcher (if in front of SAP) | `SMICM` → Trace | Route `/sap/bc/adt/*` passes through |

The server accesses the following ADT REST paths (all under `/sap/bc/adt/`):

| Path | HTTP method | Tool | Profile needed |
|------|------------|------|---------------|
| `/sap/bc/adt/discovery` | GET | `connection_status` | A |
| `/sap/bc/adt/repository/informationsystem/search` | GET | `get_objects`, `search_objects` | A |
| `/sap/bc/adt/programs/programs/{name}/source/main` | GET | `get_source_code` | A |
| `/sap/bc/adt/atc/runs` | POST | `run_atc_check` | A |
| `/sap/bc/adt/repository/informationsystem/whereused` | GET | `get_where_used` | A |
| `/sap/bc/adt/activation` | POST | `activate_objects` | **B only** |
| `/sap/bc/adt/cts/transports` | POST | `create_transport` | **B only** |

---

## 6. Network Access Requirements

### 6.1 Firewall Rules Required

| Source | Destination | Port | Protocol | Purpose |
|--------|-------------|------|----------|---------|
| Developer workstation IP / subnet | SAP application server (`SAP_HOST`) | **443** | TCP / HTTPS | ADT REST API (recommended) |
| Developer workstation IP / subnet | SAP application server (`SAP_HOST`) | 8000 | TCP / HTTP | ADT REST API (fallback, **not recommended**) |

> The MCP server itself (`127.0.0.1:8001`) is loopback-only. No inbound firewall rule
> is needed for it unless `SERVER_HOST=0.0.0.0` is configured.

### 6.2 If Portkey AI Gateway Is Used

If outbound LLM routing via Portkey is enabled (see `mcp/portkey.env`), the following
additional outbound rule is needed from the developer workstation:

| Source | Destination | Port | Protocol | Purpose |
|--------|-------------|------|----------|---------|
| Developer workstation | `api.portkey.ai` | 443 | TCP / HTTPS | LLM API gateway |

If a self-hosted Portkey instance is used, replace `api.portkey.ai` with the internal
Portkey hostname.

### 6.3 DNS Resolution

The developer workstation must be able to resolve `SAP_HOST` (the SAP application server
hostname). If the SAP system is on an internal domain, ensure:

- Corporate DNS resolves the SAP hostname, **or**
- A static `/etc/hosts` entry is approved and documented

---

## 7. TLS / Certificate Requirements

| Requirement | Detail |
|-------------|--------|
| SAP server must present a valid TLS certificate | Signed by a trusted CA or a corporate intermediate CA |
| Certificate CN or SAN must match `SAP_HOST` | Prevent certificate mismatch errors |
| Certificate must not be expired | Standard PKI hygiene |
| `SSL_VERIFY=true` (default) must not be disabled | Disabling this removes MITM protection |

If the SAP system uses a **self-signed certificate** or an **internal corporate CA**:
- Export the CA certificate chain as PEM
- Install it into the OS trust store on the developer workstation, **or**
- Set the `REQUESTS_CA_BUNDLE` / `SSL_CERT_FILE` environment variable to point to
  the custom CA bundle before starting the MCP server

> **GRC note:** Any exception to certificate validation (`SSL_VERIFY=false`) must be
> formally risk-accepted, documented, and limited to isolated non-production environments.

---

## 8. Credential Management

### 8.1 Password Storage

The SAP service user password is stored in a local file:

```
secrets/sap_password      ← permissions: 600 (owner read/write only)
```

The file must be created manually by the developer running the server:

```bash
echo -n "your_password" > secrets/sap_password
chmod 600 secrets/sap_password
```

**The password is never**:
- Committed to version control (`.gitignore` excludes `secrets/`)
- Stored in `mcp/sap.env` or any other config file
- Logged or transmitted in plaintext

### 8.2 Password Rotation

| Activity | Frequency | Responsibility |
|----------|-----------|----------------|
| Rotate SAP service user password | Every 90 days | GRC / PAM owner |
| Update `secrets/sap_password` on workstations after rotation | On each rotation | Developer |
| Review PAM vault entry for service user | Quarterly | GRC |

### 8.3 PAM / CyberArk Onboarding

Onboard the service user to your Privileged Access Management (PAM) solution:

1. Safe name: `SAP-Clean-Core-MCP` (or per your naming standard)
2. Platform: SAP (Basic Auth)
3. Account type: Service account — no interactive use
4. Reconciliation: Automatic reconciliation on expiry

---

## 9. Access Review

| Review frequency | Reviewer | Scope |
|-----------------|----------|-------|
| Quarterly | GRC / Application owner | Confirm service user is still needed; verify authorisation profile has not been extended |
| On project closure | GRC | Disable / delete service user; revoke firewall rule |
| On developer leaving team | GRC / Manager | Revoke developer's ability to read `secrets/sap_password` on their workstation; rotate password |

---

## 10. Risk Register

The following residual risks should be formally accepted and recorded:

| Risk ID | Risk | Likelihood | Impact | Mitigation |
|---------|------|-----------|--------|-----------|
| R-01 | Service user credentials stored in a local file | Low | High | `chmod 600`, gitignore, PAM vault rotation |
| R-02 | `abap-accelerator` agent can activate objects and create transports | Low | High | Profile B restricted to dev landscape; agent requires explicit confirmation before write ops |
| R-03 | AI agent responses may include ABAP source code containing sensitive business logic | Medium | Medium | Source code stays local; not sent to LLM unless agent explicitly retrieves it |
| R-04 | Portkey gateway forwards model prompts to a third-party SaaS | Medium | Medium | Portkey is SOC 2 / ISO 27001 certified; enterprise on-prem option available |
| R-05 | MCP server misconfigured to bind on `0.0.0.0` | Low | High | Default is `127.0.0.1`; firewall should block port 8001 inbound regardless |

---

## 11. Checklist for GRC Approval

- [ ] SAP service user `Z_MCP_<SYSTEM>_<CLIENT>` created (user type `S`)
- [ ] `Z_ROLE_MCP_READONLY` (Profile A) created and assigned
- [ ] `Z_ROLE_MCP_FULLACCESS` (Profile B) created; assigned only if `abap-accelerator` is in scope
- [ ] ADT service (`/sap/bc/adt`) confirmed active in `SICF`
- [ ] Firewall rule open: workstation → SAP host on port 443
- [ ] TLS certificate on SAP server validated; CA chain trusted on workstation
- [ ] Service user onboarded to PAM / CyberArk
- [ ] Password rotation schedule set (90 days)
- [ ] Quarterly access review scheduled in GRC tool
- [ ] Risk items R-01 through R-05 formally accepted and recorded
- [ ] If Portkey is used: outbound port 443 to `api.portkey.ai` opened (or self-hosted Portkey deployed)

---

## 12. Contacts & Escalation

| Role | Responsibility |
|------|---------------|
| Application owner | Confirm business need; approve access scope |
| SAP Basis team | Create service user; activate ADT; confirm TLS cert |
| Network / Firewall team | Open port 443 outbound rule |
| GRC team | Document risk acceptance; schedule reviews |
| PKI / Certificates team | Issue or validate SAP server TLS certificate |
