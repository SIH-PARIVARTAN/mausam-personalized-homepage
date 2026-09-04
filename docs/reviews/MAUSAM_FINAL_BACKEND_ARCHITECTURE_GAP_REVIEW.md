# MAUSAM FINAL BACKEND ARCHITECTURE GAP REVIEW
*(Independent, read-only audit — Problem Statement SIH26076, "Development of personalized homepage for 'Mausam' mobile application")*

---

## 1. Review Scope and Evidence Base

Five documents were supplied and read in full before forming any conclusion:
1. `MAUSAM_BACKEND_IMPLEMENTATION_STATUS.md` — current ground truth (self-reported).
2. `MAUSAM_BACKEND_CODE_REVIEW_PACKAGE.md` — the actual, unmodified source of every file under `engine/` (`models.py`, `cards.py`, `scoring.py`, `priority.py`, `compound.py`, `conflict.py`, `derived.py`, `engine.py`, `explain.py`), plus prose descriptions of `backend/`, `adapters/`, and `cache/`.
3. `MAUSAM_MASTER_SYSTEM_KNOWLEDGE_BASE.md` — historical planning context.
4. `MAUSAM_FINAL_BACKEND_RELEASE_AUDIT.md` — a prior independent audit's evidence log.
5. `DEMO_RUNBOOK.md` — operational procedures.

**Important evidence boundary, stated up front:** the code review package contains the complete, real source of every file under `engine/`. It does **not** contain the actual source of `backend/`, `adapters/`, or `cache/` — those layers are described only in prose (in documents 1, 2, and 4). Every conclusion below about `engine/` is a direct code fact. Every conclusion about `backend/`, `adapters/`, or `cache/` is explicitly marked as resting on prose evidence, not independently verified source, per the instruction to distinguish facts from assumptions.

---

## 2. Final Architecture Verdict

**B. BACKEND SHOULD RECEIVE A SMALL TARGETED PATCH BEFORE INTEGRATION.**

The deterministic engine's core architecture — pure functions, P0 override, the persona-weight/urgency/confidence scoring model, tie-break resolution, templated explanations — is sound, well-evidenced by real source code, and should not be redesigned. However, direct inspection of `engine/priority.py` and `engine/cards.py` together found one genuine, code-confirmed functional gap: **6 of the 11 cards explicitly marked `"alertable": True` can never actually receive alert treatment**, because `_HARD_ALERT_URGENCY` (the table that gates alert eligibility) was never extended to cover them when the persona set grew from 4 to 8. This is not a design flaw in the scoring model — it is an incomplete data-table update, exactly the kind of small, well-scoped, evidence-driven fix this project's own F-01/F-02 calibration precedent already demonstrates it knows how to do correctly. This does not require reopening the engine's architecture, only extending one dictionary and adding the tests to prove it.

---

## 3. What Is Already Correct and Should NOT Be Changed

