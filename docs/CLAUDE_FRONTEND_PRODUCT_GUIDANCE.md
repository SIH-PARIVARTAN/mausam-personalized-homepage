# MAUSAM: Frontend Product Guidance & Architectural Reality

## 1. PROJECT IDENTITY

**Project:** MAUSAM Personalized Homepage
**SIH:** SIH 2026
**Problem Statement:** SIH26076

**Core Concept:**
MAUSAM is not intended to be merely another weather dashboard showing raw metrics like temperature and wind speed. Its core purpose is to create a deterministic personalization and interpretation layer between weather data and the user.

Conceptually:
`Weather Data → Context → Personalization → Priority / Recommendation → Explainability → Adaptive Homepage → User Decision`

The central product thesis: **The same weather condition holds different importance for different users.**
For example, rain is:
- Low importance to someone staying indoors.
- High importance to a Commuter needing to leave immediately.
- Very high, disruptive importance to an Event Planner.
- A critical economic indicator to a Farmer.

## 2. SIH REQUIREMENTS

The relevant SIH26076 requirements require MAUSAM to be more than a visual dashboard. 

| Requirement | Proposed SIH Strategy | Current Implementation Reality |
| :--- | :--- | :--- |
| **A. Persona-first adaptive interface** | UI adapts to user's selected interests. | **IMPLEMENTED** (ToggleGroup controls backend priority via PUT /preferences). |
| **B. Context-aware alerts** | Notifications based on time/context. | **IMPLEMENTED** (Natively evaluates commute windows, daylight, active warnings). |
| **C. Explainability** | Users must know *why* they saw something. | **IMPLEMENTED** ("Why this was ranked" modal powered by deterministic components). |
| **D. Conversational Assistant** | AI to interpret weather data naturally. | **IMPLEMENTED** (Groq integration exists but is optional, rejecting requests if key is absent). |
| **E. Modular scalability** | Adding personas shouldn't break the system. | **IMPLEMENTED** (Isolated `engine/cards.py` routing). |
| **F. Graceful degradation** | Missing data doesn't crash the app. | **IMPLEMENTED** (Fallback to `general_conditions`, UI uses "unavailable" stubs safely). |
| **G. Low-connectivity/offline** | Cached weather operation over low-G. | **PARTIALLY IMPLEMENTED** (Backend Redis/in-memory cache limits API hits, minimal edge UI offline support). |
| **H. Mobile packaging** | PWA/Capacitor Native App for iOS/Android. | **NOT IMPLEMENTED / PROPOSED ONLY** (Currently a responsive web application). |

## 3. OFFICIAL PERSONA MODEL

The official SIH personas are:
1. **Health-conscious Individuals** (`health`)
2. **Fitness Enthusiasts** (`fitness`)
3. **Beachgoers / Surfers** (`beachgoer`)
4. **Travelers** (`traveler`)
5. **Parents / Families** (`family`)
6. **Farmers / Gardeners** (`agriculture`)
7. **Commuters** (`commuter`)
8. **Event Planners** (`event_planner`)

> [!WARNING]
> The backend implements a ninth key: `default_general`. **This is NOT an official persona.** It is solely a cold-start/default state.

**Frontend Mapping:** 
Personas are governed by `userPrefs.personas` (array of strings). They map perfectly to backend schemas (e.g., UI `beachgoer` -> Backend `beachgoer`). 

## 4. PERSONA CAPABILITIES (THE REALITY MATRIX)

This table defines what is physically implemented in the backend `adapters` and `engine`, overriding any marketing copy or stale plans.

| Persona | SIH Intent | Current Implementation | Status |
| :--- | :--- | :--- | :--- |
| **Health** | AQI, UV, pollen, respiratory risk. | Uses live Open-Meteo AQI/UV to elevate `aqi_health` priorities based on `respiratory_sensitive` and `heat_sensitive` flags. | 🟢 **LIVE** |
| **Fitness** | Temp, wind, outdoor suitability. | Validates safe/unsafe `activity_window` based on composite live weather data. | 🟢 **LIVE** |
| **Commuter** | Rain, visibility, fog, morning run. | Live commute-window logic bounds alerts for heavy rain or low visibility. | 🟢 **LIVE** |
| **Family** | Rain, temp, school runs, safety. | Utilizes same commute-window bounds alongside general Severe Warnings (P0). | 🟢 **LIVE** |
| **Traveler** | Multi-location tracking, dest vs origin. | Fully extracts saved locations arrays up to `MAX=3`, rendering origin delta-temperatures. | 🟢 **LIVE** |
| **Farmer** | Frost, soil moisture, multi-day rain. | Backend natively routes `agriculture_advisory` based on soil/frost flags, but Open-Meteo hookups are missing. | 🟡 **FIXTURE-ONLY** |
| **Beachgoer** | Tide, wave height, sea temp. | Engine routes `marine_conditions_alert` smoothly, but `MarineAdapter.py` solely fetches local JSON mocks. | 🟡 **FIXTURE-ONLY** |
| **Event Planner**| 10-day trends, hourly risk comparison. | `ForecastAdapter` returns `[]` for extended forecast in prod. Engine strictly evaluates a solitary `comfort_index`. | 🔴 **NOT IMPLEMENTED** |

