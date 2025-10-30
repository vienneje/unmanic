
### AMD Hardware Acceleration Transcoding - SMART EDITION

Intelligent video transcoding with AMD GPU/CPU hardware acceleration, automatic optimization, and smart file skipping to save processing time.

---

## 🚀 Quick Start

**Choose Your Experience:**

### 🟢 Easy Mode (Recommended for Beginners)
- Pick hardware: **Auto** / GPU / CPU
- Pick quality: **Fast** / Balanced / Quality / **AV1 Archive**
- Pick format: **MKV** / MP4 / Same as source
- Everything else automatic!

**NEW: AV1 Archive** - Maximum compression without quality loss (RDNA 2+ GPUs)

### 🟡 Advanced Mode (Power Users)
- All detailed settings available
- Preset profiles with clear hardware labels
- Full control over encoding parameters

### 🔴 Expert Mode (Command Line Masters)
- Write custom FFmpeg commands
- Template examples provided
- Variable support: `{input}`, `{output}`, `{render_device}`, `{width}`, `{height}`, `{bitrate}`

---

## ✨ Latest Features (v2.7.16)

### 🎯 Smart Size Prediction (v2.7.16) - **ENABLED BY DEFAULT**
- **NEW**: Test encodes 60s first to predict output size
- **Aborts** if projected savings < 5% (saves hours of wasted time!)
- **Example**: 1.0GB file → Predicts 1.2GB output → Aborts immediately
- **Time cost**: 30-60s test vs hours of pointless full encode
- **Solves**: The "0% reduction" problem permanently
- **Control**: Can disable in Advanced settings if needed

### ⚖️ Quality Adjustment (v2.7.15)
- **IMPROVED**: AV1 Archive CRF changed from 18 to 22 for better compression
- **Result**: More reliable space savings while maintaining excellent quality
- **Quality**: CRF 22 AV1 still provides archival-grade visual quality

### 🔧 Auto-Crop Fix (v2.7.14)
- **FIXED**: Crop detection creating resolutions too small for hardware encoder
- **Minimum**: 128x128 resolution enforced for VAAPI/AMF encoders
- **Result**: Files with extreme letterboxing now encode successfully

### 🔧 Codec Compatibility Fix (v2.7.13)
- **FIXED**: MPEG-4/XVID encoding failures with VAAPI
- **Smart fallback**: Software decode + hardware encode for legacy codecs
- **Works with**: All video formats including XVID, DivX, VC-1, MPEG-1

### 🐛 Critical Bug Fix (v2.7.12)
- **FIXED**: Library-specific settings now correctly applied during encoding
- **Issue**: Worker process wasn't loading per-library configurations
- **Impact**: Easy Mode, AV1 Archive, and custom settings now work properly
- **Upgrade recommended** for all users with custom library settings

### 🎬 AV1 Archive Mode (v2.7.15 - Optimized!)
- **Excellent quality with better compression** - Uses AV1 codec with CRF 22
- **GPU accelerated** - Hardware encoding on RDNA 2+ GPUs (780M, RX 6000/7000)
- **30%+ better compression** than HEVC at same visual quality
- **Perfect for archival** - Long-term storage, large libraries
- **Speed**: ~4-5x realtime encoding on RDNA 3 GPUs
- **Easy Mode**: Select "AV1 Archive" quality preset
- **Updated**: CRF 22 provides better space savings while maintaining archival quality