- **The pure-function engine boundary.** Confirmed directly from source: `engine/engine.py`'s `rank()` and every module it imports (`cards`, `compound`, `conflict`, `explain`, `models`, `priority`, `scoring`) contain no `import` of `fastapi`, `requests`, `httpx`, `psycopg`, or any I/O library. The boundary is real, not just documented.
- **P0 severe-warning override.** `classify_priority()` returns `"P0"` unconditionally whenever `card_id == "severe_warning" and cf.warnings`, checked *before* any score computation, and this path is completely independent of persona. Confirmed correct by direct code reading.
- **The F-02 alert-priority floor mechanism itself.** `apply_alert_priority_floor()` correctly elevates a P3 alert to P2 and is correctly scoped to display-priority only, never touching the underlying score. The *mechanism* is sound — see Section 4 for the *coverage* gap in what feeds it.
- **`urgency_multiplier`'s persona-blindness.** Confirmed by direct reading of every branch in `scoring.py`'s `urgency_multiplier()` — none of the 13 branches reference `cf.personas`. This is the property that prevents the engine from degenerating into a disguised lookup table, and it holds.
- **The F-01 rain-commute calibration.** The in-code comment documents the exact old value, new value, and arithmetic justification (0.95 × 2.35 × 0.7 ≈ 1.563 ≥ 1.5). This is a genuine, auditable calibration record, not a cosmetic comment — keep this pattern for all future weight changes.
- **`health_flag_multiplier` (now correctly implemented as `_resolve_persona_weight`'s modifier logic).** Confirmed live in `scoring.py`: a declared `respiratory_sensitive` flag adds +0.1 to `aqi_health`'s persona weight (capped at 1.0), `heat_sensitive` does the same for `uv_sun_exposure`, and `flags_applied` is threaded through into `score_components` and into `explain.py`'s output ("priority elevated due to your health profile"). This closes a gap flagged in earlier project reviews and is genuinely resolved in this codebase — good evidence this was deliberately fixed, not accidentally.
- **The undeclared-persona default.** `_resolve_persona_weight()` falls back to `PERSONA_WEIGHT.get((card_id, "default_general"), 0.2)`, not a flat 0.2 for every unrecognized persona — this closes another previously-flagged gap correctly.
- **`derived.py`'s comfort-index and frost-warning functions.** Pure, dependency-free, correctly isolated from any provider concern.
- **Tie-break determinism.** `conflict.py`'s `resolve_ties()` uses a fully deterministic 5-key sort tuple; confirmed no randomness or unstable ordering anywhere in the visible source.
- **Cache degradation policy, as described.** The fresh/soft-stale/hard-stale threshold model (< 60 min / 60–240 min / > 240 min) described in documents 1 and 4 is a reasonable, honest design — **this specific claim rests on prose evidence, not raw `cache/store.py` source**, and is accepted here only because it is independently corroborated across two separately-authored documents (implementation status and release audit) with matching numeric thresholds, not because the code itself was inspected.

---

## 4. Genuine Gaps Found

### GAP-01 — Six `alertable: True` cards can never actually alert
- **Severity:** HIGH.
- **Affected layer/files:** `engine/priority.py` (`_HARD_ALERT_URGENCY`, `is_alert()`), `engine/cards.py` (`CARD_DEFINITIONS`).
- **Evidence:** `CARD_DEFINITIONS` marks 11 cards `"alertable": True` (`severe_warning`, `compound_heat_aqi_danger`, `compound_driving_hazard`, `aqi_health`, `uv_sun_exposure`, `activity_window`, `rain_commute`, `visibility_commute`, `destination_alert`, `agriculture_advisory`, `marine_conditions_alert`). `_HARD_ALERT_URGENCY` contains exactly 4 keys: `aqi_health`, `uv_sun_exposure`, `activity_window`, `rain_commute`. `is_alert()`'s logic (`threshold = _HARD_ALERT_URGENCY.get(card_id); if threshold is None: return False`) means `compound_heat_aqi_danger`, `compound_driving_hazard`, `visibility_commute`, `destination_alert`, `agriculture_advisory`, and `marine_conditions_alert` will return `is_alert=False` regardless of how extreme the underlying signal is. `severe_warning` is unaffected (handled via the separate `priority == "P0"` branch).
- **Why it matters:** This directly undermines the F-02 guarantee ("an active alert is never hidden/collapsed to P3") for exactly the 6 cards that cover the newest, hardest-won persona work — including both compound "danger" cards, which are the project's own headline cross-signal-reasoning demo feature. A low-confidence but genuinely severe marine, agriculture, commuter, or compound scenario can be scored into P3 with no floor protecting it, since `apply_alert_priority_floor()` only fires when `is_alert=True`.
- **What should change:** Extend `_HARD_ALERT_URGENCY` with a documented threshold for each of the 6 affected cards, each threshold justified against `urgency_multiplier`'s own existing bands for that card (e.g., `compound_heat_aqi_danger`/`compound_driving_hazard` already return a flat urgency of 3.0 when triggered at all, so their entry can simply be a value ≤ 3.0 such as 2.5, since the compound condition being true is itself already a severe-enough signal — this should be a deliberate, documented decision, not an arbitrary copy).
- **What must not change:** `classify_priority()`'s P0 logic, `urgency_multiplier()`'s branches, `apply_alert_priority_floor()`'s own mechanism, and the `severe_warning` card's alert path — none of these need to change, only the table `is_alert()` reads from.
- **Risk if ignored:** the project's own stated safety promise ("alerts are never hidden") is quietly false for 6 of 11 alertable cards, and this specific failure mode is exactly the kind of thing that would only surface in a live judging-day scenario, not in casual use.

### GAP-02 — Dead, stale `_PERSONAS_ALL` constant in `engine/engine.py`
- **Severity:** LOW.
- **Affected layer/files:** `engine/engine.py`, line 1276 in the supplied source.
- **Evidence:** `_PERSONAS_ALL: frozenset[str] = frozenset(["health", "fitness", "family", "default_general"])` is defined once and referenced nowhere else in the entire supplied `engine/` source (confirmed by a full-text search of the code review package). The actual system now supports at least 9 persona keys (`health`, `fitness`, `family`, `commuter`, `traveler`, `agriculture`, `beachgoer`, `event_planner`, `default_general`), per `PERSONA_WEIGHT`.
- **Why it matters:** functionally inert (unused), but actively misleading to any future maintainer who greps for the persona list and finds a stale, wrong answer.
- **What should change:** delete the constant, or update it to the real 9-persona set and use it somewhere meaningful (e.g., as a validation set) if it was originally intended for that purpose.
- **What must not change:** nothing functional depends on this.
- **Risk if ignored:** low, but a real documentation-debt/confusion risk for whoever picks this up next.

### GAP-03 — Redundancy-suppression logic is real, working, and appears reasoned — but is not traced to a spec citation the way the rest of the engine is
- **Severity:** MEDIUM (documentation, not functional).
- **Affected layer/files:** `engine/engine.py`, the "Targeted Redundancy Suppression (Phase D)" block at the end of `rank()`.
- **Evidence:** every other non-trivial rule in the supplied source (P0 override, F-02 floor, F-01 calibration, the environment-only urgency invariant) carries an explicit citation to a numbered spec document and section. The suppression block — which silently removes `aqi_health`/`general_conditions` from the ranked list whenever `compound_heat_aqi_danger` is active, and `visibility_commute`/`rain_commute` whenever `compound_driving_hazard` is active — carries no such citation, only a `# Phase D` comment.
- **Why it matters:** on inspection, the suppression logic appears sound — it runs strictly after the P0/ranked split (so `severe_warning` is provably unaffected), and it only suppresses constituent cards whose information is already subsumed by the compound card's own explanation (which cites both underlying values). This is not flagged as a functional defect. It is flagged because the project's own internal discipline (spec citation for every non-obvious rule) was not followed here, which makes it harder for the next reviewer to distinguish "deliberate, reasoned design" from "undocumented side effect" — exactly the ambiguity this audit had to resolve manually by reading the code closely.
- **What should change:** add the same one-paragraph documented rationale this file already gives for F-01/F-02 to this block, and confirm (see Section 10) that the golden set actually has a scenario that exercises this suppression path, not just the compound card's own triggering.
- **What must not change:** the suppression behavior itself — it appears correct as implemented.
- **Risk if ignored:** low functionally, moderate for future maintainability.

### GAP-04 — Master Knowledge Base is materially stale relative to the actual implementation
- **Severity:** LOW (documentation only, but worth stating precisely since a prior audit's "no inconsistencies" claim did not have this document in scope).
- **Affected layer/files:** `MAUSAM_MASTER_SYSTEM_KNOWLEDGE_BASE.md` only — no code affected.
- **Evidence:** Section 3 of the knowledge base lists Traveler, Commuter, Agriculture, Beachgoer, and Event Planner as `[PLANNED]`, and Section 19 describes Phase 2 (health-flag work) as `[NEXT]` — but the actual `engine/` source shows all 8 personas fully present in `PERSONA_WEIGHT` and `CARD_DEFINITIONS`, and `health_flag`-driven scoring already implemented and active. The knowledge base's own phase numbering (Phase 0–9) also does not match the current status document's phase lettering (Phase A–F), with no cross-reference between the two schemes anywhere in the supplied documents.
- **Why it matters:** the prior release audit (document 4) states in its Section 12 that it found "no major inconsistencies" — that finding is accurate *for the three documents it actually reviewed* (its own Section 2 lists only the implementation status doc, the Phase F plan, and the demo runbook), but the Master Knowledge Base was not part of that scope, so its staleness was never actually checked until this review.
- **What should change:** either delete the Master Knowledge Base or add a prominent top-of-document notice that it is historical-only and superseded by the implementation status document — the current wording invites a future reader to treat it as current, which it is not.
- **What must not change:** nothing in code.
- **Risk if ignored:** low, but real — a future team member or judge reading the knowledge base without also reading the implementation status document would form an incorrect picture of what's built.

**No further genuine gaps were found.** Areas explicitly checked and found sufficient given the project's actual scope: database architecture (Section 7), API contract completeness (Section 8), authentication posture (Section 9's identity discussion below), logging (Section 11).

---

## 5. Recommendation Classification

**MUST IMPLEMENT BEFORE INTEGRATION**
- GAP-01: extend `_HARD_ALERT_URGENCY` to cover the 6 affected cards, with tests proving each now reaches `is_alert=True` at its documented threshold, and proving `apply_alert_priority_floor()` now actually protects them from P3 collapse in a low-confidence scenario.

**SHOULD IMPLEMENT DURING BACKEND–FRONTEND INTEGRATION**
- GAP-02: remove or repurpose the dead `_PERSONAS_ALL` constant (trivial, no reason to block integration on it, but should not be forgotten).
- GAP-03: add the missing spec citation/rationale for the redundancy-suppression block, and confirm golden-set coverage for that specific path.
- Add a permanent automated regression test for the database-unavailable-mid-request 500 behavior and the missing-`DATABASE_URL`-at-startup `ValueError` (see Section 10) — currently proven only by a manual one-off script during the prior audit, not by a repeatable test in the 163-count suite.

**FUTURE / DEFERRED — DO NOT BLOCK CURRENT FREEZE**
- GAP-04: Master Knowledge Base staleness — a documentation hygiene item with no functional impact; fix opportunistically.
- Marine/INCOIS live integration, full Firebase authentication, telemetry/ML — all correctly deferred per the project's own documented boundaries, and none of this review's findings change that.

---

## 6. Provider and External-Service Review

Weather and AQI both sourced from Open-Meteo per the implementation status document — **this specific claim rests on prose evidence** (documents 1 and 4), since `adapters/aqi_adapter.py`/`adapters/forecast_adapter.py` source was not included in the supplied package. Within that evidence boundary: a single-provider architecture for weather/AQI, behind an adapter abstraction that the engine never sees through, is an appropriate and sufficient design for this project's stage — the `ContextFrame`/`SignalValue` contract (confirmed real from `engine/models.py`) is exactly what makes a future second provider or a swap a config-level change, not a rewrite. **A second live provider is not recommended now** — no concrete reliability problem with the current single-provider setup is evidenced anywhere in the supplied documents, and adding one without such evidence would be complexity for its own sake, which this review explicitly rejects per its own anti-scope-creep instruction. The documented timeout (1.5s per the demo runbook), retry/cache-fallback behavior, and three-tier freshness policy are all reasonable and, per the corroborating evidence across two documents, appear to be genuinely implemented, not just planned.

---

## 7. Database and Runtime Resilience Review

**Verdict: the current PostgreSQL-hard-dependency behavior (HTTP 500 on mid-request DB loss) should remain unchanged, but must be more precisely documented, not patched.**

The project's own stated design principle — "the backend is designed not to serve unpersonalized dummy data in place of safety alerts" — is a defensible, deliberate choice, not an oversight, for a system whose entire value proposition depends on `preferences` being genuinely correct rather than silently substituted. Forcing a hard failure when the source of truth for personalization is unreachable is more honest than serving a default homepage that looks personalized but isn't. This review does not recommend adding a fallback-to-default-homepage path for a DB outage — that would reintroduce exactly the kind of silent-wrongness this project's design has consistently avoided elsewhere (e.g., the explicit `source`/`confidence` labeling on every environmental signal). The one genuine improvement recommended is procedural, not architectural: the failure mode is currently proven correct by a one-off manual script (per document 4, Section 6), not by a permanent test — see Section 10.

---

## 8. API Contract and Frontend Integration Readiness

`GET /homepage`, `GET /explain`, `PUT /preferences` — per documents 1 and 4, all three exist and are contract-tested. `RankedCard` and `EngineOutput` (confirmed real from `engine/models.py`) are well-typed, and every field a frontend would need to render a card, its priority, its alert state, and its explanation is present and structured. **One integration-readiness note, not a defect:** GAP-01 means the frontend cannot currently trust `is_alert` as a signal for 6 card types — if the frontend's rendering logic branches on `is_alert` to decide alert styling (a reasonable thing to do given the field exists precisely for that purpose), it will silently under-style genuinely severe marine/agriculture/commuter/compound scenarios until GAP-01 is patched. This is worth surfacing to the frontend team explicitly as a known, temporary limitation if integration begins before the patch lands. No other backend-side contract change is recommended before integration begins.

---

## 9. Future LLM/Groq Integration Boundary

Recommended architecture, unchanged in spirit from what the task described, confirmed technically feasible from the actual `RankedCard`/`EngineOutput` structures already in the codebase:

```
User
  |
Frontend
  |
FastAPI
  |-- Deterministic Homepage Pipeline
  |       |
  |   Authoritative HomepageResponse (RankedCard[], override_warnings[])
  |
  |-- Optional Future Conversation Layer
          |
       Structured Engine Output (RankedCard.explanation_text, .signal_refs, .score_components)
          |
        Groq / LLM
          |
Natural Language / Translation / Explanation (display-layer only)
```

- **LLM MAY DO:** rephrase, translate, or conversationally present an already-computed `explanation_text` string; answer a user's follow-up question about a card using `signal_refs`/`score_components` as grounding context.
- **LLM MUST NOT DO:** compute or influence `priority`, `is_alert`, `score`, or card ordering; be called anywhere inside `engine/`; ever be the sole source of an explanation with no underlying `signal_refs` to ground it.
- **DATA THE LLM SHOULD RECEIVE:** the already-serialized `HomepageResponse` (or individual `RankedCard` objects) — nothing that isn't already exposed to the frontend today.
- **DATA THE LLM MUST NOT CONTROL:** anything upstream of `HomepageResponse` — no write access to `ContextFrame`, no ability to alter `PERSONA_WEIGHT`, `urgency_multiplier`, or any file under `engine/`.
- **WHETHER ANY CODE CHANGE IS REQUIRED NOW:** **No.** The existing `RankedCard`/`EngineOutput` contract (confirmed from real source) already exposes exactly the structured, traceable data a future conversational layer would need — `explanation_text` for direct reuse, `signal_refs`/`score_components` for grounding a more elaborate LLM-generated response without inventing numbers. No preparatory backend work is needed; this boundary is already naturally satisfied by decisions made for unrelated reasons (explainability, not LLM-readiness) earlier in the project.

---

## 10. Testing and Evaluation Gap Review

The 163-pass / 34-of-34 figures are not, on their own, sufficient evidence that the system is fully protected — and the project's own Section 23 (in the historical knowledge base) makes exactly this point ("passing tests means the contracts operate predictably," not "the engine ranks correctly"), which this review agrees with as a sound testing philosophy, even though the knowledge base document it appears in is otherwise stale.

**Concrete, currently-unconfirmed test coverage this review recommends checking or adding — each tied to a specific risk, not a general "add more tests" instruction:**
1. **Does the golden set assert `is_alert` values, not just priority/rank order, for the 6 cards named in GAP-01?** If the golden set only checks ranking and priority tier, it would not have caught GAP-01 at all, which would explain why 34/34 passed despite the gap existing. This should be checked before assuming the golden set would catch a regression here — and if it doesn't currently assert `is_alert`, that assertion should be added alongside the GAP-01 patch, not as a separate, deferrable item.
2. **A permanent automated test for the DB-unavailable-mid-request → HTTP 500 path**, and for the missing-`DATABASE_URL` → `ValueError` startup path — both are currently proven only by a manual, one-off script (document 4, Section 6), which will not catch a future regression the way a suite member would.
3. **A permanent test confirming the redundancy-suppression path (GAP-03)** produces the correct, single, consolidated card set when a compound condition triggers — specifically distinguishing this from a test that only confirms the compound card itself appears.

**Explicitly not recommended:** any test added purely to inflate the count past 163 or 34; a dedicated malformed-payload/`aqi=-999` test cannot be evaluated here since the adapter source was not supplied — if the team can confirm from `adapters/aqi_adapter.py` directly that such a guard already exists, no action is needed; if not, it is a reasonable low-cost addition, but this review cannot state with evidence that it's currently missing, only that it could not be confirmed present.

---

## 11. Security, Configuration and Logging Review

Per the supplied evidence (documents 1 and 4): `DATABASE_URL` is never printed by standard logging, no payload dictionaries or credentials are dumped, secrets load via `.env.local` with an explicit non-default `--env-file` flag rather than being silently picked up. No concern is raised here beyond what's already documented, because no evidence in the supplied artifacts points to an actual leak or misconfiguration — this review will not manufacture a security finding unsupported by the evidence. One procedural note, not a defect: the `--env-file .env.local` requirement (rather than the framework's own `.env` default) is an easy step to forget when someone new runs the project for the first time — worth a one-line addition to the pre-demo checklist confirming the *exact* command was used, not just that the file exists (the demo runbook's existing pre-demo checklist already checks for the file's presence but not for the correct startup invocation).