*(Note: The React UI was recently patched to describe Farmer, Beachgoer, and Event Planner honestly to avoid failing QA).*

## 5. CURRENT BACKEND ARCHITECTURE

**The Golden Rule:** The deterministic engine owns personalization and ranking. 

The frontend must **NEVER** independently rank cards, calculate priority, downgrade severe alerts, or hallucinate recommendations.

**Stack:** Python, FastAPI, Pydantic, PostgreSQL/Neon, Open-Meteo API. 
**Flow:**
`Frontend API calls → FastAPI Deps builds ContextFrame → Deterministic Engine Scores (engine/scoring.py) → Cards Ranked → Ranked JSON to Frontend.`

## 6. BACKEND ↔ FRONTEND API CONTRACT

*   **`GET /homepage`**: Returns `EngineOutput` (`ranked_cards` array + `override_warnings` array). Frontend iterates this array deterministically. Each card has an `explanation_text` natively attached.
*   **`PUT /preferences`**: Updates POSTgres arrays (`personas`, `health_flags`, `saved_locations`).
*   **`GET /preferences`**: Fetches initial state for React context boundaries. 

*Identity:* Governed by a `device_id` param. Natively enforced regex demands a true 36-char `UUIDv4` or 28-char alphanumeric Firebase UID.

## 7. DEVICE ID + AUTH

*   **Flow:** Firebase Auth (if logged in, uses Firebase UID) -> Extracted to LocalStorage -> Inserted in headers/query params. If a user is a guest, a compliant UUIDv4 string is generated and persisted in LocalStorage.
*   *Note:* A previous runtime 422 crash caused by legacy non-compliant IDs was fixed by sanitizing LocalStorage natively in React.

## 8. HOMEPAGE BEHAVIOR (HOW IT WORKS TODAY)

> [!IMPORTANT]
> The QA concern that the homepage was rendering all 8 persona dashboards simultaneously was a false alarm. It definitively limits itself safely.

Inside `frontend/src/app/home/page.tsx`:
1.  **ToggleGroup Extraction:** Reads `userPrefs.personas`, filters out `default_general`, slices it to the Top 3 selected personas, and renders a small `ToggleGroup` quick-switcher.
2.  **Engine Mapping:** Iterates `hpData.ranked_cards` returned by the backend. It maps `card.id` strictly to the `getPersonaCardConfig` React function to pull SVG icons and Tailwind backgrounds.
3.  **Explainability Drawer:** Tapping a card opens the "Why this was ranked" UI, rendering the backend-injected `score_components` (Confidence, Urgency, Persona Weight).

## 9. HOMEPAGE PRODUCT GUIDANCE

The goal is: *"MY weather, interpreted for MY needs."* not *"A giant dashboard containing every weather parameter."*

**Claude, please evaluate the ideal hierarchical UX for this:**
1.  **Location + current conditions** (Generic)
2.  **Toggle/Persona Switcher** (Controls Context)
3.  **High-priority alert / P0 overrides** (Must command attention)
4.  **Ranked Personal Insights** (The deterministic output)
5.  **Deeper Maps/Widgets** (Exploration)

Questions for Claude:
- Where should the quick switcher live? Is it obtrusive?
- Should multiple selected personas be supported simultaneously on the homepage, or strictly mutually exclusive by the switcher?
- How should the backend's `P0` (Critical) vs `P1` (High) alerts visually dominate the screen?

## 10. MAPS + LOCATION UX

