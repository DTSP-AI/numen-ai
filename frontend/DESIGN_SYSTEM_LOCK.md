# Design System Lock File
## ⚠️ DO NOT MODIFY THESE SPECIFICATIONS WITHOUT EXPLICIT USER APPROVAL

This file documents the approved design specifications for the application. Any changes to these values require explicit user consent.

---

## **AgentBuilder Component**

### Step Flow Configuration
- **Total Steps**: 9 steps (formerly 6, expanded to include Voice, Avatar, and refined UX)
- **Step Order**:
  1. Identity & Purpose (Name, Roles, Mission)
  2. Core Attributes (4 primary traits)
  3. Voice Selection (ElevenLabs integration)
  4. Avatar Creation (DALL·E 3 / Upload)
  5. Communication Style (Interaction styles)
  6. Manifestation Focus Areas
  7. Philosophy & Approach
  8. Review & Create
  9. (Reserved for future expansion)

### Progress Indicator
```typescript
// Progress dots configuration
{[1, 2, 3, 4, 5, 6, 7, 8].map((s) => (
  <div className={`w-10 h-10 rounded-full ...`}>
    {s}
  </div>
  {s < 8 && <div className={`h-1 w-6 mx-1 ...`} />}
))}
```
- **Dot Size**: `w-10 h-10` (40px × 40px)
- **Spacing Between Dots**: `w-6 mx-1` (24px width, 4px margins = 32px total)
- **Connector Line**: `h-1` (4px height)

### Layout & Spacing
- **Container Max Width**: `max-w-4xl` (56rem / 896px)
- **Card Padding**: `p-8` on desktop, `p-6` on mobile
- **Vertical Spacing**: `space-y-6` between sections
- **Button Spacing**: `space-x-4` between navigation buttons

---

## **globals.css Specifications**

### Glass Morphism Effects
```css
.glass-card {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.glass-card-dark {
  background: rgba(11, 30, 61, 0.4);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
}
```

### ⚠️ CRITICAL: Framer Motion Animation Support
**DO NOT ADD THE FOLLOWING CSS**:
```css
/* ❌ NEVER ADD THIS - It breaks Framer Motion animations */
[style*="opacity:0"] {
  opacity: 1 !important;
}
```

**Reason**: This CSS override forces all elements with `opacity: 0` to be visible, which breaks:
- Framer Motion's initial animation states
- Page transition effects
- Step-by-step reveal animations
- Component overlap issues

### Gradient Utilities (Locked)
```css
.gradient-kurzgesagt {
  background: linear-gradient(135deg, #00BFA5 0%, #4C63D2 100%);
}

.gradient-kurzgesagt-reverse {
  background: linear-gradient(135deg, #4C63D2 0%, #00BFA5 100%);
}

.gradient-purple-aqua {
  background: linear-gradient(135deg, #7928CA 0%, #00D9C0 100%);
}
```

---

## **Color Palette (Kurzgesagt Theme)**

### Primary Colors
- **Purple**: `#7928CA` / `rgb(121, 40, 202)` / `hsl(271, 64%, 47%)`
- **Aqua**: `#00BFA5` / `rgb(0, 191, 165)` / `hsl(174, 100%, 37%)`
- **Navy**: `#0B1E3D` / `rgb(11, 30, 61)` / `hsl(219, 71%, 14%)`
- **Yellow**: `#FFD93D` / `rgb(255, 217, 61)` / `hsl(45, 100%, 62%)`

### Text Colors
- **Light Mode**: Navy `#0B1E3D`
- **Dark Mode**: White `#FFFFFF`
- **Muted**: `rgba(255, 255, 255, 0.6)` for secondary text

---

## **Typography**

### Font Weights
- **Headings**: `font-bold` (700)
- **Subheadings**: `font-semibold` (600)
- **Body**: `font-normal` (400)

### Text Sizes
- **Page Title**: `text-3xl` (1.875rem / 30px)
- **Section Heading**: `text-lg` (1.125rem / 18px)
- **Body**: `text-base` (1rem / 16px)
- **Small/Meta**: `text-sm` (0.875rem / 14px)
- **Extra Small**: `text-xs` (0.75rem / 12px)

---

## **Component Specifications**

