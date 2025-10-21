# Transcode AMD v2 - Hardware Acceleration Plugin

Comprehensive AMD hardware acceleration plugin for Unmanic with automatic CPU and GPU detection.

## Overview

This plugin automatically detects your AMD hardware (CPU and GPU) and uses the most appropriate encoder for video transcoding. It supports AMD's AMF (Advanced Media Framework) and VAAPI (Video Acceleration API) hardware encoders, with intelligent fallback to optimized CPU software encoding.

## Features

### Hardware Detection
- **AMD CPU Detection**: Automatically detects AMD processors, core count, and supported instruction sets (AVX, AVX2, AVX512, etc.)
- **AMD GPU Detection**: Detects AMD graphics cards, driver type (amdgpu/radeon), and available hardware encoders
- **Encoder Detection**: Automatically identifies available FFmpeg encoders (AMF, VAAPI, software)

### Encoding Modes
1. **Auto Mode** (Default)
   - Intelligent selection: GPU (AMF) → GPU (VAAPI) → CPU (Software)
   - Best for general use cases
   - Automatic fallback on errors

2. **GPU Only Mode**
   - Forces GPU hardware acceleration
   - Uses AMF or VAAPI encoders
   - Reduces CPU load
   - May fail if GPU unavailable

3. **CPU Only Mode**
   - Forces software encoding
   - Optimized thread usage (cores - 1)
   - Leverages CPU features (AVX, etc.)
   - Best quality output

### Supported Encoders

#### GPU Encoders (Hardware Acceleration)
| Encoder | Description | Performance |
|---------|-------------|-------------|
| `h264_amf` | AMD AMF H.264 | Fastest |
| `hevc_amf` | AMD AMF HEVC | Very Fast |
| `h264_vaapi` | VAAPI H.264 | Fast |
| `hevc_vaapi` | VAAPI HEVC | Fast |

#### CPU Encoders (Software)
| Encoder | Description | Quality |
|---------|-------------|---------|
| `libx264` | x264 H.264 | Excellent |
| `libx265` | x265 HEVC | Excellent |

### Codec Support
- **H.264/AVC**: Most compatible, good quality/size ratio
- **H.265/HEVC**: Better compression, smaller files
- **Copy**: No re-encoding, preserves original codec

## Installation

### Prerequisites
- Unmanic with plugin support
- FFmpeg 4.0+ with AMD support (Jellyfin FFmpeg 7+ recommended)
- Linux system with AMD hardware
- Proper AMD drivers (amdgpu kernel module)
- Access to `/dev/dri/` devices

### Recommended Docker Image
For best results, use the enhanced Unmanic AMD image:
```bash
docker pull viennej/unmanic-amd:latest
```

This image includes:
- Jellyfin FFmpeg 7.1.2 with full AMD support
- LLVM 21.1.3 for optimal GPU compatibility
- All required AMD drivers and libraries

### Plugin Installation
1. Download or copy the plugin to Unmanic's plugins directory
2. Restart Unmanic
3. Enable the plugin in Unmanic UI
4. Configure settings as needed
5. Add to library workflow

## Configuration

### Settings

#### Encoding Mode
- **auto**: Automatic selection (GPU → CPU fallback)
- **gpu_only**: Force GPU hardware acceleration
- **cpu_only**: Force CPU software encoding

#### Prefer AMF over VAAPI
- When enabled, AMF encoders are preferred over VAAPI
- AMF typically offers better performance on modern AMD GPUs
- Default: Enabled

#### Target Codec
- **h264**: H.264/AVC (most compatible)
- **hevc**: H.265/HEVC (better compression)
- **copy**: Keep original codec (no transcoding)

#### Video Quality (Hardware Encoders)
- **speed**: Fastest encoding, good quality
- **balanced**: Recommended balance of speed and quality
- **quality**: Best quality, slower encoding

#### Bitrate Settings
- **Video Bitrate**: Target bitrate (e.g., 2M, 5M, 10M)
- **Max Video Bitrate**: Maximum bitrate cap (e.g., 4M, 8M, 15M)

#### Audio Settings
- **Audio Codec**: aac or copy
- **Audio Bitrate**: Target bitrate (e.g., 128k, 256k)

### Recommended Settings

#### For Speed (Real-time encoding)
```
Encoding Mode: gpu_only
Prefer AMF: ✓
Target Codec: h264
Video Quality: speed
Bitrate: 2M
Max Bitrate: 4M
Audio Codec: copy
```

#### For Quality (Archival)
```
Encoding Mode: cpu_only
Target Codec: hevc
Bitrate: 10M
Max Bitrate: 15M
Audio Codec: aac
Audio Bitrate: 256k
```

#### For Balance (Recommended)
```
Encoding Mode: auto
Prefer AMF: ✓
Target Codec: h264
Video Quality: balanced
Bitrate: 2M
Max Bitrate: 4M
Audio Codec: aac
Audio Bitrate: 128k
```

## Usage

### Adding to Library Workflow
1. Navigate to **Libraries** in Unmanic
2. Select your library
3. Go to **Plugin Flow** tab
4. Add **Transcode AMD v2** to the workflow
5. Drag to desired position in the flow
6. Save library configuration

