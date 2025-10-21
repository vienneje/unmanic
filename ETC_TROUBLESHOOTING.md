# ETC Troubleshooting Guide

## ✅ Status Update

### What's Working
- ✅ Plugin v2.3.0 installed
- ✅ Library scanning working - files being added to pending
- ✅ Worker processing files
- ✅ Progress bar showing (0-100%)
- ✅ Frontend fix deployed (calculateEtc guard condition)

### What's Not Working
- ❌ ETC still showing empty

## 🔍 Likely Cause: Browser Cache

The frontend fix IS deployed, but your browser might be **caching the old JavaScript file**.

## ✅ Solution: Force Browser Refresh

### Method 1: Hard Refresh (Try This First)

1. Open http://zeus.local:9092 in your browser
2. **Force reload** to clear cache:
   - **Windows/Linux**: `Ctrl + Shift + R` or `Ctrl + F5`
   - **Mac**: `Cmd + Shift + R`
3. Wait for page to fully reload
4. Check if ETC now appears

### Method 2: Clear Browser Cache

1. Open browser Developer Tools: `F12`
2. Right-click on the **Reload button** (next to address bar)
3. Select **"Empty Cache and Hard Reload"**
4. Wait for page to reload
5. Check ETC display

### Method 3: Clear All Site Data

1. Press `F12` (Developer Tools)
2. Go to **Application** tab (Chrome) or **Storage** tab (Firefox)
3. Find "Clear storage" or "Clear site data"
4. Click **"Clear site data"** for http://zeus.local:9092
5. Close Developer Tools
6. Reload the page
7. Check ETC display

### Method 4: Incognito/Private Window

1. Open a **new incognito/private window**
2. Navigate to http://zeus.local:9092
3. This bypasses all cache
4. Check if ETC shows here

### Method 5: Different Browser

Try accessing Unmanic from a completely different browser (Chrome, Firefox, Edge, Safari) that you haven't used before.

## 🧪 Verification Steps

Once you've cleared the cache:

### 1. Check JavaScript Console
1. Press `F12` to open Developer Tools
2. Go to **Console** tab
3. Look for any errors related to:
   - `calculateEtc`
   - `Infinity`
   - `NaN`
   - `printSecondsAsDuration`

### 2. Watch Network Tab
1. In Developer Tools, go to **Network** tab
2. Reload the page
3. Look for `app.a476fd30.js` being loaded
4. Verify size is **~234KB** (the fixed version)
5. Check if the file is loaded from cache or fresh

### 3. Check WebSocket Messages
1. In Network tab, filter by **WS** (WebSocket)
2. Click on the websocket connection
3. Go to **Messages** tab
4. Watch for worker status updates
5. Look for data like:
   ```json
   {
     "subprocess": {
       "percent": "15",
       "elapsed": 120
     }
   }
   ```

### 4. Test ETC Calculation Manually
In the browser console, paste this:
```javascript
function calculateEtc(percent_completed, time_elapsed) {
  let percent = parseInt(percent_completed);
  let elapsed = parseInt(time_elapsed);
  
  if (isNaN(percent) || isNaN(elapsed) || percent <= 0) {
    return 0;
  }
  
  let percent_to_go = (100 - percent);
  return (elapsed / percent) * percent_to_go;
}

// Test it
console.log("ETC at 2%, 30s elapsed:", calculateEtc("2", 30));
console.log("ETC at 10%, 60s elapsed:", calculateEtc("10", 60));
console.log("ETC at 0%, 10s elapsed:", calculateEtc("0", 10));
```

**Expected output:**
```
ETC at 2%, 30s elapsed: 1470
ETC at 10%, 60s elapsed: 540
ETC at 0%, 10s elapsed: 0
```

## 🔧 If ETC Still Doesn't Show

### Verify Frontend Fix is Loaded

Check the index.html to see which JS file should be loaded:
```bash
ssh root@zeus.local "docker exec unmanic-noble cat /usr/local/lib/python3.12/dist-packages/unmanic/webserver/public/index.html" | grep app.*js
```

Should show: `app.a476fd30.js`

### Check File Hash Matches

```bash
# On Zeus container
ssh root@zeus.local "docker exec unmanic-noble md5sum /usr/local/lib/python3.12/dist-packages/unmanic/webserver/public/js/app.a476fd30.js"

# On local build
md5sum /tmp/unmanic-frontend/dist/spa/js/app.a476fd30.js
```

Both should match.

### Alternative: Use Original Frontend

If the fix still doesn't work, you can report this issue to Unmanic and use the original frontend for now:

```bash
# This won't show ETC, but everything else works
# The plugin is still functional for encoding
```

## 📊 Expected Behavior After Fix

Once browser cache is cleared and fix is loaded:

| Progress | Elapsed | ETC Display |
|----------|---------|-------------|
| 0% | 5s | Empty (guard condition) |
| 1% | 10s | "16 minutes" |
| 2% | 30s | "24 minutes" |
| 10% | 60s | "9 minutes" |
| 50% | 300s | "5 minutes" |
| 90% | 540s | "1 minute" |
| 99% | 594s | "6 seconds" |

## 🎯 Most Likely Solution

**HARD REFRESH YOUR BROWSER** with `Ctrl + Shift + R` (or `Cmd + Shift + R` on Mac).

This will force your browser to download the new JavaScript file with the ETC fix.

---

**Try the hard refresh first and let me know if ETC appears!** 🚀
