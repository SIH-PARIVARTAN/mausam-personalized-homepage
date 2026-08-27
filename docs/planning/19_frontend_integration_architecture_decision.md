# 19. Frontend Integration Architecture Decision

**Topic:** Final architectural reconciliation between the main SIH repository (`FastAPI` + `Next.js` scaffold) and the teammate's separate prototype (`Flask` + `Jinja` + `Firebase`).
**Status:** DECISION
**Date:** 2026-08-27

## 1. Core Architectural Verdict
**DECISION:** The MAIN REPOSITORY architecture (`FastAPI` > `Adapters` > `Engine` > `Postgres`) remains the strict, authoritative baseline.

**JUSTIFICATION:**
The separate prototype contains an excellent UI layout, strong responsive custom CSS, and a working onboarding flow. However, its backend architecture constitutes a massive regression from the SIH MVP constraints:
- It bypasses the deterministic scoring engine and implements its own hardcoded scoring math in `personalization.py`.
- It directly couples to Open-Meteo in `weather_service.py`, ignoring our standardized Adapter boundaries (essential for IMD).
- It duplicates preference data in Firestore instead of the established Postgres cache.

To accept the teammate's Flask app as the final repo would mean throwing away our core MVP logic and auditability. Therefore, the UI will be salvaged, migrated to the original Next.js scaffold, and connected to the existing FastAPI backend.

## 2. Component Disposition Summary

| Component (Source) | Final Decision | Target | Action |
|---------------------|----------------|--------|--------|
| Main `engine/` | **KEEP** | Main Repo | Retain as the only source of truth for scoring math. Do not accept Python math from Flask repo. |
| Main `backend/` | **KEEP** | Main Repo | Retain as the only API handler. |
| Main `adapters/` | **KEEP** | Main Repo | Continue using fixtures/live adapters. Discard `weather_service.py` from Flask. |
| Flask `app.py` | **DISCARD** | N/A | Routing logic will shift to Next.js App Router (`app/page.tsx`, etc.). |
| Flask `templates/` | **MIGRATE** | Next.js Components | Convert Jinja HTML structure into React `.tsx` components, stripping Jinja logic. |
| Flask `css/` & Assets| **MIGRATE** | Next.js `public/` & `src/` | Preserve the teammate's visual design. |
| Firebase Auth | **ADAPT** | Next.js + FastAPI | Shift Auth purely to Next.js client side. See Document 21. |
| Firestore DB | **DISCARD** | N/A | We will pass Firebase UIDs to backend, but Postgres owns preference persistence. |
| Local `personalization.py`| **DISCARD**| N/A | Replaced fully by main repo `engine/`. |

## 3. Data-Source Ownership
**DECISION:** The separate implementation's Open-Meteo logic is **DISCARDED / DEFERRED**.
The frontend must not fetch weather on its own. It requests `/homepage` with location coordinates, and the backend adapters decide whether to use fixtures, Astral sun computation, or eventually real IMD endpoints. The current MVP reality (`fixture` mode) applies.

## 4. Persona Scope Reconciliation
The external UI showcases 8 visual persona options during onboarding. However, only 3 (`health`, `fitness`, `family`) plus cold-start are fully supported by internal adapters and thresholds currently.
**DECISION:** The UI can show the others, but they should be visually marked as "Coming Soon" or deferred at the Next.js level. The frontend cannot claim a persona is working if the `/homepage` cannot rank its underlying cards appropriately.
