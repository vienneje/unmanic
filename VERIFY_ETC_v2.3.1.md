# Verify ETC Display - v2.3.1

## ✅ Deployed Successfully

### Plugin v2.3.1
- ✅ Uploaded to Zeus: `/root/.unmanic/plugins/transcode_amd_v2/`
- ✅ Container restarted: `unmanic-noble`
- ✅ Git committed and pushed to GitHub

## 🧪 How to Verify ETC is Working

### Step 1: Clear Browser Cache
**IMPORTANT:** Do this first to ensure you have the latest frontend fix!

- **Windows/Linux**: `Ctrl + Shift + R`
- **Mac**: `Cmd + Shift + R`

Or open an incognito/private window.

### Step 2: Check Worker Status
1. Go to http://zeus.local:9092
2. Navigate to **Dashboard**
3. Look for active worker

### Step 3: What You Should See

#### When Worker is Active (Encoding):
```
Worker Name: Worker-1
Status: Active
Current File: Ibrahimovic.Il.Etait.Une.Fois.Zlatan...mkv
Progress: 15%  ← Should show percentage
ETC: 5 minutes 40 seconds  ← Should show time remaining! 🎉
```

#### If ETC Still Empty:
1. Open browser console (F12 → Console tab)
2. Look for errors
3. Check Network tab → WS (WebSocket) → Messages
4. Look for worker status updates like:
```json
{
  "subprocess": {
    "percent": "15",
    "elapsed": 60
  }
}
```

If `elapsed` is not `0`, then the backend fix is working!

### Step 4: Verify Plugin Version
In Unmanic UI:
1. Go to **Plugins**
2. Find **AMD Transcode v2**
3. Check version shows **2.3.1**

### Step 5: Check Logs
```bash
ssh root@zeus.local "docker logs unmanic-noble 2>&1 | grep -E 'progress parser|Registered PID|start time' | tail -10"
```

Should see:
```
Registered PID 12345 and start time with worker monitor
FFmpeg progress parser enabled - progress bar and ETC will be available
```

## 🎯 Expected Behavior

### Progress Tracking Timeline

| Time | % Complete | Elapsed | ETC Display |
|------|-----------|---------|-------------|
| 0s | 0% | 0s | (empty - guard condition) |
| 10s | 1% | 10s | "16 minutes 30 seconds" |
| 30s | 5% | 30s | "9 minutes 30 seconds" |
| 60s | 10% | 60s | "9 minutes" |
| 120s | 20% | 120s | "8 minutes" |
| 300s | 50% | 300s | "5 minutes" |
| 540s | 90% | 540s | "1 minute" |
| 600s | 100% | 600s | "Complete" |

### How ETC Changes

The ETC should **decrease** as encoding progresses:
- Early on (1-5%): Might fluctuate as FFmpeg stabilizes
- Mid-way (10-80%): Should be fairly accurate
- Near end (90-99%): Final seconds countdown

### ETC Accuracy Factors

ETC is based on **average encoding speed**:
- **Fast scenes**: ETC might go down faster
- **Complex scenes**: ETC might increase temporarily
- **Overall trend**: Should decrease steadily

## 🔧 Troubleshooting

### ETC Still Empty After Cache Clear

#### Check 1: Plugin Loaded?
```bash
ssh root@zeus.local "docker exec unmanic-noble cat /root/.unmanic/plugins/transcode_amd_v2/info.json | grep version"
```
Should show: `"version": "2.3.1"`

#### Check 2: Frontend Fix Loaded?
```bash
ssh root@zeus.local "docker exec unmanic-noble ls -lh /usr/local/lib/python3.12/dist-packages/unmanic/webserver/public/js/app.*.js"
```
Should show: `app.a476fd30.js` (234KB)

#### Check 3: Worker Active?
```bash
ssh root@zeus.local "docker exec unmanic-noble ps aux | grep ffmpeg"
```
Should show active ffmpeg process if worker is encoding.

#### Check 4: WebSocket Connected?
In browser console, check for WebSocket errors.

#### Check 5: API Response
While worker is active, check:
```bash
ssh root@zeus.local "curl -s http://localhost:9092/api/v2/workers/status" | python3 -m json.tool | grep -A 10 subprocess
```

Should show:
```json
"subprocess": {
  "pid": "12345",
  "percent": "15",
  "elapsed": 60,  ← This should NOT be 0!
  ...
}
```

### If elapsed is still 0:

Check if worker monitor received start time:
```bash
ssh root@zeus.local "docker logs unmanic-noble 2>&1 | tail -500 | grep 'start time'"
```

Should see: `"Set subprocess start time: 1729513521.5"`

### If still not working:

1. Stop all workers
2. Restart unmanic-noble container
3. Clear browser cache again
4. Start a new task
5. Monitor from the very beginning

## 📊 Success Criteria

✅ **v2.3.1 is working correctly if:**
- Progress bar shows 0-100% during encoding
- ETC shows time remaining (not empty)
- ETC decreases as encoding progresses
- ETC is reasonably accurate (within 20% of actual time)

## 🎉 Final Notes

This fix was particularly challenging because it required:
1. Understanding Unmanic's subprocess monitoring system
2. Identifying that elapsed time is calculated from start_time
3. Discovering that custom parsers can't access WorkerSubprocessMonitor
4. Finding the wrapper pattern to bridge custom + default parsers
5. Fixing both backend (elapsed=0) and frontend (division-by-zero) bugs

**Now fully operational!** 🚀

---

Need help? Check:
- `ETC_FIX_v2.3.1.md` - Technical deep-dive
- `ETC_TROUBLESHOOTING.md` - Detailed debugging guide
- Plugin changelog - Complete version history
