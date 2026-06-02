---
name: fix-implementation-planning
description: >
  Creates detailed, actionable ABAP/S4 fix implementation plans from ATC check results.
  Use this skill when:
  - User wants to fix Clean Core violations found by the ATC checker agent
  - User asks "how do I fix this ATC finding?"
  - User needs a prioritised plan to address non-Clean-Core-compliant ABAP code
  - User wants effort estimates for ABAP code migration to Clean Core
  - User asks about migrating from a specific SAP pattern to a clean-core alternative

model: claude-opus-4-5
applyTo: "agents/abap-fix-planner/**,reports/fix-plans/**,reports/atc/**"
---

# ABAP Fix Implementation Planning Skill

## Purpose
This skill guides the creation of detailed implementation plans to fix ABAP/S4 code
that violates SAP Clean Core principles.

## When to Use This Skill

Activate when:
1. An ATC report exists in `reports/atc/` with HIGH or MEDIUM severity findings
2. The user asks "how do I fix [violation]?"
3. The user asks the `abap-fix-planner` agent to run
4. The user wants to prioritise remediation work

## How to Invoke the Fix Planner Agent

```bash
# Generate fix plan from the latest ATC report
kiro run abap-fix-planner

# Generate fix plan from a specific ATC report
kiro run abap-fix-planner --input reports/atc/atc-report-2026-06-01.json

# Generate fix plan for HIGH severity only
kiro run abap-fix-planner --severity HIGH
```

## Fix Plan Structure

A generated plan has these sections:

1. **Executive Summary** — total violations, total effort estimate
2. **Priority Ranking** — P0 (block migration), P1 (this sprint), P2 (informational)
3. **Fix Items** — one entry per violation with:
   - Object name, type, package
   - Exact violation (API name, line number)
   - Root cause explanation
   - Step-by-step fix instructions
   - SAP standard alternative
   - Test approach
   - Transport strategy
4. **Dependency Map** — which objects must be fixed before others
5. **Rollback Plan** — how to reverse each change

## Fix Pattern Quick Reference

| Violation Type | Fix Pattern | Typical Effort |
|----------------|-------------|----------------|
| Direct read of `BKPF`/`BSEG` | Use `I_JournalEntry` CDS View | M (4-8h) |
| Direct read of `KNA1` | Use `I_Customer` CDS View | S (<4h) |
| Direct read of `MARA`/`MARC` | Use `I_Product` CDS View | S-M |
| Write to standard table | Use BAPI or RAP BO action | L-XL |
| Unreleased function module call | Replace with released BAPI/OData | M |
| Classic user exit | Migrate to BAdI implementation | M-L |
| `CALL TRANSACTION` | Use BAPI or RAP BO action | L |
| SAP standard include | Create BAdI / Enhancement Spot | L-XL |
| Old-style BAPI (deprecated) | Switch to OData V4 / RAP | M-L |

## Generating a Fix for a Specific Pattern

### Example: Fix direct BKPF/BSEG read

If the ATC finding is:
```
Object: ZFIN_POSTING_REPORT
API: BSEG (table read)
Classification: NOT_RELEASED
Severity: HIGH
```

The generated fix plan step will be:

```abap
" BEFORE (non-Clean-Core):
SELECT * FROM bseg INTO TABLE @lt_bseg
  WHERE bukrs = @lv_bukrs AND gjahr = @lv_year.

" AFTER (Clean Core compliant):
SELECT * FROM I_JournalEntryItem INTO TABLE @lt_items
  WHERE CompanyCode = @lv_bukrs AND FiscalYear = @lv_year.
```

With transport instructions:
1. Create workbench transport
2. Replace SELECT statement in `ZFIN_POSTING_REPORT`
3. Map old field names to new CDS View field names (use `I_JournalEntryItem` field mapping)
4. Test: run report and compare output against non-modified DEV system
5. Release transport to QA

## Plan File Locations

- Plans are written to: `reports/fix-plans/`
- Latest plan pointer: `reports/fix-plans/latest.json`
- Human-readable: `reports/fix-plans/fix-plan-<timestamp>.md`
- Machine-readable: `reports/fix-plans/fix-plan-<timestamp>.json`

> **Note**: `reports/fix-plans/` is git-ignored as it may contain SAP source code.
