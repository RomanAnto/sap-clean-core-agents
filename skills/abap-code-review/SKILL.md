---
name: abap-code-review
description: >
  Reviews ABAP/S4 source code for Clean Core compliance, security vulnerabilities,
  code quality issues, and best-practice violations. Use this skill when:
  - User pastes ABAP code and asks for a review
  - User wants to know if a piece of code is Clean Core compliant
  - User asks for ABAP code quality analysis
  - User wants to refactor ABAP code to follow modern patterns

model: claude-sonnet-4-5
applyTo: "**/*.abap,agents/abap-accelerator/**,agents/documenter/**"
---

# ABAP Code Review Skill

## Purpose
Expert ABAP code review capability covering Clean Core compliance, security, and quality.

## Review Checklist

### Clean Core Compliance
- [ ] No direct reads/writes on SAP standard tables (`BKPF`, `BSEG`, `KNA1`, `MARA`, etc.)
- [ ] No calls to NOT_RELEASED function modules
- [ ] No use of `CALL TRANSACTION` for posting
- [ ] No modification of SAP standard includes or programs
- [ ] No use of SYSTEM_INTERNAL APIs
- [ ] Uses CDS Views instead of direct table access where available

### Security
- [ ] No hardcoded credentials or passwords in source
- [ ] User authority checks present for sensitive operations (`AUTHORITY-CHECK`)
- [ ] Input validation for all user-supplied parameters
- [ ] SQL injection prevention (avoid dynamic `WHERE` clauses with user input)
- [ ] Proper error handling (no silent catches that swallow exceptions)

### Code Quality
- [ ] Methods are focused (< 50 lines ideally, < 100 lines max)
- [ ] No dead code (unreachable branches, unused variables)
- [ ] Proper ABAP documentation header present
- [ ] Uses structured exceptions (`CX_` classes) not `MESSAGE ... TYPE 'E'`
- [ ] No `FIELD-SYMBOLS` where class attributes would be cleaner
- [ ] Uses `DATA(lv_var)` inline declarations (ABAP 7.40+)

## Common Anti-Patterns to Flag

### Direct Table Read (NOT_RELEASED)
```abap
" ❌ WRONG — direct standard table read
SELECT SINGLE * FROM bkpf INTO ls_bkpf WHERE bukrs = lv_bukrs.

" ✅ CORRECT — use released CDS View
SELECT SINGLE * FROM I_JournalEntry INTO @ls_journal WHERE CompanyCode = @lv_bukrs.
```

### Dynamic SQL with user input (Security)
```abap
" ❌ WRONG — SQL injection risk
SELECT * FROM (lv_tablename) INTO TABLE lt_data WHERE (lv_where_clause).

" ✅ CORRECT — use static, validated queries only
```

### Swallowed exceptions (Quality)
```abap
" ❌ WRONG
TRY.
  " ... something
CATCH cx_root.  " catches everything, does nothing
ENDTRY.

" ✅ CORRECT
TRY.
  " ... something
CATCH cx_specific_exception INTO DATA(lx_exc).
  RAISE EXCEPTION TYPE cx_my_exception EXPORTING previous = lx_exc.
ENDTRY.
```

## SAP Clean Core Extension Patterns

When code needs to extend standard SAP behaviour, use these patterns in priority order:

1. **BAdI** (Business Add-In) — preferred for process extensions
2. **RAP Business Object** — preferred for UI and API-driven scenarios
3. **CDS View Extension** — for data model extensions
4. **ABAP Cloud API call** — for integration with released services
5. **Stable Interface** — only if no released alternative exists

## How to Request a Review

In VS Code Copilot chat, reference this skill and paste code:
```
@workspace Review this ABAP code for Clean Core compliance using the abap-code-review skill:

[paste code here]
```
