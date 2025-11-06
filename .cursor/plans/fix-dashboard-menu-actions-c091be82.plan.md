<!-- c091be82-60e9-4151-ae20-6799e2ad1c4a 82cf319b-29f4-4109-87c6-37e56145bd08 -->
# Avatar Generation Diagnostic & Fix Plan

## Problem Statement

Avatar generation button is not firing/working. Need to diagnose root cause and fix.

## Current Implementation Analysis

### Frontend (`frontend/src/components/AgentBuilder.tsx`)

**Function**: `generateAvatar` (lines 196-233)

- ✅ Function exists and is properly defined
- ✅ Button has `onClick={generateAvatar}` (line 801)
- ✅ Button disabled state: `disabled={isGeneratingAvatar || !avatarPrompt.trim()}` (line 802)
- ⚠️ **ISSUE**: Missing `x-tenant-id` and `x-user-id` headers (line 206)
- ⚠️ **ISSUE**: Using manual URL resolution instead of `resolveAvatarUrl` utility

**Button Component**:

- ✅ Using Radix UI Button component (not native button)
- ✅ Button is NOT inside a form element
- ✅ No form submission interference

### Potential Issues

#### Issue 1: Missing Headers (CRITICAL)

**Location**: `frontend/src/components/AgentBuilder.tsx` line 206

**Problem**: Request doesn't include tenant/user headers

```typescript
headers: { "Content-Type": "application/json" },  // Missing x-tenant-id and x-user-id
```

**Impact**: Backend defaults to hardcoded IDs, but may cause:

- CORS issues
- Authentication failures
- Tenant isolation problems

#### Issue 2: Button Disabled State

**Location**: `frontend/src/components/AgentBuilder.tsx` line 802

**Problem**: Button disabled when `avatarPrompt.trim()` is empty

```typescript
disabled={isGeneratingAvatar || !avatarPrompt.trim()}
```

**Diagnosis**: Check if `avatarPrompt` state is properly initialized and updating

#### Issue 3: Error Handling

**Location**: `frontend/src/components/AgentBuilder.tsx` lines 222-225

**Problem**: Errors only logged to console and shown via alert

- May miss network errors
- No detailed error information for debugging

#### Issue 4: Event Handler Not Firing

**Possible Causes**:

1. Button disabled state preventing clicks
2. JavaScript error preventing function execution
3. Event propagation issue
4. React state update issue

## Diagnostic Steps

### Step 1: Verify Button State

- Check if `avatarPrompt` state is initialized (line 84)
- Verify `avatarPrompt` updates when Textarea changes (line 794)
- Check if button is actually disabled in browser DevTools

### Step 2: Add Console Logging

Add debug logs to verify function execution:

```typescript
const generateAvatar = async () => {
  console.log("🔵 generateAvatar called", { avatarPrompt, isGeneratingAvatar })
  if (!avatarPrompt.trim()) {
    console.log("⚠️ Avatar prompt is empty")
    alert("Please enter a description for your avatar")
    return
  }
  // ... rest of function
}
```

### Step 3: Check Network Requests

- Open browser DevTools → Network tab
- Click "Generate Avatar" button
- Check if request is sent to `/api/avatar/generate`
- Check request headers and payload
- Check response status and error messages

### Step 4: Verify Backend Endpoint

- Confirm backend is running on `localhost:8003`
- Test endpoint directly with curl/Postman
- Check backend logs for incoming requests

## Fixes Required

### Fix 1: Add Missing Headers

**File**: `frontend/src/components/AgentBuilder.tsx`

**Location**: Line 204-213

**Change**:

```typescript
const response = await fetch("http://localhost:8003/api/avatar/generate", {
  method: "POST",
  headers: { 
    "Content-Type": "application/json",
    'x-tenant-id': '00000000-0000-0000-0000-000000000001',
    'x-user-id': userId || '00000000-0000-0000-0000-000000000001',
  },
  body: JSON.stringify({
    prompt: avatarPrompt,
    size: "1024x1024",
    quality: "auto",
    background: "opaque"
  })
})
```

### Fix 2: Add Event Handler Debugging

**File**: `frontend/src/components/AgentBuilder.tsx`

