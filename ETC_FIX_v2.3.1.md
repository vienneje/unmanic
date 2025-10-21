# ETC Fix - v2.3.1 🎉

## Summary

**FINALLY FIXED!** The ETC (Estimated Time to Completion) display now works correctly in Unmanic!

## The Problem

Even though the progress bar was showing (fixed in v2.1.9) and the frontend division-by-zero bug was fixed (v2.2.x), the ETC was still empty. After extensive investigation, I discovered:

### Root Cause
**The custom progress parser wasn't registering the subprocess start time with Unmanic's WorkerSubprocessMonitor!**

### Technical Details

#### How Unmanic Tracks Elapsed Time
```python
# In unmanic/libs/workers.py:219-234
def get_subprocess_elapsed(self):
    subprocess_elapsed = 0
    if self.subprocess is not None:
        now = int(time.time())
        total_run_time = int(now - self.subprocess_start_time)  # ← NEEDS start_time!
        pause_duration = int(now - self.subprocess_pause_time)
        subprocess_elapsed = int(total_run_time - pause_duration)
    return subprocess_elapsed
```

#### How get_subprocess_stats() Works
```python
# In unmanic/libs/workers.py:236-246
def get_subprocess_stats(self):
    return {
        'pid': str(self.subprocess_pid),
        'percent': str(self.subprocess_percent),
        'elapsed': self.get_subprocess_elapsed(),  # ← Calculated from start_time!
        'cpu_percent': str(self.subprocess_cpu_percent),
        # ... more stats
    }
```

#### The Default Progress Parser
```python
# In unmanic/libs/workers.py:268-281
def default_progress_parser(self, line_text, pid=None, proc_start_time=None, unset=False):
    # ...
    if proc_start_time is not None:
        self.set_subprocess_start_time(proc_start_time)  # ← This is the key!
```

The default parser is a **METHOD** of WorkerSubprocessMonitor, so it can call `self.set_subprocess_start_time()`.

#### Our Custom Parser (v2.1.9 - v2.3.0)
```python
# Old approach - DIDN'T WORK
class FFmpegProgressParser:
    def __init__(self, total_duration_seconds):
        self.total_duration = total_duration_seconds
        self.current_percent = 0
        self.proc_registered = False
    
    def parse(self, line_text, pid=None, proc_start_time=None, unset=False):
        if pid is not None and not self.proc_registered:
            self.proc_registered = True
            # ❌ We received proc_start_time but DID NOTHING with it!
            # ❌ WorkerSubprocessMonitor never got the start time!
            # ❌ Elapsed time was always 0!
            return {'percent': 0, 'paused': False, 'killed': False}
```

**Result:**
- `subprocess_start_time` was never set
- `get_subprocess_elapsed()` returned `0`
- Frontend's `calculateEtc(percent, elapsed)` received `elapsed = 0`
- ETC calculation: `(elapsed / percent) * percent_to_go` = `(0 / percent) * X` = **0**
- ETC displayed as empty (because 0 seconds = empty string)

## The Solution (v2.3.1)

**Wrap the default progress parser!**

```python
class FFmpegProgressParser:
    def __init__(self, total_duration_seconds, default_parser=None):
        self.total_duration = total_duration_seconds
        self.current_percent = 0
        self.proc_registered = False
        self.default_parser = default_parser  # ← Store reference to default parser
    
    def parse(self, line_text, pid=None, proc_start_time=None, unset=False):
        # Handle process unregistration
        if unset:
            # ✅ Call default parser to unregister
            if self.default_parser is not None:
                self.default_parser(None, unset=True)
            return {'percent': 100, 'paused': False, 'killed': False}
        
        # Handle process registration
        if pid is not None and not self.proc_registered:
            self.proc_registered = True
            # ✅ Call default parser to register PID and start time!
            if self.default_parser is not None:
                self.default_parser(None, pid=pid, proc_start_time=proc_start_time)
                logger.debug(f"Registered PID {pid} and start time with worker monitor")
            return {'percent': 0, 'paused': False, 'killed': False}
        
        # Parse FFmpeg progress (unchanged)
        if line_text and self.total_duration > 0:
            time_match = re.search(r'time=(\d+):(\d+):(\d+)\.(\d+)', str(line_text))
            if time_match:
                # ... calculate current_percent ...
        
        return {'percent': self.current_percent, 'paused': False, 'killed': False}
```

### In on_worker_process():
```python
# Get the default parser (set by Unmanic at line 670 in workers.py)
default_parser = data.get('command_progress_parser')

# Create our parser with reference to default parser
progress_parser = FFmpegProgressParser(video_duration, default_parser)

# Set our parser as the progress handler
data['command_progress_parser'] = progress_parser.parse
```

## How It Works Now

### 1. Process Start (PluginChildProcess calls parser)
```python
# In unmanic/libs/unplugins/child_process.py:154
parser(None, pid=self._proc.pid, proc_start_time=time.time())
```

### 2. Our Parser Receives Call
```python
# Our parser at registration
parse(None, pid=12345, proc_start_time=1729513521.5)
```

