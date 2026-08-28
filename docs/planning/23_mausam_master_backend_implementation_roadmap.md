# Mausam PS26076 — Master Phase-Wise Implementation Roadmap

Authoritative execution blueprint, built directly on `MAUSAM_BACKEND_ML_ARCHITECTURE_REVIEW.md`'s audited findings (code-verified, not doc-claimed). Every "current-state problem" cited below traces to a specific finding in that review. No code is modified by this document.

---

## 1. EXECUTIVE DECISION

Take the current 2.5-of-8-persona, well-architected but partially-stubbed system through **10 sequential-with-limited-parallelism phases** (Phase 0–9) to a complete 8-persona, resilient, explainable, hybrid-ready system. The deterministic engine's core design (pure `engine/`, P0 override, F-02 alert floor, templated explanations) is preserved and extended, never rebuilt. Novelty is added as a deterministic **cross-signal reasoning layer** first (cheap, defensible, extends an already-proven pattern), with ML deliberately deferred until real interaction data exists — not before. The first phase to execute is **Phase 0 (Foundation Stabilization & Contract Integrity)**, because every later phase's testability depends on it existing first.

---

## 2. RECOMMENDED NUMBER OF PHASES + WHY

**10 phases (0–9).** Reasoning for this exact count, not a rounder number:

- **Phase 0 is separated from Phase 1** because contract/test stabilization (mechanical, low-risk, no domain logic) and engine weight *validation* (analytical, requires running the spike, may surface a PIVOT signal) are different kinds of work with different risk profiles — collapsing them would hide a possible PIVOT finding behind unrelated test-writing.
- **Phase 2 (context/health-condition completion) is separated from persona completion (Phases 3–4)** because it's infrastructure every subsequent persona phase depends on (`health_flags` actually affecting scoring, `saved_locations` reaching the engine) — building new personas on top of an incomplete `ContextFrame` would mean redoing work.
- **Persona completion is split into two phases (3 and 4), not one**, because Traveler/Commuter reuse existing signals and adapters (cheap, low external-dependency risk) while Agriculture/Beachgoer/Event-Planner require genuinely new domain data models and, in two cases, unconfirmed external data availability (INCOIS, soil moisture) — merging them would force a fast-and-cheap milestone to wait on a slow-and-uncertain one.
- **Live data integration (Phase 5) comes after persona completion, not before**, because widening the deterministic rule base first (Phase 2–4) means the live-data resilience work in Phase 5 has more surface area to prove itself against, and because AQI/UV live integration doesn't block any persona's *fixture-mode* demoability.
- **The novelty layer (Phase 6) is its own phase**, not folded into persona work, because it's explicitly a cross-cutting capability (reasoning across cards, not within one card) and deserves its own scope boundary and its own demo narrative validation.
- **Telemetry (Phase 7) is separated from ML (Phase 8)** for the same reason the original ML brief separated them: you cannot design a training pipeline before you know what data collection actually looks like in practice.
- **Evaluation/observability/demo hardening is its own final phase (9)**, not scattered across every phase, because judging-day resilience (health checks, warm-up, fallback rehearsal) is a distinct concern from feature completeness and deserves a dedicated, final pass across the *whole* system rather than partial passes per feature.

This avoids both failure modes named in the brief: it's not artificially forced to a round number, and no phase bundles unrelated architectural risk just to save a phase count.

---

## 3. TARGET END-STATE ARCHITECTURE

```
Frontend / Mobile Client
        ↓
FastAPI API Layer  (validated inputs, stable error envelope, /health)
        ↓
Device Identity (anonymous device_id — unchanged; auth deliberately NOT added, see §9)
        ↓
Preference / Persona Service  (8-persona enum, health_flags now scoring-relevant,
        saved_locations now engine-reachable)
        ↓
Location + Temporal Context  (unchanged, extended: destination context for Traveler)
        ↓
Live Data Aggregation Layer  (AQI/UV real HTTP + timeout/retry/cache; new adapters:
        visibility, marine [if confirmed feasible], soil-moisture-proxy, extended forecast)
        ↓
Data Normalization  (SignalValue contract — unchanged, extended to new signal types)
        ↓
Candidate Generation  (CARD_DEFINITIONS grown from 8 → ~14-16 cards across 8 personas)
        ↓
Deterministic Safety & Hard Rules  (P0 override, F-02 floor — UNCHANGED, untouched by any phase)
        ↓
Cross-Signal Reasoning Layer  (NEW — compound-condition detection, still deterministic)
        ↓
Feature Construction  (score_components — extended for future ML features, Phase 8+)
        ↓
Personalization Ranking  (deterministic through Phase 7; hybrid-capable from Phase 8)
        ↓
Conflict / Diversity Resolution  (resolve_ties — unchanged)
        ↓
Explanation Generation  (templated — extended with delta/"why now" reasoning, Phase 6)
        ↓
Interaction Telemetry  (NEW, Phase 7 — impressions/clicks/dismissals logged)
        ↓
Database  (Neon — 2 tables today → 3-4 tables: preferences, signal_cache,
        interaction_events [Phase 7], optionally model_version [Phase 8])
```

---

## 4. CURRENT → TARGET GAP SUMMARY

| Area | Current (audited) | Target | Closed by |
|---|---|---|---|
| Backend contract test coverage | Empty file | Full `/homepage`/`/explain`/`/preferences` contract suite | Phase 0 |
| AQI/UV fixture demoability | Single static sample | Scenario-driven, mirrors forecast/warning | Phase 0 |
| Engine weight validation | One manual fix (F-01), spike never run | Golden-set spike executed, GO/CONDITIONAL/PIVOT verdict recorded | Phase 1 |
| Undeclared-persona default | Silent 0.2 (worse than doing nothing) | Falls back to `default_general` weights | Phase 1 |
| `health_flags` effect on scoring | Zero — cosmetic only | Modifies urgency thresholds/weights for declared conditions | Phase 2 |
| `saved_locations` | Stored, DB-only, engine-blind | Reaches `ContextFrame`, powers Traveler destination alerts | Phase 2 |
| Personas implemented | 2 full + 1 partial of 8 | 8 of 8 (with honest per-persona MVP-vs-enhancement scoping) | Phases 3–4 |
| AQI/UV live data | Stub, always `unavailable` in live mode | Real HTTP, timeout/retry, `cache.store` actually wired | Phase 5 |
| Cross-card reasoning | None (each card scored independently) | Deterministic compound-condition detection | Phase 6 |
| Interaction data | None | Logged, typed, separated explicit/implicit | Phase 7 |
| ML | 0% | Baseline offline model, hybrid inference at the `persona_weight` seam only | Phase 8 |
| Demo/judging resilience | Ad hoc | Rehearsed, monitored, explicitly tested failure modes | Phase 9 |

---

## 5. FULL PHASE-BY-PHASE IMPLEMENTATION ROADMAP

### Phase 0 — Foundation Stabilization & Contract Integrity

**A. Phase Objective.** Make the *existing* system verifiably correct and demoable before any new capability is added.

**B. Why This Phase Comes Here.** Every later phase adds tests "mirroring the existing pattern" — that pattern must actually exist and be trustworthy first. Building new personas on an unverified contract multiplies, not just adds, risk.

**C. Current-State Problems Being Solved.** Empty `backend/tests/test_homepage_contract.py`; static single-sample AQI/UV fixture with no scenario variation; no `device_id` format validation; no persona/health-flag enum validation; silent 0.2-default weight for undeclared personas (worse than the `default_general` fallback).

**D. Scope.**
- IN SCOPE: contract tests for all 3 existing endpoints; scenario-driven AQI/UV fixtures; input validation (device_id format, persona/health-flag enums); fix the undeclared-persona default.
- OUT OF SCOPE: any new persona, any new card, any live external call, any schema change beyond validation.

**E. Detailed Implementation Tasks.**
1. Write `backend/tests/test_homepage_contract.py`: assert response shape matches `07_api_and_data_contracts.md` exactly for a normal scenario, a severe-warning scenario (`warnings_override` populated), and an all-unavailable scenario (`system_notice` populated). *Why:* zero API-level verification currently exists. *Layer:* backend. *Expected behavior after:* a broken contract fails CI, not a demo.
2. Split `aqi_uv_recorded_samples.json` into `aqi_uv_normal.json`, `aqi_uv_moderate.json`, `aqi_uv_poor.json`, `aqi_uv_severe.json`, selected by `FIXTURE_SCENARIO` the same way forecast/warning already are. *Why:* cannot currently demo an AQI-alert moment without hand-editing JSON. *Layer:* adapters. *Expected behavior:* `FIXTURE_SCENARIO=poor` produces a visible P1 AQI alert end-to-end.
3. Add device_id UUID-v4 format validation in `backend/models_api.py` and the `/homepage` query path; add a fixed enum check for `personas`/`health_flags` against the documented set. *Why:* currently any string is accepted silently. *Layer:* backend. *Expected behavior:* malformed input returns 422 with the standard error envelope, not silently stored garbage.
4. Fix `PERSONA_WEIGHT.get((card_id, persona), 0.2)` in `engine/scoring.py` to fall back to `default_general`'s weight for that card when the persona is unrecognized, not a flat 0.2. *Why:* audited as a real, currently-worse-than-nothing UX bug. *Layer:* engine (pure, isolated one-line-logic change, no architecture impact).

