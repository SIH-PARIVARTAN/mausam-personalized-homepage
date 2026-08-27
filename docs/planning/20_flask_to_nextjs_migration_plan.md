# 20. Flask to Next.js Migration Plan

**Topic:** Translating the external frontend UI (Flask/HTML/CSS/JS) into the main repository's Next.js scaffold.
**Status:** PLAN
**Date:** 2026-08-27

## 1. Migration Philosophy
We are performing a "Strangler Fig" style extraction of the UI elements. We will conceptually slice the Jinja templates into reusable React components. We will **NOT** copy any Python backend logic.

## 2. Target Next.js Route Structure

| Route Path | Original Source | Purpose | Backend Dependency |
|------------|-----------------|---------|--------------------|
| `/` | N/A | Redirects to `/login` if no session; else `/home` | N/A |
| `/login` | `login.html` | Authentication | Firebase Auth |
| `/signup` | `signup.html` | Registration | Firebase Auth |
| `/onboarding/preferences` | `preferences.html` | Persona selection (first-time) | Firebase Auth state |
| `/onboarding/location` | `location.html` | Geolocation request | Firebase Auth state |
| `/home` | `index.html` | Main Personalized Dashboard | GET `/homepage`, GET `/explain`, PUT `/preferences` |

## 3. Translation Strategy: HTML / CSS
1. **Global CSS:** The external `style.css` will be imported directly into `app/globals.css`. The CSS classes and structure appear modular enough that Tailwind is not strictly required if we preserve their external CSS definitions for the MVP.
2. **Templates to JSX:**
   - Extract the `header.topbar` into a `<Header />` Server/Client component.
   - Extract the `.weather-card.main-weather` into a `<WeatherHero />` component.
   - Extract `.recommendations` (which the JS previously mutated manually) into a `<CardList />` component that `.map()`s over the `cards[]` array provided by FastAPI `GET /homepage`.
3. **JS to React State:**
   - `app.js` manually updated DOM IDs (e.g. `document.getElementById('rec-title-1')`). This logic is stripped entirely.
   - Next.js will use React State or `TanStack Query` to fetch `GET /homepage` and just re-render dynamically.

## 4. Feature Enhancements Needed in Migration
- **Warnings Banner:** The main architecture outputs `warnings_override[]`. The UI needs a new component at the top of the dashboard to render this when active.
- **Explainability Modal:** The external UI did not have the transparency feature. We must build a `<BottomSheet />` or `<Modal />` that calls `GET /explain` and shows the exact values that resulted in the rank.
- **Source Badges:** The external UI assumed live Open-Meteo data. We must add UI badging for "Simulated", "Live", or "Unavailable" from the `CardResponse.source`.

## 5. UI/API Integration Contract
**Component: Dashboard Root**
- Call: `GET /homepage?device_id={uid}&lat={lat}&lon={lon}`
- Map `response.cards` strictly in index order. Ignore older manual JS re-ordering logic.

**Component: Preference Editor**
- On submit, fire `PUT /preferences`. Immediately invalidate the TanStack Query cache for `/homepage` to provoke a visible UI rerender/reorder.
