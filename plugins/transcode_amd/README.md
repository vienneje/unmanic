# Transcode AMD Plugin

AMD Hardware Acceleration Transcoding Plugin for Unmanic.

## Overview

This plugin automatically detects AMD GPU capabilities and uses the best available hardware acceleration features for video transcoding. It supports both VAAPI and AMF encoders, with intelligent fallback to software encoding when needed.

## Features

- **Automatic AMD GPU Detection**: Detects available AMD hardware and capabilities
- **Multiple Encoder Support**: VAAPI and AMF encoder support
- **Intelligent Codec Selection**: Chooses optimal encoders based on GPU capabilities
- **Hardware Fallback**: Falls back to software encoding if hardware fails
- **Codec Support**: H.264, HEVC, AV1, and VP9 codecs
- **Quality Presets**: Speed, Balanced, and Quality modes
- **Configurable Settings**: Customizable bitrates and quality settings

## Supported Codecs

| Codec | VAAPI | AMF | Software Fallback |
|-------|-------|-----|-------------------|
| H.264 | ✅ | ✅ | ✅ (libx264) |
| HEVC  | ✅ | ✅ | ✅ (libx265) |
| AV1   | ✅ | ✅ | ✅ (libsvtav1) |
| VP9   | ✅ | ❌ | ✅ (libvpx_vp9) |

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

### Basic Settings

- **Enable AMD GPU Detection**: Automatically detect AMD GPU capabilities
- **Prefer AMF over VAAPI**: Use AMD AMF encoders when available
- **Fallback to Software Encoding**: Use software encoding if hardware fails

### Quality Settings

- **Video Quality**: Choose between Speed, Balanced, or Quality presets
- **Video Bitrate**: Target bitrate for video encoding (e.g., 2M, 5M)
- **Maximum Bitrate**: Maximum bitrate for video encoding (e.g., 4M, 8M)
- **Audio Bitrate**: Bitrate for audio encoding (e.g., 128k, 256k)

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