**F. Exact Repository Impact.**
- Modify: `backend/tests/test_homepage_contract.py`, `backend/models_api.py`, `engine/scoring.py` (one function, `score()` or a new `_persona_weight()` helper).
- Create: `adapters/fixtures/aqi_uv_normal.json`, `aqi_uv_moderate.json`, `aqi_uv_poor.json`, `aqi_uv_severe.json`; `adapters/tests/test_aqi_adapter.py`, `adapters/tests/test_uv_adapter.py` (currently the only tested adapters are forecast/warning/sun).
- No DB migration. No new env vars (reuses existing `FIXTURE_SCENARIO`).

**G. Data Flow.** Unchanged shape; only fixture content and validation gates change:
`FIXTURE_SCENARIO=poor → AQIAdapter reads aqi_uv_poor.json → SignalValue(aqi=178,...) → ContextFrame → engine.rank() → P1 alert card → /homepage response`

**H. Engine / Deterministic Logic Impact.** One isolated fix (undeclared-persona default). No scoring formula, threshold, P0 rule, or F-02 rule changes.

**I. API Contract Impact.** No new endpoints. Response shape unchanged. New: 422 responses for malformed `device_id`/persona/health-flag inputs (previously silently accepted).

**J. Database Impact.** None.

**K. External Dependency Impact.** None — all fixture-mode, no credentials needed.

**L. Testing Strategy.**
1. Unit: `test_scoring.py` gets a new case for an unrecognized persona falling back to `default_general` weights.
2. Integration: adapter tests for AQI/UV across all 4 new scenario files.
3. Contract: the new `test_homepage_contract.py` suite (3 scenarios minimum).
4. Failure-mode: malformed `device_id` → 422; unrecognized persona string → 422.
5. Regression: existing 137 engine tests must still pass unchanged.

**M. Definition of Done.** All contract tests pass; `FIXTURE_SCENARIO=poor` demoable end-to-end via `curl`; malformed input rejected with 422; undeclared-persona fallback test passes.

**N. Risks and Failure Modes.** Low risk overall. Main risk: enum validation is too strict and rejects a persona value the frontend already sends — mitigate by cross-checking against `09_ux_ui_specification.md`'s S4 persona list before locking the enum.

**O. Estimated Complexity: Low.** No architecture change, no external dependency, small well-scoped diffs, matches the "first sprint" recommendation from the prior review.

---

### Phase 1 — Deterministic Engine Validation & Calibration

**A. Phase Objective.** Establish, with evidence, whether the current 32-weight table (and the 3 personas it covers) actually outperforms the two rejected baselines (generic homepage, static persona template) — the central novelty claim this whole project rests on, never yet tested against real code.

**B. Why This Phase Comes Here.** Every later persona-completion phase adds *more* unvalidated weight rows on top of an already-unvalidated base. Validating now, on the smaller 3-persona surface, is cheaper and catches a possible PIVOT signal before it's compounded across 8 personas.

**C. Current-State Problems Being Solved.** The feasibility spike (`04_personalization_feasibility_spike_plan.md`/`05_evaluation_dataset_and_annotation_plan.md`) was fully designed but never executed against the real engine; only one isolated manual fix (F-01) is evidenced, not a systematic pass.

**D. Scope.**
- IN SCOPE: build `eval/golden_set.json` (20–30 hand-annotated scenarios per the existing plan), build `eval/run_spike.py` (Engine vs. Baseline A/generic vs. Baseline B/static-persona), execute it, record the GO/CONDITIONAL/PIVOT verdict, apply any weight corrections the evidence supports.
- OUT OF SCOPE: any new card or persona; any change to the scoring *formula* (only weight *values* may change, not the multiplicative model itself, unless the verdict is PIVOT — see Risks).

