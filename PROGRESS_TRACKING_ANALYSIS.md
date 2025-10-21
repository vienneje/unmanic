# Progress Tracking Analysis for AMD Transcode Plugin

## Summary

After analyzing the Unmanic plugin system and comparing our `transcode_amd_v2` plugin with the official `video_transcoder` plugin, I've identified the issue with progress tracking and ETC (Estimated Time to Completion).

## Current Situation

### Our Plugin (transcode_amd_v2 v2.1.8)
```python
# Line 376 in plugin.py
data['exec_command'] = cmd

# Note: Lines 378-380 explain we're NOT setting a custom parser
# We're relying on Unmanic's built-in FFmpeg progress detection
```

**Problem**: We're not setting `data['command_progress_parser']`, which means:
- Unmanic uses its default progress parser
- The default parser expects simple numeric percentages in the output
- FFmpeg doesn't output simple percentages - it outputs complex progress lines

### video_transcoder Plugin Approach
```python
# Line 282-284 in plugin.py
parser = Parser(logger)
parser.set_probe(probe)
data['command_progress_parser'] = parser.parse_progress
```

**The `Parser` class** comes from `video_transcoder.lib.ffmpeg` and:
1. Uses FFprobe data to get the total duration of the video
2. Parses FFmpeg's progress output (lines like `frame=1234 fps=30 time=00:01:23.45 ...`)
3. Calculates percentage based on `current_time / total_duration * 100`
4. Returns progress dict with percentage, allowing Unmanic to show progress bar and ETC

## How Unmanic's Progress System Works

### 1. Default Progress Parser
Located in `unmanic/libs/workers.py` (line 268):
```python
def default_progress_parser(self, line_text, pid=None, proc_start_time=None, unset=False):
    # ... tries to parse line_text as a float percentage
    stripped_text = str(line_text).strip()
    text_float = float(stripped_text)
    self.subprocess_percent = int(text_float)
```

**This explains why we see no progress**:
- FFmpeg outputs: `frame=  123 fps= 30 q=28.0 size=    2048kB time=00:00:05.12 bitrate=3276.8kbits/s speed=1.02x`
- Default parser tries to parse this as a float → FAILS
- No progress is reported → No progress bar, no ETC

### 2. Custom Progress Parser (needed for FFmpeg)
The parser must:
1. **Extract the current time** from FFmpeg output (the `time=HH:MM:SS.MS` part)
2. **Know the total duration** of the video (from FFprobe)
3. **Calculate percentage**: `(current_time / total_duration) * 100`
4. **Return a dict**: `{'percent': calculated_percent, 'paused': False, 'killed': False}`

### 3. FFmpeg Progress Output Format
FFmpeg outputs progress information like this:
```
frame=  456 fps= 29 q=28.0 Lsize=   12345kB time=00:01:23.45 bitrate=1234.5kbits/s speed=1.5x
```

We need to:
- Parse the `time=HH:MM:SS.MS` value
- Convert it to seconds
- Divide by total duration to get percentage

## Solution: Implement FFmpeg Progress Parser

We need to create a custom progress parser that:
1. Gets the video duration using FFprobe before transcoding
2. Parses FFmpeg's `time=` output to track current position
3. Calculates and returns the completion percentage

### Implementation Plan

```python
def parse_ffmpeg_progress(self, line_text, total_duration_seconds, pid=None, proc_start_time=None, unset=False):
    """
    Parse FFmpeg progress output and calculate percentage completion.
    
    Args:
        line_text: FFmpeg output line
        total_duration_seconds: Total video duration in seconds (from FFprobe)
        pid: Process ID (for initial registration)
        proc_start_time: Process start time (for initial registration)
        unset: If True, unregister the process
    
    Returns:
        Dict with 'percent', 'paused', 'killed' keys
    """
    # Handle process registration/unregistration
    if unset:
        # Unset the process (it's completed)
        return {'percent': 100, 'paused': False, 'killed': False}
    
    if pid is not None and proc_start_time is not None:
        # Register the process (initial call)
        return {'percent': 0, 'paused': False, 'killed': False}
    
    # Parse FFmpeg output for time information
    # Example: "time=00:01:23.45" → convert to seconds → calculate percentage
    import re
    
    # Look for time= in the output
    time_match = re.search(r'time=(\d+):(\d+):(\d+)\.(\d+)', str(line_text))
    if time_match and total_duration_seconds > 0:
        hours = int(time_match.group(1))
        minutes = int(time_match.group(2))
        seconds = int(time_match.group(3))
        centiseconds = int(time_match.group(4))
        
        current_seconds = hours * 3600 + minutes * 60 + seconds + centiseconds / 100.0
        percent = min(99, int((current_seconds / total_duration_seconds) * 100))
        
        return {'percent': percent, 'paused': False, 'killed': False}
    
    # If we can't parse, return current state
    return {'percent': 0, 'paused': False, 'killed': False}
```

## Why video_transcoder Has This Working

The `video_transcoder` plugin imports `Parser` and `Probe` from `video_transcoder.lib.ffmpeg`, but these files are missing in the repository. This suggests:

1. **They're dynamically generated** during plugin installation
2. **They're part of a separate package** that gets installed
3. **The plugin bundles them** but they weren't in the git clone

Most likely, the `Parser` class is similar to what I've described above - it:
- Uses FFprobe to get duration
- Parses FFmpeg time output
- Calculates percentage

## Recommended Fix for transcode_amd_v2

### Option 1: Implement Custom Parser (Recommended)
Add a custom FFmpeg progress parser to our plugin that:
1. Uses FFprobe to get video duration before encoding
2. Parses FFmpeg's `time=` output
3. Calculates completion percentage
4. Sets `data['command_progress_parser']` to this custom function

**Pros**:
- Full control over progress tracking
- Can add custom logging/metrics
- No external dependencies

**Cons**:
- More code to maintain
- Need to handle edge cases (unknown duration, live streams, etc.)

### Option 2: Use video_transcoder's Parser (If Available)
Try to import and use the `Parser` class from `video_transcoder` plugin if it's installed.

**Pros**:
- Battle-tested code
- Handles edge cases

**Cons**:
- Requires video_transcoder plugin to be installed
- Dependency on external plugin
- May break if video_transcoder changes

### Option 3: Keep Current Approach (Not Recommended)
Continue relying on Unmanic's default parser.

**Cons**:
- No progress bar
- No ETC
- Poor user experience

## Next Steps

1. **Implement Option 1**: Create a custom FFmpeg progress parser
2. **Test thoroughly**: Ensure it works with various video files
3. **Update plugin version**: Bump to v2.1.9
4. **Update changelog**: Document the progress tracking fix
5. **Deploy and test**: Push to Docker Hub and test on both local and Zeus systems

## Additional Notes

### FFprobe Command to Get Duration
```bash
ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 input.mkv
```

This returns the duration in seconds (e.g., `7845.123000`).

### Why ETC is Empty
ETC (Estimated Time to Completion) is calculated by Unmanic based on:
- Current progress percentage
- Time elapsed since process start
- Simple formula: `time_remaining = (time_elapsed / percent) * (100 - percent)`

Without progress percentage, Unmanic can't calculate ETC, hence it shows as empty.

### Testing Progress Tracking
To verify progress tracking works:
1. Start a transcoding job
2. Monitor the Unmanic web UI
3. Check for:
   - Progress bar showing 0-100%
   - ETC showing estimated completion time
   - Progress updates in real-time (every few seconds)
