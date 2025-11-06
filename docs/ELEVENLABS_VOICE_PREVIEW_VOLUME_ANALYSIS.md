# ElevenLabs Voice Preview Volume Analysis

**Date**: 2025-01-15  
**Issue**: Voice preview volume is very low despite laptop volume being up  
**Status**: Analysis Complete

---

## Current Implementation

### Frontend Audio Playback
**File**: `frontend/src/components/AgentBuilder.tsx` (lines 159-195)

```typescript
const playVoicePreview = async (voiceId: string) => {
  // ... fetch audio blob ...
  const audio = new Audio(audioUrl)
  audio.onerror = () => { ... }
  audio.onended = () => { ... }
  audio.play()  // ❌ NO VOLUME SETTING
}
```

### Backend Audio Generation
**File**: `backend/services/elevenlabs_service.py` (lines 118-144)

```python
async def generate_speech_with_voice_id(
    self,
    text: str,
    voice_id: str,
    model: str = "eleven_turbo_v2",
    stability: float = 0.75,      # ❌ Accepted but NOT USED
    similarity_boost: float = 0.75 # ❌ Accepted but NOT USED
) -> bytes:
    audio_bytes = self.client.generate(
        text=text,
        voice=voice_id,
        model=model
        # ❌ stability and similarity_boost NOT passed to API
    )
```

---

## Issues Affecting Volume

### 1. **Frontend: No Explicit Volume Setting** ⚠️ CRITICAL

**Problem**: HTML5 Audio element volume defaults to 1.0, but:
- Browser/system settings may override
- Autoplay policies may reduce volume
- No explicit control = unpredictable behavior

**Location**: `frontend/src/components/AgentBuilder.tsx:174`

**Fix Required**:
```typescript
const audio = new Audio(audioUrl)
audio.volume = 1.0  // ✅ Explicitly set to maximum
audio.play()
```

### 2. **Backend: Voice Settings Not Applied** ⚠️ MODERATE

**Problem**: `stability` and `similarity_boost` parameters are accepted but never passed to ElevenLabs API.

**Impact**: 
- These don't directly control volume, but affect audio quality
- Missing voice settings may result in lower-quality audio that sounds quieter
- API may use default settings that aren't optimal

**Location**: `backend/services/elevenlabs_service.py:132-136`

**Fix Required**:
```python
audio_bytes = self.client.generate(
    text=text,
    voice=voice_id,
    model=model,
    voice_settings={  # ✅ Add voice settings
        "stability": stability,
        "similarity_boost": similarity_boost
    }
)
```

### 3. **No Web Audio API Gain Control** ⚠️ OPTIONAL ENHANCEMENT

**Problem**: Using basic HTML5 Audio without Web Audio API gain control.

**Impact**: 
- Less precise volume control
- Can't boost volume beyond 1.0 if needed
- No per-audio gain adjustment

**Enhancement Option**: Use Web Audio API with GainNode for better control:
```typescript
const audioContext = new AudioContext()
const source = audioContext.createMediaElementSource(audio)
const gainNode = audioContext.createGain()
gainNode.gain.value = 1.0  // Can be set > 1.0 for boost
source.connect(gainNode)
gainNode.connect(audioContext.destination)
```

### 4. **Browser Autoplay Policies** ⚠️ POSSIBLE

**Problem**: Some browsers reduce volume for autoplay content.

**Impact**: Browser may automatically reduce volume for programmatically played audio.

**Mitigation**: 
- Ensure user interaction before playing (already done via button click)
- Set volume explicitly after user interaction

### 5. **ElevenLabs API Output Gain** ⚠️ CHECK API DOCS

**Problem**: ElevenLabs API may support output gain/volume parameters.

**Action Required**: Check ElevenLabs API documentation for:
- `output_gain` parameter
- `volume` parameter
- Any audio normalization settings

**Note**: The ElevenLabs Python SDK may have additional parameters not shown in current code.

---

## Recommended Fixes (Priority Order)

### Priority 1: Frontend Volume Setting (CRITICAL)

**File**: `frontend/src/components/AgentBuilder.tsx`

**Change**: Add explicit volume setting before play

```typescript
const audio = new Audio(audioUrl)
audio.volume = 1.0  // Explicitly set to maximum
audio.onerror = () => {
  console.error("Audio playback failed for preview")
  setIsPlayingPreview(null)
}
audio.onended = () => {
  setIsPlayingPreview(null)
  URL.revokeObjectURL(audioUrl)
}
audio.play().catch(err => {
  console.error("Playback failed:", err)
  setIsPlayingPreview(null)
})
```

**Impact**: Ensures maximum volume regardless of browser/system settings

### Priority 2: Backend Voice Settings (MODERATE)

**File**: `backend/services/elevenlabs_service.py`

**Change**: Pass voice settings to ElevenLabs API

