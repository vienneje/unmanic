
### AMD Hardware Acceleration Transcoding - SMART EDITION

Automatically detects and uses AMD CPU and GPU hardware for optimal video transcoding performance with intelligent file validation and processing.

---

#### 🎯 NEW in v2.7.0: Enhanced Easy & Expert Modes

**Even easier for beginners, more powerful for experts!**

- **🟢 Easy Mode** - For Beginners (Enhanced!)
  - Pick your hardware: GPU / CPU / Auto
  - **NEW: Pick your quality: Fast / Balanced / Quality**
  - **NEW: Choose output format: MKV / MP4 / Same as source**
  - Everything else uses optimal defaults
  - Automatic: HDR preservation, auto-crop, AAC audio, HEVC codec
  - Perfect for "set it and forget it"

- **🟡 Advanced Mode** - For Power Users
  - All the detailed settings you know and love
  - Preset profiles: Fast/Balanced/Quality/Archive
  - Shows which hardware each preset uses!
  - **NEW: Output container selection**
  - Full control over every encoding parameter

- **🔴 Expert Mode** - For Command Line Masters (Enhanced!)
  - **NEW: Command templates dropdown** (GPU HEVC, CPU HEVC, H.264, AV1)
  - **NEW: Extended variables**
    - `{input}`, `{output}`, `{render_device}`
    - `{width}`, `{height}`, `{bitrate}`, `{duration}`, `{codec}`
  - Write your own custom FFmpeg command
  - Complete freedom for unique workflows
  - Example: `ffmpeg -vaapi_device {render_device} -i {input} -vf scale={width}:-1 -c:v hevc_vaapi {output}`

**Preset profiles now clearly show hardware:**
- Fast **[GPU only]** - Maximum speed
- Balanced **[Auto GPU/CPU]** - Recommended
- Quality **[CPU only]** - Better quality
- Archive **[CPU only]** - Maximum quality

---

#### 🚀 NEW in v2.5.1: Smart Processing

- **🛡️ Pre-Flight File Validation**
  - Automatically validates files before queueing
  - Prevents failures from corrupted or 0-byte files
  - Categorizes errors (FILE_NOT_FOUND, FILE_CORRUPTED, FILE_TIMEOUT)
  - Saves time by skipping problematic files early

- **🎯 Skip Already Optimal Files**
  - Analyzes bitrate vs resolution to determine if re-encoding needed
  - Skips files already well-compressed (within 120% of optimal)
  - Prevents unnecessary processing and quality degradation
  - Saves hours of wasted encoding time

- **📊 Better Logging & Error Reporting**
  - Clear categorized warnings for skipped files
  - Detailed reasons for each skip decision
  - Easy troubleshooting and debugging

---

#### 🎯 Core Features (v2.4.x)

- **🔍 Automatic Hardware Detection**
  - Detects AMD CPU (cores, model, threads)
  - Detects AMD GPU (model, generation, capabilities)
  - Identifies GPU generation (RDNA 3.5, RDNA 3, RDNA 2, RDNA 1, GCN)
  - Determines 10-bit HEVC and AV1 hardware support

- **🎛️ Preset Profiles**
  - **Fast**: GPU-only encoding for maximum speed
  - **Balanced**: GPU with CPU fallback (recommended)
  - **Quality**: CPU encoding for best quality
  - **Archive**: Maximum quality preservation

- **🎬 Advanced Video Support**
  - **10-bit HEVC**: Automatic profile detection (Main/Main10)
  - **HDR Metadata**: Preserves HDR10, HLG, color space
  - **AV1 Codec**: Hardware encoding on RDNA 2+
  - **Auto-Crop**: Detects and removes black bars

- **🎵 Audio & Subtitle Handling**
  - **Multi-Audio**: Keep all, first, or by language
  - **Audio Downmix**: Convert 5.1/7.1 to stereo
  - **Subtitle Formats**: Copy, SRT, or ASS conversion

- **⚙️ Smart Encoding Options**
  - **Rate Control**: VBR, CRF (quality-based), or CBR
  - **Auto-Bitrate**: Resolution-based optimization
  - **Scene Detection**: Adaptive quality for CPU encoding
  - **Two-Pass**: Optional multi-pass encoding

- **🧪 Testing & Debug Features**
  - **Dry-Run Mode**: Preview FFmpeg command
  - **Test Duration**: Encode only first N seconds
  - **Comprehensive Validation**: Pre-flight parameter checks

---

#### 🖥️ Hardware Support

