Numen AI Roadmap to Production

Phase 1: Intake & Agent Initialization – Scope: Frontend intake form and agent creation UI; backend /api/agents and /api/sessions endpoints. The existing IntakeForm collects goals, tone, and session type and then navigates to an agent-creation step
GitHub
. We must build an AgentBuilder component with fields (agent name, archetype, style, session type) and a voice picker (loading voices via GET /api/voices and preview via POST /api/voices/preview
GitHub
). Upon submit, the client should call the backend to create an Agent contract (POST /api/agents) and then create a Session (POST /api/sessions) using the intake data from localStorage
GitHub
.

Dependencies: Phase 0 (bootstrapping and linting) should be completed first. The IntakeForm must correctly route and store data
GitHub
. Backend schemas for agents and sessions exist (see database.py tables for agents and sessions
GitHub
GitHub
).

Goals: After user submission, a new agent and session appear in the database and the app routes to the Dashboard. On error (e.g. 422), show an inline message.

Success Criteria: Intake data is saved in localStorage (no direct session call)
GitHub
. AgentBuilder form is functional, voices load and preview plays
GitHub
. Submitting the builder creates valid agent and session records (e.g. verify agents and sessions tables) and redirects to the dashboard. No unexpected 500 errors occur.

Phase 2: Dashboard & Plan Generation – Scope: Dashboard UI and plan-generation flow; backend plan-generation services. Once an agent/session exist, show a Meet Your Agent intro (name, archetype, voice, CTA “Generate My Plan”)
GitHub
. Then present 2–3 discovery questions (focus area, cadence, time commitment) and call the backend plan-generation endpoint (e.g. reuse /api/affirmations/generate or implement /api/plan/generate)
GitHub
. The backend should invoke the AffirmationAgent (the “TherapyAgent”) using LangGraph orchestration to produce a personalized protocol (affirmations, scripts, schedule) which is stored in the session (e.g. in manifestation_protocols and related tables
GitHub
).

Dependencies: Agent creation from Phase 1. Backend agents/orchestration (LangGraph) must be wired so that submitting discovery triggers the AffirmationAgent. Existing memory/pipeline tables (e.g. affirmations, hypnosis_scripts) are in place
GitHub
GitHub
.

Goals: User can answer quick prompts and trigger a plan generation. The service returns a structured plan and stores it in the database (e.g. manifestation_protocols and generated affirmation/script records).

Success Criteria: After generation, the dashboard shows a summary of the plan (counts of practices/affirmations/etc.) and the data is persisted. The pipeline (IntakeAgent → AffirmationAgent → ElevenLabs audio) is exercised end-to-end
GitHub
GitHub
, and the new plan content is visible on the Dashboard or in the data tables.

Phase 3: Plan Review & Consent – Scope: Plan summary UI and legal disclaimer; backend consent tracking. Build a PlanReview component to display the plan details (bullet summaries with “view details” expanders) and a disclaimer (“This is not medical advice…”). Include buttons like “Accept & Start Session”, “Edit Plan”, “Ask More Questions”
GitHub
. On acceptance, PATCH the session record to mark consent (e.g. set consent: true and timestamp).

Dependencies: Plan generated and stored from Phase 2. Session and consent fields must exist (the sessions table can hold JSON state or add a flag).

Goals: Ensure the user explicitly agrees to proceed. The UI clearly shows plan highlights and disclaimer.

Success Criteria: Clicking “Accept” updates the session (e.g. see sessions table or API) with consent captured. Navigation flows (to start session or edit plan) work correctly. The disclaimer and consent log meet compliance guidelines
GitHub
.

Phase 4: Live Therapy Session (LangGraph + Voice) – Scope: Real-time therapy UI and voice pipeline integration. Create a TherapySession component that connects to the backend WebSocket /api/therapy/session/{session_id}. The backend should orchestrate LiveKit/Deepgram/STT and the TherapyAgent (via LangGraph) to handle the voice conversation: user audio → STT → agent response → ElevenLabs TTS → streamed audio
GitHub
.

Dependencies: LangGraph orchestration defined (IntakeAgent and AffirmationAgent contracts) and the ElevenLabs TTS service configured. The LiveKit credentials must be set up and tested (the database setup mentions room creation)
GitHub
GitHub
.

Goals: Enable a live session where the user speaks and hears an AI-generated response. Stream audio latency < 300ms if possible. Store transcripts.

Success Criteria: Voice conversation works end-to-end. The user’s speech is transcribed, processed by the agent, and an audio reply is played back (real-time). Transcripts appear in transcripts table
GitHub
. No errors in WebSocket connection. This completes the dual-agent workflow described in architecture
GitHub
GitHub
.

