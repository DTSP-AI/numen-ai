📜 Claude Code Prompt
You are coding in a Next.js + TailwindCSS project styled in a Kurzgesagt-like modern vector aesthetic.  
Extend the existing `main` landing page (currently featuring HypnoAgent personalization UI) with the following new sections under the CTA:

---

## 🔹 Section 1: About (Mission Statement)
- Full-width section with **gradient teal → purple background**.  
- Left-aligned headline: `About Numen AI` in bold white sans-serif.  
- Sub-head text (max-width: 2/3):  
  > *Our mission is to unlock the Divine Spark of Becoming. We blend the Law of Attraction, Positive Mindset Training, and Quantum Shifting with modern AI therapy. Your Agent listens, learns, and personalizes affirmations, mantras, guided meditations, and hypnotherapy sessions tailored to your unique goals.*  
- Add two floating **vector-style PNG assets** (orb + headphones man) positioned with `absolute` and low opacity.  

---

## 🔹 Section 2: How It Works (Split Grid)
- Two-column responsive grid.  
- Left side: illustration (use PNG asset of "woman at vision board").  
- Right side: bullets with icons:  
  - ✨ *Personalized Affirmations & Mantras*  
  - 🧘 *Guided Meditation & Visualization*  
  - 🌌 *Self-Guided Hypnosis aligned with your goals*  
  - 🤖 *Adaptive AI that refines content every session*  
- CTA button at bottom-right: `Start My Journey` (gradient violet → pink, rounded-xl).  

---

## 🔹 Section 3: Benefits
- 3 feature cards with subtle drop shadow, floating style.  
- Each card includes a minimal vector icon + short description:  
  - *Affirmation*: “Anchor positive beliefs that rewire your subconscious.”  
  - *Mantra*: “Repeat focused patterns that align with abundance.”  
  - *Hypnotherapy*: “Relax deeply and unlock change through suggestion.”  

---

## 🔹 Section 4: Responsible Use & Compliance
- Background: light neutral (gray-50).  
- Small text block, subdued font size (`text-xs text-gray-500`):  
  > *Disclaimer: Numen AI supports personal growth through affirmations and hypnotherapy. It is not a substitute for licensed medical or psychiatric care. All sessions are confidential, user data is SOC 2 and HIPAA compliant.*  

---

## 🔹 Section 5: Final CTA
- Full-width, centered headline:  
  > *Your Divine Spark Awaits.*  
- Subheadline:  
  > *Begin your personalized journey now.*  
- Large CTA button: `Begin Session` (purple gradient with hover glow).  
- Floating vector PNG background (the glowing orb waves asset).  

---

### 🔧 Requirements
- Use **Tailwind utility classes** consistently.  
- Follow **Kurzgesagt-inspired color palette**:  
  - Teal `#00D4C6`  
  - Purple `#7C3AED`  
  - Orange highlight `#FF9F1C`  
- All sections must be **responsive** with `flex` / `grid` layouts.  
- Keep CTA buttons **large, rounded-xl, gradient, with hover glow**.  
- Reuse the same typography scale (`text-3xl font-bold`, etc.).  

Generate the full **React/Next.js JSX code** for the new sections and insert them under the existing personaliz