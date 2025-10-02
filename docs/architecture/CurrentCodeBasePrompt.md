# Claude Code Prompt Chain – Critical Path UX (Numen AI)

> Purpose: Implement the polished end‑to‑end user journey **without breaking** the codebase. Every phase is copy‑pasteable for Claude Code in Cursor and includes strict guardrails, file scopes, and acceptance criteria. Adjust paths for your repo layout (`frontend/src/...` or `apps/web/src/...`).

---

## Phase 0 — Branch + Guardrails Bootstrap

**Task:** Create branches and enforce guardrails/lint gates.

**Scope (files):** `package.json`, `frontend/package.json`, root CI config (later), repo only.

**Guardrails:**

* Do **not** modify app logic in this phase.
* Add/confirm scripts: `lint`, `typecheck`, `build` for frontend; `lint:py`, `test` for backend.
* Add a PR checklist template.

**Prompt:**

> Create branches `release/0.2.0-alpha`, `feat/ux-critical-path`, `fix/api-session-contract`. Ensure `npm run lint && npm run typecheck` pass in frontend and `pytest` in backend. If missing, add scripts and minimal config (Prettier/ESLint for TS; Black/Ruff for Py) without changing app logic. Output all changed files.

**Acceptance:**

* Branches created.
* Lint/typecheck/test commands exist and run.

---

## Phase 1 — Intake Form aligns with pipeline (no session POST)

**Task:** Ensure IntakeForm saves data and routes to AgentBuilder only.

**Scope (files):** `IntakeForm.tsx` (find under `frontend/src/components/` or `apps/web/src/components/`).

**Guardrails:**

* Do **not** call `/api/sessions` here.
* Store `{ goals[], tone, session_type }` in `localStorage.intakeData`.
* Route to `/create-agent` with a demo `userId` if needed.

**Prompt:**

> Edit only `IntakeForm.tsx`. On submit: validate fields, `localStorage.setItem('intakeData', JSON.stringify({goals, tone, session_type}))`, then `router.push('/create-agent')`. Add minimal error UI (inline text) — no new deps. Do not create a session here.

**Acceptance:**

* Submitting intake navigates to `/create-agent` without 500s.
* `localStorage.intakeData` contains the form JSON.

---

## Phase 2 — AgentBuilder simplified + ElevenLabs voice selection

**Task:** Minimal fields + voice picker with preview.

**Scope (files):** `AgentBuilder.tsx`; optional new UI components in `components/`.

**Guardrails:**

* Single manual text field: **Agent Name**.
* Dropdowns: **Archetype**, **Style**, **Session Type**.
* **Voice Picker**: Fetch voices from backend `GET /api/voices`; preview via `POST /api/voices/preview` returning audio/mpeg.
* No extra sliders/knobs.

**Prompt:**

> Edit only `AgentBuilder.tsx` (+ a small `VoicePicker.tsx` if needed). Build a form with: Name (text), Archetype (dropdown: Stoic, Spiritual Guide, Motivator, Therapist), Style (dropdown: Empathetic, Tough Love, Neutral), Session Type (from intake or dropdown), Voice (list from `/api/voices` with Preview button). Keep layout clean and responsive. No new libraries.

**Acceptance:**

* Voices load and preview plays.
* Form is compact, keyboard‑accessible.

---

## Phase 3 — Create Agent then Create Session (contract‑first)

**Task:** After AgentBuilder submit, call `/api/agents` then `/api/sessions` with proper schema.

**Scope (files):** `AgentBuilder.tsx`, `frontend/src/lib/api.ts` (or equivalent), backend `sessions.py` only if needed to enforce schema.

**Guardrails:**

* **Payload 1 (POST /api/agents):** include contract with identity/traits/config derived from builder; include chosen voice.
* **Payload 2 (POST /api/sessions):**

```json
{
  "user_id": "<uuid | demo-user>",
  "agent_id": "<uuid from agent>",
  "metadata": { "intake_data": { "goals": [...], "tone": "calm", "session_type": "manifestation" }, "created_by": "agent" }
}
```

* If backend returns 422, show toast and keep user on page.

**Prompt:**

> Update only `AgentBuilder.tsx` and `api.ts`. Implement: (1) POST `/api/agents` with the built contract; on success capture `agent.id`. (2) Read `intakeData` from localStorage; POST `/api/sessions` using the exact schema above. (3) On success, `router.push('/dashboard?agentId=...&sessionId=...&success=true')`. Add minimal loading states and error toasts; do not add libraries.

**Acceptance:**

* Successful flow yields agent + session rows and routes to dashboard.
* No 500s; 422s show inline errors.

---

## Phase 4 — Meet Your Agent (intro/teaser step)

**Task:** After redirect, show a brief agent intro with CTA to generate plan.

**Scope (files):** `dashboard/page.tsx` or a new `MeetYourAgent.tsx`.

**Guardrails:**

* Keep it short; allow expand for details.
* CTA: **“Generate My Plan”**.

**Prompt:**

> Add a `MeetYourAgent` section on the dashboard when `success=true`. Show agent name, archetype, voice chosen, and a 2‑3 bullet capability list. Provide a primary button “Generate My Plan”. Do not start content generation yet.

**Acceptance:**

* Dashboard shows intro when arriving from creation flow.
* Button is keyboard‑accessible.

---

## Phase 5 — Discovery Qs + Plan Generation

**Task:** Ask 2‑3 clarifying questions → generate plan via backend.