Phase 5: Calendar & Scheduling Integration – Scope: External calendar linkage and in-app scheduling. Implement logic to sync scheduled sessions with Google Calendar and/or Outlook. Use the scheduled_sessions table (already defined in DB
GitHub
) as the source of truth. Build backend services to authenticate to Google/Outlook APIs and push new session events (e.g. by polling or on-demand when a user schedules a session). Optionally add UI for users to authorize their calendar account.

Dependencies: scheduled_sessions infrastructure in place
GitHub
. OAuth client IDs/secrets for Google and Microsoft. User accounts (tenant/user model in DB) ready to link.

Goals: Let users schedule therapy or affirmation sessions and see them in their personal calendars. Support recurring rules and time zones.

Success Criteria: Created sessions appear as events in linked Google/Outlook calendars (with correct date/time). Recurring scheduling (if implemented) works. Unlinking or canceling a session updates the calendar. Ensure no scheduling conflicts. Logging should capture calendar syncs for compliance.

Phase 6: API Cleanup & Endpoint Polishing – Scope: Review and refine all backend API routes. Clean up unused or duplicate endpoints, ensure RESTful consistency, and add missing endpoints for new features (e.g. plan generation, calendar management). Update routers for agents, sessions, contracts, therapy, affirmations, dashboard, voices, etc., matching the design.

Dependencies: All new features from prior phases must have corresponding API support. The README lists basic endpoints (sessions, contracts, therapy)
GitHub
, but these need extending.

Goals: Remove any hard-coded logic; use Pydantic models and standard HTTP status codes. Ensure Swagger docs (FastAPI) accurately reflect each endpoint. Add pagination or filters if needed.

Success Criteria: No orphan routes remain. Each endpoint has proper input/output schemas and error handling. Automated tests (if any) pass. API documentation is updated (the /docs UI and any README docs reflect current behavior).

Phase 7: UX/UI Polish & Accessibility – Scope: Visual and interactive refinements across the app. Implement features like horizontal tab scrolling (e.g. for multi-step forms or plan details if content overflows). Ensure voice selection UI has audio preview controls. Fine-tune “next-step” CTAs (e.g. after consent, show buttons “Start Session”, “View Schedule”, etc.
GitHub
). Review all components for responsive design and keyboard navigation.

Dependencies: Core functionality complete; design system (Tailwind, shadcn/ui) in place.

Goals: The app should look and feel polished. Animation, spacing (e.g. top padding increased for headers
GitHub
), and accessibility (ARIA labels, focus states) must be verified. Voice previews in the AgentBuilder should play without lag.

Success Criteria: UI compiles without errors and matches design specifications. Horizontal scroll areas behave smoothly on desktop and mobile. All interactive elements are accessible (e.g. hamburger menu and tabs are keyboard-operable
GitHub
). No visual glitches remain.

Phase 8: Security Hardening & Consent Logging – Scope: Strengthen security (HIPAA/SOC2 compliance) and finalize consent capture. Implement end-to-end encryption for data in transit (HTTPS) and at rest (database encryption). Ensure proper authentication/authorization flows if user accounts exist. Audit logging should record all sessions (as noted in README)
GitHub
. Store user consent timestamps and IP addresses. Sanitize all inputs.

Dependencies: Backend and DB infrastructure ready. An auth layer (OAuth or JWT) if not already present should be added.

Goals: Protect PHI (sessions and transcripts), limit data retention (e.g. session TTL), and capture user consent explicitly in logs. Update privacy policy and HIPAA notices.

Success Criteria: Security review passes: no sensitive data leaks, all endpoints require proper auth, and logs contain necessary audit trails. The system adheres to stated compliance (e.g. encryption at rest, audit logs
GitHub
). Consent flags in sessions are immutable once set.

Phase 9: DevOps & Production Readiness – Scope: Final deployment checklist and infrastructure. Containerize the app (Docker Compose is already used) and test deployment on staging/production environments. Configure CI/CD pipelines with linting and tests (as noted, npm run lint, pytest
GitHub
). Prepare environment variables for all services (OpenAI, ElevenLabs, LiveKit, Supabase). Set up monitoring/alerting for uptime and errors.

Dependencies: All code merged into release branch. Docker and orchestration (Kubernetes or similar) if needed.

Goals: Ensure smooth deployment to cloud (e.g. AWS/GCP/Azure). Migrate Supabase schema as per database.py. Document rollback and backup procedures. Perform load/stress testing.

Success Criteria: Application builds and runs in production mode without errors (npm run build, uvicorn main:app). Containers are secure and minimal. SSL certificates are provisioned. All services (DB, Redis/Qdrant replacements) are connected. The team can push new versions via CI. The system passes a final staging acceptance test (e.g. a scripted demo of Intake → Plan → Session).