### 🎯 Smart Skip Logic
- **Cross-codec bitrate check** - Skips well-compressed files regardless of codec
- **Codec efficiency hierarchy** - AV1 > HEVC > H.264 (won't downgrade)
- **Intelligent analysis** - Skip if source ≤ 120% of target optimal bitrate
- **Result**: Eliminates 0% file size reduction transcodes

### 🛡️ Pre-Flight Validation
- Validates files before queueing
- Detects corrupted, 0-byte, or missing files
- Prevents 99% of avoidable failures

### 📊 Auto-Bitrate Optimization
- Resolution-based bitrate targets
- Automatic bitrate cap (prevents bloated files)
- HDR metadata preservation
- 10-bit HEVC support (RDNA 2+)

---

## 🎛️ Preset Profiles

| Preset | Hardware | Speed | Quality | Use Case |
|--------|----------|-------|---------|----------|
| **Fast** | GPU only | ⚡⚡⚡ | Good | Maximum speed |
| **Balanced** ⭐ | Auto GPU/CPU | ⚡⚡ | Great | Recommended |
| **Quality** | CPU only | ⚡ | Excellent | Best quality |
| **Archive** | CPU only | 🐌 | Maximum | Archival storage |

---

## 🖥️ Hardware Support

### AMD GPUs
- **RDNA 3.5** (Radeon 8060S, 800M) - 10-bit HEVC, AV1
- **RDNA 3** (RX 7000, 780M/760M) - 10-bit HEVC, AV1
- **RDNA 2** (RX 6000, 680M) - 10-bit HEVC, AV1
- **RDNA 1** (RX 5000) - 8-bit HEVC
- **GCN 5** (Vega) - 8-bit H.264/HEVC

### AMD CPUs
- All Ryzen series (automatic thread optimization)
- Ryzen AI (8040/7040 series)
- EPYC processors

### Requirements
- FFmpeg 7.0+ with AMD support (Jellyfin FFmpeg 7.1.2+ recommended)
- VAAPI drivers for GPU encoding
- `/dev/dri/renderD128` accessible
- Docker: `viennej/unmanic-amd:latest`

---

## 📊 Bitrate Targets by Resolution

| Resolution | HEVC | H.264 | AV1 |
|------------|------|-------|-----|
| 4K (2160p) | 15 Mbps | 25 Mbps | 10 Mbps |
| 1440p | 8 Mbps | 12 Mbps | 5 Mbps |
| 1080p | 4 Mbps | 6 Mbps | 2.5 Mbps |
| 720p | 2 Mbps | 3 Mbps | 1.5 Mbps |
| 480p | 1 Mbps | 1.5 Mbps | 0.75 Mbps |

Files already within 120% of these targets are automatically skipped!

---

## 🎬 Supported Codecs

### H.265/HEVC (Recommended)
- Best compression ratio
- 8-bit: Main profile (all GPUs)
- 10-bit: Main10 profile (RDNA 2+)
- HDR support (HDR10, HLG)

### H.264/AVC
- Most compatible
- Universal device support
- Fast hardware encoding

### AV1 (Experimental)
- RDNA 2+ hardware support
- 30% better compression than HEVC
- Future-proof codec

### Copy Mode
- No re-encoding (fastest)
- Container changes only

---

## 🎯 Key Features

### Automatic Hardware Detection
- AMD CPU detection (cores, model, threads)
- AMD GPU detection (model, generation, capabilities)
- 10-bit and AV1 capability detection
- Automatic encoder selection

### Smart Processing
- Skip already-optimal files
- Skip files with better source codec
- Pre-flight file validation
- Automatic bitrate optimization

### Video Features
- 10-bit HEVC (auto profile: Main/Main10)
- HDR metadata preservation
- Auto-crop black bars
- Scene detection for CPU encoding

### Audio & Subtitles
- Multi-audio handling (all/first/by language)
- Audio downmix (5.1/7.1 → stereo)
- AAC audio encoding
- Subtitle conversion (SRT/ASS)

### Advanced Options
- Rate control: VBR / CRF / CBR
- Two-pass encoding
- Test duration (encode first N seconds)
- Dry-run mode (preview command)

---

## 💡 Usage Tips

### For Maximum Speed
- Use **Fast** preset (GPU only)
- Choose H.264 codec
- Copy audio (don't re-encode)

### For Best Quality
- Use **Quality** or **Archive** preset (CPU)
- Choose HEVC codec
- Enable scene detection

### For Best Balance ⭐
- Use **Balanced** preset (Auto GPU/CPU)
- Choose HEVC codec
- Let plugin auto-optimize

### For Storage Savings
- Use HEVC or AV1 codec
- Enable auto-bitrate optimization
- Skip already-optimal files enabled

---

## 📈 Version History

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

<details>
<summary>Show older versions</summary>

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

</details>

---

## 🔗 Additional Information

**Author**: viennej
**Version**: 2.7.10
**License**: MIT
**Last Updated**: October 2025

**Docker Image**: `viennej/unmanic-amd:latest`

**⭐ Recommended for:** All AMD GPU/CPU users wanting smart, efficient transcoding!

---

### Need Help?

- Check worker logs for encoding details
- Validation errors appear in library scan logs
- GPU detection logged at job start
- Full changelog available in plugin files
