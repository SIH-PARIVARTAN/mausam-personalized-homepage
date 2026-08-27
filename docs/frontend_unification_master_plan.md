# Frontend Unification Master Plan

**Date:** 2026-08-27
**Target:** Translating external Flask UI repo into SIH Main Architecture
**Objective:** One Unified Repository (Next.js + FastAPI + Postgres)

## 1. Executive Decision
The FastAPI/PostgreSQL/Engine backend in the original repository remains the strict authoritative implementation. The external teammate's Flask app is deprecated. However, their excellent UI layouts, Firebase Auth flow, and styling will be structurally imported into the main repository's Next.js frontend scaffold. The backend math guarantees must not be duplicated or overridden by the frontend.

## 2. Final Target Architecture
- **Frontend Stack**: Next.js 16 (React, Tailwind/Custom CSS, TanStack Query)
- **Identity**: Firebase Auth (pure frontend side) → yields `UID`.
- **Backend API**: FastAPI (Authoritative router)
- **Core Engine**: Pure Python `engine/rank()` function (untouched).
- **Database**: PostgreSQL/Neon (Persistence for preferences, tied to Firebase `UID`).
- **Data Adapters**: Backend-controlled data fetchers. Frontend is barred from direct weather API calls.

## 3. Component Disposition
- Flask Backend (`app.py`, `services/*`): **DISCARD**
- Firebase Firestore Data: **DISCARD** (Handled by Postgres)
- Jinja Templates (`templates/*`): **MIGRATE to JSX**
- Styles & JS (`css/*`, `js/*`): **MIGRATE to Next.js**
- `engine/`, `backend/`, `adapters/`: **KEEP, UNTOUCHED**

## 4. Persona Scope Reconciliation
The UI contains visual buttons for 8 personas. The backend engine supports 3 fully plus 1 cold-start. We will display the unused personas in UI as disabled or "Coming Soon," ensuring honesty with SIH judges regarding current backend scope.

## 5. Migration Phases
- **Phase 0 (Current)**: Architecture frozen. Approval of this document.
- **Phase 1 (Preparation)**: Extract HTML structures and CSS out of the Flask repository into static React layouts without API connections yet.
- **Phase 2 (Auth integration)**: Wire up Next.js Firebase Auth UI (Login/Signup). Convert Firebase response to global `UID` state.
- **Phase 3 (Preference API)**: Attach Onboarding layout to `PUT /preferences` in FastAPI.
- **Phase 4 (Dashboard Integration)**: Attach Dashboard layout to `GET /homepage` using TanStack Query. Render cards strictly identically to backend array order.
- **Phase 5 (Explanation UX)**: Add the "Why did I see this?" modal invoking `GET /explain`.

## 6. Git & Collaboration Strategy
- The main branch is protected.
- Create integration branch `feature/frontend-nextjs-import`.
- Ensure all teammate commits only touch the `frontend/` folder to prevent backend conflicts.
- Code reviews must enforce that `Array.sort`, filtering, or local weather logic (e.g. Open-Meteo SDKs) never enter frontend commits.

## 7. Next Action Recommended
Authorize the start of **Phase 1 & 2** — specifically migrating the UI assets and Next.js Firebase Authentication implementation inside the `frontend/` directory.
