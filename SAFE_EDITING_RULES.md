# Safe Editing Rules - Prevent Application Breakage

## Critical Rules for UI Changes

### 1. **Never Use Experimental CSS Classes**
- ❌ **BANNED**: `text-balance` (causes runtime errors in Next.js)
- ✅ **USE**: Standard Tailwind classes only
- Always verify class compatibility before adding

### 2. **Test Incrementally**
- Make ONE change at a time
- Check browser after each change
- Never batch multiple risky changes

### 3. **Avoid Complex Layout Refactors**
- ❌ Don't add conflicting flex properties (`flex-grow` + `min-h-screen` + `items-center`)
- ✅ Use simple spacing utilities: `mb-*`, `mt-*`, `py-*`
- Keep layout structure unchanged when possible

### 4. **Responsive Breakpoint Safety**
- Always specify mobile AND desktop: `mb-48 lg:mb-16`
- Never leave one breakpoint without a value
- Test both mobile and desktop views

### 5. **Motion/Animation Safety**
- Don't change motion.div structure
- Only modify className props
- Keep initial/animate/transition props intact

### 6. **Pre-Flight Checks**
```bash
# Before editing UI:
1. Read the entire component first
2. Identify risky changes (layout, new classes, animations)
3. Make minimal changes only
4. Check dev server output immediately
```

### 7. **Rollback Protocol**
If page crashes:
1. Immediately revert to last working state
2. Remove experimental classes
3. Test in browser
4. Apply changes one at a time

### 8. **Banned Patterns**
```tsx
// ❌ DON'T DO THIS
<div className="text-balance">
<div className="min-h-screen flex-grow items-center">

// ✅ DO THIS
<div className="leading-relaxed">
<div className="mb-48 lg:mb-16">
```

## Applied to This Project
- **Root Cause**: `text-balance` class is not supported in production
- **Solution**: Removed class, used `<span className="block mt-2">` for line breaks
- **Lesson**: Always verify experimental Tailwind features before using
