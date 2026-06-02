---
name: clean-core-compliance
description: >
  Provides SAP Clean Core compliance knowledge, S/4HANA extension model guidance,
  and classification of SAP APIs. Use this skill when:
  - User asks what "Clean Core" means in SAP context
  - User needs to understand SAP extensibility tiers (Tier 1/2/3)
  - User wants to know the correct extension pattern for a SAP process
  - User asks about ABAP Cloud, BTP integration, or SAP public APIs
  - User needs to understand the SAP API Business Hub

model: claude-sonnet-4-5
applyTo: "agents/**,skills/**,reports/**"
---

# SAP Clean Core Compliance Skill

## What is SAP Clean Core?

SAP Clean Core is the principle of keeping the SAP S/4HANA core system unmodified
(or minimally modified) to ensure:
- Smooth upgrades without custom code breaking
- Access to SAP innovation delivered via standard releases
- Lower total cost of ownership
- Compatibility with SAP BTP (Business Technology Platform) extensions

## SAP Extensibility Tiers

SAP defines three extensibility tiers:

### Tier 1 — ABAP Cloud (Highest restriction)
- Only SAP-released APIs (`C1` released) may be used
- Code must compile in ABAP Cloud environment
- Used for: new custom apps on BTP ABAP Environment
- ATC variant: `ABAP_CLOUD_COMPATIBILITY_CHECK`

### Tier 2 — S/4HANA Extensions (Standard restriction)
- Released APIs plus SAP-internal stable APIs may be used
- Code runs in the S/4HANA embedded ABAP stack
- Used for: S/4HANA custom extensions that must survive upgrades
- ATC variant: `ABAP_CLOUD_READINESS_CHECK`

### Tier 3 — Legacy Custom Code (No restriction, not recommended)
- Any API can be used including NOT_RELEASED
- High upgrade risk
- Target: migrate Tier 3 code to Tier 1 or Tier 2

## SAP API Classification in Code

```abap
" Check the API classification in ABAP:
" Go to transaction SE84 → Repository Information System
" Or check: https://api.sap.com (SAP API Business Hub)
```

## Key SAP Extension Points

| Extension Need | Use This | Not This |
|----------------|----------|----------|
| Enhance standard business logic | BAdI | Implicit enhancement / `INCLUDE`) |
| Custom UI on standard Fiori app | Fiori Extension / Key User tool | Custom BSP/WebDynpro |
| Custom data model | CDS View Extension (`EXTEND VIEW`) | Adding Z-fields to standard tables |
| Process orchestration | SAP BTP Integration Suite | Z-FM calling RFC |
| AI/ML augmentation | SAP AI Core + ABAP SDK | Custom ML code in ABAP |
| Custom reports | RAP BO + Analytical CDS View | Classical ALV reports reading standard tables |

## SAP Public API Resources

- **SAP API Business Hub**: https://api.sap.com
- **S/4HANA Cloud APIs**: Search for `S/4HANA Cloud` product
- **ABAP Platform Released APIs**: Transaction `SE84` → Released APIs
- **ATC Classification Data**: https://github.com/SAP/abap-atc-cr-cv-s4hc

## Clean Core Certification Criteria

For a system to be considered Clean Core:
1. No modification of SAP standard objects (allowed: 0 modifications)
2. All custom code uses only RELEASED or STABLE APIs
3. All extensions use SAP-approved extension patterns (BAdI, RAP, CDS Extension)
4. No direct reads/writes on SAP standard database tables without using released APIs
5. ATC check variant `ABAP_CLOUD_READINESS_CHECK` passes with zero HIGH findings
