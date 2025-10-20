# Transcode AMD Plugin

AMD Hardware Acceleration Transcoding Plugin for Unmanic with CPU and GPU support.

## Overview

This plugin automatically detects AMD CPU and GPU capabilities and uses the best available hardware acceleration features for video transcoding. It supports VAAPI and AMF GPU encoders, as well as optimized CPU encoding, with intelligent fallback options.

## Features

- **🔍 Automatic Detection**: Detects both AMD CPU and GPU hardware
- **🎛️ Encoding Mode Selection**: Choose between CPU-only, GPU-only, or Auto mode
- **📊 Detailed Capability Detection**: Shows CPU model, cores, features, GPU model, and available encoders
- **🚀 Multiple Encoder Support**: VAAPI, AMF (GPU) and optimized software encoders (CPU)
- **⚡ Intelligent Selection**: Automatically chooses the best encoder based on your hardware
- **🔄 Hardware Fallback**: Falls back gracefully if preferred hardware is unavailable
- **🎬 Codec Support**: H.264 and HEVC codecs
- **⚙️ Quality Presets**: Speed, Balanced, and Quality modes for hardware encoding
- **🎚️ Configurable Settings**: Customizable bitrates, quality, and audio settings

## Encoding Modes

### 🔄 Auto Mode (Recommended)
- Automatically selects the best available encoder
- Preference: GPU (AMF) → GPU (VAAPI) → CPU (Software)
- Ideal for mixed workloads

### 🎮 GPU Only Mode
- Forces GPU hardware acceleration
- Uses VAAPI or AMF encoders
- Falls back to CPU if GPU unavailable (with warning)
- Best for freeing up CPU resources

### 💻 CPU Only Mode
- Forces software encoding on CPU
- Uses optimized thread allocation
- Leverages AMD CPU features (AVX, AVX2, etc.)
- Best for maximum quality or GPU compatibility issues

## Supported Codecs

| Codec | GPU (AMF) | GPU (VAAPI) | CPU (Software) |
|-------|-----------|-------------|----------------|
| H.264 | ✅ h264_amf | ✅ h264_vaapi | ✅ libx264 |
| HEVC  | ✅ hevc_amf | ✅ hevc_vaapi | ✅ libx265 |

## Detected Capabilities

The plugin automatically detects and displays:

### AMD CPU
- Model name (e.g., AMD Ryzen 9 5900X)
- Number of cores/threads
- CPU features (AVX, AVX2, SSE4.1, SSE4.2, FMA, AES, etc.)

### AMD GPU
- Model name (e.g., AMD RX 7600 XT)
- Vendor and Device IDs
- Driver (amdgpu/radeon)
- Render device path

### Available Encoders
- AMF encoders (h264_amf, hevc_amf, etc.)
- VAAPI encoders (h264_vaapi, hevc_vaapi, etc.)
- Software encoders (libx264, libx265, etc.)

## Requirements

- AMD GPU with hardware acceleration support
- FFmpeg with VAAPI/AMF support
- Linux with proper AMD drivers
- Unmanic with plugin support

## Installation

1. Copy the `transcode_amd` folder to your Unmanic plugins directory
2. Restart Unmanic
3. Enable the plugin in the Unmanic interface
4. Configure settings as needed

## Configuration

### Encoding Settings

- **Encoding Mode**: Choose between Auto, GPU Only, or CPU Only
  - **Auto**: Prefer GPU, fallback to CPU (recommended)
  - **GPU Only**: Force GPU encoding
  - **CPU Only**: Force CPU encoding
  
- **Prefer AMF over VAAPI**: When using GPU, prefer AMF encoders over VAAPI
- **Fallback to Software**: Allow fallback to CPU encoding on errors

### Video Settings

- **Target Codec**: H.264, HEVC, or Copy (same as source)
- **Video Quality**: For hardware encoding - Speed, Balanced, or Quality
- **Video Bitrate**: Target bitrate (e.g., 2M, 5M, 10M)
- **Max Bitrate**: Maximum bitrate cap (e.g., 4M, 8M, 15M)

### Audio Settings

- **Audio Codec**: AAC or Copy
- **Audio Bitrate**: Bitrate for AAC encoding (e.g., 128k, 256k)

### Information Display

- **AMD Capabilities Detected**: Shows detailed information about detected hardware
  - CPU model, cores, and features
  - GPU model and vendor/device IDs
  - Available encoders (AMF, VAAPI, Software)

## Usage

1. Enable the plugin in Unmanic
2. Configure your preferred settings
3. Add video files to your library
4. The plugin will automatically use the best available AMD hardware acceleration

## Troubleshooting

### Hardware Not Detected

- Ensure AMD drivers are properly installed
- Check that `/dev/dri/renderD*` devices exist
- Verify FFmpeg has VAAPI/AMF support

### Performance Issues

- Try different quality presets
- Adjust bitrate settings
- Check GPU utilization during encoding

### Fallback to Software

- Check plugin logs for error messages
- Verify hardware acceleration is working
- Consider updating drivers or FFmpeg

## Logs

The plugin logs detailed information about:
- AMD GPU detection results
- Encoder selection process
- FFmpeg command execution
- Performance metrics

Check the Unmanic logs for detailed information about the transcoding process.

## Support

For issues and feature requests, please visit:
- GitHub Issues: https://github.com/vienneje/unmanic/issues
- Documentation: https://github.com/vienneje/unmanic/blob/main/docs/

## License

This plugin is licensed under the same terms as Unmanic.