**AMD GPUs:**
- **RDNA 3.5** (Radeon 8060S, 800M series) - 10-bit HEVC, AV1
- **RDNA 3** (RX 7000, 780M/760M) - 10-bit HEVC, AV1
- **RDNA 2** (RX 6000, 680M) - 10-bit HEVC, AV1
- **RDNA 1** (RX 5000) - 8-bit only
- **GCN 5** (Vega) - 8-bit H.264/HEVC

**AMD CPUs:**
- Ryzen series (all generations)
- Ryzen AI (8040/7040 series)
- EPYC processors
- Automatic thread optimization

**Drivers:**
- amdgpu (modern, recommended)
- VAAPI support required for GPU encoding
- Jellyfin FFmpeg 7.x+ recommended

---

#### 📋 Encoding Modes Explained

**Auto Mode** (Recommended)
- Intelligently selects GPU or CPU
- Tries VAAPI → AMF → CPU fallback
- Handles 10-bit automatically
- Best for most users

**GPU Only Mode**
- Forces hardware acceleration
- Uses VAAPI or AMF encoders
- Frees CPU for other tasks
- Fails if GPU unavailable/incompatible

**CPU Only Mode**
- Uses libx265/libx264
- Optimized thread allocation
- Scene detection support
- Best quality, slower speed

---

#### 🎬 Supported Codecs & Profiles

**H.265/HEVC** (Recommended)
- 8-bit: Main profile (all GPUs)
- 10-bit: Main10 profile (RDNA 2+)
- Best compression ratio
- Smaller files, great quality

**H.264/AVC**
- Most compatible codec
- Good quality/size ratio
- Fast hardware encoding
- Universal device support

**AV1** (Experimental)
- RDNA 2+ hardware support
- Best compression (30% better than HEVC)
- Future-proof codec
- Limited device support currently

**Copy Mode**
- No re-encoding
- Fastest processing
- No quality loss
- Useful for container changes only

---

#### 💡 Preset Profiles Guide

**Fast Preset**
- GPU-only encoding
- VBR rate control
- Auto-bitrate optimization
- Copy audio for speed
- **Use when**: Speed is priority

**Balanced Preset** ⭐ (Recommended)
- Auto GPU/CPU selection
- VBR rate control
- Auto-bitrate optimization
- AAC audio re-encode
- HDR preservation
- **Use when**: Good balance needed

**Quality Preset**
- CPU-only encoding
- CRF quality mode (CRF 20)
- Medium preset
- All audio tracks preserved
- HDR preservation
- **Use when**: Quality > speed

**Archive Preset**
- CPU-only encoding
- CRF 18 (very high quality)
- Scene detection enabled
- Maximum preservation
- **Use when**: Archival quality needed

---

#### 📊 Resolution-Based Bitrate Targets

The plugin automatically optimizes bitrates based on resolution:

| Resolution | HEVC | H.264 | AV1 |
|------------|------|-------|-----|
| **4K (2160p)** | 15 Mbps | 25 Mbps | 10 Mbps |
| **1440p** | 8 Mbps | 12 Mbps | 5 Mbps |
| **1080p** | 4 Mbps | 6 Mbps | 2.5 Mbps |
| **720p** | 2 Mbps | 3 Mbps | 1.5 Mbps |
| **480p** | 1 Mbps | 1.5 Mbps | 0.75 Mbps |

Files already within 120% of these targets are automatically skipped!

---

#### 🛡️ File Validation (v2.5.1)

**Automatic Checks:**
1. File exists and accessible
2. File size > 0 bytes
3. File size > 100KB minimum
4. FFprobe can read file
5. File has valid duration (> 1 second)

**Error Categories:**
- **FILE_NOT_FOUND**: File doesn't exist or was deleted
- **FILE_CORRUPTED**: 0 bytes, too small, or damaged
- **FILE_TIMEOUT**: FFprobe timeout (likely corrupted)
- **FILE_ERROR**: Permission or access issues

**Benefits:**
- ✅ Prevents 99% of avoidable failures
- ✅ Cleaner queue (no bad files)
- ✅ Better log clarity
- ✅ Saves processing time

---

#### 🎯 Skip Optimal Files (v2.5.1)

**How It Works:**
1. Checks if file is already target codec
2. Analyzes current bitrate
3. Compares to optimal for resolution
4. Skips if ≤ 120% of optimal

**Example:**
```
File: movie.mkv (1080p)
Current: HEVC @ 4.5 Mbps
Optimal: HEVC @ 4.0 Mbps
Decision: SKIP (4.5 ≤ 4.8 [120%])
```

**Benefits:**
- ✅ Don't re-encode already-good files
- ✅ Prevent quality degradation
- ✅ Save hours of processing
- ✅ Focus on files that need work