---

## 12. Exact Recommended Implementation Plan

### PATCH 1 — Extend alert-eligibility coverage (resolves GAP-01)
**Objective:** every card marked `"alertable": True` in `CARD_DEFINITIONS` can actually reach `is_alert=True` at a documented, justified threshold.
**Exact files to modify:** `engine/priority.py` (`_HARD_ALERT_URGENCY` dictionary only).
**Exact files not to modify:** `engine/scoring.py`, `engine/cards.py`, `engine/conflict.py`, `engine/compound.py`, `engine/engine.py`, `engine/explain.py`, `engine/models.py` — none of these need to change for this patch.
**Implementation steps:**
1. For each of the 6 affected cards (`compound_heat_aqi_danger`, `compound_driving_hazard`, `visibility_commute`, `destination_alert`, `agriculture_advisory`, `marine_conditions_alert`), determine the correct threshold by reading that card's own `urgency_multiplier()` branch and picking the value that corresponds to its own "genuinely severe" band — for example, `visibility_commute`'s branch already returns 2.5 at its worst band, so its `_HARD_ALERT_URGENCY` entry should reasonably be set at or near 2.5, not copied from an unrelated card.
2. Add each entry to `_HARD_ALERT_URGENCY` with a one-line comment justifying the chosen number against that card's own urgency bands, matching the documentation discipline already used for the existing 4 entries.
3. Do not change any urgency band, any weight, or any priority threshold — this patch only extends which cards `is_alert()` is even allowed to evaluate.
**Regression tests:**
- New unit tests: for each of the 6 cards, a synthetic `ContextFrame` at the card's own worst-case band produces `is_alert=True`.
- New unit test: a synthetic low-confidence (e.g., `source="simulated"`) but severe scenario for one of the 6 cards, previously landing at P3, now correctly floors to P2 via `apply_alert_priority_floor()` — this is the test that actually proves the fix closes the real risk, not just that the boolean flips.
- Full existing 163-test suite re-run, confirming zero change to any of the 4 already-covered cards' behavior.
- Golden-set re-run (34 scenarios) confirming no regression, plus the `is_alert` assertion check from Section 10, item 1.
**Acceptance criteria:** all 11 `alertable: True` cards can reach `is_alert=True`, each at a documented and justified threshold; the low-confidence-floor test passes for at least one of the 6 previously-unprotected cards; existing suite and golden set both remain green.

