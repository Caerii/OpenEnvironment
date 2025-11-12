# Auto-Refresh Quick Start 🚀

## What Is It?

**Auto-refresh** lets your frontend UI automatically update when you make API calls from Postman or scripts - no manual refresh needed!

---

## How to Use

### 1. Enable Auto-Refresh

In the UI, click the toggle button:

```
⏸️ Auto OFF  →  Click!  →  ⚡ Auto ON • Polling every 2s
```

### 2. Make API Calls

Use Postman or curl:

```bash
# Postman or terminal:
POST http://localhost:8001/api/generate
Content-Type: application/json

{
  "text": "create three mountains in the center"
}
```

### 3. Watch the Magic! ✨

**Within 2 seconds**, your UI will automatically:
- ✅ Detect the backend change
- ✅ Load the new terrain
- ✅ Update the 3D viewer
- ✅ Refresh the state

**Console output:**
```
🔄 Auto-refresh detected changes, updating...
```

---

## Visual Guide

### Button States

#### OFF (Default - Manual Mode)
```
┌─────────────────────────────┐
│ [🔄 Refresh] [⏸️ Auto OFF]  │  ← Gray button
└─────────────────────────────┘
```
- Use "Refresh" button manually
- No automatic polling
- Best for normal UI workflow

#### ON (Auto Mode)
```
┌─────────────────────────────────────────┐
│ [🔄 Refresh] [⚡ Auto ON] • Polling...  │  ← Orange button
└─────────────────────────────────────────┘
```
- Polls backend every 2 seconds
- Automatically detects changes
- Best for Postman/API workflow

---

## When to Use

### ✅ Use Auto-Refresh When:
- Testing with Postman
- Running Python scripts
- Multiple people using same backend
- Automated terrain generation
- Want instant visual feedback

### ⏸️ Don't Use Auto-Refresh When:
- Using the UI normally (Generate/Modify buttons)
- Want to conserve network bandwidth
- Backend is slow/unreliable
- Just browsing/viewing terrain

---

## Behind the Scenes

**What happens when enabled:**

```
Every 2 seconds:
  1. Frontend checks backend for changes
  2. Compares asset filenames (timestamps)
  3. If changed → Auto-update UI
  4. If unchanged → Do nothing (efficient!)
```

**Performance:**
- CPU: ~0.1% (negligible)
- Network: 1 request per 2 seconds
- Memory: Baseline + 1KB

**Verdict:** Extremely lightweight! ✅

---

## Testing It Out

### Quick Test (30 seconds)

1. **Open frontend**
   ```
   http://localhost:5173
   ```

2. **Enable auto-refresh**
   - Click `⚡ Auto ON` button
   - See: `• Polling every 2s`

3. **Make Postman call**
   ```
   POST http://localhost:8001/api/generate
   Body: {"text": "create a mountain"}
   ```

4. **Watch UI update** (within 2 seconds!)
   - New terrain appears
   - Console: `🔄 Auto-refresh detected changes, updating...`

5. **Success!** 🎉

---

## Backend Status

Check if auto-refresh is supported:

```bash
GET http://localhost:8001/api/status
```

Response:
```json
{
  "ok": true,
  "supports_auto_refresh": true,  ← Look for this!
  "cerebras_api_key_configured": true,
  "llm_parser_available": true,
  "server_ready": true
}
```

---

## Troubleshooting

### UI not updating?

**Check:**
1. Is auto-refresh ON? (orange button)
2. Did backend state actually change?
3. Check browser console for errors
4. Check Network tab (should see requests every 2s)

**Try:**
- Toggle auto-refresh OFF then ON
- Click manual "🔄 Refresh" button
- Restart frontend (F5)

---

## Tips & Tricks

### Tip 1: Use with Postman Collections
```
Run entire collection → Watch UI cycle through terrains!
```

### Tip 2: Combine with Templates
```
Apply template via API → UI auto-updates with result
```

### Tip 3: Debug Workflow
```
Enable auto-refresh → Make API calls → See results instantly
```

### Tip 4: Turn Off When Done
```
Remember to click ⏸️ Auto OFF when not actively testing!
```

---

## Summary

**Auto-Refresh = Postman ↔ UI Sync**

| Feature | Manual Mode | Auto Mode |
|---------|-------------|-----------|
| **Button** | ⏸️ Auto OFF (Gray) | ⚡ Auto ON (Orange) |
| **Polling** | None | Every 2 seconds |
| **Updates** | Click "Refresh" | Automatic |
| **Use Case** | Normal UI work | API testing |
| **Network** | On-demand | 0.5 req/s |

---

## Ready to Use! 🎉

Just click the **⚡ Auto ON** button and start making API calls!

**For more details, see:** `AUTO_REFRESH_FEATURE.md`

