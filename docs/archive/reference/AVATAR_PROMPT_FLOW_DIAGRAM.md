# Avatar Prompt Data Flow - Complete Trace

**Date:** 2025-10-07

---

## End-to-End Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER INPUT                               │
│  "Dr. Manhattan - glowing blue skin, bald, intense eyes"        │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FRONTEND (AgentBuilder.tsx)                   │
├─────────────────────────────────────────────────────────────────┤
│  Line 753: Textarea component                                   │
│    value={avatarPrompt}                                         │
│    onChange={(e) => setAvatarPrompt(e.target.value)}           │
│                                                                  │
│  State: avatarPrompt = "Dr. Manhattan - glowing blue..."        │
└────────────────────────────┬────────────────────────────────────┘
                             │ User clicks "Generate Avatar"
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              generateAvatar() Function (Line 180)                │
├─────────────────────────────────────────────────────────────────┤
│  1. Validate: if (!avatarPrompt.trim()) → alert()              │
│  2. Set loading: setIsGeneratingAvatar(true)                   │
│  3. Build request payload:                                      │
│     {                                                            │
│       prompt: avatarPrompt,    ← USER INPUT UNCHANGED          │
│       size: "1024x1024",                                        │
│       quality: "auto",                                          │
│       background: "opaque"                                      │
│     }                                                            │
│  4. POST to: http://localhost:8000/api/avatar/generate         │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP POST with JSON body
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│            BACKEND (backend/routers/avatar.py)                   │
├─────────────────────────────────────────────────────────────────┤
│  Line 47: Function signature                                    │
│    async def generate_avatar(                                   │
│      request: AvatarGenerateRequest,  ← Pydantic validation    │
│      ...                                                         │
│    )                                                             │
│                                                                  │
│  Line 61: Log incoming request                                  │
│    logger.info(f"Avatar requested: {request.prompt}")          │
│                                                                  │
│  request.prompt = "Dr. Manhattan - glowing blue..."            │
│  request.size = "1024x1024"                                     │
│  request.quality = "auto"                                       │
│  request.background = "opaque"                                  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                  PROMPT ENHANCEMENT (Line 74)                    │
├─────────────────────────────────────────────────────────────────┤
│  enhanced_prompt = f"Headshot portrait: {request.prompt}"      │
│                                                                  │
│  Result:                                                         │
│    "Headshot portrait: Dr. Manhattan - glowing blue skin,      │
│     bald, intense eyes"                                         │
│                                                                  │
│  ✅ Only 2 words added: "Headshot portrait:"                   │
│  ✅ User's creative input 100% preserved                        │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              OPENAI API CALL (Lines 78-92)                       │
├─────────────────────────────────────────────────────────────────┤
│  POST https://api.openai.com/v1/images/generations             │
│                                                                  │
│  Headers:                                                        │
│    Authorization: Bearer {OPENAI_API_KEY}                       │
│    Content-Type: application/json                               │
│                                                                  │
│  JSON Payload:                                                   │
│  {                                                               │
│    "model": "gpt-image-1",                                      │
│    "prompt": "Headshot portrait: Dr. Manhattan - glowing       │
│               blue skin, bald, intense eyes",                   │
│    "size": "1024x1024",                                         │
│    "quality": "auto",          ← Lets model decide style       │
│    "background": "opaque",                                      │
│    "n": 1                                                        │
│  }                                                               │
└────────────────────────────┬────────────────────────────────────┘
                             │ OpenAI processes request
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                   GPT-IMAGE-1 PROCESSING                         │
├─────────────────────────────────────────────────────────────────┤
│  1. Parse prompt: "Headshot portrait: Dr. Manhattan..."        │
│  2. Understand constraints:                                     │
│     - Format: Headshot (not full body)                         │
│     - Orientation: Portrait (vertical)                          │
│  3. Interpret creative elements:                                │
│     - "Dr. Manhattan" → Comic character reference              │
│     - "glowing blue skin" → Supernatural effect                │
│     - "bald" → No hair                                          │
│     - "intense eyes" → Emotional expression                    │
│  4. Generate image matching ALL user specifications            │
│  5. Return temporary URL (valid 60 minutes)                    │
└────────────────────────────┬────────────────────────────────────┘
                             │ Returns JSON response
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              BACKEND IMAGE DOWNLOAD (Lines 102-115)              │
├─────────────────────────────────────────────────────────────────┤
│  Line 103: Extract URL from response                            │
│    image_url = data["data"][0]["url"]                          │
│                                                                  │
│  Line 107: Download image bytes                                 │
│    image_response = await client.get(image_url)                │
│    image_bytes = image_response.content                        │
│                                                                  │
│  Why? OpenAI's URL expires after 60 minutes                    │
│  We need permanent storage                                      │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│          SUPABASE STORAGE UPLOAD (Lines 122-133)                 │
├─────────────────────────────────────────────────────────────────┤
│  if supabase_storage.available:                                │
│    avatar_url = await supabase_storage.upload_avatar(          │
│      file_bytes=image_bytes,                                   │
│      filename=unique_filename,                                 │
│      tenant_id=tenant_id,                                      │
│      user_id=user_id,                                          │
│      content_type="image/png"                                  │
│    )                                                             │
│                                                                  │
│  Result URL:                                                     │
│    https://{project}.supabase.co/storage/v1/object/public/    │
│    avatars/{tenant_id}/{user_id}/{uuid}.png                   │
│                                                                  │
│  ✅ Permanent storage with tenant isolation                    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                RESPONSE TO FRONTEND (Line 136)                   │
├─────────────────────────────────────────────────────────────────┤
│  return AvatarResponse(                                         │
│    avatar_url=avatar_url,                                      │
│    prompt_used=enhanced_prompt                                 │
│  )                                                               │
│                                                                  │
│  JSON Response:                                                  │
│  {                                                               │
│    "avatar_url": "https://...supabase.co/.../uuid.png",       │
│    "prompt_used": "Headshot portrait: Dr. Manhattan..."       │
│  }                                                               │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP 200 OK response
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                  FRONTEND RECEIVES RESPONSE                      │
├─────────────────────────────────────────────────────────────────┤
│  Line 199-200: Handle success                                   │
│    if (response.ok) {                                           │
│      const data = await response.json()                        │
│      setAvatarUrl(data.avatar_url)  ← Updates UI              │
│    }                                                             │
│                                                                  │
│  Line 210: Clear loading state                                  │
│    setIsGeneratingAvatar(false)                                │
│                                                                  │
│  Result: Avatar displays in UI immediately                      │
└─────────────────────────────────────────────────────────────────┘
```

---

## Key Checkpoints

### ✅ Checkpoint 1: User Input Preservation
**Location:** `frontend/src/components/AgentBuilder.tsx:192`
```typescript
prompt: avatarPrompt,  // ← Sent exactly as user typed it
```

### ✅ Checkpoint 2: Backend Receives Intact
**Location:** `backend/routers/avatar.py:61`
```python
logger.info(f"Avatar requested: {request.prompt}")
# Logs: "Dr. Manhattan - glowing blue skin, bald, intense eyes"
```

### ✅ Checkpoint 3: Minimal Enhancement Only
**Location:** `backend/routers/avatar.py:74`
```python
enhanced_prompt = f"Headshot portrait: {request.prompt}"
# Result: "Headshot portrait: Dr. Manhattan - glowing blue skin, bald, intense eyes"
# Added: 2 words
# Changed: 0 words
```

### ✅ Checkpoint 4: GPT-Image-1 Receives Full Context
**Location:** `backend/routers/avatar.py:86`
```python
json={
    "prompt": enhanced_prompt,  # ← Contains full user creativity
    "quality": "auto",          # ← Doesn't force professional style
    ...
}
```

---

## Potential Issues & Solutions

### Issue 1: "Headshot portrait:" May Still Add Bias
**Symptom:** Even with minimal prompt, results look too similar
**Root Cause:** "portrait" word might imply formal/traditional style
**Solution:** Test if removing "portrait" improves diversity:
```python
enhanced_prompt = f"Headshot: {request.prompt}"
```

### Issue 2: `quality: "auto"` Interpretation
**Symptom:** Model still choosing "polished" look by default
**Root Cause:** "auto" might default to "high quality" = professional
**Test:** Try explicit quality values:
- `quality: "medium"` → More casual/varied
- `quality: "low"` → More artistic/stylized

### Issue 3: Background Constraint
**Current:** `background: "opaque"`
**Impact:** Might force simple backgrounds
**Alternative:** Let user specify in prompt, remove parameter entirely

---

## Testing Checklist

Test these prompts to verify NO style constraints:

1. **Comic Style**
   - Input: `"Deadpool - red suit, katanas, fourth wall breaking expression"`
   - Expected: Comic book aesthetic, bold colors
   - Check: NOT corporate headshot with red tint

2. **Anime Style**
   - Input: `"Anime character with blue hair, large expressive eyes, school uniform"`
   - Expected: Anime art style
   - Check: NOT realistic photo with blue hair dye

3. **Oil Painting**
   - Input: `"Oil painting portrait, Renaissance style, dramatic chiaroscuro lighting"`
   - Expected: Classical painting texture
   - Check: NOT photo with painting filter

4. **Sci-Fi**
   - Input: `"Cyborg with half-mechanical face, glowing red eye, exposed circuitry"`
   - Expected: Futuristic sci-fi aesthetic
   - Check: NOT clean professional with subtle tech elements

---

## Current Status

**Prompt Enhancement:** ✅ Minimal (2 words added)
**User Input Preservation:** ✅ 100% intact
**Style Constraints:** ✅ Removed (was 3 sentences, now 2 words)
**Quality Bias:** ✅ Set to "auto" (was "high")
**Background Constraint:** ✅ Set to "opaque" (more reliable than transparent)

**Ready for testing!**
