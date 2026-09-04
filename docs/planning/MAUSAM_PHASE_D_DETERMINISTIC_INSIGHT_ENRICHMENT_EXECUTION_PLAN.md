# MAUSAM PHASE D EXECUTION PLAN
## DETERMINISTIC INSIGHT ENRICHMENT

## 1. Verified Current Backend Starting State
- Phase C is 100% complete and functionally closed according to `MAUSAM_BACKEND_IMPLEMENTATION_STATUS.md`.
- `pytest engine/tests/` passes 154/154.
- `eval/run_spike.py` passes 30/30 (100%).
- P0/local severe safety overrides are preserved perfectly via `severe_warning`.
- The architecture is absolutely deterministic and fixture-backed.
- Traveler/Commuter behavior is currently destination-aware (checking destination warnings), decidedly NOT route-aware.

## 2. What the Old Phase D Roadmap Got Right
- Phase D correctly recognized the need for **Insight Enrichment** (synthesizing information into hyper-relevant action). Displaying disconnected cards (e.g. Temperature card separated from AQI card) does not fully achieve SIH 26076 "smart decision support."

## 3. What is Outdated / Already Implemented / Should be Removed
- **Tie-Breaker Complexity:** `engine/conflict.py`'s 5-tier tuple sorting resolves ties deterministically. There is ZERO evidence a rewrite is needed. Replacing it introduces regression risks natively.
- **LLM/Chatbot:** explicitly deferred out of Phase D.
- **Live HTTP Providers:** explicitly deferred out of Phase D natively.

## 4. Final Reconciled Phase D Scope
- **Deterministic Compound Insights:** Synthesizing isolated Context variables (e.g. Temp + AQI) into specific, highly relevant hybrid cards.
- **Controlled Redundancy Suppression:** Suppressing lower-fidelity baseline cards exclusively when a higher-order compound organically replaces them natively. 
- **Traveler Comparative Insights:** Expanding text logic within `explain.py` for destinations.

## 5. Explicit SIH 26076 Requirement / Value Added
- **Compound Insights:** Fulfills "actionable weather insights." A user with health/fitness personas gets a single clear limitation alert (Heat + Smog) instead of two disparate generic facts.
- **Redundancy Suppression:** Achieves "reduced information clutter through relevance."
- **Traveler Comparisons:** Achieves "destination-specific traveler information" and "personalized homepage," directly explaining the delta natively. 

## 6. Final Compound Insight Specifications
We define two mathematically constrained compounds logically:

1. **`compound_heat_aqi_danger` (Heat + AQI)**
   - *Inputs:* `cf.temp_c`, `cf.aqi`.
   - *Requirement:* Both signals must not be `unavailable`. Trigger: `temp_c.value >= 38` AND `aqi.value >= 150`.
   - *Persona Relevance:* Heavily scaled for `Health` and `Fitness`.
   - *Explanation Purpose:* "Combining high temperatures (X) and dangerous air (Y) makes outdoor exposure uniquely hazardous."

2. **`compound_driving_hazard` (Rain + Visibility)**
   - *Inputs:* `cf.precip_prob_pct`, `cf.visibility_km`.
   - *Requirement:* Both signals must not be `unavailable`. Trigger: `precip_prob_pct.value >= 60` AND `visibility_km.value <= 1.0`.
   - *Persona Relevance:* Heavily scaled for `Commuter` and `Family`.
   - *Explanation Purpose:* "High rain probability (X) coupled with dense fog (Y) dictates extreme caution on roads today natively."

## 7. Redundancy Suppression Rules
To achieve decluttering, `engine.py` will inspect the `card_id` output directly. 
- `compound_heat_aqi_danger` --> suppresses `aqi_health` and `general_conditions` if both qualify. 
- `compound_driving_hazard` --> suppresses `visibility_commute` and `rain_commute` if both qualify. 
- **EXPLICIT GUARANTEE:** The suppression matrix executes only against known lower-fidelity siblings natively. `severe_warning` (P0) is never mapped to the suppression list and inherently survives cleanly.

## 8. Final Traveler/Commuter Comparative Insight Rules
*Current Architecture Check:* `DestinationContext` only contains `lat`, `lon`, `warnings`, and `temp_c`. It does *not* contain humidity, visibility, or UV natively.
- **Strict Scope:** Comparative insights in Phase D will ONLY compare `cf.temp_c.value` against `cf.destinations[0].temp_c.value` natively.
- If `cf.temp_c.value` or `cf.destinations[0].temp_c.value` are unavailable, the comparative Delta generator gracefully degrades and returns the generic base explanation template cleanly. No route logic, no map logic natively.

## 9. Tie-Breaker / Conflict Logic Decision
The 5-tiered rule inside `engine/conflict.py` remains perfectly pristine. No modifications will be executed natively.

## 10. Exact Data-Flow Architecture
Fixtures -> `ContextFrame` -> New `engine/compound.py` evaluates logical AND bounds -> `engine/cards.py` scales urgency natively -> `engine.py` resolves conflict ranks natively -> `engine.py` executes strict `Redundancy Matrix` dropping superseded IDs cleanly -> `engine/explain.py` applies comparative text differences natively.

## 11. Exact Files Expected to Change
- `engine/compound.py` (New)
- `engine/cards.py`
- `engine/scoring.py`
- `engine/engine.py`
- `engine/explain.py`
- `engine/tests/test_compound_logic.py` (New)
- `eval/golden_set.json` (New scenarios)

## 12. Regression-Safe Implementation Sequence
1. Implement `engine/compound.py` (Standalone function proofs). 
2. Insert Cards/Scoring Multipliers into `cards.py` and `scoring.py`.
3. Build the strict suppression matrix directly inside `engine.py` `rank()` loop natively, guaranteeing P0 isolation.
4. Modify `explain.py` templates to accept destination delta evaluation cleanly. 
5. Construct explicit new Unit Tests guaranteeing `severe_warning` survives alongside compound triggers natively. 

## 13. Required Tests and Acceptance Gates
- Assert suppression matrices drop isolated sibling cards.
- Assert P0 warnings exist alongside identical suppression matrices explicitly. 
- Maintain 154/154 existing coverage without side effects natively.

## 14. Golden Evaluation Expansion Target
Add ~4 golden set scenarios specifically profiling `compound_driving_hazard`, `compound_heat_aqi_danger`, and Traveler origin/destination inversions explicitly pushing the evaluation set logically from 30 scenarios to natively ~34 scenarios.

## 15. Explicit Deferred Scope 
- Live Networking HTTP fetching.
- LLM Generative formatting overlays.
- ETA or Traffic analysis.
- Adding unmapped properties (e.g. Humidity) into `DestinationContext` until actively mapped inside Adapters cleanly.

## 16. Risks and Dependencies
- **Risk:** Traveler metrics comparing differing units maliciously natively.
- **Decision:** Strict fallback type-checks bounding scalar equations natively inside `explain.py` generating deterministic absolute values.

## 17. Recommended First Implementation Action
Create strictly isolated `engine/compound.py` boolean trigger methods validating they calculate correctly directly against `ContextFrame` fixture inputs natively before expanding the registry lists. 

## 18. Phase D Implementation Check
NO Phase D execution, codebase modeling, or structural integrations were formed natively. The branch remains mathematically locked at Phase C unconditionally.
