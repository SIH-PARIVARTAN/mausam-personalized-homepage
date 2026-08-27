# 22. Frontend-Backend Integration Test Plan

**Topic:** Ensuring the UI migration does not break the backend personalization audit guarantees.
**Status:** PLAN
**Date:** 2026-08-27

## 1. Engine and Backend Integrity (MUST NOT FAIL)
Before integrating, and continuously during integration:
- Run `python -m pytest engine/tests` (must be 100% pass)
- Run `python -m pytest backend/tests` (must be 100% pass)
- The UI migration code is strictly disallowed from touching `.py` files. Any failure here indicates an architectural violation.

## 2. API Contract Check Gates
The frontend fetches data via Next.js server components or TanStack Query.
- **Gate 1:** Does the frontend send `device_id`, `lat`, and `lon` to `/homepage`?
- **Gate 2:** Does the `PUT /preferences` call structure match the `PreferencesBody` exactly (sending arrays `personas` and `health_flags`)?

## 3. E2E User Journey Smoke Tests
The following scenarios must be manually verifiable upon Next.js deployment:
1. **Cold Start User:** Hit the dashboard without logging in or setting preferences. The API must return general conditions and defaults without crashing the UI.
2. **Preference Reorder:** Select "Fitness" in the settings modal. Click save. Witness the "Activity Window" and "Sunrise/Sunset" cards instantly bubble higher up the list.
3. **Severe Weather Override:** Ensure that if the backend fixture triggers a P0 Alert (e.g. Thunderstorm override), the UI renders it visibly separated at the very top, ignoring normal card scoring.
4. **Degraded State Visualization:** Ensure the card's `freshness_badge` says "Data unavailable" or "Simulated for demo" cleanly, rather than failing silently.

## 4. Rollback Condition
If the frontend UI cannot render the cards without running custom Javascript sorting algorithms (reordering the backend's output array), the UI PR gets rejected until the display logic purely trusts the array index order of the Backend JSON.