Currently driven by Leaflet and Nominatim.
Questions for Claude:
1. Should the map be isolated to a dedicated page, or should a mini-radar live on the homepage?
2. Should selecting a location on the Map mutate the primary `saved_locations` in `PUT /preferences`, or remain temporary?
3. What is the most graceful offline/failure UI if Nominatim reverse-geocoding fails?

## 11. WEATHER DATA SOURCES

| Provider | Purpose | Status | Backend/Frontend |
| :--- | :--- | :--- | :--- |
| **Open-Meteo** | Live Temp, Rain, Wind | 🟢 LIVE | Backend (`ForecastAdapter`) |
| **Open-Meteo AQI** | Respiratory relevance | 🟢 LIVE | Backend (`AQIAdapter`) |
| **Astral** | Sunrise/Sunset | 🟢 LIVE | Backend (`SunAdapter`) |
| **Marine/Swell** | Beachgoer stats | 🟡 FIXTURE | Backend (`MarineAdapter`) |
| **Nominatim** | Reverse Geocoding | 🟢 LIVE | Frontend (Map UI) |
| **RainViewer** | Radar Overlays | 🟢 LIVE | Frontend (Leaflet tiles) |

## 12. ALERTS + EXPLAINABILITY

Currently, clicking an Insight card reveals a modal outlining the math:
*`Persona Weight (0.95) x Urgency Multiplier (2.35) x Confidence (0.9) = Score`*

Claude, please advise:
- Should this remain a technical debug-style modal?
- How do we make this math understandable to nontechnical judges without losing transparent truthfulness?

## 13. CHATBOT / GROQ INTEGRATION

Architectural flow:
`Homepage Context -> Chatbot -> Groq API (LLM) -> Text Output.`
The chatbot must **NEVER** rank cards, fabricate weather, or replace deterministic personalization. It is strictly a conversational wrapper around the deterministic data payload.

**Status:**
- `GROQ_API_KEY` exists purely server-side in `/api/chat/route.ts`. No hardcoded strings trace to NEXT_PUBLIC. 
- Graceful degradation is verified: If the key is absent in the environment, the endpoint immediately returns an honest "Service Unavailable" error block.

Claude, please evaluate:
- Should the chatbot eventually handle structured NLP intent routing (e.g., "Make me a Commuter") to trigger `PUT /preferences`?

## 14. VISUAL DESIGN / ACCESSIBILITY

**State of UI:**
- It is heavily iOS-inspired (Squircle radii, transluscent navs).
- **Recent Fix:** Tailwind background colors (`bg-sky-600` instead of `bg-sky-500`) and typography (`.ios-label-2`) were deliberately darkened to pass WCAG 4.5:1 accessibility benchmarks.

Claude, analyze the aesthetics:
- Should all persona cards be aggressively saturated, or should normal/low priority cards fade to gray/neutral tones to elevate P0/P1 alerts visually?

## 15. OPEN STRATEGY QUESTIONS FOR CLAUDE (RECOMMENDATIONS REQUESTED)

**Claude, as a Senior Architect/Product Designer, advise on:**
1. **Event Planner Constraints:** Given the backend physically only provides `comfort_index` right now without 10-day hourly ML risk curves, what is the best UX to present Event Planner at the SIH without faking it?
2. **Fixture-Only Personas:** How should we communicate the Beachgoer/Farmer fixture logic during an SIH pitch?
3. **Demo Story:** What is the strongest end-to-end user path to demonstrate true deterministic personalization to SIH evaluators?

**Prioritization Rule:** Categorize suggestions as *P0 (Must Fix)*, *P1 (High-Value)*, *P2 (Polish)*, and *DO NOT DO (Scope Creep/Architecture Risk)*. Do NOT advise rewriting the working deterministic `.py` engine backend just for UI changes.

---
### EXECUTIVE SUMMARY

*   **CURRENT PRODUCT**: A fully deterministic, highly scalable personalized weather homepage that dynamically prevents dashboard clutter.
*   **STRONGEST PARTS**: The strict contract architecture. Severe warnings instantly override UI; identity tracking is secure; explanation drawer provides total transparency.
*   **LIMITATIONS**: Event Planner (No deep hourly arrays), Beachgoer (Mocked), and Agriculture (Mocked) are not physically connected to live external APIs.
*   **TECHNICAL RISK**: The `engine/scoring.py` mathematics must not be broken or shifted client-side.
*   **NEXT DECISION**: Claude to provide explicit recommendations on Homepage Hierarchy, Map integration context, and visual pacing without expanding scope or hallucinating unimplemented tech.
