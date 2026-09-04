# 06: API AND FRONTEND CONTRACT AUDIT

## 1. Expected Contracts (Backend Truth)
The frontend application (Next.js) exclusively depends on the FastAPI backend for its data.

### 1) GET `/homepage?device_id=...&lat=...&lon=...`
**Purpose:** Fetch personalized weather insights.
**Contract Issue:** The `device_id` is passed as a raw string. If Next.js has Firebase Auth implemented, the backend is not enforcing it. Anyone can hit `/homepage` with any string.

### 2) GET `/preferences?device_id=...`
**Purpose:** Fetch the user's currently selected personas and health flags.
**Contract Issue:** See above. No Auth.

### 3) PUT `/preferences` (JSON Body: `device_id`, `personas`, `health_flags`, `saved_locations`)
**Purpose:** Update user settings.
**Contract Issue:** Overwrites preferences in Neon Postgres. Completely open endpoint.

## 2. Test and Validation Audit
**Test Coverage: 100% Core Passing**
- Command executed: `pytest backend/ engine/ adapters/`
- Result: **137 Tests Passed in <1 second**. 
- Coverage details: Tests run heavily in `engine/tests/` verifying logic, overrides, and missing data scenarios perfectly.
- Mocks: `adapters/` are tested specifically using simulated fixture responses. 

## 3. Tech Debt & Gaps
- **Critical (P0):** Lack of Firebase token validation on `GET /homepage`.
- **Medium (P1):** Live data integration is incomplete. The adapter structure is ready but HTTP calls are faked/handled as failures.
- **Low (P2):** Currently limited to 3 personas (`health`, `fitness`, `family`) instead of the targeted 8.
