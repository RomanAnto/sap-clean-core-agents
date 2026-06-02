---
name: sap-atc-analysis
description: >
  Runs SAP ATC (ABAP Test Cockpit) checks and classifies findings against SAP Clean Core
  API classification data. Use this skill when you need to analyse ABAP/S4 code for
  Clean Core compliance violations, check API usage classification, or interpret ATC results.
  
  Relevant when:
  - User asks to check Clean Core compliance of an ABAP package
  - User provides ATC check results and wants them interpreted
  - User asks what SAP APIs are RELEASED vs NOT_RELEASED
  - User needs to understand an ATC finding message

model: claude-sonnet-4-5
applyTo: "agents/atc-checker/**,reports/atc/**,input/**"
---

# SAP ATC Analysis Skill

## Purpose
This skill provides domain knowledge for SAP ABAP Test Cockpit (ATC) analysis and
SAP Clean Core API classification.

## Clean Core API Classification Levels

| Level | Meaning | Action Required |
|-------|---------|-----------------|
| `RELEASED` | Officially released by SAP for customer use | None — safe to use |
| `STABLE` | Used by SAP internally, not officially released | Avoid; use with caution |
| `NOT_RELEASED` | Must not be used in Clean Core compliant systems | **Replace immediately** |
| `DEPRECATED` | Will be removed in a future release | Plan migration |
| `SYSTEM_INTERNAL` | SAP kernel/system internal — never for customer code | Replace immediately |

## Common ATC Check Variants for Clean Core

| Variant | Description |
|---------|-------------|
| `ABAP_CLOUD_COMPATIBILITY_CHECK` | Checks for ABAP Cloud (Tier 1 Clean Core) compliance |
| `ABAP_CLOUD_READINESS_CHECK` | Less strict; checks for S/4HANA readiness |
| `USAGE_STATISTICS` | Identifies unused objects |
| `CUSTOM_CODE_MIGRATION` | Checks readiness for S/4HANA migration |

## How to Invoke the ATC Checker Agent

```bash
# Check a specific package
kiro run sap-atc-checker --package ZFINANCE_CUSTOM

# Check multiple packages
kiro run sap-atc-checker --package ZFINANCE_CUSTOM,ZLOGISTICS_MM

# Check with a specific ATC variant
kiro run sap-atc-checker --package ZFINANCE_CUSTOM --variant ABAP_CLOUD_COMPATIBILITY_CHECK
```

## Interpreting Report Output

The ATC report JSON has this key structure:
```json
{
  "findings": [{
    "cleanCoreClassification": "NOT_RELEASED",
    "severity": "HIGH",
    "apiName": "FUNCTION_MODULE_NAME",
    "atcMessage": "...",
    "objectName": "ZFIN_REPORT",
    "lineNumber": 42
  }]
}
```

## Required Files
- `input/ABAP_COMPATIBILITY_CHECK.csv` — downloaded from SAP/abap-atc-cr-cv-s4hc
- `input/ABAP_API_CLASSIFICATION.csv` — downloaded from SAP/abap-atc-cr-cv-s4hc
- `input/SHA256SUMS` — integrity checksums

## When to Use This Skill
Use this skill when the user asks about:
- SAP Clean Core compliance in ABAP code
- Interpreting ATC findings
- Understanding which SAP APIs are safe to use
- Running an ATC check on a package
