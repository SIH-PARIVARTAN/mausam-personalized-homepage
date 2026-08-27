# 21. Unified User Identity and Data Ownership

**Topic:** Reconciling the external UI's use of Firebase Authentication and Firestore with the main repository's `device_id` + PostgreSQL implementation.
**Status:** DECISION
**Date:** 2026-08-27

## 1. Authentication Options Analysis

| Option | Pros | Cons | Verdict |
|--------|------|------|---------|
| **1. `device_id` only (Original MVP)** | Zero dependency on external Google services; privacy-first; easiest to maintain. | No visual login screen; harder to demo "cross-device" syncing. | **DEFER.** (Good for production anonymity, bad for hackathon demo flow). |
| **2. Firebase Auth (via Frontend) + FastAPI `uid` Mapping** | Preserves teammate's excellent Signup/Login responsive screens; judges expect to see a login flow. | Requires passing `uid` securely to `/homepage` and `/preferences`. | **RECOMMENDED.** |
| **3. Postgres-backed Auth (JWT via FastAPI)** | 100% unified code. | Requires building Auth from scratch in Python, losing teammate's working auth UI. | **DISCARD.** |

## 2. Target Identity Verdict: Option 2 (Firebase Auth Frontend)
We will leverage **Firebase Auth** entirely on the Next.js client-side.
- **Registration/Login:** Happens in frontend Firebase SDK.
- **Identity Bridge:** The `firebase.auth().currentUser.uid` string is subsequently passed mathematically as the `device_id` parameter to the FastAPI backend endpoints (e.g., `GET /homepage?device_id={uid}`).
- **Security Scope:** For this SIH MVP, passing `uid` as a query param is acceptable. In a v2 production environment, this would be upgraded to verifying Firebase JWT tokens via FastAPI middleware.

## 3. Database Ownership Verdict
The teammate's Flask app used Firestore database (`users/{uid}`) to save location and interests.
**DECISION:** Firestore is completely removed from the architecture.
- **Why?** Having duplicate state between Postgres and Firestore leads to sync issues, orphaned data, and breaks our `/preferences` endpoint caching logic.
- **Migration:** Firebase Auth creates the UID, but immediately afterward, the user is forwarded to the Next.js Preference onboarding screen, which fires `PUT /preferences` directly to FastAPI/PostgreSQL.

## 4. Weather & Geolocation Data Ownership
The teammate's `weather_service.py` accessed Open-Meteo API using longitude and latitude requested by `navigator.geolocation` or Nominatim API.
- **Location Acquisition:** The Next.js client MAY still use the browser's `navigator.geolocation` or a Google Places autocomplete to obtain Lat/Lon.
- **Weather Fetching:** The Next.js client MUST NOT call Open-Meteo. The Lat/Lon are simply appended to `GET /homepage?lat=Y&lon=X`. The backend FastAPI `Adapters` decide how to fetch or simulate the weather cleanly.
