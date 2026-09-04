# MAUSAM Phase A Context Model Execution Plan

## 1. Executive Decision
The reconciled roadmap correctly identified `health_flags` and `saved_locations` as critically missing from the engine's decision-making flow. However, the historical proposal to shove these raw fields straight into the `ContextFrame` and add a new `health_flag_multiplier` is architecturally flawed. 

**Decision:**
1.  **Health Flags:** We will **not** add a 4th scalar multiplier. Instead, health preferences will dynamically modify the `persona_weight` directly in `_resolve_persona_weight()`. This honors the 3-term scoring formula (`pw * um * cfac`) while successfully granting sensitive users higher priority without making medical claims.
2.  **Saved Locations:** The engine is purely deterministic and performs NO network I/O. Therefore, passing raw `saved_locations` into `ContextFrame` is useless because the engine cannot fetch the weather for them. Instead, `backend/deps.py` will handle `saved_locations`, fetching relevant data before creating the `ContextFrame`, passing the *resolved* data into the frame.

## 2. Current Repository Findings
*   **Database/API Models:** The API correctly validates `PreferencesBody` featuring `health_flags` and `saved_locations`. They are successfully written to and read from Postgres in `backend/routers/preferences.py` and `backend/db.py`.
*   **Homepage Flow:** `backend/routers/homepage.py` fetches preferences but actively *drops* `saved_locations` before calling `backend/deps.py`.
*   **Engine Context:** `ContextFrame` contains `health_flags` but it is utterly inert (never read by `scoring.py`). `saved_locations` does not exist in `ContextFrame`.
*   **Scoring Logic:** `scoring.py` strictly prevents `urgency_multiplier` from reading persona data.

## 3. Reconciled Scope for Phase A
*   **Health Flags:** Inject `health_flags` awareness into `_resolve_persona_weight()` in `scoring.py`. E.g., if checking `aqi_health` and `"respiratory_sensitive"` is in `health_flags`, boost the weight mathematically. 
*   **Saved Locations:** Update `/homepage` to retrieve `saved_locations`. Update `backend/deps.py` to accept them. Do NOT put them in `ContextFrame` yet. Scaffold the space in `backend/deps.py` where warnings for these locations will be fetched in Phase B. 
*   **Explanations:** Update `explain.py` to append the health sensitivity context if a health flag influenced the score.

## 4. Explicit Non-Goals
*   Do NOT build the Traveler `destination_alert` card. The goal is simply to bridge the data from the DB to the edge of the engine.
*   Do NOT alter the `urgency_multiplier` rules.
*   Do NOT build an entirely new 4th scalar into the scoring formula. 

## 5. Recommended Architecture / Data Ownership
*   **Persistent Preferences:** Owned by Postgres database (`preferences` table).
*   **Health-Related Preferences:** Retrieved from Postgres alongside `personas`. Belong natively in the `ContextFrame` as they directly modify personalization weighing behavior. 
*   **Saved Locations:** Stored in Postgres. At Request time, the API fetches them. `backend/deps.py` resolves them via external Adapters. The *resolved insights* (not the raw DB coordinates) will eventually populate the `ContextFrame`. 

## 6. `health_flags` Design Decision
We will inject a modifier into `_resolve_persona_weight` inside `engine/scoring.py`. 
If a user has `respiratory_sensitive` and the card is `aqi_health`, the baseline persona weight (e.g., 0.9) will be increased by a fixed modifier (e.g., +0.1) explicitly citing the flag in the explanation constraints. This effectively raises the card's priority at lower environmental urgency thresholds. We explicitly avoid medical claims by keeping it framed as "preference weight adjustments."

## 7. `saved_locations` Design Decision
`saved_locations` will be fetched in `routers/homepage.py` and passed into `dependencies/build_context_frame`. To maintain the engine's strict purity (No I/O), `saved_locations` will NOT enter `ContextFrame` directly. Instead, Phase B will map them to `destination_warnings` after `deps.py` fires the `WarningAdapter` for each coordinate. For now, we only ensure `homepage.py` safely routes the DB field to `deps.py`. 