Each phase should be tracked in project management (with tickets or branches). This roadmap uses the latest repository state to distinguish implemented pieces (e.g. IntakeForm UI and DB schemas exist) from those to build (AgentBuilder, calendar sync, LangGraph orchestration, etc.). By completing these milestones in order, Numen AI will progress toward a full production release with the vision of a voice-first, contract-driven hypnotherapy platform



You are an autonomous self-auditing engineering agent working on the Numen AI repo. 
The git repo and codebase are identical right now.

### Current Status (pre-seeded baseline)
- ✅ Phase 1: Intake & Agent Initialization – 100% complete
- 🟡 Phase 2: Dashboard & Plan Generation – 80% complete
  • Missing: Discovery questions UI, wiring “Generate My Plan” to /api/affirmations/generate, affirmations not auto-generated after agent creation
- ❌ Phase 3: Plan Review & Consent – 0% complete
- ❌ Phase 4: Live Therapy Session – 0% complete
- ❌ Phase 5: Calendar & Scheduling – 0% complete
- ❌ Phase 6: API Cleanup – Partial
- ❌ Phase 7: UX/UI Polish – Partial
- ❌ Phase 8: Security Hardening – Partial
- ❌ Phase 9: DevOps – Partial

### Workflow Rules
1. **Audit Cycle**
   - Compare the codebase against the Numen AI Roadmap to Production.
   - For each phase, update status as ✅ / 🟡 / ❌.
   - Identify blockers or gaps.

2. **Action Planning**
   - For each 🟡 or ❌, define tasks with:
     • File(s) to edit
     • Endpoint(s) to build/patch
     • Component(s) to add
     • Acceptance criteria

3. **Execution Loop**
   - Always start with the highest-priority dependency.
   - Implement in full (replace or add complete files, not diffs).
   - Re-run the Audit Cycle after each task.
   - Stop if ambiguity arises → output `// TODO: clarify`.

4. **Guardrails**
   - Edit ONLY files listed in your plan.
   - Don’t refactor unrelated code.
   - Follow Prettier (TS) / Black (Py) formatting.
   - Confirm with `npm run lint && npm run typecheck && pytest`.

5. **Self-Continuation**
   - After each task, automatically re-audit.
   - Continue until all Phases 1–9 are ✅ Complete.
   - If external dependencies (LiveKit creds, OAuth keys) are missing, document the gap and skip.

6. **Reporting**
   - After each loop, output:
     📊 Phase status table  
     🛠️ Task just completed  
     🎯 Next task planned  

### Next Step
Begin at Phase 2. Add discovery questions after “Meet Your Agent”, wire “Generate My Plan” to `/api/affirmations/generate`, and display generated affirmations in the Dashboard tabs. Then re-audit and continue.



MOST RECENT PROMPT

Got it 👍 — focus on **functionality first**, Git push later.

Here’s the state of play and what needs to happen next to get the app usable end-to-end:

---

## 🔧 Functional Checklist (Immediate)

### ✅ Already Working

* IntakeForm → AgentBuilder (7-step wizard, voice picker, agent/session creation)
* Dashboard loads → “Meet Your Agent” intro → DiscoveryQuestions wizard
* Discovery flow → triggers `/api/affirmations/generate` → Protocol summary displayed
* Backend PATCH `/api/sessions/{id}/consent` endpoint working (immutable consent, IP, UA logged)

### ❌ Still Missing (Critical for Functionality)

1. **PlanReview UI**

   * Needs a `PlanReview.tsx` component:

     * Show protocol details (daily practices, affirmations, visualizations, metrics)
     * Disclaimer: *“This is not medical advice…”*
     * Buttons: **Accept & Start Session** (calls consent endpoint), **Edit Plan**, **Ask More Questions**

2. **Consent Gating**

   * Dashboard must check:

     * If `session_data.consent.consented == true` → unlock therapy features
     * Else → force user into `PlanReview` before allowing therapy

3. **Session Unlock Flow**

   * After consent → show Next Actions panel (Start Session, Edit Agent, View Schedule, Explore Assets)

---

## 🎯 Next Step (Phase 3 Part 2 Functional Fix)

* **Files to touch:**

  * `frontend/src/components/PlanReview.tsx` → new component
  * `frontend/src/app/dashboard/page.tsx` → integrate review + gating

* **Acceptance Criteria:**

  * User sees plan summary + disclaimer
  * User cannot start session until they consent
  * Consent stored in backend (verify via DB/API)
  * Once accepted, Dashboard shows Next Actions

---