### Monitoring
The plugin logs detailed information during encoding:
```
AMD CPU detected: AMD RYZEN AI MAX+ 395 w/ Radeon 8060S
AMD GPU detected: c6:00.0 Display controller [AMD/ATI] Device 1586
Mode: auto, Encoder: h264_amf (gpu)
[AMD] Mode: auto, Encoder: h264_amf (gpu)
```

Check the **Workers** tab in Unmanic to see active transcoding jobs and their logs.

## Troubleshooting

### GPU Not Detected
**Symptoms**: Plugin always uses CPU encoding

**Solutions**:
1. Verify AMD GPU is installed: `lspci | grep -i vga`
2. Check for /dev/dri devices: `ls -la /dev/dri/`
3. Ensure amdgpu module is loaded: `lsmod | grep amdgpu`
4. Check FFmpeg has AMD support: `ffmpeg -encoders | grep amf`

### Hardware Encoding Fails
**Symptoms**: Encoding fails or falls back to CPU

**Solutions**:
1. Check GPU driver: `dmesg | grep -i amdgpu`
2. Verify render device permissions: Container needs access to `/dev/dri`
3. Try different encoder: Enable/disable "Prefer AMF over VAAPI"
4. Use CPU Only mode as fallback

### Performance Issues
**Symptoms**: Slow encoding or high CPU usage

**Solutions**:
1. Use GPU Only mode for best speed
2. Choose "Speed" quality preset
3. Lower bitrate settings
4. Ensure GPU isn't busy with other tasks

### Quality Issues
**Symptoms**: Poor video quality or artifacts

**Solutions**:
1. Increase bitrate settings
2. Use "Quality" preset
3. Try CPU Only mode for best quality
4. Use HEVC codec for better compression

## Hardware Compatibility

### Tested Hardware

**CPUs**:
- AMD Ryzen AI MAX+ 395 (32 cores, AVX512) ✅
- AMD Ryzen 9 5900X ✅
- AMD Ryzen 7 series ✅

**GPUs**:
- AMD RX 7600 XT (RDNA 3.5, gfx1150) ✅
- AMD RX 6000 series (RDNA 2) ✅
- AMD RX 5000 series (RDNA 1) ✅

**Encoders**:
- AMF: av1_amf, h264_amf, hevc_amf ✅
- VAAPI: av1_vaapi, h264_vaapi, hevc_vaapi, vp9_vaapi ✅
- Software: libx264, libx265, libsvtav1 ✅

### Known Limitations

1. **RDNA 3.x GPUs (gfx1150+)**:
   - VAAPI may show "resource allocation failed" errors
   - AMF encoders work better on newer architectures
   - Software fallback always available

2. **Older GPUs**:
   - May not support all codecs
   - AMF might not be available
   - VAAPI usually works

3. **Driver Requirements**:
   - amdgpu driver required for modern GPUs
   - radeon driver for legacy GPUs
   - Proper kernel support needed

## Performance Benchmarks

Approximate encoding speeds (1080p content):

| Mode | Encoder | Speed | Quality | CPU Usage |
|------|---------|-------|---------|-----------|
| GPU (AMF) | h264_amf | 5-10x realtime | Good | Low (10-20%) |
| GPU (VAAPI) | h264_vaapi | 3-6x realtime | Good | Low (10-20%) |
| CPU | libx264 | 1-2x realtime | Excellent | High (90%+) |
| GPU (AMF) | hevc_amf | 3-6x realtime | Good | Low (10-20%) |
| CPU | libx265 | 0.5-1x realtime | Excellent | High (95%+) |

*Results vary based on hardware and content*

## Development

### Plugin Structure
```
transcode_amd_v2/
├── plugin.py         # Main plugin code
├── info.json         # Plugin metadata
├── changelog.txt     # Version history
├── description.md    # Short description
└── README.md         # Full documentation
```

### Testing
Test the plugin manually:
```bash
docker exec unmanic-amd python3 -c "
import sys
sys.path.insert(0, '/config/.unmanic/plugins/transcode_amd_v2')
import plugin
# Test detection
gpu = plugin.detect_amd_gpu()
cpu = plugin.detect_amd_cpu()
print(f'GPU: {gpu}')
print(f'CPU: {cpu}')
"
```

## Contributing

This plugin is part of the enhanced Unmanic AMD project:
- Repository: https://github.com/vienneje/unmanic
- Issues: https://github.com/vienneje/unmanic/issues
- Docker: https://hub.docker.com/r/viennej/unmanic-amd

## License

MIT License - See repository for details

## Credits

- Based on official Unmanic plugin patterns
- Inspired by the Unmanic community
- Enhanced for AMD hardware by viennej

## Version History

See [changelog.txt](changelog.txt) for detailed version history.

## Support

For issues, questions, or feature requests:
1. Check this README and troubleshooting section
2. Review Unmanic logs for errors
3. Open an issue on GitHub
4. Include hardware details and logs

---

**Version**: 2.2.0  
**Last Updated**: 2025-10-21  
**Author**: viennej  
**License**: MIT