**Scope (files):** `dashboard/page.tsx` (or `PlanWizard.tsx`), `api.ts`; backend endpoint if missing (reuse existing `/api/affirmations/generate` per E2E report).

**Guardrails:**

* Questions: priority focus, cadence (daily/weekly), time per day.
* POST to existing generation endpoint (or create `/api/plan/generate` wrapper) and store protocol in session.

**Prompt:**

> Implement a small discovery step (3 short questions with defaults). On submit, call the existing generation endpoint to create a personalized plan (affirmations/daily practices) and persist it under the session’s `session_data.manifestation_protocol`. Show progress/loading and handle 422 with inline messages.

**Acceptance:**

* Generation returns a structured plan and is stored on the session.
* UI shows a compact summary (counts of practices/affirmations/visualizations).

---

## Phase 6 — Review + Consent

**Task:** Present plan, disclaimer, and capture consent.

**Scope (files):** `PlanReview.tsx` (new), `api.ts` (to update session consent flag).

**Guardrails:**

* Disclaimer: non‑medical guidance.
* Buttons: **Accept & Start**, **Edit**, **Ask More**.

**Prompt:**

> Create `PlanReview.tsx` that shows a concise plan summary (bullets + “View details” expanders), a clear disclaimer (“This is not medical advice…”), and buttons for Accept, Edit, Ask More. On Accept, PATCH the session with `{ consent: true, consent_at: now }`. Do not add dependencies.

**Acceptance:**

* Consent captured and persisted.
* Navigation buttons work.

---

## Phase 7 — Next Actions (Start / Edit / Schedule / Explore)

**Task:** Provide next steps panel.

**Scope (files):** `dashboard/page.tsx` (actions area), routes for `/dashboard/agents`, `/dashboard/affirmations`, `/dashboard/scripts`.

**Guardrails:**

* “Start Session Now”: open session player (text/voice) — can be stub if player pending.
* “View Schedule”: navigate to user schedule.
* “Edit Agent”: return to AgentBuilder with current defaults.
* “Explore Assets”: go to counts list.

**Prompt:**

> Add a “Next Actions” panel with 4 cards: Start Session Now, View Schedule, Edit Agent, Explore Assets. Use Next.js `Link` for navigation (no full reload). Ensure keyboard and screen reader labels.

**Acceptance:**

* Each card routes to the correct page.
* No console errors; Lighthouse interaction ≥ 90.

---

## Phase 8 — Immediate UX polish (from prior list)

**Task:**

1. Tabs row horizontally scrolls independently with snap.
2. Dashboard count cards navigate.
3. Purge all agents except Marcus Aurelius & Deepak Chopra.

**Scope (files):** tabs component (`HorizontalTabs.tsx`), dashboard cards (`DashboardStatCard.tsx`), backend admin route or SQL migration.

**Guardrails:**

* No global CSS changes; only local component styles.
* Admin purge endpoint must use parameterized queries.

**Prompt:**

> (a) Implement a `HorizontalTabs` component with `overflow-x-auto`, `snap-x`, `touch-action: pan-x`, wheel→horizontal behavior; integrate on dashboard. (b) Make Output Asset count cards act as links to their pages using Next `Link`. (c) Add an admin route `/admin/agents/purge` that deletes all agents not named `Marcus - Stoic Wisdom Coach` or `Deepak Chopra`, cascading related interactions safely. Use parameterized queries.

**Acceptance:**

* Tabs drag horizontally and snap; page doesn’t scroll while dragging.
* Clicking a count card navigates to the corresponding page.
* Only the two target agents remain; no orphaned rows; counts update.

---

## Phase 9 — Error Handling, Toasters, Logging

**Task:** Centralize API errors and add helpful UI feedback.

**Scope (files):** `api.ts`, a simple `useToast()` hook or existing UI lib toasts.

**Guardrails:**

* No new libraries; re‑use existing toast if present.
* Map HTTP codes: 4xx → user guidance, 5xx → retry or contact support.

**Prompt:**

> Refactor `api.ts` to a small client with baseURL, JSON helpers, and uniform error handling. Add lightweight toasts for common failures (network, 422 validation). Ensure all Phase 1–7 calls use the client. Do not change endpoint contracts.

**Acceptance:**

* All API calls go through the client.
* Clear, consistent error toasts visible on failures.

---

## Phase 10 — Sanity Tests & Demo Script

**Task:** Validate the entire critical path and script a 2‑minute demo.

**Scope (files):** none (tests/manual steps). Optional Cypress skeleton.

**Guardrails:**

* Do not add dependencies; provide a manual test checklist.

**Prompt:**

> Produce a short checklist that verifies: Intake → AgentBuilder (voices preview) → Agent created → Session created → Dashboard intro → Discovery → Plan generated → Consent captured → Next Actions routes. Include the exact payloads observed in network tab and confirm session JSON includes `session_data.manifestation_protocol`.

**Acceptance:**

* Checklist executed with screenshots/recording.
* No blockers; all navigation works.

---

### Notes & Conventions

* If file paths differ, first **locate by filename**, then constrain edits to the found path.
* Prefer **422 with validation detail** over 500s; log `RAW BODY` on backend during development.
* Keep copy concise. Long explanations should be behind an expandable disclosure.
* ElevenLabs endpoints assumed present (`GET /api/voices`, `POST /api/voices/preview`). If missing, propose minimal backend stubs using existing service wrappers.

> Run phases in order. Each phase should result in a small PR with screenshots. Stop on ambiguity and emit `// TODO: clarify` rather than guessing.