### Multi-Select Role/Style Buttons
```typescript
// Selection limit: 1-3 items
const [selectedRoles, setSelectedRoles] = useState<string[]>([])

// Button states
- Selected: "bg-white text-kurzgesagt-purple"
- Unselected: "bg-white/10 text-white hover:bg-white/20"
- Disabled (limit reached): "bg-white/5 text-white/40 cursor-not-allowed"

// Layout
className="grid grid-cols-2 gap-3"
className="px-4 py-3 rounded-lg font-semibold"
```

### Voice Selection Cards
```typescript
// Card layout
className="p-4 rounded-lg transition-all text-left"

// Selected state
bg-white text-kurzgesagt-purple border-2 border-white

// Unselected state
bg-white/10 text-white border-2 border-white/20 hover:bg-white/20

// Preview button
className="bg-kurzgesagt-yellow text-kurzgesagt-navy hover:bg-kurzgesagt-yellow/90"
```

### Slider (Trait Adjustments)
```typescript
// Range input styling
className="w-full h-2 bg-white/20 rounded-lg appearance-none cursor-pointer"
style={{
  background: `linear-gradient(to right, #00BFA5 0%, #00BFA5 ${value}%, rgba(255,255,255,0.2) ${value}%, rgba(255,255,255,0.2) 100%)`
}}

// Value display
className="text-white/80 text-sm font-mono"
```

---

## **Animation Specifications (Framer Motion)**

### Step Transitions
```typescript
initial={{ opacity: 0, x: 20 }}
animate={{ opacity: 1, x: 0 }}
exit={{ opacity: 0, x: -20 }}
transition={{ duration: 0.3 }}
```

### DO NOT:
- Add global CSS that overrides `opacity`
- Use `!important` on animation-related properties
- Modify Framer Motion's inline styles
- Add `visibility: visible !important` hacks

---

## **Button Specifications**

### Primary Action Button
```typescript
className="bg-kurzgesagt-purple text-white px-6 py-3 rounded-lg font-semibold hover:bg-kurzgesagt-purple/90 transition-all"
```

### Secondary Action Button
```typescript
className="bg-white/10 text-white px-6 py-3 rounded-lg font-semibold hover:bg-white/20 transition-all border border-white/20"
```

### Accent Button (Yellow)
```typescript
className="bg-kurzgesagt-yellow text-kurzgesagt-navy px-6 py-3 rounded-lg font-semibold hover:bg-kurzgesagt-yellow/90 transition-all"
```

---

## **Port Configuration**

### Development Servers
- **Backend**: `http://localhost:8000` (Fixed)
- **Frontend**: `http://localhost:3002` or `http://localhost:3003` (User preference)
  - Command: `npm run dev -- -p 3002`

---

## **Validation Rules**

### Step 1: Identity & Purpose
- Agent name: Required (non-empty string)
- Roles: Minimum 1, Maximum 3 selections
- Mission: Required (non-empty string)

### Step 3: Voice Selection
- Must select exactly 1 voice before proceeding

### Step 5: Communication Style
- Interaction styles: Minimum 1, Maximum 3 selections

---

## **File References**

### Core Design Files
- `frontend/src/components/AgentBuilder.tsx` - Main component (lines 1-1000+)
- `frontend/src/app/globals.css` - Global styles (lines 100-125)
- `tailwind.config.ts` - Theme configuration

### Related Backend
- `backend/routers/voices.py` - Voice API endpoint
- `backend/routers/avatar.py` - Avatar generation/upload
- `backend/services/elevenlabs_service.py` - Voice synthesis

---

## **Change Protocol**

### Before Making Design Changes:
1. ✅ Check this lock file for existing specifications
2. ✅ Ask user for explicit approval if modifying locked values
3. ✅ Test changes don't break Framer Motion animations
4. ✅ Verify responsive behavior (mobile/desktop)
5. ✅ Update this lock file with new approved specs

### Red Flags (Require User Approval):
- Changing step count or flow order
- Modifying progress indicator dimensions
- Adding global CSS overrides for `opacity`, `visibility`, or `display`
- Changing color palette values
- Altering glassmorphism effects
- Modifying button size/padding standards

---

## **Testing Checklist**

### Visual Regression Prevention
- [ ] No component overlapping between steps
- [ ] Smooth Framer Motion transitions (no flashing)
- [ ] Progress indicator dots properly sized and spaced
- [ ] Glass cards have correct backdrop blur
- [ ] Multi-select buttons enforce 1-3 limit
- [ ] Voice preview plays without blocking UI

---

**Last Updated**: 2025-10-03
**Status**: ✅ LOCKED - Design approved by user
**Version**: 1.0.0