---

#### 💡 Performance Tips

**For Maximum Speed**:
- Use **Fast** preset (GPU only)
- Choose H.264 codec
- Lower bitrates
- Copy audio

**For Best Quality**:
- Use **Quality** or **Archive** preset (CPU)
- Choose HEVC codec
- Higher bitrates or CRF mode
- Scene detection enabled

**For Best Balance**: ⭐
- Use **Balanced** preset (Auto GPU/CPU)
- Choose HEVC codec
- Auto-bitrate enabled
- Let plugin optimize

**For Storage Savings**:
- Use HEVC or AV1
- CRF mode (quality-based)
- Auto-bitrate optimization
- Skip already-optimal files

---

#### 🔍 Hardware Detection Examples

The plugin automatically logs detected hardware:

```
AMD GPU detected: Radeon 780M (RDNA 3, gfx1150)
GPU supports 10-bit HEVC encoding
Mode: auto, Encoder: hevc_vaapi (gpu)
```

```
AMD GPU detected: RX 7900 XTX (RDNA 3, gfx1100)
GPU supports 10-bit HEVC and AV1 encoding
Mode: gpu_only, Encoder: hevc_vaapi (gpu)
```

```
GPU not available, using CPU fallback
Mode: auto, Encoder: libx265 (cpu)
```

Check worker logs to see what hardware is being used!

---

#### 🛠️ Requirements

**Software:**
- FFmpeg 7.0+ with AMD support
- Jellyfin FFmpeg 7.1.2+ (recommended)
- VAAPI drivers for GPU encoding

**Hardware:**
- AMD GPU (any generation)
- /dev/dri/renderD128 accessible
- amdgpu kernel module loaded

**Docker:**
- Use `viennej/unmanic-amd:latest` or similar
- GPU passthrough configured
- Proper device permissions

---

#### 📚 Advanced Settings

**Rate Control Modes:**
- **VBR** (Variable Bitrate): Best for GPU, good quality/size
- **CRF** (Constant Rate Factor): Best for CPU, quality-based
- **CBR** (Constant Bitrate): Predictable file sizes

**Audio Options:**
- **Mode**: all, first, best, or by language
- **Codec**: AAC, copy, or passthrough
- **Bitrate**: 128k-320k
- **Channels**: Stereo or 5.1/7.1
- **Downmix**: Convert multichannel to stereo

**Subtitle Options:**
- **Copy**: Keep original format
- **SRT**: Convert to SubRip
- **ASS**: Convert to Advanced SubStation

**Advanced Features:**
- Auto-crop black bars (threshold: >5%)
- Scene detection for CPU encoding
- Test encoding (first N seconds)
- Dry-run mode (preview command)
- Skip 10-bit files option

---

#### 📈 Version History

**v2.7.10** (2025-10-29) - CROSS-CODEC BITRATE CHECK
- Fixed: Bitrate check now applies to ALL codecs (H.264, HEVC, AV1)
- Enhanced: Well-compressed H.264 files are now skipped instead of wastefully re-encoded
- Example: H.264 at 2.1 Mbps (below HEVC 4.0 Mbps target) won't be re-encoded
- Logic: Skip if source bitrate ≤ 120% of target codec's optimal bitrate
- Impact: Eliminates 0% file size reduction transcodes

**v2.7.9** (2025-10-29) - CODEC EFFICIENCY HIERARCHY
- New: Skip AV1 files when targeting HEVC (AV1 is more efficient)
- Codec efficiency ranking: AV1 (best) > HEVC > H.264 (least efficient)
- Prevents wasteful transcoding from better to worse codecs
- Saves hours of processing time on modern streaming service encodes

**v2.7.8** (2025-10-29) - ENHANCED BITRATE DETECTION
- Fixed: Bitrate detection with fallback calculation when stream bitrate unavailable
- Calculates from file size/duration for files without bitrate metadata
- Ensures bitrate cap applies correctly to all files (remuxes, etc.)

**v2.7.7** (2025-10-28) - PREVENT BLOATED FILES
- Added: Automatic bitrate cap at 1.5x source bitrate for CRF/VBR modes
- Fixed: GPU constant quality mode could exceed source bitrate by 2-3x
- Protects against "Reject File if Larger than Original" failures

**v2.7.6** (2025-10-28) - SKIP EFFICIENT FILES
- Fixed: is_already_optimal() now correctly uses video-only bitrate
- Prevents re-encoding well-compressed files that would result in larger output
- Saves hours of processing time on already-optimized content

**v2.7.5** (2025-10-27) - COMPLETED TASKS FIX
- Fixed: file_out path not being updated when changing output container
- All completed transcodes now properly appear in history/stats panels