### PATCH 2 — Documentation hygiene (resolves GAP-02, GAP-03, GAP-04)
**Objective:** remove misleading dead code and close the spec-citation gap for one undocumented rule; correct the historical document's staleness.
**Exact files to modify:** `engine/engine.py` (remove or repurpose `_PERSONAS_ALL`), the redundancy-suppression block's comment (add rationale + spec citation, or create the missing citation target if one doesn't yet exist), `MAUSAM_MASTER_SYSTEM_KNOWLEDGE_BASE.md` (add a superseded/historical notice at the top).
**Exact files not to modify:** anything under `backend/`, `adapters/`, `cache/`.
**Implementation steps:** straightforward text/comment changes; no logic changes.
**Regression tests:** none required — this patch changes no runtime behavior. If `_PERSONAS_ALL` removal is chosen, confirm via a repository-wide search that nothing external imports it (this review found no such reference in the supplied code, but that search was scoped to the supplied `engine/` package only).
**Acceptance criteria:** dead constant resolved one way or the other; suppression block carries the same citation discipline as the rest of the file; knowledge base clearly marked historical.

**No PATCH 3 is required.** These two patches, both small and precisely scoped, are sufficient to close every genuine gap this review found.

---

## 13. Explicit Rejections

- **Adding a second live weather/AQI provider now.** Rejected — no evidence of a reliability problem with the current single-provider setup exists in the supplied documents; the adapter abstraction already makes this a future config change, not an architecture change, whenever real evidence justifies it.
- **Adding a fallback-to-default-homepage path for database outages.** Rejected — this would reintroduce exactly the "silently unpersonalized but looks fine" failure mode the project has otherwise consistently avoided; the current hard-fail is the more honest design for this project's actual risk profile.
- **Adding Firebase/full authentication now.** Rejected — nothing in the supplied evidence shows a concrete requirement this blocks; anonymous device identity is sufficient for the current integration stage and was correctly deferred, not forgotten.
- **Adding Redis, a message queue, or any additional infrastructure service.** Rejected — no concrete gap in the supplied evidence points to a need for any of these; PostgreSQL's existing role covers both preference persistence and signal caching adequately at this project's scale.
- **Inflating the test count.** Rejected as a goal in itself — the three specific tests recommended in Section 10/Patch 1 exist because each closes a named, evidenced risk, not to move a number.
- **Rewriting or restructuring the deterministic engine's core scoring model.** Rejected — the model itself (persona_weight × urgency_multiplier × confidence_factor, with P0/F-02 as hard overrides) is sound and evidenced; the one real defect found (GAP-01) is a data-table completeness issue, not a model defect, and does not justify touching `scoring.py`'s formula or `engine.py`'s pipeline shape.
- **Introducing any ML or LLM logic into the ranking path.** Rejected, consistent with the project's own explicit, correct, and unchanged boundary — nothing in this review's findings creates any justification for revisiting that boundary.

---

## 14. Final Backend Freeze Recommendation

**PATCH THEN FREEZE.**

Patch 1 is small, precisely scoped, and directly closes a real gap in the project's own stated safety guarantee for 6 cards. Patch 2 is documentation-only and can proceed in parallel or immediately after. Neither requires reopening the engine's architecture, redesigning the API, or touching the database/provider layers. Once Patch 1's acceptance criteria are met and the golden set is confirmed to actually assert `is_alert` for the previously-unprotected cards, the backend should be refrozen and frontend integration should proceed exactly as currently planned.
