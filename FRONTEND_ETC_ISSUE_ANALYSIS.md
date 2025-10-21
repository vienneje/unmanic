# Frontend ETC Issue - Root Cause Analysis

## 🔍 Investigation Summary

After analyzing the Unmanic frontend code at https://github.com/Unmanic/unmanic-frontend, I've identified the **exact location and logic** for ETC calculation.

## 📍 ETC Calculation Location

**File**: `src/pages/MainDashboard.vue`  
**Lines**: 154-157

```javascript
function calculateEtc(percent_completed, time_elapsed) {
  let percent_to_go = (100 - parseInt(percent_completed))
  return (parseInt(time_elapsed) / parseInt(percent_completed) * percent_to_go)
}
```

**Usage** (Lines 258-259):
```javascript
const etcDuration = calculateEtc(worker.subprocess.percent, worker.subprocess.elapsed)
workerData['worker-' + worker.id].etc = dateTools.printSecondsAsDuration(etcDuration);
```

## 🐛 Potential Issues

### Issue 1: Division by Zero at Low Percentages

When encoding just starts:
- `percent_completed` = `"2"` (from your logs)
- `parseInt("2")` = `2`
- Calculation: `(elapsed / 2) * (100 - 2)` = `(elapsed / 2) * 98`

This should work, but there's a problem when `percent` is `0`:
- `parseInt("0")` = `0`
- Calculation: `(elapsed / 0) * 100` = `Infinity`
- Result: ETC shows as empty or "Infinity"

### Issue 2: Condition Check (Line 250)

```javascript
if (typeof worker.subprocess.percent !== 'undefined' && worker.subprocess.percent !== '') {
```

This checks:
1. `percent` is not undefined ✅
2. `percent` is not empty string `''` ✅

But from your logs, the percent should be passing these checks since it's `"2"`, `"3"`, etc.

### Issue 3: Data Type Mismatch

The backend returns (from `workers.py` line 240):
```python
'percent': str(self.subprocess_percent),  # String: "2"
'elapsed': self.get_subprocess_elapsed(),  # Integer: 45
```

Frontend expects both as strings for `parseInt()`, which should work fine.

## 🔬 Your Specific Case

From your debug logs:
```
FFmpeg progress: 151.23s / 6974.33s = 2%
FFmpeg progress: 215.61s / 6974.33s = 3%
```

**Expected ETC calculation**:
```javascript
// At 2% with 30 seconds elapsed
percent_completed = "2"
time_elapsed = 30

percent_to_go = 100 - 2 = 98
etc = (30 / 2) * 98 = 15 * 98 = 1470 seconds = ~24.5 minutes
```

This should display "24 minutes" in the UI, but it's showing empty.

## 🎯 Possible Root Causes

### 1. **Zero or Very Low Initial Percent**
If the first progress update sends `percent = 0`:
```javascript
parseInt("0") = 0
etc = (elapsed / 0) * 100 = Infinity
```
Result: `printSecondsAsDuration(Infinity)` might return empty string

### 2. **Data Not Reaching Frontend**
The websocket might not be sending the `subprocess` data properly:
- Check if `worker.subprocess` exists
- Check if `worker.subprocess.percent` is actually set
- Check if `worker.subprocess.elapsed` is actually set

### 3. **Frontend Console Errors**
JavaScript errors in `calculateEtc()` or `printSecondsAsDuration()` might be silently failing

## 🧪 Debugging Steps

### Step 1: Check Browser Console
Open the Unmanic web UI in your browser and:
1. Open Developer Tools (F12)
2. Go to Console tab
3. Look for JavaScript errors
4. Look for warnings about `NaN`, `Infinity`, or calculation errors

### Step 2: Check Websocket Data
In Browser Developer Tools:
1. Go to Network tab
2. Filter by WS (WebSocket)
3. Click on the websocket connection
4. Watch the Messages tab
5. Look for worker status updates
6. Verify `subprocess.percent` and `subprocess.elapsed` are being sent