**v2.7.4** (2025-10-27) - COVER ART FIX V2
- Fixed: Cover art handling for files with multiple video streams
- Improved stream mapping logic for complex media files

**v2.7.3** (2025-10-26) - UI BUG FIX
- Fixed: Duplicate labels in Easy Mode quality selector
- Improved UI clarity for beginners

**v2.7.2** (2025-10-26) - ENHANCED MODES
- Improved Easy/Expert mode UI organization
- Better preset profile descriptions
- More intuitive configuration options

**v2.7.1** (2025-10-25) - CRITICAL FIX
- Fixed: Attached pictures (cover art) causing encoding failures
- Stream mapping now excludes MJPEG cover art
- Prevents conversion errors with embedded poster images

**v2.7.0** (2025-10-23) - ENHANCED EASY & EXPERT MODES
- Easy Mode: Quality selector (Fast/Balanced/Quality)
- Output container selection (MKV/MP4/Same)
- Expert Mode: Command templates dropdown
- Expert Mode: Extended variables (width, height, bitrate, duration, codec)
- More flexible encoding options

**v2.6.2** (2025-10-23) - THREE-TIER CONFIGURATION (Improved)
- Expert Mode now has helpful default command pre-filled
- Shows Easy Mode equivalent as starting point
- Variables clearly labeled in field description

**v2.6.1** (2025-10-23) - THREE-TIER CONFIGURATION (Fixed)
- Fixed: Conditional settings display working correctly
- Easy Mode properly hides advanced settings
- Advanced Mode shows all settings
- Expert Mode properly hides everything except command field

**v2.6.0** (2025-10-23) - THREE-TIER CONFIGURATION
- Easy Mode for beginners (just pick hardware)
- Expert Mode for command-line control
- Preset profiles show hardware usage
- Better UI organization

**v2.5.1** (2025-10-23) - SMART EDITION
- Pre-flight file validation
- Skip already optimal files
- Smart bitrate analysis
- Better error categorization

**v2.4.2** (2025-10-23)
- GPU detection for Radeon 780M/760M (Phoenix APU)
- Added device ID 150e to RDNA 3 list

**v2.4.0** - COMPREHENSIVE EDITION
- 10-bit HEVC support
- HDR metadata preservation
- Preset profiles system
- Multi-audio/subtitle handling
- AV1 codec support
- GPU capability detection
- Resolution-based bitrate optimization

---

#### 🎓 Quick Start Guide

**Choose Your Experience Level:**

**🟢 Beginners - Easy Mode (Recommended)**
1. Install plugin in Unmanic
2. Set "Configuration Mode" to **Easy**
3. Pick your hardware:
   - **Auto** (recommended) - Let plugin decide GPU/CPU
   - **GPU** - Force hardware acceleration
   - **CPU** - Force software encoding
4. Done! Everything else is automatic

**🟡 Power Users - Advanced Mode**
1. Install plugin in Unmanic
2. Set "Configuration Mode" to **Advanced**
3. Select Preset:
   - Fast [GPU only] → Maximum speed
   - Balanced [Auto] → Recommended
   - Quality [CPU only] → Best quality
   - Archive [CPU only] → Maximum quality
4. Optionally customize individual settings

**🔴 Experts - Expert Mode**
1. Install plugin in Unmanic
2. Set "Configuration Mode" to **Expert**
3. Write custom FFmpeg command
4. Use variables: `{input}`, `{output}`, `{render_device}`
5. Example:
   ```
   ffmpeg -vaapi_device {render_device} -hwaccel vaapi -i {input} -c:v hevc_vaapi -qp 20 -c:a aac {output}
   ```

The plugin automatically:
- ✅ Validates all files
- ✅ Skips corrupted files
- ✅ Skips optimal files
- ✅ Chooses best encoder (Easy/Advanced modes)
- ✅ Optimizes settings (Easy/Advanced modes)

---

#### 🔗 Additional Resources

**Documentation:**
- Full changelog in plugin files
- Detailed logs in Unmanic UI
- Error messages are self-explanatory

**Docker Images:**
- `viennej/unmanic-amd:latest` (recommended)
- Includes Jellyfin FFmpeg 7.x
- LLVM 21+ for optimal AMD support

**Support:**
- Check worker logs for encoding details
- Validation errors appear in library scan logs
- GPU detection logged at job start

---

**Author**: viennej
**Version**: 2.7.10
**License**: MIT
**Last Updated**: October 2025

**⭐ Recommended for:** All AMD GPU/CPU users wanting smart, efficient transcoding!