## 8. Exact Request and Data Flow
1.  **User Hits `/homepage`:** `routers/homepage.py` queries `get_preferences`.
2.  **Pref Fetching:** Returns `personas`, `health_flags`, and now `saved_locations`.
3.  **Dependency Assembly:** `build_context_frame(prefs, ...)` receives all three.
4.  **Context Frame Init:** `cf = ContextFrame(...)` receives `health_flags`. (In Phase B, `deps.py` will fetch warnings for `saved_locations` and attach them to `cf`).
5.  **Scoring (`scoring.py`):** `_resolve_persona_weight` recognizes `"respiratory_sensitive"` in `cf.health_flags` and boosts `pw`.
6.  **Explanation (`explain.py`):** Mentions the health flag if relevant.

## 9. File-by-File Proposed Changes
1.  **`backend/routers/homepage.py`:** Update `get_preferences` to SELECT and JSON-load `saved_locations`.
2.  **`backend/deps.py`:** Update `build_context_frame` signature to anticipate upcoming location resolution strategies.
3.  **`engine/scoring.py`:** Add conditional weight-boosting logic to `_resolve_persona_weight` responding to `cf.health_flags`. 
4.  **`engine/explain.py`:** Ensure explanations correctly parse flag influences (e.g. "Elevated priority due to respiratory sensitivity"). 
5.  **`engine/tests/test_scoring.py` (or new test file):** Add unit tests for `health_flag` weight modifications.

## 10. Backward Compatibility Strategy
*   **Missing Traits:** If `health_flags` or `saved_locations` are missing from the DB or the user is anonymous, they default to `[]`. The `_resolve_persona_weight` function will gracefully bypass the modifier.
*   **Existing Tests:** Golden evaluations currently run with `health_flags: []`. These will experience literally zero change in scoring behavior, sustaining the exact 25/25 verified score securely. 

## 11. Explainability and Safety Boundaries
Health explanations must maintain NFR-1 traceability and remain strictly non-medical. 
*Acceptable:* "Because you marked a respiratory sensitivity, we have elevated the priority of this Air Quality reading."
*Unacceptable:* "You are at risk of an asthma attack due to the AQI."

## 12. Detailed Testing and Acceptance Gates
*   **Unit Tests:** Create `test_health_flag_modifiers` verifying that `score()` produces mathematically distinct and elevated output for a profile possessing `"respiratory_sensitive"` vs one without. 
*   **Regression Tests:** Run `pytest engine/tests/` to guarantee P0 overrides function correctly.
*   **Golden Evaluation:** Run `python eval/run_spike.py` securing the 25/25 golden baseline remains untouched.
*   **Integration:** Write to `/preferences` and correctly read back `/homepage` guaranteeing no server 500s.

## 13. Implementation Sequence in Small Steps
*   **Step 1:** Modify `routers/homepage.py` `get_preferences()` to extract `saved_locations`.
*   **Step 2:** Scaffold `backend/deps.py` for future destination resolution.
*   **Step 3:** Implement the weight adjustment in `engine/scoring.py`.
*   **Step 4:** Implement text explanation appending in `engine/explain.py`.
*   **Step 5:** Write unit assertions, test, and perform golden evaluation spike.

## 14. Documentation Updates Required After Implementation
*   Update `docs/project_knowledge/MAUSAM_BACKEND_IMPLEMENTATION_STATUS.md` reflecting Phase A closure.
*   No other documents require forced modification; historical continuity rules apply. 

## 15. Risks / Open Questions
*   **Risk:** Inflating the persona weight > 1.0 could theoretically disrupt relative scales. 
*   **Solution:** We clamp `pw = min(1.0, pw + modifier)`. 

## 16. Final Go/No-Go Recommendation
**GO.** The scope is minimal, non-disruptive to the core 25/25 engine, natively scales without over-inflating multipliers, and is fully backward compatible. Implementation of Phase A is safe to begin.