Example expected data:
```json
{
  "id": "1",
  "subprocess": {
    "percent": "2",
    "elapsed": 45,
    "pid": "12345",
    ...
  }
}
```

### Step 3: Add Debug Logging
You could temporarily modify the frontend code to add logging:

```javascript
// In MainDashboard.vue, line 258-259
console.log('Worker subprocess:', worker.subprocess);
console.log('Percent:', worker.subprocess.percent, 'Elapsed:', worker.subprocess.elapsed);
const etcDuration = calculateEtc(worker.subprocess.percent, worker.subprocess.elapsed)
console.log('Calculated ETC duration:', etcDuration);
workerData['worker-' + worker.id].etc = dateTools.printSecondsAsDuration(etcDuration);
console.log('Formatted ETC:', workerData['worker-' + worker.id].etc);
```

## 💡 Likely Issue

Based on the code analysis, the most likely issue is:

**The `printSecondsAsDuration()` function might be failing when ETC is calculated at very low percentages (like 2-3%), resulting in very large numbers (like 3000+ seconds).**

Or:

**The initial progress update sends `percent = "0"` which causes `Infinity`, and the UI gets stuck showing empty even when subsequent updates have valid percentages.**

## 🔧 Potential Fixes

### Fix 1: Guard Against Division by Zero in Frontend

Modify `calculateEtc()` to handle zero percent:
```javascript
function calculateEtc(percent_completed, time_elapsed) {
  let percent = parseInt(percent_completed);
  let elapsed = parseInt(time_elapsed);
  
  // Guard against division by zero
  if (percent <= 0 || isNaN(percent) || isNaN(elapsed)) {
    return 0;  // or return null
  }
  
  let percent_to_go = (100 - percent);
  return (elapsed / percent) * percent_to_go;
}
```

### Fix 2: Don't Return Percent Until > 0

Modify the plugin to not return progress until it's > 0:
```python
# In plugin.py FFmpegProgressParser.parse()
if self.current_percent > 0:
    return {
        'percent': self.current_percent,
        'paused': False,
        'killed': False
    }
else:
    # Don't report progress until we have a non-zero value
    return {
        'percent': None,  # or don't include percent key
        'paused': False,
        'killed': False
    }
```

But this might break the progress bar itself.

## 📊 Data Flow

1. **Plugin** calculates: `12%` (integer)
2. **Plugin** returns: `{'percent': 12}`
3. **Worker** receives: `12`
4. **Worker** stores: `subprocess_percent = 12`
5. **Worker** returns stats: `{'percent': '12', 'elapsed': 45}`
6. **WebSocket** sends to frontend: `{"subprocess": {"percent": "12", "elapsed": 45}}`
7. **Frontend** receives: `worker.subprocess.percent = "12"`
8. **Frontend** calculates: `calculateEtc("12", 45)`
9. **Frontend** displays: `printSecondsAsDuration(result)`

## 🎯 Next Steps

1. **Check browser console** for JavaScript errors
2. **Check websocket messages** to verify data is being sent
3. **Verify `printSecondsAsDuration()`** isn't failing on large numbers
4. **Test with higher percentages** - does ETC appear at 10%? 20%?
5. **Check if ETC appears after 5-10% progress**

## 📝 Conclusion

**The plugin is working correctly** - it's calculating and returning progress percentage accurately.

**The backend is working correctly** - it's storing and sending the data via API/WebSocket.

**The frontend ETC calculation is mathematically correct** - but might be failing due to:
- Edge cases (division by zero at 0%)
- Large number formatting issues
- JavaScript errors in `printSecondsAsDuration()`
- Websocket data not reaching the updateWorkerProgressCharts function

**This is a frontend display/calculation issue, not a plugin issue.**

---

**Recommendation**: Check the browser console and websocket messages to identify exactly where the ETC calculation is failing.
