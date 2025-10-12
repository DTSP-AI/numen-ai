# Documentation Index

**Last Updated:** October 8, 2025

This directory contains all project documentation organized by purpose.

---

## Quick Start

**New to the project?** Start here:
1. [`architecture/CLAUDE.md`](architecture/CLAUDE.md) - Project overview and tech stack
2. [`architecture/AGENT_CREATION_STANDARD.md`](architecture/AGENT_CREATION_STANDARD.md) - Core architectural standard
3. [`setup/SUPABASE_SETUP.md`](setup/SUPABASE_SETUP.md) - Environment setup

---

## 📁 Current Documentation (16 files)

### Core Architecture (`architecture/`)

| File | Description | Status |
|------|-------------|--------|
| **[CLAUDE.md](architecture/CLAUDE.md)** | Main project overview for Claude Code | ✅ Current |
| **[AGENT_CREATION_STANDARD.md](architecture/AGENT_CREATION_STANDARD.md)** | JSON Contract-First Architecture (THE standard) | ✅ Current |
| **[CurrentCodeBasePrompt.md](architecture/CurrentCodeBasePrompt.md)** | Current codebase state & context prompt | ✅ Current |
| **[E2E_PIPELINE_REPORT.md](architecture/E2E_PIPELINE_REPORT.md)** | End-to-end pipeline flow documentation | ✅ Current |
| **[CODEBASE_COMPLIANCE_AUDIT_2025-10-08.md](architecture/CODEBASE_COMPLIANCE_AUDIT_2025-10-08.md)** | Latest compliance audit (78% → 100%) | ✅ Current |

### Memory System (Mem0)

| File | Description | When to Use |
|------|-------------|-------------|
| **[MEM0_MIGRATION_GUIDE.md](architecture/MEM0_MIGRATION_GUIDE.md)** | Setup, troubleshooting, rollback | Setup & issues |
| **[MEM0_IMPLEMENTATION_SUMMARY.md](architecture/MEM0_IMPLEMENTATION_SUMMARY.md)** | Technical details, API reference | Development |
| **[FINAL_MEM0_STATUS.md](architecture/FINAL_MEM0_STATUS.md)** | Current status, verification | Status check |

### Integration References

| File | Description | When to Use |
|------|-------------|-------------|
| **[ULTIMATE-11LABS-KB.md](architecture/ULTIMATE-11LABS-KB.md)** | ElevenLabs TTS integration guide | Voice features |
| **[ULTIMATE-LIVEKIT-KB.md](architecture/ULTIMATE-LIVEKIT-KB.md)** | LiveKit real-time audio guide | Voice streaming |

### User Guides & Security

| File | Description | Audience |
|------|-------------|----------|
| **[USER_GUIDE_CONTROLS.md](architecture/USER_GUIDE_CONTROLS.md)** | User-facing control sliders | Frontend dev |
| **[SECURITY_QUICK_REFERENCE.md](architecture/SECURITY_QUICK_REFERENCE.md)** | Security guidelines & RLS | Security review |

### Setup & Configuration (`setup/`)

| File | Description | When to Use |
|------|-------------|-------------|
| **[SUPABASE_SETUP.md](setup/SUPABASE_SETUP.md)** | Complete Supabase setup guide | Initial setup |
| **[SUPABASE_CONFIG.md](setup/SUPABASE_CONFIG.md)** | Configuration reference | Configuration |
| **[GET_SUPABASE_CONNECTION_STRING.md](setup/GET_SUPABASE_CONNECTION_STRING.md)** | Connection string retrieval | Database connection |

---

## 📦 Archived Documentation (30 files)

Historical documentation preserved for reference:

### `archive/audits/` (12 files)
Old audit reports superseded by latest compliance audit.

### `archive/implementations/` (7 files)
Implementation summaries from earlier development phases.

### `archive/status/` (4 files)
Historical status reports and end-of-day summaries.

### `archive/reference/` (7 files)
Old references, prompts, and completed checklists.

**Note:** Archived docs are kept for historical context but are no longer current.

---

## Documentation Standards

### File Naming Convention

```
CATEGORY_DESCRIPTION.md           # General docs
CATEGORY_DESCRIPTION_YYYY-MM-DD.md  # Dated reports
```

**Examples:**
- `AGENT_CREATION_STANDARD.md` - Standard (no date, always current)
- `CODEBASE_COMPLIANCE_AUDIT_2025-10-08.md` - Dated audit report

### When to Archive

Archive documentation when:
1. ✅ Superseded by newer version
2. ✅ Objective completed (e.g., remediation checklists)
3. ✅ Historical value only (e.g., implementation summaries)

**Never delete** - always archive for historical reference.

---

## Quick Reference Guide

### "I need to..."

**Understand the project** → [`CLAUDE.md`](architecture/CLAUDE.md)

**Follow standards** → [`AGENT_CREATION_STANDARD.md`](architecture/AGENT_CREATION_STANDARD.md)

**Set up environment** → [`setup/SUPABASE_SETUP.md`](setup/SUPABASE_SETUP.md)

**Implement memory** → [`MEM0_MIGRATION_GUIDE.md`](architecture/MEM0_MIGRATION_GUIDE.md)

**Add voice features** → [`ULTIMATE-11LABS-KB.md`](architecture/ULTIMATE-11LABS-KB.md), [`ULTIMATE-LIVEKIT-KB.md`](architecture/ULTIMATE-LIVEKIT-KB.md)

**Check security** → [`SECURITY_QUICK_REFERENCE.md`](architecture/SECURITY_QUICK_REFERENCE.md)

**Review architecture** → [`E2E_PIPELINE_REPORT.md`](architecture/E2E_PIPELINE_REPORT.md)

**Check compliance** → [`CODEBASE_COMPLIANCE_AUDIT_2025-10-08.md`](architecture/CODEBASE_COMPLIANCE_AUDIT_2025-10-08.md)

---

## Maintenance

### Adding New Documentation

1. Create in appropriate directory (`architecture/`, `setup/`, etc.)
2. Add entry to this README
3. Follow naming conventions
4. Include "Last Updated" date in header

### Archiving Old Documentation

```bash
# Move to archive with category
mv docs/architecture/OLD_DOC.md docs/archive/{category}/

# Update this README to remove entry
```

### Reviewing Documentation

**Quarterly:** Review all current docs for accuracy
**After major changes:** Update relevant docs and audit reports
**Before release:** Verify all setup guides work

---

## Contributing

When adding/updating documentation:
1. ✅ Update this README index
2. ✅ Use clear, descriptive titles
3. ✅ Include "Last Updated" dates
4. ✅ Follow existing formatting patterns
5. ✅ Archive (don't delete) obsolete docs

---

## Support

**Questions about docs?** Check:
1. This README for navigation
2. [`CLAUDE.md`](architecture/CLAUDE.md) for project overview
3. Relevant guide from table above

**Need to update docs?** Follow the standards above.

---

## Summary

✅ **16 essential current docs** - Easy to find
📦 **30 archived docs** - Historical reference
📋 **Clear organization** - By purpose and category
🔍 **Quick navigation** - Use tables above

**Last Cleanup:** October 8, 2025