**Location**: Line 196

**Add**:

```typescript
const generateAvatar = async (e?: React.MouseEvent) => {
  e?.preventDefault() // Prevent any default behavior
  e?.stopPropagation() // Prevent event bubbling
  
  console.log("🔵 generateAvatar called", { 
    avatarPrompt, 
    promptLength: avatarPrompt.trim().length,
    isGeneratingAvatar 
  })
  
  if (!avatarPrompt.trim()) {
    console.log("⚠️ Avatar prompt is empty")
    alert("Please enter a description for your avatar")
    return
  }
  // ... rest of function
}
```

### Fix 3: Improve Error Handling

**File**: `frontend/src/components/AgentBuilder.tsx`

**Location**: Lines 222-229

**Change**:

```typescript
if (!response.ok) {
  const errorText = await response.text()
  console.error("Avatar generation failed:", {
    status: response.status,
    statusText: response.statusText,
    error: errorText
  })
  alert(`Failed to generate avatar: ${response.statusText}. Check console for details.`)
  return
}
```

### Fix 4: Use resolveAvatarUrl Utility

**File**: `frontend/src/components/AgentBuilder.tsx`

**Location**: Lines 217-221

**Change**:

```typescript
import { resolveAvatarUrl } from "@/lib/avatar-utils"

// ... in generateAvatar function:
if (response.ok) {
  const data = await response.json()
  const fullAvatarUrl = resolveAvatarUrl(data.avatar_url)
  setAvatarUrl(fullAvatarUrl)
}
```

### Fix 5: Add Button Type Attribute

**File**: `frontend/src/components/AgentBuilder.tsx`

**Location**: Line 800

**Change**:

```typescript
<Button
  type="button"  // Explicitly prevent form submission
  onClick={generateAvatar}
  disabled={isGeneratingAvatar || !avatarPrompt.trim()}
  className="w-full bg-kurzgesagt-purple text-white hover:bg-kurzgesagt-purple/90"
>
  {isGeneratingAvatar ? "Generating..." : "Generate Avatar"}
</Button>
```

## Testing Checklist

- [ ] Verify button is not disabled when avatarPrompt has text
- [ ] Click button and verify console log appears
- [ ] Check Network tab for request to `/api/avatar/generate`
- [ ] Verify request includes all required headers
- [ ] Verify request body includes prompt, size, quality
- [ ] Check response status and error messages
- [ ] Verify backend receives request (check backend logs)
- [ ] Test with valid prompt and verify avatar URL returned
- [ ] Verify avatar displays correctly after generation

## Expected Behavior After Fix

1. User enters description in Textarea
2. Button becomes enabled
3. User clicks "Generate Avatar"
4. Console shows "generateAvatar called" log
5. Network request sent with proper headers
6. Backend processes request
7. Avatar URL returned and displayed
8. Loading state shows "Generating..." during request

## Debugging Commands

### Check if function is being called:

```javascript
// In browser console:
document.querySelector('button:contains("Generate Avatar")').click()
```

### Check avatarPrompt state:

```javascript
// Add to component temporarily:
console.log("avatarPrompt state:", avatarPrompt)
```

### Test backend directly:

```bash
curl -X POST http://localhost:8003/api/avatar/generate \
  -H "Content-Type: application/json" \
  -H "x-tenant-id: 00000000-0000-0000-0000-000000000001" \
  -H "x-user-id: 00000000-0000-0000-0000-000000000001" \
  -d '{"prompt": "A wise elderly woman with kind eyes", "size": "1024x1024", "quality": "auto"}'
```

### To-dos

- [ ] Add x-tenant-id and x-user-id headers to avatar generation request in AgentBuilder.tsx
- [ ] Add debug logging to generateAvatar function to verify it is being called
- [ ] Add preventDefault and stopPropagation to generateAvatar event handler
- [ ] Improve error handling with detailed error logging and user feedback
- [ ] Replace manual URL resolution with resolveAvatarUrl utility in generateAvatar
- [ ] Add explicit type="button" attribute to Generate Avatar button
- [ ] Test avatar generation flow: verify button enabled, click handler fires, request sent, response received