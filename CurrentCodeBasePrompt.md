Got it. What you want is a **single meta-prompt** you can drop into Claude that explains:

* What Numen AI is.
* Why the pipeline is structured this way.
* How the **Agent Creation Standard JSON contract** applies to Intake → Affirmation → Output → Dashboard.
* The expectations for Claude: turn this into working scaffolding.

Here’s that **Claude Implementation Prompt**:

---

# 🧩 Claude Prompt — Numen AI Agent Pipeline (Contract-First)

**Context for Claude:**
We are building **Numen AI**, an application that combines manifestation, affirmations, hypnosis scripting, and audio synthesis into a persistent, personalized pipeline.
The system must be designed using our **Agent Creation Standard**: every agent is defined by a JSON contract that specifies its identity, configuration, workflow, and metadata.

This prompt explains **why** and **how** we are structuring Numen AI so you can scaffold and implement it.

---

## 🎯 Purpose

Numen AI is not just an affirmation app.
It is a **memory-aware, agent-driven manifestation OS**.

The pipeline must:

* Intake raw discovery data from the user.
* Use that intake to generate a **custom Affirmation Agent**.
* Have the Affirmation Agent generate affirmations, mantras, hypnosis scripts.
* Pipe those outputs into **ElevenLabs SDK** for audio.
* Persist all outputs in a **Dashboard Agent** where users can view, edit, and replay.
* Run on scheduled cycles (morning/evening, weekly, etc.).

Everything must adhere to our **Contract-First JSON Standard** so the agents are portable, versioned, and auditable.

---

## 🔁 Pipeline Flow

1. **User → Intake Agent**

   * Role: **Prompt Engineer**.
   * Gathers raw discovery data (goals, limiting beliefs, outcomes, schedule).
   * Stores this in a **static dev-only JSON object**.
   * Converts it into a **JSON contract** that defines a new Affirmation Agent.
   * Non-negotiable: this agent must be skilled at transforming vague user input into an effective, psychologically-grounded system prompt.

2. **Intake Agent → Affirmation Agent**

   * Role: **Guide + Voice**.
   * Created dynamically by the Intake Agent’s JSON contract.
   * Must generate affirmations, mantras, hypnosis scripts, and reinforcement routines.
   * Rooted in **Law of Attraction, Quantum Theory metaphors, CBT/Positive Psychology, and hypnotherapy pacing**.
   * Includes configuration for **ElevenLabs Voice SDK**.
   * Produces text + audio + schedules.

3. **Affirmation Agent → Output Layer**

   * Outputs are passed through ElevenLabs → `.mp3/.wav` audio.
   * Audio + text saved in user’s persistent profile.
   * Scheduling logic ensures recurring playback reminders.

4. **Dashboard Agent**

   * Role: **Archivist + Editor**.
   * Manages persistence: stores all agents, their content, past threads.
   * Displays affirmations, hypnosis scripts, and audio.
   * Provides editing + rescheduling capabilities.
   * All user-facing access flows through here.

---

## 📦 JSON Contract Examples

* **Intake Agent** (prompt engineer)
* **Affirmation Agent** (voice + hypnosis scripts)
* **Dashboard Agent** (storage + editing)

Each contract includes:

* `identity` (short + full description, character role, mission, style)
* `configuration` (LLM, tokens, temperature, memory, voice/tool settings)
* `workflow` (trigger, schedule, iterations)
* `metadata` (tenant, tags, status)

---

## 🧠 Why This Matters

* **Scalability:** Every agent is a portable contract. Easy to version, replace, or extend.
* **Psychological Effectiveness:** Affirmation Agents are prompt-engineered to embody proven principles of manifestation + psychology.
* **Persistence:** Dashboard layer ensures no outputs are lost; everything is editable and replayable.
* **Separation of Concerns:** Intake Agent engineers prompts. Affirmation Agent generates rituals. Dashboard manages persistence.

---

## ⚡ Claude’s Task

1. **Scaffold the pipeline:** Implement the Intake → Affirmation → Output → Dashboard pipeline using JSON contracts.
2. **Write sample code:** Python/TypeScript scaffolds for each agent, ElevenLabs SDK wrapper, scheduler module, and dashboard UI.
3. **Demonstrate flow:** Show how a user’s intake → generates JSON contract → spawns Affirmation Agent → outputs audio + text → persists in dashboard.
4. **Keep to standard:** All agents must strictly follow our **Agent Creation Standard JSON schema**.

---

👉 Claude, do not shortcut this.
We want a **production-ready scaffold** that can be plugged into our LangGraph + Next.js architecture.
Your job is to deliver contracts, code stubs, and clear wiring for the pipeline.

---
Run C:\AI_src\AffirmationApplication\CurrentCodeBasePrompt.md as a prompt using our C:\AI_src\AffirmationApplication\AGENT_CREATION_STANDARD.md as a reference