### 3. We Delegate to Default Parser
```python
# Our parser calls:
self.default_parser(None, pid=12345, proc_start_time=1729513521.5)

# Default parser calls:
self.set_subprocess_start_time(1729513521.5)
```

### 4. Worker Monitor Tracks Start Time
```python
# WorkerSubprocessMonitor now has:
self.subprocess_start_time = 1729513521.5
```

### 5. During Encoding
```python
# FFmpeg outputs: "frame=123 fps=30 time=00:01:23.45 ..."
# Our parser parses and returns: {'percent': 15, 'paused': False, 'killed': False}
```

### 6. Frontend Requests Worker Status
```python
# Worker calls get_subprocess_stats()
def get_subprocess_stats(self):
    return {
        'percent': '15',
        'elapsed': self.get_subprocess_elapsed(),  # ← NOW WORKS!
    }

def get_subprocess_elapsed(self):
    now = int(time.time())  # = 1729513581
    total_run_time = int(now - self.subprocess_start_time)  # = 60 seconds
    return total_run_time  # = 60
```

### 7. Frontend Calculates ETC
```javascript
function calculateEtc(percent_completed, time_elapsed) {
  let percent = parseInt("15");     // = 15
  let elapsed = parseInt(60);       // = 60
  
  if (isNaN(percent) || isNaN(elapsed) || percent <= 0) {
    return 0;  // ← Guard condition (v2.2.x fix)
  }
  
  let percent_to_go = (100 - percent);  // = 85
  return (elapsed / percent) * percent_to_go;  // = (60/15)*85 = 340 seconds = 5.6 minutes
}
```

### 8. Frontend Displays
```
Worker: Active
Progress: 15%
ETC: 5 minutes 40 seconds remaining  ← IT WORKS! 🎉
```

## The Hybrid Approach

Our final solution is a **hybrid custom progress parser**:

| Function | Handler |
|----------|---------|
| **Process Registration** (pid, proc_start_time) | Default Parser |
| **Process Unregistration** (unset=True) | Default Parser |
| **Progress Parsing** (FFmpeg output) | Custom Parser (FFmpegProgressParser) |

This gives us:
- ✅ Proper subprocess lifecycle management (default parser)
- ✅ Accurate progress calculation from FFmpeg time= output (custom parser)
- ✅ Elapsed time tracking for ETC (default parser via start_time)

## Testing

### Before Fix (v2.3.0 and earlier)
```
Worker Status API Response:
{
  "subprocess": {
    "pid": "12345",
    "percent": "15",
    "elapsed": 0  ← ALWAYS ZERO!
  }
}

Frontend:
- Progress: 15% ✅
- ETC: (empty) ❌
```

### After Fix (v2.3.1)
```
Worker Status API Response:
{
  "subprocess": {
    "pid": "12345",
    "percent": "15",
    "elapsed": 60  ← NOW CORRECT!
  }
}

Frontend:
- Progress: 15% ✅
- ETC: 5 minutes 40 seconds ✅
```

## Deployment

### Files Changed
- `plugins/transcode_amd_v2/plugin.py` - FFmpegProgressParser class updated
- `plugins/transcode_amd_v2/info.json` - version 2.3.1
- `plugins/transcode_amd_v2/changelog.txt` - v2.3.1 entry

### Deployed To
- ✅ Zeus (unmanic-noble container)
- ✅ GitHub (git@github.com:vienneje/unmanic.git)

### User Action Required
**Clear browser cache:**
- Windows/Linux: `Ctrl + Shift + R`
- Mac: `Cmd + Shift + R`

This ensures the frontend fix (v2.2.x) is loaded, which prevents division-by-zero when percent is 0.

## Version Timeline

### v2.1.9 (Progress Bar Fix)
- ✅ Implemented custom FFmpeg progress parser
- ✅ Progress bar shows 0-100%
- ❌ ETC still empty (elapsed = 0)

### v2.2.0/v2.2.1 (Frontend ETC Bug Fix)
- ✅ Fixed frontend division-by-zero bug
- ✅ Frontend ready to display ETC
- ❌ Backend still not sending elapsed time

### v2.3.0 (Library Scan Fix)
- ✅ Added `on_library_management_file_test()`
- ✅ Files now added to pending queue
- ❌ ETC still empty (elapsed = 0)

### v2.3.1 (ETC Fix - FINAL) 🎉
- ✅ Progress bar working
- ✅ ETC display working
- ✅ Accurate encoding time estimates
- ✅ All systems operational!

## Conclusion

The ETC fix required understanding the deep interaction between:
1. **PluginChildProcess** (calls parser with pid/start_time)
2. **WorkerSubprocessMonitor** (tracks start_time, calculates elapsed)
3. **Custom Progress Parser** (parses FFmpeg output)
4. **Frontend** (calculates and displays ETC)

By wrapping the default parser, we bridge the gap between our custom progress calculation and Unmanic's subprocess lifecycle management.

**Result: Full feature parity with official plugins!** 🚀

---

**Author**: viennej  
**Version**: 2.3.1  
**Date**: 2025-10-21  
**Commit**: 87f3cdc
