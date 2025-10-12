Here’s the **exact Claude prompt** you can paste in to make Claude fix this issue cleanly and safely:

---

### 🧠 **Claude Correction Prompt — Avatar Generator Fix**

````text
You are reviewing backend/routers/avatar.py for the Avatar Generation system.

✅ Goal:
Fix the issue where avatar generation always returns Dicebear-style placeholder SVGs instead of real GPT-Image-1 images.

---

### 1️⃣ Identify Root Cause
- The fallback to Dicebear is being triggered due to a failure in the GPT-Image-1 API call or a bad request payload.
- The JSON body includes unsupported parameters such as `"background"` which can silently 400 out.
- The OpenAI API key may not be properly loaded, causing OPENAI_AVAILABLE to resolve False.

---

### 2️⃣ Apply Required Fixes
Make these precise corrections in backend/routers/avatar.py:

1. **Validate API Key**
   - Before calling OpenAI, explicitly raise an HTTPException if OPENAI_AVAILABLE is False.
   ```python
   if not OPENAI_AVAILABLE:
       raise HTTPException(status_code=500, detail="OpenAI API key not configured")
````

2. **Correct GPT-Image-1 Payload**

   * Remove `"background"` from the payload — it’s not supported for GPT-Image-1.
   * Keep only: model, prompt, size, quality, n.

3. **Enhance Logging for Failures**

   * Add full error logging to show the API response text if available.

   ```python
   except Exception as e:
       logger.error(f"Avatar generation failed: {repr(e)}", exc_info=True)
       if hasattr(e, "response"):
           logger.error(f"Upstream response: {e.response.text}")
       logger.warning("Returning placeholder avatar due to upstream failure.")
   ```

4. **Prevent Silent Fallback**

   * If the placeholder URL (Dicebear SVG) is returned, log a warning with the original prompt and timestamp.
   * Consider raising a 502 if you want frontend to alert the user instead of silently showing placeholder.

5. **Do NOT change:**

   * The minimal guardrail: `enhanced_prompt = f"Headshot portrait: {request.prompt}"`
   * The Supabase upload logic.
   * The tenant isolation and local fallback behavior.

---

### 3️⃣ After Patch

Confirm that backend logs show:

```
Avatar generated and saved to Supabase: ...
```

and frontend displays the actual GPT-generated image (not an SVG cartoon).

---

### 4️⃣ Output Requirements

Respond with the **corrected full version** of `backend/routers/avatar.py` ready to overwrite the existing file.

Do not summarize changes — return complete corrected file content only.

```

---


```