```python
async def generate_speech_with_voice_id(
    self,
    text: str,
    voice_id: str,
    model: str = "eleven_turbo_v2",
    stability: float = 0.75,
    similarity_boost: float = 0.75
) -> bytes:
    try:
        # Check if client.generate supports voice_settings parameter
        # ElevenLabs SDK may use different parameter names
        audio_bytes = self.client.generate(
            text=text,
            voice=voice_id,
            model=model,
            voice_settings={  # Try this first
                "stability": stability,
                "similarity_boost": similarity_boost
            }
        )
        
        # Alternative: Check SDK documentation for correct parameter name
        # May be: voice_settings, settings, or passed differently
        
        # Convert generator to bytes if needed
        if hasattr(audio_bytes, '__iter__'):
            audio_bytes = b"".join(audio_bytes)

        logger.info(f"Generated audio with voice {voice_id} ({len(audio_bytes)} bytes)")
        return audio_bytes
    except Exception as e:
        logger.error(f"Failed to generate speech with voice {voice_id}: {e}")
        raise
```

**Impact**: Ensures optimal voice quality settings are applied

### Priority 3: Web Audio API Enhancement (OPTIONAL)

**File**: `frontend/src/components/AgentBuilder.tsx`

**Enhancement**: Use Web Audio API for better control

```typescript
const playVoicePreview = async (voiceId: string) => {
  setIsPlayingPreview(voiceId)
  try {
    const response = await fetch("http://localhost:8003/api/voices/preview", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        voice_id: voiceId,
        text: "Hello, I'm your personalized Guide..."
      })
    })

    if (response.ok) {
      const audioBlob = await response.blob()
      const audioUrl = URL.createObjectURL(audioBlob)
      
      // Use Web Audio API for better control
      const audio = new Audio(audioUrl)
      const audioContext = new (window.AudioContext || window.webkitAudioContext)()
      const source = audioContext.createMediaElementSource(audio)
      const gainNode = audioContext.createGain()
      
      // Set gain (can be > 1.0 for boost if needed)
      gainNode.gain.value = 1.0
      
      source.connect(gainNode)
      gainNode.connect(audioContext.destination)
      
      audio.onerror = () => {
        console.error("Audio playback failed for preview")
        setIsPlayingPreview(null)
        audioContext.close()
      }
      
      audio.onended = () => {
        setIsPlayingPreview(null)
        URL.revokeObjectURL(audioUrl)
        audioContext.close()
      }
      
      await audio.play()
    } else {
      // ... error handling
    }
  } catch (error) {
    // ... error handling
  }
}
```

**Impact**: Provides precise volume control and potential for volume boost

### Priority 4: Check ElevenLabs API Documentation

**Action**: Review ElevenLabs API/SDK documentation for:
- Volume/output gain parameters
- Audio normalization settings
- Voice settings parameter structure

**Location**: Check `elevenlabs` Python SDK documentation or API reference

---

## Testing Checklist

After implementing fixes:

- [ ] Test voice preview with volume set to 1.0
- [ ] Test on different browsers (Chrome, Firefox, Safari, Edge)
- [ ] Test on different operating systems (Windows, macOS, Linux)
- [ ] Verify audio is audible at system volume 50%
- [ ] Verify audio is audible at system volume 100%
- [ ] Test with headphones vs speakers
- [ ] Test Web Audio API implementation (if implemented)
- [ ] Verify voice settings are applied in backend logs
- [ ] Compare audio quality before/after voice settings fix

---

## Additional Considerations

### Browser-Specific Issues

1. **Chrome**: May reduce autoplay volume
   - **Fix**: Ensure user interaction before play (already done)

2. **Safari**: Strict autoplay policies
   - **Fix**: Explicit volume setting + user interaction

3. **Firefox**: Generally good audio support
   - **Fix**: Standard volume setting should work

### System-Level Issues

1. **Windows**: System volume mixer may have per-app volume
   - **Check**: Windows Volume Mixer for browser volume

2. **macOS**: System volume + per-app volume
   - **Check**: System Preferences > Sound

3. **Linux**: PulseAudio/ALSA configuration
   - **Check**: System audio settings

### Audio File Quality

1. **ElevenLabs Output**: May generate audio at lower volume
   - **Check**: Download audio file and test in external player
   - **Compare**: Volume level vs other audio files

2. **Audio Encoding**: MP3 encoding may affect perceived volume
   - **Check**: Audio normalization in encoding process

---

## Quick Fix (Immediate)

**Minimum change to fix volume issue**:

```typescript
// In AgentBuilder.tsx, line 174
const audio = new Audio(audioUrl)
audio.volume = 1.0  // ✅ ADD THIS LINE
audio.onerror = () => { ... }
audio.onended = () => { ... }
audio.play()
```

This single line addition should resolve the volume issue in most cases.

---

## Summary

**Root Cause**: No explicit volume setting on HTML5 Audio element, allowing browser/system defaults to potentially reduce volume.

**Primary Fix**: Set `audio.volume = 1.0` explicitly before playing.

**Secondary Fix**: Pass voice settings to ElevenLabs API for optimal audio quality.

**Estimated Impact**: 
- Primary fix: Should resolve volume issue immediately
- Secondary fix: Improves audio quality, may indirectly help with perceived volume

---

**Analysis Complete**: 2025-01-15  
**Next Steps**: Implement Priority 1 fix (frontend volume setting)

