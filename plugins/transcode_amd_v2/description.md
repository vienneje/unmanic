
### AMD Hardware Acceleration Transcoding

Automatically detects and uses AMD CPU and GPU hardware for optimal video transcoding performance.

---

#### 🎯 Features

- **🔍 Automatic Hardware Detection**
  - Detects AMD CPU (cores, model)
  - Detects AMD GPU (model, vendor ID, driver)
  - Identifies available encoders (AMF, VAAPI, software)

- **🎛️ Flexible Encoding Modes**
  - **Auto**: Intelligently selects GPU or CPU (recommended)
  - **GPU Only**: Forces GPU hardware acceleration
  - **CPU Only**: Forces optimized CPU software encoding

- **🚀 Hardware Accelerated Encoders**
  - **AMF**: h264_amf, hevc_amf (AMD Media Framework)
  - **VAAPI**: h264_vaapi, hevc_vaapi (Video Acceleration API)
  - **Software**: libx264, libx265 (CPU optimized)

- **⚙️ Configurable Settings**
  - Codec selection (H.264, HEVC, or copy)
  - Quality presets (Speed, Balanced, Quality)
  - Bitrate control (target and maximum)
  - Audio codec and bitrate options

---

#### 🖥️ Hardware Support

**AMD CPUs:**
- Ryzen series (all generations)
- EPYC processors
- Automatic thread optimization

**AMD GPUs:**
- RDNA 3.x (RX 7000 series)
- RDNA 2.x (RX 6000 series)
- RDNA 1.x (RX 5000 series)
- Older GCN architectures

**Drivers:**
- amdgpu (open source)
- radeon (legacy)

---

#### 📋 Encoding Modes Explained

**Auto Mode** (Recommended)
- Tries GPU first (AMF → VAAPI)
- Falls back to CPU if GPU unavailable
- Best for general use

**GPU Only Mode**
- Forces hardware acceleration
- Uses AMF or VAAPI encoders
- Frees CPU for other tasks
- May fail on unsupported GPUs

**CPU Only Mode**
- Uses software encoding
- Optimized thread allocation
- Leverages CPU features (AVX, AVX2, AVX512)
- Best quality, slower speed

---

#### 🎬 Supported Codecs

**H.264/AVC**
- Most compatible
- Good quality/size ratio
- Fast hardware encoding
- Recommended for compatibility

**H.265/HEVC**
- Better compression
- Smaller file sizes
- Requires more GPU power
- Best for storage savings

**Copy Mode**
- No re-encoding
- Keeps original codec
- Fastest processing
- No quality loss

---

#### ⚙️ Settings Guide

**Video Quality (Hardware)**
- **Speed**: Fastest encoding, good quality
- **Balanced**: Recommended for most content
- **Quality**: Best quality, slower encoding

**Bitrate Settings**
- **2M-5M**: Standard definition and HD
- **5M-10M**: Full HD (1080p)
- **10M+**: 4K content

**Audio Settings**
- **AAC**: Re-encode audio (recommended)
- **Copy**: Keep original audio (faster)

---

#### 💡 Performance Tips

1. **For Maximum Speed**: 
   - Use GPU Only mode
   - Choose Speed quality
   - Use H.264 codec

2. **For Best Quality**:
   - Use CPU Only mode
   - Choose Quality preset
   - Higher bitrates

3. **For Best Balance**:
   - Use Auto mode
   - Choose Balanced quality
   - Default bitrates (2M/4M)

---

#### 🔍 Hardware Detection

The plugin automatically logs detected hardware:
```
AMD CPU detected: AMD RYZEN AI MAX+ 395 w/ Radeon 8060S
AMD GPU detected: RX 7600 XT (Device 1586)
Mode: auto, Encoder: h264_amf (gpu)
```

Check worker logs to see what hardware is being used!

---

#### 🛠️ Requirements

- **FFmpeg**: Version 4.0 or higher with AMD support
- **Drivers**: amdgpu or radeon kernel modules
- **Linux**: Proper /dev/dri devices
- **Jellyfin FFmpeg**: Recommended for best AMD support

---

#### 📚 Additional Information

This plugin is designed to work with the enhanced Unmanic AMD Docker images that include:
- Jellyfin FFmpeg 7.1.2+
- LLVM 21+ for optimal AMD GPU support
- Proper AMD driver integration

For best results, use the `viennej/unmanic-amd:latest` Docker image.

---

**Author**: viennej  
**Version**: 2.0.1  
**License**: MIT