**E. Detailed Implementation Tasks.**
1. Author the golden set across the 5 scenario families already specified (same-weather-different-user, same-user-changing-context, cold-start, missing-data, P0-override), using the 3 currently-implemented personas. *Why:* this is the evidence base every weight decision should trace to. *Layer:* new `eval/` module, outside `engine/`.
2. Build the spike runner: feeds each scenario's `ContextFrame` through `engine.rank()`, Baseline A (fixed order), and Baseline B (persona-locked order); computes top-1 match rate, top-3 overlap, alert correctness against the hand-written expected labels. *Layer:* `eval/`.
3. Run it, record results honestly (including if only CONDITIONAL GO), update `docs/IMPL_CALIBRATION_DECISIONS.md` with any resulting weight changes, each documented the same way F-01 was (old value, new value, reasoning, what's unchanged).

**F. Exact Repository Impact.**
- Create: `eval/golden_set.json`, `eval/run_spike.py`, `eval/README.md` (methodology, matching `04_...md`/`05_...md`).
- Modify (only if the spike's evidence supports it): specific `PERSONA_WEIGHT` rows in `engine/scoring.py`, `docs/IMPL_CALIBRATION_DECISIONS.md`.
- No new tests beyond the spike itself, since `eval/` validates the engine, it isn't part of the production test suite.

**G. Data Flow.** No production data flow change — `eval/run_spike.py` calls `engine.rank()` directly with hand-built `ContextFrame` objects, entirely offline from the API/adapters.

**H. Engine / Deterministic Logic Impact.** Potentially changes specific `PERSONA_WEIGHT` values (data, not logic) if evidence supports it — exactly the same class of change as F-01. No threshold, P0, or F-02 logic touched. If the verdict is a genuine PIVOT (engine doesn't beat static-persona baseline), that is escalated as an explicit decision point, not silently absorbed — see Risks.

**I. API Contract Impact.** None.

**J. Database Impact.** None.

**K. External Dependency Impact.** None.

**L. Testing Strategy.** This phase *is* a testing/evaluation exercise. 1. Unit: none new. 2. Integration: the spike itself. 3. Contract: none. 4. Failure-mode: n/a. 5. Regression: re-run existing `engine/tests/` after any weight change to confirm nothing documented elsewhere breaks (e.g., the cold-start ordering sanity check comment in `scoring.py`).

**M. Definition of Done.** Golden set exists and is peer-reviewed (per the original annotation-process plan: author + independent reviewer); spike executed; a documented GO/CONDITIONAL/PIVOT verdict exists; any resulting weight changes are committed with F-01-style documentation.

**N. Risks and Failure Modes.** **The real risk this phase exists to surface:** a PIVOT result. If the engine does not clearly beat the static-persona baseline, do not proceed to Phase 2 silently — this must be escalated as a genuine decision point (re-derive weights with more rigor, or reconsider whether Differentiator 4 — degradation/trust transparency — should become the primary novelty claim instead, per the original `02_novelty_and_competitive_landscape.md` framing). Treat this as the single highest-leverage risk in the entire roadmap: catching it here is cheap; catching it after Phase 4 is expensive.

**O. Estimated Complexity: Medium.** Not technically hard (no new architecture), but requires careful, honest annotation work and real discipline not to write expected labels that match whatever the engine already outputs.

---

### Phase 2 — Context Model Completion & Health-Condition-Aware Personalization

**A. Phase Objective.** Make `health_flags` and `saved_locations` actually reach and influence the engine — closing the two most concrete "stored but inert" gaps found in the audit.

**B. Why This Phase Comes Here.** This is infrastructure: Phase 3's Traveler persona needs `saved_locations` in `ContextFrame`; making health-flags scoring-relevant now (rather than per-persona later) means every subsequent persona phase inherits the same, already-tested mechanism instead of reinventing it.

**C. Current-State Problems Being Solved.** `health_flags` is stored and passed through but never read by `urgency_multiplier()` or `PERSONA_WEIGHT` — a health-persona user with "respiratory_sensitive" scores identically to one with no flags. `saved_locations` is a fully-wired DB column with zero `ContextFrame` presence.

**D. Scope.**
- IN SCOPE: add `saved_locations: list[dict]` to `ContextFrame`; design and implement a deliberate, narrow health-flag modifier mechanism (not a full rewrite of scoring); wire both through `backend/deps.py`.
- OUT OF SCOPE: Traveler's actual destination-alert *card* (that's Phase 3 — this phase only makes the data reachable); any new external adapter.

**E. Detailed Implementation Tasks.**
1. Add `saved_locations: list[dict] = field(default_factory=list)` to `ContextFrame` (`engine/models.py`); populate it in `build_context_frame()` from `prefs.get("saved_locations", [])`. *Why:* currently entirely absent from the engine's input. *Layer:* engine model + backend deps.
2. Design the health-flag modifier as an **explicit, small, separate multiplier** — `health_flag_multiplier(card_id, cf) -> float`, called alongside (not folded silently into) `urgency_multiplier()`, so the existing "urgency is environment-only" invariant and its test (`test_urgency_is_environment_only_not_persona`) stay true and meaningful. *Why:* preserves the audited safety property (Risk R5 mitigation) that made the engine trustworthy in the first place, while still letting a declared condition matter. *Layer:* new small function in `engine/scoring.py`, called from `engine/engine.py`'s `score()` orchestration only for the `aqi_health`/`uv_sun_exposure` cards initially. *Expected behavior:* a `health` persona user with `respiratory_sensitive` reaches P1 at a *lower* AQI threshold than one without it (e.g., effective threshold band shifted, not the raw urgency changed) — this is documented, testable, and explainable, not hidden inside `urgency_multiplier`.
3. Update `build_explanation()`'s `aqi_health`/`uv_sun_exposure` templates to mention the health flag explicitly when it materially changed the outcome (e.g., "...and because you've flagged respiratory sensitivity, this is shown as..."). *Why:* the explanation must stay honest about *why* — silently applying a modifier without surfacing it in the explanation would violate NFR-1.

**F. Exact Repository Impact.**
- Modify: `engine/models.py` (new field), `backend/deps.py` (populate it), `engine/scoring.py` (new `health_flag_multiplier()` function), `engine/engine.py` (call it), `engine/explain.py` (template update).
- Create: `engine/tests/test_health_flag_modifier.py`.
- No DB migration (columns already exist; only the read-path into the engine changes).

**G. Data Flow. BEFORE:** `preferences.saved_locations/health_flags → get_preferences() → prefs dict → (health_flags passed to ContextFrame but read only by cosmetic explanation clause; saved_locations dropped entirely, never reaches ContextFrame)`.
**AFTER:** `preferences.saved_locations/health_flags → get_preferences() → prefs dict → ContextFrame.saved_locations [NEW] + ContextFrame.health_flags → score() reads health_flag_multiplier() [NEW] → priority/explanation reflect it`.

**H. Engine / Deterministic Logic Impact.** Adds one new, clearly-separated multiplier factor to the scoring pipeline for 2 cards initially (AQI, UV) — this is an *addition* to the formula (`score = persona_weight × urgency_multiplier × confidence_factor × health_flag_multiplier`, with `health_flag_multiplier` defaulting to 1.0 when no relevant flag is declared, so all existing behavior for flag-less users is byte-for-byte unchanged). P0/F-02 untouched. This is the single most safety-sensitive change in the whole roadmap because it touches the scoring formula itself — hence its own dedicated, small, tightly-tested phase rather than being bundled into general persona work.

**I. API Contract Impact.** `PUT /preferences`'s `saved_locations` field was already accepted (Pydantic model `PreferencesBody` already has it) — no contract change there. No response shape change yet (destination-alert cards come in Phase 3).

**J. Database Impact.** None — both columns already exist; this phase only changes what the backend/engine *does* with data already being stored.

**K. External Dependency Impact.** None.

**L. Testing Strategy.**
1. Unit: `health_flag_multiplier()` returns 1.0 for no/irrelevant flags, >1.0 only for the specific documented (card, flag) pairs.
2. Integration: `build_context_frame()` correctly populates `saved_locations` from a preferences fixture.
3. Contract: `/preferences` round-trip test confirms `saved_locations` survives a write/read cycle unchanged (already likely true, now explicitly tested).
4. Failure-mode: a malformed/unknown health flag string doesn't crash the multiplier — defaults to 1.0, doesn't raise.
5. Regression: full `engine/tests/` suite, specifically re-confirm `test_urgency_is_environment_only_not_persona` still passes untouched (proves the new multiplier didn't leak into `urgency_multiplier`).

**M. Definition of Done.** A health-persona user with a declared relevant flag demonstrably reaches a higher priority/alert state at a lower raw signal value than one without, with the explanation text saying so; `saved_locations` is present and populated in a live `ContextFrame` (verified via a debug/log inspection or a temporary test endpoint, not yet surfaced as a card).

**N. Risks and Failure Modes.** Risk of scope creep into "redesign scoring for every flag × every card" — mitigate by explicitly scoping this phase to 2 cards (AQI, UV) and the 1–2 flags with the clearest PS justification (respiratory_sensitive, heat_sensitive), leaving broader flag coverage as a Phase 4/enhancement item, not blocking this phase's completion.

**O. Estimated Complexity: Medium-High.** Not architecturally large, but it is the first phase to touch the scoring *formula* itself since the engine was frozen — requires the same care the original F-01/F-02 calibration fixes show, and should be reviewed with the same rigor.

---

### Phase 3 — Persona Completion, Tier 1 (Traveler, Commuter)

**A. Phase Objective.** Bring 2 more personas to genuine, demoable coverage using data/mechanisms that already exist or are cheap additions.

**B. Why This Phase Comes Here.** Both personas reuse existing signals (`severe_warning` logic for Traveler, a new but simple `visibility` field for Commuter) and the now-reachable `saved_locations` from Phase 2 — no new external-data uncertainty, no new domain modeling. Sequenced before Tier 2 specifically because it's the cheaper, lower-risk half of persona completion and de-risks the "8 personas" narrative fastest.

**C. Current-State Problems Being Solved.** Traveler: `saved_locations` inert (now fixed by Phase 2), no destination-alert logic, no packing suggestions. Commuter: does not exist as a distinct persona at all (`PERSONA_WEIGHT` has no `commuter` key); no `visibility` field; fog/storm only representable via generic free-text warning fields.

**D. Scope.**
- IN SCOPE: `traveler` and `commuter` added to `PERSONA_WEIGHT`'s persona dimension; new cards `destination_alert` and `packing_suggestion` (Traveler); new field `visibility` and card `visibility_commute` (Commuter); enriched `WarningAdapter` fixtures with typed fog/storm entries.
- OUT OF SCOPE: real traffic data (unresearched — flagged as its own scoping task, not committed to in this phase); real destination weather (destination alert reuses the *current* warning-fixture mechanism keyed to a second lat/lon, fixture-mode only for now).

**E. Detailed Implementation Tasks.**
1. Add `("destination_alert", persona)` and `("packing_suggestion", persona)` rows to `PERSONA_WEIGHT` for all 4 existing + 2 new personas (traveler highest, others low-but-present per the established pattern). *Layer:* engine data.
2. Add `CARD_DEFINITIONS["destination_alert"]` — required signal: `saved_locations` non-empty; `_card_applies()` gate checks at least one saved location has an active warning (a second `WarningAdapter.fetch()` call per saved destination, capped at e.g. 3 destinations for the MVP). *Why:* directly answers the PS's "severe weather alerts affecting travel/flights" bullet using an already-proven mechanism. *Layer:* engine + backend deps (multiple warning fetches).
3. Add `CARD_DEFINITIONS["packing_suggestion"]` — a **templated, rule-based lookup** (temp/precip band → phrase, e.g., "Carry a raincoat" for high precip probability at a saved destination), explicitly following the same non-LLM pattern as `explain.py` — this is a deliberate architectural choice to preserve the "never an LLM/free-text decision" property established in `02_novelty_and_competitive_landscape.md`. *Layer:* new small lookup table, engine.
4. Add `visibility: SignalValue` to `ContextFrame`; add `CARD_DEFINITIONS["visibility_commute"]`, weight highest for `commuter`; add urgency thresholds (e.g., <1km = high urgency) mirroring the AQI/UV threshold pattern exactly. *Layer:* engine + new adapter field (fixture-backed initially, same pattern as forecast fields).
5. Enrich `warning_*.json` fixtures with a `type` field explicitly set to `"fog"`/`"storm"`/`"heatwave"` etc. (the field already exists in the model, just needs richer fixture content) so Commuter's storm/fog PS bullet has concrete, demoable backing.

**F. Exact Repository Impact.**
- Modify: `engine/cards.py` (2-4 new entries + `CARD_DEFINITION_ORDER`), `engine/scoring.py` (new PERSONA_WEIGHT rows, new `packing_suggestion` lookup table), `engine/priority.py` (`_HARD_ALERT_URGENCY` additions), `engine/engine.py` (`_card_applies`/`_primary_signal_for`/`_signal_refs_for` new branches), `engine/explain.py` (new templates), `engine/models.py` (`visibility` field), `backend/deps.py` (multi-destination warning fetch, visibility signal wiring), `adapters/fixtures/warning_*.json` (richer `type` values).
- Create: `adapters/visibility_adapter.py` (fixture-mode, mirrors `forecast_adapter.py`'s pattern exactly), `engine/tests/test_traveler_persona.py`, `engine/tests/test_commuter_persona.py`.
- No DB migration.

**G. Data Flow.**
**BEFORE (Traveler):** `preferences.saved_locations → DB only, never read by engine`.
**AFTER:** `preferences.saved_locations → ContextFrame.saved_locations [Phase 2] → backend/deps.py fetches WarningAdapter per saved location → destination_alert card scored/ranked → explanation cites the specific destination`.
**NEW (Commuter):** `VisibilityAdapter.fetch() → SignalValue → ContextFrame.visibility → visibility_commute card`.

**H. Engine / Deterministic Logic Impact.** Purely additive — new `PERSONA_WEIGHT` rows, new cards, new urgency branches, following the exact established pattern. No existing card's scoring changes. P0/F-02 untouched. `packing_suggestion` is explicitly rule-based/templated, preserving the no-LLM-on-decision-path constraint.

**I. API Contract Impact.** `HomepageResponse.cards[]` can now include `destination_alert`, `packing_suggestion`, `visibility_commute` card IDs — additive, backward compatible (existing consumers ignore unknown card IDs gracefully if the frontend is built defensively; flag this as a frontend coordination point, not a backend risk).

**J. Database Impact.** None — `saved_locations` column already exists.

**K. External Dependency Impact.** None new — destination alerts reuse the existing fixture-mode `WarningAdapter`; visibility is fixture-mode. Real traffic data is explicitly deferred (flagged, not silently dropped).

**L. Testing Strategy.**
1. Unit: `PERSONA_WEIGHT` completeness test extended to the new (card × persona) pairs, mirroring `test_all_32_combinations_present`.
2. Integration: a saved-location-with-active-warning scenario produces a `destination_alert` card; a low-visibility fixture produces a `visibility_commute` alert.
3. Contract: `HomepageResponse` schema still validates with new card IDs present.
4. Failure-mode: empty `saved_locations` → no `destination_alert` card, no crash; >3 saved locations → capped gracefully, not an error.
5. Regression: full existing suite unchanged.

**M. Definition of Done.** Traveler and Commuter personas each produce at least 2 genuinely differentiated, demoable cards backed by fixture data; PS bullets for both personas now map to actual code (per an updated version of the Deliverable-3 matrix from the forensic review).

**N. Risks and Failure Modes.** Multi-destination warning fetching could be slow if not capped — mitigate with the stated 3-destination cap. Risk of the packing-suggestion lookup feeling gimmicky if not tightly scoped to 3-4 clear bands — mitigate by keeping it small and explicitly rule-based, resisting the urge to "make it smarter" with free text.

**O. Estimated Complexity: Medium.** New cards follow an established pattern (low risk), but touches 6 files per persona and introduces the first multi-fetch (per-destination) backend call pattern.

---

### Phase 4 — Persona Completion, Tier 2 (Agriculture, Beachgoer, Event Planner)

**A. Phase Objective.** Complete PS persona coverage to 8 of 8.

**B. Why This Phase Comes Here.** These three need genuinely new domain data models (soil moisture, marine signals, multi-day forecast arrays) and, in two cases, external data availability that was never confirmed in the original research (INCOIS public API, validated soil-moisture source) — deliberately sequenced after the cheaper Tier 1 work and after Phase 5's live-data-resilience patterns exist to reuse, if any of these end up needing a live call rather than pure fixtures.

**C. Current-State Problems Being Solved.** All three personas: zero representation in `PERSONA_WEIGHT`, `CARD_DEFINITIONS`, or `ContextFrame` today.

**D. Scope.**
- IN SCOPE: `agriculture`, `beachgoer`, `event_planner` added as personas; `soil_moisture_proxy` (simulated, explicitly labeled — no validated live source confirmed), `sea_conditions` (fixture-only unless INCOIS access is separately confirmed — see K), `extended_forecast: list[dict]` (new schema addition, multi-day), `comfort_index` (computed, not fetched).
- OUT OF SCOPE: any claim of live/validated data for soil moisture or marine signals unless Phase 4's own research step (task 1 below) confirms a source — otherwise these ship as clearly-labeled simulated/illustrative cards, following the exact precedent already set by `pollen_illustrative`.
- OUT OF SCOPE: real frost-prediction modeling (a rule-based temp threshold is in scope; a genuine agromet model is not).

**E. Detailed Implementation Tasks.**
1. **Research task (must complete before committing to "live" framing for any signal in this phase):** confirm or rule out INCOIS public API access (Flag 1 from the original consistency-check doc was never resolved) and any soil-moisture data source realistically usable in the timeframe. *Why:* avoid repeating the original project's own "never claim live data without verifying it" discipline. *Layer:* research, not code.
2. Add `extended_forecast: list[dict]` to `ContextFrame` (a short array of `{day_offset, temp_c, precip_prob_pct}`), sourced from `ForecastAdapter` extended to return multiple days in fixture mode. *Layer:* engine model + adapter.
3. Add `comfort_index` as a **computed** field (not fetched) — a simple deterministic formula over temp/humidity/wind (e.g., a heat-index-style calculation), computed in `backend/deps.py` or a small `engine/derived.py` helper, never an external call. *Why:* PS explicitly asks for this and it is honestly and cheaply computable, no data-sourcing risk at all.
4. Add `CARD_DEFINITIONS` entries: `soil_moisture_advisory` (agriculture, explicitly labeled simulated per task 1's outcome), `sea_conditions` (beachgoer, same labeling discipline), `extended_outlook` (event_planner, uses `extended_forecast`), `comfort_index` (event_planner primary, others secondary).
5. Add `PERSONA_WEIGHT` rows for the 3 new personas across all cards (existing + new) — following the exact same completeness-test pattern as before.

**F. Exact Repository Impact.**
- Modify: `engine/models.py` (`extended_forecast`, `soil_moisture`, `sea_conditions` fields — each a `SignalValue`), `engine/cards.py`, `engine/scoring.py`, `engine/priority.py`, `engine/explain.py`, `engine/engine.py`, `backend/deps.py`, `adapters/forecast_adapter.py` (extend for multi-day).
- Create: `engine/derived.py` (comfort index calculation, pure function, lives inside `engine/` since it's deterministic and I/O-free — consistent with the frozen boundary), `adapters/soil_moisture_adapter.py`, `adapters/marine_adapter.py` (both fixture-only unless task 1 changes this), `engine/tests/test_agriculture_persona.py`, `test_beachgoer_persona.py`, `test_event_planner_persona.py`, `engine/tests/test_comfort_index.py`.
- No DB migration.

**G. Data Flow.** Same additive pattern as Phase 3, extended to 3 more personas; `comfort_index` is notably **computed, not fetched** — `temp_c + humidity_pct + wind_kmh (already in ContextFrame) → engine/derived.py::comfort_index() → new card`, demonstrating that not every PS bullet needs a new adapter.

**H. Engine / Deterministic Logic Impact.** Purely additive, same pattern as Phase 3. `comfort_index` is the one genuinely new *derived computation* (not just a threshold lookup) — still deterministic, still pure, still inside `engine/`'s boundary correctly.

**I. API Contract Impact.** Additive card IDs, same as Phase 3.

**J. Database Impact.** None.

**K. External Dependency Impact.** Contingent on task 1's research outcome. If INCOIS/soil-moisture sources are confirmed unusable (as the original research suggested but never fully verified), `sea_conditions` and `soil_moisture_advisory` ship as **permanently simulated/illustrative** cards, exactly like `pollen_illustrative` — this is an acceptable, honest, precedented MVP outcome, not a failure of this phase.

**L. Testing Strategy.** Same 5-category pattern as Phase 3, plus a dedicated `comfort_index` formula unit test (known input → known output, boundary values).

**M. Definition of Done.** All 8 personas have `PERSONA_WEIGHT` coverage and at least 1-2 demoable cards each; every simulated-only signal is labeled as such in `source` (matching the `pollen_illustrative` precedent) with no exceptions.

**N. Risks and Failure Modes.** Highest risk of any persona-completion phase: temptation to overstate data quality for agriculture/beachgoer to make the "8 personas" claim feel stronger. Mitigate exactly as the original project's own audit culture did with pollen — label honestly, defend narrowly.

**O. Estimated Complexity: High.** Three personas, one genuine schema extension (`extended_forecast`), one new derived-computation pattern, and unresolved external-data uncertainty going in.

---

### Phase 5 — Live External Data Integration & Resilience

**A. Phase Objective.** Replace the AQI/UV stub with real, resilient live data, and wire the already-imported-but-unused `cache.store` into an actual fallback chain.

**B. Why This Phase Comes Here.** Deliberately after persona completion: live-data resilience patterns (timeout, retry, cache, malformed-data handling) are best proven against the widest possible signal surface, and no persona's *fixture-mode* demoability depends on this phase existing first.

**C. Current-State Problems Being Solved.** `ADAPTER_MODE=live` currently always returns `unavailable` — no real HTTP call is attempted despite `httpx` being imported; `cache.store` is imported in both `aqi_adapter.py` and `uv_adapter.py` but never called.

**D. Scope.**
- IN SCOPE: real `httpx` calls to CPCB (data.gov.in primary, aqicn.org fallback) and OpenWeatherMap; timeouts (5s connect/8s read); one retry on network failure only; malformed-response validation; wiring `cache.store` as the fallback tier between live failure and `unavailable`.
- OUT OF SCOPE: live data for any Phase 4 signal (soil moisture, marine) unless Phase 4's research explicitly confirmed a usable source.

**E. Detailed Implementation Tasks.** (Directly implements what `08_data_source_and_integration_plan.md` §2 and `16_production_architecture_reassessment.md` §3 already specified but the code never built.)
1. Implement the real `AQIAdapter.fetch()` live branch: data.gov.in call → on failure, aqicn.org call → on failure, `cache.store.get()` → if stale, return with `source="stale"` → else `unavailable`. *Layer:* adapters.
2. Same pattern for `UVAdapter` (OpenWeatherMap only, no secondary provider per prior research).
3. Add response-shape validation (e.g., AQI value in plausible 0-500 range) before constructing a `SignalValue` — malformed data is treated as a fetch failure, never passed through.
4. Wire `cache.store.set()` on every successful live fetch (write-through).
5. Handle missing API key at adapter init (log once, skip live attempt entirely, not per-request).
6. Handle 429/rate-limit distinctly from a generic failure (no immediate retry into a rate limit).

**F. Exact Repository Impact.**
- Modify: `adapters/aqi_adapter.py`, `adapters/uv_adapter.py` (the actual live-path bodies), `cache/store.py` (verify/complete — not part of the supplied handoff, status genuinely unconfirmed until this phase inspects it directly).
- Create: `adapters/tests/test_aqi_adapter_live_fallback.py`, `test_uv_adapter_live_fallback.py` (mocked HTTP failures, confirming the fallback chain).
- Config: `.env` gets real `AQI_DATA_GOV_IN_KEY`, `AQI_AQICN_TOKEN`, `OWM_API_KEY` (human task, per `HUMAN_RESEARCH_AND_ACCESS_CHECKLIST.md`, already documented).

**G. Data Flow. BEFORE:** `ADAPTER_MODE=live → immediate return of make_unavailable_signal(), no HTTP attempted`.
**AFTER:** `ADAPTER_MODE=live → httpx call (5s/8s timeout) → on failure, 1 retry (network errors only) → on failure, aqicn.org fallback (AQI only) → on failure, cache.store.get() → stale-flagged or unavailable → SignalValue with correct source/confidence`.

**H. Engine / Deterministic Logic Impact.** None whatsoever — the engine already correctly consumes whatever `source`/`confidence` an adapter returns; this phase only changes *how* adapters populate those fields. This is the cleanest possible illustration of why the adapter/engine boundary was worth enforcing from the start.

**I. API Contract Impact.** None — `source` values already include `"live"`/`"cached"`/`"stale"`/`"unavailable"` in the existing contract; this phase makes them actually reachable instead of `live`/`cached`/`stale` being currently-unreachable dead states for AQI/UV specifically.

**J. Database Impact.** None new — `signal_cache` table already exists; this phase makes it actually get read/written.

**K. External Dependency Impact.** This is the phase where external dependency risk becomes real: data.gov.in/aqicn.org/OpenWeatherMap registration turnaround and rate limits (previously only theoretical in planning docs) now matter in practice. Mitigation: register credentials at the *start* of this phase, not the end, so any registration delay is discovered with time to react.

**L. Testing Strategy.**
1. Unit: response-validation function (plausible-range check) on both good and malformed sample payloads.
2. Integration: mocked `httpx` failures at each tier (timeout, 429, malformed body) confirm the correct fallback tier is reached.
3. Contract: `/homepage` response still validates when AQI is `stale`/`unavailable` (badge fields populated correctly).
4. Failure-mode: missing API key at startup → adapter logs once, never attempts a live call, falls straight to cache/unavailable.
5. Regression: fixture-mode (`ADAPTER_MODE=fixture`) behavior is completely unchanged — this phase must not touch the fixture path at all.

**M. Definition of Done.** A live `/homepage` call with valid credentials returns real, current AQI/UV data with `source="live"`; killing network access mid-session produces a graceful `cached`/`stale`/`unavailable` degradation, never a crash or a fabricated-looking live value.

**N. Risks and Failure Modes.** Credential registration delay (flagged since the original planning phase, never yet resolved in practice) is the single biggest risk — see mitigation above. Secondary risk: `cache/store.py`'s actual current implementation is unverified from this handoff; if it doesn't already match the expected `get()`/`set()` interface, this phase's estimate should absorb a small buffer to complete/fix it, not assume it's ready.

**O. Estimated Complexity: Medium-High.** Not architecturally novel (the pattern was already fully specified in prior planning docs), but real-world external dependencies always carry more uncertainty than internal refactors.

---

### Phase 6 — Deterministic Novelty Layer (Cross-Signal Reasoning & Proactive "Why Now" Explanations)

**A. Phase Objective.** Add the project's most defensible novelty capability: reasoning **across** cards, not just within one card — compound-condition detection and trend-aware ("why now, not yesterday") explanations, both fully deterministic.

**B. Why This Phase Comes Here.** Needs the widened persona/card surface from Phases 3–4 to be meaningfully cross-signal (compound reasoning across 2 cards is a much weaker demo than across 8), and benefits from Phase 5's live data existing so a "why now" delta has something real to compare against, not just fixture noise.

**C. Current-State Problems Being Solved.** Not a bug-fix phase — this addresses the roadmap brief's explicit "do not implement 8 isolated weather dashboards" requirement. Today, `activity_window` is the *only* card with any composite/cross-signal reasoning (`urgency_multiplier`'s `bad =` boolean combining AQI+UV+temp+wind); nothing generalizes this pattern or exposes it as an explicit, named feature.

**D. Scope.**
- IN SCOPE: (1) a small set of named **compound conditions** (e.g., "Heat + Poor Air Quality" — genuinely worse combined than either alone, relevant to health *and* fitness personas simultaneously) detected deterministically and surfaced as their own explained insight, not just a higher score on an existing card; (2) a lightweight **"why now" delta explanation** — comparing the current snapshot's key signal values against the last cached snapshot for the same device/location (using `signal_cache`, already populated by Phase 5) to say e.g. "AQI rose from 96 to 178 since your last visit."
- OUT OF SCOPE: any ML-based pattern detection (this is rule-based cross-referencing, explicitly); any change to the underlying P0/F-02 safety logic; any new persona.

**E. Detailed Implementation Tasks.**
1. Define a small `COMPOUND_CONDITIONS` registry (data, not branching logic, following the `CARD_DEFINITIONS` pattern) — e.g., `{"heat_and_poor_air": {"triggers": [("temp_c", ">=", 38), ("aqi", ">=", 150)], "relevant_personas": ["health","fitness"], "message_template": "..."}`. *Why:* generalizes the one-off `activity_window` composite pattern into a reusable, inspectable mechanism, directly answering the "cross-signal reasoning" novelty goal named in the task brief. *Layer:* new `engine/compound.py`, called from `engine/engine.py` after normal card scoring, before final tie-break.
2. Compound conditions produce their own card (`card_id="compound_<name>"`) with `priority` derived from the *stronger* of its constituent signals' priorities (never lower than either alone) — this is a deliberate design rule to keep the safety-priority ordering internally consistent, and should be unit-tested explicitly.
3. Implement `_delta_explanation(cf, cache_lookup)` in `engine/explain.py` — reads the *previous* cached signal value (via a value passed in by the backend from `signal_cache`, not fetched by the engine itself, preserving the pure-function boundary) and, when a meaningful change occurred, appends a delta clause to the existing explanation template. *Why:* directly extends NFR-1's "traceable to real values" property to include *change over time*, not just a single snapshot — this is a genuinely differentiated capability few weather apps expose transparently.
4. Backend (`backend/deps.py` or `routers/homepage.py`) reads the last cached snapshot for this device/location from `signal_cache` and passes the relevant prior values into `engine.rank()` as an optional parameter — **this is the one place this phase touches the engine's function signature**, and must be done carefully to keep `rank()` still callable with no prior-snapshot data (cold start / first visit) without error.

**F. Exact Repository Impact.**
- Create: `engine/compound.py`, `engine/tests/test_compound_conditions.py`, `engine/tests/test_delta_explanation.py`.
- Modify: `engine/engine.py` (call compound detection + optional prior-snapshot parameter, defaulting to `None`), `engine/explain.py` (delta clause), `engine/models.py` (optional `PriorSnapshot` lightweight type, not a new `ContextFrame` field — kept separate since it's not "current context," it's historical comparison data), `backend/routers/homepage.py` / `backend/deps.py` (read prior snapshot from `signal_cache`, pass to `rank()`).

**G. Data Flow.** `signal_cache (previous fetched_at/value) → backend reads prior snapshot → engine.rank(cf, prior_snapshot=...) [new optional param] → compound.py detects cross-signal conditions + explain.py computes delta → new compound card + enriched explanation text → API response`.

**H. Engine / Deterministic Logic Impact.** **This is the second and last phase in the whole roadmap that touches `engine.rank()`'s core orchestration** (Phase 2 touched the scoring formula; this touches the function signature and adds a post-scoring detection pass). Both remain fully deterministic — compound-condition rules are a fixed registry, delta explanations are pure string formatting against passed-in values. P0/F-02 remain completely untouched and still execute first/unconditionally, exactly as before; compound cards are explicitly barred from ever outranking a P0 warning (enforced the same way `resolve_ties()` already handles priority tiers).

**I. API Contract Impact.** Additive — new possible `card_id` values (`compound_*`); existing `ExplainResponse.text` may now contain an additional delta sentence — backward compatible for any consumer treating it as opaque display text.

**J. Database Impact.** None new — reuses `signal_cache`, already populated by Phase 5 (or by fixture-mode writes, if the caching layer is exercised in fixture mode too — worth deciding explicitly in this phase: recommend yes, so this feature is demoable even without live credentials).

**K. External Dependency Impact.** None new.

**L. Testing Strategy.**
1. Unit: each `COMPOUND_CONDITIONS` entry triggers correctly on its exact threshold boundary and not just below it.
2. Unit: a compound card's priority is never lower than its strongest constituent's.
3. Integration: `rank()` called with `prior_snapshot=None` (cold start) behaves identically to today — critical regression guard, since this is a signature change.
4. Integration: `rank()` called with a prior snapshot showing a meaningful AQI rise produces the expected delta clause.
5. Regression: full existing suite must pass with `prior_snapshot` defaulted, unchanged.

**M. Definition of Done.** At least 2 named compound conditions demoable end-to-end; a repeat visit (or a scripted before/after in the demo) shows a delta-aware explanation; `rank()`'s existing callers (all current tests) work unmodified thanks to the default `None`.

**N. Risks and Failure Modes.** The main risk is exactly the one named in the roadmap brief itself — gimmick risk. Mitigate by keeping the compound registry small (2-4 conditions, each with a clear, real safety/relevance rationale, not "add more for the demo"), and by treating delta-explanation as *enhancement* to existing cards, never a new decision-making input to score/priority (it only affects explanation text, never ranking) — this keeps the safety-critical scoring path completely unaffected by a feature whose only job is narrative richness.

**O. Estimated Complexity: Medium-High.** Genuinely new capability (not just more of the existing pattern like Phases 3-4), touches the engine's public function signature for the first time since Milestone 1, requires care to preserve backward compatibility and determinism guarantees.

---

### Phase 7 — Interaction Telemetry Foundation

**A. Phase Objective.** Build the data-collection foundation Stage 2 of the ML brief requires — nothing ML-related is trained yet, only logged.

**B. Why This Phase Comes Here.** Deliberately after full persona/novelty completion (Phases 3-6): logging interaction data against a narrow, incomplete card surface would bias any future training signal toward whatever happened to be built first — per the ML section's own reasoning in the prior forensic review.

**C. Current-State Problems Being Solved.** Zero interaction/telemetry infrastructure exists — no table, no endpoint.

**D. Scope.**
- IN SCOPE: new `interaction_events` table; `POST /api/telemetry` endpoint; explicit separation of implicit (impression, click, dismiss, time-on-card) vs. explicit (any future thumbs-up/down) signal types.
- OUT OF SCOPE: any model training, any use of this data to influence ranking (that's Phase 8, and only after real volume accumulates).

**E. Detailed Implementation Tasks.**
1. Design `interaction_events` schema: `event_id`, `device_id`, `context_snapshot_id` (already generated per `/homepage` call, reuse it), `card_id`, `persona`, `event_type` (`impression`/`click`/`dismiss`/`explicit_feedback`), `score_components_json` (cheap to log, already computed), `created_at`.
2. Implement `POST /api/telemetry` accepting a batch of events per session (reduce request volume vs. one-call-per-event).
3. Frontend coordination note (not this phase's code, but its dependency): the frontend must actually call this endpoint on card impression/click/dismiss — flag explicitly as a cross-team dependency, not assume it happens automatically once the endpoint exists.

**F. Exact Repository Impact.**
- Create: `backend/routers/telemetry.py`, `backend/tests/test_telemetry_contract.py`.
- Modify: `backend/db.py` (new table DDL, idempotent `CREATE TABLE IF NOT EXISTS` per the existing pattern), `backend/main.py` (mount new router).

**G. Data Flow.** `Frontend card impression/click/dismiss → POST /api/telemetry (batched) → interaction_events table` — a new, separate flow that does not touch the `/homepage` request path at all, preserving its latency characteristics.

**H. Engine / Deterministic Logic Impact.** None — the engine remains completely unaware this data exists. This is a deliberate, load-bearing architectural choice: telemetry collection must never create a feedback loop into `engine/` until Phase 8 explicitly and carefully introduces one.

**I. API Contract Impact.** One new endpoint, additive, no changes to existing ones.

**J. Database Impact.** New table `interaction_events` (device_id + context_snapshot_id + card_id indexed for later query patterns); no impact on `preferences`/`signal_cache`. Data retention: flag explicitly for later decision (e.g., a rolling window) rather than assuming indefinite retention — not urgent for a hackathon timeframe but worth stating as a known open question.

**K. External Dependency Impact.** None.

**L. Testing Strategy.** 1. Unit: event-type enum validation. 2. Integration: a batch write round-trips correctly. 3. Contract: malformed event batch returns 422, not a partial silent write. 4. Failure-mode: telemetry endpoint failure must never affect `/homepage`'s own success (fully decoupled). 5. Regression: n/a (new subsystem).

**M. Definition of Done.** Telemetry endpoint live and tested; schema documented; explicitly zero coupling to `engine/` verified by code review (no import of telemetry anywhere under `engine/`).

**N. Risks and Failure Modes.** Risk of the frontend never actually being wired to call this endpoint, leaving the table empty regardless of backend correctness — flag this as a cross-team checkpoint, not a backend-only Definition of Done item.

**O. Estimated Complexity: Low-Medium.** Standard CRUD-shaped addition, low architectural risk, clearly decoupled from the safety-critical path.

---

### Phase 8 — ML Baseline & Hybrid Personalization

**A. Phase Objective.** Once real interaction volume exists (post-hackathon realistically, per the honest timeline), train a baseline model and introduce it at the one correct seam identified in the forensic review: `persona_weight`.

**B. Why This Phase Comes Here.** Cannot happen before Phase 7 produces real data — this is a hard dependency, not a sequencing preference. Explicitly gated on data volume, not on calendar time.

**C. Current-State Problems Being Solved.** N/A — this phase doesn't fix an audited gap, it's the deliberate, honest evolution path the ML brief asked for, scoped correctly against what the codebase's architecture already supports.

**D. Scope.**
- IN SCOPE: offline dataset construction from `interaction_events`; a baseline model (XGBoost/LightGBM, per the prior review's agreement with the original brief) predicting click/engagement probability per `(card_id, persona, environment_state)`; a hybrid inference path where the model's output *augments or replaces* `PERSONA_WEIGHT` lookups specifically, with a documented, tested fallback to the static table whenever prediction confidence is low or the model is unavailable.
- OUT OF SCOPE: touching `urgency_multiplier` (must stay environment-only/rule-based per the R5 safety property) or `P0`/`F-02` (must stay hard rules, non-negotiable, explicitly restated from the original constraints and the prior review).

**E. Detailed Implementation Tasks.** (High-level, since this phase is explicitly gated on data that doesn't exist yet — full task-level detail belongs in a dedicated Phase 8 planning pass once Phase 7's data volume is known.)
1. Build the offline dataset extraction from `interaction_events` + the corresponding historical `ContextFrame` state (requires deciding whether to snapshot full `ContextFrame`s at telemetry time or reconstruct approximately — flag as an open design question for Phase 8's own detailed plan, not resolved here).
2. Train a baseline model; evaluate offline against a held-out split.
3. Add a `model_version` table/field for tracking which model produced which historical ranking (needed for the evaluation/monitoring requirement in Deliverable 6 of the prior review).
4. Implement the hybrid inference call inside `engine/scoring.py`'s `score()` — **behind a feature flag**, defaulting OFF, with the static `PERSONA_WEIGHT` table remaining the deterministic fallback whenever the flag is off, the model is unavailable, or confidence is below a documented threshold.

**F. Exact Repository Impact.** New `ml/` module (training scripts, offline evaluation, entirely outside `engine/`'s runtime boundary), modification to `engine/scoring.py`'s `score()` to optionally call a model-inference function (behind the flag), new `model_version` table, new `backend/settings.py` flag.

**G. Data Flow.** `interaction_events (Phase 7) → offline training (ml/) → trained model artifact → (if flag ON) score() calls model inference for persona_weight → falls back to PERSONA_WEIGHT table if unavailable/low-confidence`.

**H. Engine / Deterministic Logic Impact.** The most safety-sensitive change in the entire roadmap, by design gated behind a flag and an explicit fallback. `urgency_multiplier`, P0, and F-02 are explicitly, permanently out of scope for ML — restated here as a hard constraint carried through from the original project constitution, the prior forensic review, and this roadmap's own brief.

**I. API Contract Impact.** None required — this is an internal scoring change; `RankedCard.score_components` could optionally gain a `"weight_source": "table"|"model"` field for transparency, which would itself be a small, deliberate explainability improvement worth including.

**J. Database Impact.** New `model_version` table.

**K. External Dependency Impact.** None beyond standard ML tooling (scikit-learn/XGBoost, already anticipated in the original brief).

**L. Testing Strategy.** 1. Unit: fallback path (model unavailable) produces byte-identical output to the pre-Phase-8 deterministic engine — this is the single most important test in this phase. 2. Integration: flag ON with a mock model produces a different-but-valid ranking. 3. Contract: response shape unaffected. 4. Failure-mode: model file missing/corrupted → falls back cleanly, logs a warning, never crashes `/homepage`. 5. Regression: full existing suite must pass with the flag OFF (default), unchanged.

**M. Definition of Done.** A trained baseline model exists with a documented offline evaluation; the hybrid path is flag-gated and defaults OFF; the fallback-to-deterministic path is proven byte-identical to pre-Phase-8 behavior; P0/F-02/`urgency_multiplier` are demonstrably untouched by any part of this phase (code review checklist item).

**N. Risks and Failure Modes.** The single named risk from the original brief: "ML for marketing" — mitigate by keeping this phase's Definition of Done centered on the fallback guarantee, not on the model's own accuracy, which is secondary to the architectural honesty this whole project has been built around.

**O. Estimated Complexity: Very High.** Genuinely new discipline (ML engineering) layered onto an existing system with hard safety constraints it must not violate — the complexity is as much about proving *nothing broke* as about the model itself.

---

### Phase 9 — Evaluation, Observability & Demo Hardening

**A. Phase Objective.** A dedicated final pass across the *whole*, now-complete system for judging-day resilience — not scattered piecemeal across earlier phases.

**B. Why This Phase Comes Here.** Deliberately last: hardening a system that's still gaining major features (Phases 0-8) would mean redoing hardening work repeatedly; doing it once, at the end, against the true final surface area, is strictly more efficient.

**C. Current-State Problems Being Solved.** No dedicated observability pass exists yet; demo-day rehearsal (pre-warm `/health`, offline fallback snapshot, intentional feed-kill demo) was specified in earlier planning docs but only partially exercised.

**D. Scope.**
- IN SCOPE: structured logging across all 8 personas' card generation; a demo-day runbook (pre-warm sequence, offline fallback snapshot per demo location, rehearsed feed-kill moment); a final full run of the golden-set spike (from Phase 1) against the now-8-persona system, to confirm nothing regressed across the additions.
- OUT OF SCOPE: any new feature.

**E. Detailed Implementation Tasks.** 1. Structured logging (persona, card_id, priority, source) on every `/homepage` call, at a volume appropriate for post-demo debugging, not a full observability stack. 2. Demo runbook document, rehearsed at least once against the actual deployed environment. 3. Re-run the Phase 1 spike methodology against the full 8-persona system as a final regression/quality gate.

**F. Exact Repository Impact.** Modify: `backend/main.py`/routers (structured logging), `eval/run_spike.py` (re-run against expanded golden set, extend the golden set itself to cover all 8 personas). Create: `docs/DEMO_RUNBOOK.md`.

**G-K.** No architecture, contract, DB, or new external-dependency changes — this phase is verification and operational readiness, not construction.

**L. Testing Strategy.** The golden-set spike re-run *is* this phase's primary test; additionally, a full manual demo rehearsal against the deployed environment, including the intentional feed-kill moment.

**M. Definition of Done.** Demo runbook exists and has been rehearsed at least once end-to-end; the expanded golden-set spike shows the 8-persona system still beats both baselines; structured logs are sufficient to debug a live demo failure after the fact.

**N. Risks and Failure Modes.** The risk this phase exists to close: a late-discovered regression across 8 personas' worth of accumulated changes, found for the first time on judging day instead of here.

**O. Estimated Complexity: Medium.** Mostly verification and documentation work, not new engineering, but requires genuine discipline to actually execute the rehearsal rather than assume readiness.

---

## 6. PHASE DEPENDENCY MAP

```
Phase 0 (Foundation Stabilization)
   ↓
Phase 1 (Engine Validation) ──── PIVOT gate: if failed, escalate before proceeding
   ↓
Phase 2 (Context Model Completion — health_flags, saved_locations)
   ↓
Phase 3 (Persona Tier 1: Traveler, Commuter) ───┐
   ↓                                              │ both feed into
Phase 4 (Persona Tier 2: Agriculture,            │
         Beachgoer, Event Planner)  ─────────────┘
   ↓
Phase 5 (Live Data Integration & Resilience)
   ↓
Phase 6 (Cross-Signal Reasoning / Novelty Layer)
   ↓
Phase 7 (Interaction Telemetry) ──── hard data-volume gate, not calendar-time gate
   ↓
Phase 8 (ML Baseline & Hybrid)
   ↓
Phase 9 (Evaluation & Demo Hardening)
```

**Strictly sequential (cannot reorder):** 0→1 (validation needs stable contracts to trust), 1→2 (weight changes should land before new formula terms are added on top), 2→3/4 (saved_locations/health_flags must exist before personas that use them), 7→8 (hard data dependency), 6/7/8→9 (final hardening needs the final feature surface).

**Could theoretically run in limited parallel, with care:** Phase 3 and Phase 4 do not depend on each other and *could* be built by two workstreams simultaneously once Phase 2 is done — flagged as the one genuine parallelization opportunity in this roadmap, appropriate for a 6-person team split into two pairs. Phase 6's compound-condition registry work could begin in parallel with the tail end of Phase 4 (it only needs *some* multi-persona card surface, not literally all 8), though the "why now" delta-explanation half of Phase 6 does need Phase 5's cache-population to be meaningful and should wait.

---

## 7. 8-PERSONA COMPLETION MATRIX

| Persona | Current Status | Audited Gaps | Required Data Signals | Required Engine/Context Changes | Required Cards | External Dependencies | Phase | Deterministic vs. ML | Test Coverage Needed |
|---|---|---|---|---|---|---|---|---|---|
| Health-conscious | Mostly implemented | health_flags inert | AQI, UV, humidity, pollen | health_flag_multiplier | aqi_health, uv_sun_exposure, pollen_illustrative | CPCB, OWM | 2, 5 | Deterministic | New health-flag modifier tests |
| Outdoor fitness | Partially implemented | Heat alert not distinct; "best hours" generic | temp, wind, AQI, UV, sunrise/sunset | none beyond existing | activity_window, sunrise_sunset | Astral (done), OWM | (already mostly done) | Deterministic | Existing suite sufficient |
| Beachgoers & surfers | Not implemented | Entirely absent | sea conditions, tide, wave height, water temp | new ContextFrame fields | sea_conditions | INCOIS (unconfirmed) | 4 | Deterministic | New persona test suite |
| Travelers | Schema-only | saved_locations inert, no logic | saved_locations, warnings per destination | ContextFrame.saved_locations | destination_alert, packing_suggestion | Reuses existing WarningAdapter | 2, 3 | Deterministic | New persona test suite |
| Parents & families | Fully implemented | School-specificity generic | commute window, precip, warnings | none | rain_commute, severe_warning | Fixture/IMD | (already done) | Deterministic | Existing suite sufficient |
| Agriculture & gardeners | Not implemented | Entirely absent | soil moisture, frost, rainfall | new ContextFrame fields | soil_moisture_advisory | Unconfirmed source | 4 | Deterministic | New persona test suite |
| Commuters | Not implemented as distinct persona | Conflated with fitness in naming only | visibility, traffic (deferred), fog/storm typing | ContextFrame.visibility | visibility_commute | Fixture; traffic unresearched | 3 | Deterministic | New persona test suite |
| Event planners | Not implemented | Entirely absent | extended forecast, comfort index | ContextFrame.extended_forecast, derived comfort calc | extended_outlook, comfort_index | Fixture/OWM forecast | 4 | Deterministic | New persona test suite + comfort formula test |

All 8 personas remain **deterministic through Phase 8** — ML, when introduced, augments the `persona_weight` seam for *all* personas equally via the hybrid mechanism, not persona-by-persona.

---

## 8. NOVELTY / INNOVATION STRATEGY

1. **Cross-signal compound-condition reasoning** (Phase 6). *Problem solved:* single-signal cards can't express "this combination is worse than either alone." *Improves over a normal homepage:* generalizes the one existing composite pattern (`activity_window`) into a named, reusable, explainable capability. *Personas:* health, fitness primarily, extensible to others. *New data:* none — reuses existing signals. *Deterministic/ML/hybrid:* fully deterministic, by design. *Complexity:* Medium-High. *MVP or enhancement:* strong differentiator, recommended as MVP-adjacent (Phase 6, not deferred to "someday").

2. **"Why now" delta-aware explanations** (Phase 6). *Problem solved:* every current explanation is a snapshot; none say *why this changed*. *Improves over a normal homepage:* most weather apps don't expose change-over-time reasoning at all. *Personas:* all. *New data:* reuses `signal_cache` (Phase 5). *Deterministic.* *Complexity:* Medium. *MVP or enhancement:* strong differentiator, same phase as above.

3. **Destination-aware travel risk reuse** (Phase 3). *Problem solved:* travelers care about weather somewhere else, not just here. *Improves over a normal homepage:* reuses the existing `severe_warning` mechanism against a second location instead of building something new. *Personas:* traveler. *New data:* none beyond `saved_locations`. *Deterministic.* *Complexity:* Medium. *MVP.*

4. **Computed comfort index** (Phase 4). *Problem solved:* PS explicitly asks for it; most apps either omit it or fetch it from a paid provider. *Improves over a normal homepage:* honestly computed, not fabricated or paid-sourced. *Personas:* event planner, secondarily all. *New data:* none — pure function over existing signals. *Deterministic.* *Complexity:* Low. *MVP.*

5. **Multi-persona household framing** (surfacing, not new engine work — the backend's `_best_persona_for_card` multi-persona support already exists). *Recommendation:* invest in demo/UI framing to make this visible, not new backend work — nearly free, already-built capability.

6. **Hybrid ML-personalized ranking** (Phase 8). *Problem solved:* long-term, table-driven weights don't adapt to real usage patterns. *Improves over a normal homepage:* most competitors either skip real ranking entirely or use an opaque LLM; this stays auditable via the fallback guarantee. *Personas:* all, uniformly. *New data:* interaction telemetry (Phase 7). *Hybrid, explicitly gated.* *Complexity:* Very High. *Enhancement, post-hackathon-realistic, not MVP.*

**Explicitly rejected (per the "no gimmicks" instruction):** an LLM-generated natural-language assistant layered on top of the engine (already rejected in the original novelty analysis — commercially saturated, undermines auditability); a chatbot interface; gamification/streaks; social/sharing features — none of these serve the PS's actual core ask and all were considered and set aside.

---

## 9. ML ROADMAP

1. **Is ML required for the SIH MVP?** No — restated from the prior review, unchanged by anything in this roadmap.
2. **What stays deterministic permanently?** `urgency_multiplier` (all cards), P0 override, F-02 alert-priority-floor, `packing_suggestion`/compound-condition templates (Phase 3/6) — none of these are ever ML candidates, at any future phase.
3. **First useful ML problem:** predicted engagement/usefulness probability per `(card_id, persona, environment_state)`, feeding the `persona_weight` seam only.
4. **Interaction data needed:** impressions, clicks, dismisses, time-on-card (implicit); any future explicit feedback — separated by `event_type`, per Phase 7.
5. **Schema needed:** `interaction_events` (Phase 7), `model_version` (Phase 8).
6. **Cold start under ML:** unchanged — persona + explicit preferences + deterministic rules, exactly as today; the hybrid fallback (Phase 8) degrades to the same static table whenever confidence is low, which is functionally identical to "cold start" for a specific context bucket even after a model exists.
7. **First model family:** XGBoost/LightGBM — lightweight, interpretable-enough, appropriate for tabular engagement prediction, no objection to the original brief's choice.
8. **Where it sits:** inside `engine/scoring.py`'s `score()`, replacing/augmenting the `PERSONA_WEIGHT` lookup only, behind a feature flag.
9. **Deterministic fallback:** the static table, proven byte-identical to pre-ML behavior when the flag is off or the model is unavailable/low-confidence (Phase 8's core Definition of Done).
10. **Evaluation:** the same golden-set spike methodology from Phase 1/9, re-run against the hybrid system, comparing it against both the deterministic engine *and* the original two baselines — not just "does the model have good offline accuracy," but "does the end-to-end ranked homepage actually get better."
11. **What must NOT be attempted before enough data exists:** any of Phase 8 — restated as a hard, non-negotiable gate, not a soft preference.

---

## 10. RISKS / EXTERNAL DEPENDENCIES

| Risk | Phase | Mitigation |
|---|---|---|
| PIVOT verdict from the engine validation spike | 1 | Escalate explicitly before proceeding; do not silently absorb |
| Scoring-formula change (health_flag_multiplier) introduces a subtle regression | 2 | Dedicated small phase, explicit regression test on the R5 environment-only invariant |
| INCOIS/soil-moisture data confirmed unusable | 4 | Explicitly acceptable fallback: simulated/illustrative labeling, same precedent as pollen |
| Credential registration delay (CPCB/aqicn.org/OWM) | 5 | Register at phase *start*, not end |
| `cache/store.py`'s actual current state unknown | 5 | Verify/complete as part of this phase's own scope, don't assume readiness |
| Compound-condition/delta feature feels gimmicky if over-scoped | 6 | Keep registry small (2-4 conditions), explanation-only impact, never a ranking input |
| `rank()` signature change (prior_snapshot param) breaks an existing caller | 6 | Default `None`, explicit regression test against full existing suite |
| Frontend never wired to call the telemetry endpoint | 7 | Explicit cross-team checkpoint, not assumed automatic |
| ML phase attempted before real data volume exists | 8 | Hard data-volume gate, explicitly restated as non-negotiable |
| Demo-day regression across the full 8-persona system | 9 | Dedicated final spike re-run + rehearsed runbook |

---

## 11. RECOMMENDED EXECUTION SEQUENCE

- **Phase 0 — Execute next.** No dependencies; closes the most demo-risky gaps found in the audit.
- **Phase 1 — Execute immediately after 0.** Requires 0's contract stability to trust its own tests; produces the PIVOT/GO gate every later phase implicitly assumes passed.
- **Phase 2 — Execute after 1.** Requires a validated base before adding a new scoring term.
- **Phases 3 & 4 — Execute after 2**, optionally in parallel across two workstreams; 3 before 4 if sequential, since 3 is cheaper and lower-risk.
- **Phase 5 — Execute after 3/4.** Benefits from the widened signal surface; blocked by nothing else.
- **Phase 6 — Execute after 5** (delta-explanation needs cache population); compound-condition work could start slightly earlier in parallel with the tail of Phase 4 if capacity allows.
- **Phase 7 — Execute after 6.** Needs the full feature surface to log against meaningfully.
- **Phase 8 — Execute only once Phase 7 has produced real volume** — this is a data gate, not a calendar gate, and may fall outside the hackathon timeline entirely, which is the honest and correct outcome.
- **Phase 9 — Execute last**, against whatever the true final feature surface turns out to be (which may be end of Phase 6/7 if Phase 8 doesn't fit the timeline — Phase 9 should run regardless of whether Phase 8 happens).

### THE FIRST PHASE WE SHOULD IMPLEMENT

**Phase 0 — Foundation Stabilization & Contract Integrity.**

Exactly why: it is the only phase with zero dependencies, the lowest risk of any phase in this roadmap, the fastest to complete, and it closes the two gaps most likely to visibly embarrass a demo *today*, regardless of how much of the rest of this roadmap ultimately gets built. Every other phase's testing strategy explicitly says "mirroring the existing pattern" — Phase 0 is what makes that pattern trustworthy in the first place. Nothing about wanting to win SIH is served by adding an 8th persona on top of an unverified 3-persona foundation; it's served by making the foundation provably solid first, then building outward from it exactly as this roadmap sequences.
