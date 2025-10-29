#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    transcode_amd v2.7.10

    AMD Hardware Acceleration Transcoding Plugin - SMART EDITION

    Automatically detects and uses AMD CPU and GPU hardware for video transcoding.
    Supports AMF, VAAPI GPU encoders and optimized CPU software encoding.

    NEW in v2.7.0:
    - Easy Mode: Added quality selector (Fast/Balanced/Quality)
    - Output container selection: Choose MKV, MP4, or same as source
    - Expert Mode: Command templates (GPU HEVC, CPU HEVC, GPU H.264, CPU H.264, AV1)
    - Expert Mode: Extended variables ({width}, {height}, {bitrate}, {duration}, {codec})
    - More flexible and powerful encoding options

    NEW in v2.6.0:
    - Three-tier configuration modes (Easy/Advanced/Expert)
    - Easy Mode: Just select hardware (GPU/CPU/Auto), optimal defaults applied
    - Expert Mode: Custom FFmpeg command line with variable substitution
    - Preset profiles now show which hardware they use (GPU/CPU/Auto)
    - Much simpler UI for beginners, full control for experts

    NEW in v2.5.1:
    - Pre-flight file validation (prevents corrupted/0-byte file failures)
    - Skip already optimal files (saves hours of unnecessary processing)
    - Smart bitrate analysis (don't re-encode well-compressed files)
    - Better error categorization and logging

    Features from v2.4.0:
    - 10-bit HEVC support with auto-profile detection
    - HDR metadata preservation
    - Multi-audio and subtitle handling
    - Resolution-based bitrate optimization
    - CRF quality mode
    - GPU capability detection (RDNA generation)
    - AV1 codec support
    - Preset profiles (Fast/Balanced/Quality/Archive)
    - Two-pass encoding option
    - Auto-crop detection
    - Dry-run mode
    - Comprehensive error validation
"""

import os
import subprocess
import logging
import re
import json
from collections import Counter

from unmanic.libs.unplugins.settings import PluginSettings

# Configure logging
logger = logging.getLogger("Unmanic.Plugin.transcode_amd")


# ============================================================================
# PRESET PROFILES
# ============================================================================

PRESET_PROFILES = {
    "fast": {
        "description": "Fast encoding with GPU acceleration [Hardware: GPU only]",
        "encoding_mode": "gpu_only",
        "target_codec": "hevc",
        "rate_control": "vbr",
        "use_auto_bitrate": True,
        "audio_codec": "copy",
        "copy_subtitles": True,
    },
    "balanced": {
        "description": "Balanced quality and speed (recommended) [Hardware: Auto GPU/CPU]",
        "encoding_mode": "auto",
        "target_codec": "hevc",
        "rate_control": "vbr",
        "use_auto_bitrate": True,
        "audio_codec": "aac",
        "copy_subtitles": True,
        "preserve_hdr": True,
    },
    "quality": {
        "description": "High quality encoding [Hardware: CPU only]",
        "encoding_mode": "cpu_only",
        "target_codec": "hevc",
        "rate_control": "crf",
        "crf_value": "20",
        "audio_codec": "aac",
        "audio_mode": "all",
        "copy_subtitles": True,
        "preserve_hdr": True,
    },
    "archive": {
        "description": "Maximum quality for archival [Hardware: CPU only]",
        "encoding_mode": "cpu_only",
        "target_codec": "hevc",
        "rate_control": "crf",
        "crf_value": "18",
        "enable_two_pass": False,  # CRF doesn't benefit from two-pass
        "audio_mode": "all",
        "copy_subtitles": True,
        "preserve_hdr": True,
        "use_scene_detection": True,
    },
}


class Settings(PluginSettings):
    settings = {
        # Configuration mode (NEW in v2.6.0)
        "config_mode": "easy",  # easy, advanced, expert

        # Easy mode settings (NEW in v2.7.0: added quality selector)
        "easy_hardware": "auto",  # gpu, cpu, auto
        "easy_quality": "balanced",  # fast, balanced, quality

        # Output settings (NEW in v2.7.0)
        "output_container": "same",  # same, mkv, mp4

        # Expert mode settings (NEW in v2.7.0: added templates)
        "expert_template": "custom",  # custom, gpu_hevc, cpu_hevc, gpu_h264, cpu_h264, av1
        "expert_command": "ffmpeg -vaapi_device {render_device} -hwaccel vaapi -hwaccel_output_format vaapi -i {input} -c:v hevc_vaapi -qp 23 -c:a aac -b:a 192k {output}",  # Custom FFmpeg command line

        # Preset system (Advanced mode)
        "use_preset": True,
        "preset_profile": "balanced",

        # Encoding settings
        "encoding_mode": "auto",
        "prefer_amf_over_vaapi": False,
        "target_codec": "hevc",

        # Quality settings
        "rate_control": "vbr",  # vbr, crf, cbr
        "crf_value": "23",
        "video_quality": "balanced",

        # Bitrate settings
        "use_auto_bitrate": True,
        "bitrate": "4M",
        "max_bitrate": "6M",

        # Audio settings
        "audio_mode": "all",  # all, first, best, language
        "audio_language": "eng",
        "audio_codec": "aac",
        "audio_bitrate": "192k",
        "audio_channels": "2",
        "downmix_multichannel": False,

        # Subtitle settings
        "copy_subtitles": True,
        "subtitle_format": "copy",  # copy, srt, ass

        # Advanced settings
        "preserve_hdr": True,
        "enable_two_pass": False,
        "auto_crop": False,
        "use_scene_detection": False,

        # Testing/debugging
        "dry_run": False,
        "test_encode_duration": 0,  # 0 = full file, >0 = test first N seconds
        "skip_10bit_files": False,  # Skip 10-bit sources entirely
    }

    form_settings = {
        "config_mode": {
            "label": "Configuration Mode",
            "input_type": "select",
            "select_options": [
                {"value": "easy", "label": "Easy - Just pick hardware (GPU/CPU/Auto), optimal defaults"},
                {"value": "advanced", "label": "Advanced - Full control with all settings"},
                {"value": "expert", "label": "Expert - Custom FFmpeg command line"},
            ],
        },
        "easy_hardware": {
            "label": "Hardware Selection (Easy Mode)",
            "input_type": "select",
            "select_options": [
                {"value": "auto", "label": "Auto - Prefer GPU, fallback to CPU (recommended)"},
                {"value": "gpu", "label": "GPU - Force hardware acceleration only"},
                {"value": "cpu", "label": "CPU - Force software encoding only"},
            ],
        },
        "easy_quality": {
            "label": "Quality Preset (Easy Mode)",
            "input_type": "select",
            "select_options": [
                {"value": "fast", "label": "Fast - Quick encoding, larger files"},
                {"value": "balanced", "label": "Balanced - Good quality/speed (recommended)"},
                {"value": "quality", "label": "Quality - Best quality, slower"},
                {"value": "av1_quality", "label": "AV1 Archive - Maximum compression, no quality loss"},
            ],
        },
        "output_container": {
            "label": "Output Container Format",
            "input_type": "select",
            "select_options": [
                {"value": "same", "label": "Same as source"},
                {"value": "mkv", "label": "MKV - Matroska (recommended)"},
                {"value": "mp4", "label": "MP4 - MPEG-4 Part 14"},
            ],
        },
        "expert_template": {
            "label": "Command Template (Expert Mode)",
            "input_type": "select",
            "select_options": [
                {"value": "custom", "label": "Custom - Use command below"},
                {"value": "gpu_hevc", "label": "GPU HEVC - Hardware accelerated H.265"},
                {"value": "cpu_hevc", "label": "CPU HEVC - Software H.265 (best quality)"},
                {"value": "gpu_h264", "label": "GPU H.264 - Hardware accelerated H.264"},
                {"value": "cpu_h264", "label": "CPU H.264 - Software H.264"},
                {"value": "av1", "label": "AV1 - Hardware AV1 (RDNA 2+)"},
            ],
        },
        "expert_command": {
            "label": "Custom FFmpeg Command - Variables: {input} {output} {render_device} {width} {height} {bitrate} {duration} {codec}",
            "sub_setting": False,
        },
        "use_preset": {
            "label": "Use Preset Profile",
            "sub_setting": True,
        },
        "preset_profile": {
            "label": "Preset Profile",
            "input_type": "select",
            "select_options": [
                {"value": "fast", "label": "Fast [GPU only] - Quick encoding with GPU"},
                {"value": "balanced", "label": "Balanced [Auto GPU/CPU] - Recommended"},
                {"value": "quality", "label": "Quality [CPU only] - Better quality, slower"},
                {"value": "archive", "label": "Archive [CPU only] - Maximum quality"},
            ],
        },
        "encoding_mode": {
            "label": "Encoding Mode",
            "input_type": "select",
            "select_options": [
                {"value": "auto", "label": "Auto - Prefer GPU, fallback to CPU"},
                {"value": "gpu_only", "label": "GPU Only - Force hardware acceleration"},
                {"value": "cpu_only", "label": "CPU Only - Force software encoding"},
            ],
        },
        "prefer_amf_over_vaapi": {
            "label": "Prefer AMF over VAAPI (GPU mode)",
        },
        "target_codec": {
            "label": "Target Codec",
            "input_type": "select",
            "select_options": [
                {"value": "h264", "label": "H.264/AVC"},
                {"value": "hevc", "label": "H.265/HEVC (Recommended)"},
                {"value": "av1", "label": "AV1 (Best compression, slower)"},
                {"value": "copy", "label": "Copy (same as source)"},
            ],
        },
        "rate_control": {
            "label": "Rate Control Mode",
            "input_type": "select",
            "select_options": [
                {"value": "vbr", "label": "VBR - Variable Bitrate (fast, predictable size)"},
                {"value": "crf", "label": "CRF - Constant Quality (better quality/size)"},
                {"value": "cbr", "label": "CBR - Constant Bitrate (streaming)"},
            ],
        },
        "crf_value": {
            "label": "CRF Value (18-28, lower=better quality)",
        },
        "video_quality": {
            "label": "Video Quality Preset (hardware encoders)",
            "input_type": "select",
            "select_options": [
                {"value": "speed", "label": "Speed - Fastest encoding"},
                {"value": "balanced", "label": "Balanced - Recommended"},
                {"value": "quality", "label": "Quality - Best quality"},
            ],
        },
        "use_auto_bitrate": {
            "label": "Auto-select bitrate based on resolution",
        },
        "bitrate": {
            "label": "Video Bitrate (e.g., 2M, 5M, 10M)",
        },
        "max_bitrate": {
            "label": "Max Video Bitrate (e.g., 4M, 8M, 15M)",
        },
        "audio_mode": {
            "label": "Audio Track Selection",
            "input_type": "select",
            "select_options": [
                {"value": "all", "label": "All tracks (preserve multi-language)"},
                {"value": "first", "label": "First track only"},
                {"value": "language", "label": "Specific language"},
            ],
        },
        "audio_language": {
            "label": "Preferred Audio Language (if audio_mode=language)",
        },
        "audio_codec": {
            "label": "Audio Codec",
            "input_type": "select",
            "select_options": [
                {"value": "aac", "label": "AAC"},
                {"value": "copy", "label": "Copy (no re-encode)"},
            ],
        },
        "audio_bitrate": {
            "label": "Audio Bitrate (e.g., 128k, 192k, 256k)",
        },
        "audio_channels": {
            "label": "Audio Channels (e.g., 2 for stereo, 6 for 5.1)",
        },
        "downmix_multichannel": {
            "label": "Downmix 5.1/7.1 to stereo",
        },
        "copy_subtitles": {
            "label": "Copy subtitle tracks",
        },
        "subtitle_format": {
            "label": "Subtitle Format",
            "input_type": "select",
            "select_options": [
                {"value": "copy", "label": "Copy (preserve original)"},
                {"value": "srt", "label": "SRT (SubRip)"},
                {"value": "ass", "label": "ASS (Advanced SubStation)"},
            ],
        },
        "preserve_hdr": {
            "label": "Preserve HDR metadata (HDR10, Dolby Vision)",
        },
        "enable_two_pass": {
            "label": "Enable two-pass encoding (CPU mode, better quality)",
        },
        "auto_crop": {
            "label": "Auto-detect and remove black bars",
        },
        "use_scene_detection": {
            "label": "Scene-based encoding (libx265 only, better quality)",
        },
        "dry_run": {
            "label": "Dry run - preview command without executing",
        },
        "test_encode_duration": {
            "label": "Test mode - encode first N seconds (0=disabled)",
        },
        "skip_10bit_files": {
            "label": "Skip 10-bit video files entirely",
        },
    }

    def __init__(self, *args, **kwargs):
        super(Settings, self).__init__(*args, **kwargs)
        # Dynamically update form_settings based on config_mode
        config_mode = self.get_setting('config_mode')

        # Update form_settings with visibility rules
        self.form_settings = {
            **self.form_settings,  # Keep existing form_settings
            "easy_hardware": self.__set_easy_mode_visibility("easy_hardware"),
            "easy_quality": self.__set_easy_mode_visibility("easy_quality"),
            "output_container": self.__set_output_container_visibility(),
            "expert_template": self.__set_expert_mode_visibility("expert_template"),
            "expert_command": self.__set_expert_mode_visibility("expert_command"),
            # Hide all advanced settings in Easy/Expert modes
            "use_preset": self.__set_advanced_mode_visibility(),
            "preset_profile": self.__set_advanced_mode_visibility(),
            "encoding_mode": self.__set_advanced_mode_visibility(),
            "prefer_amf_over_vaapi": self.__set_advanced_mode_visibility(),
            "target_codec": self.__set_advanced_mode_visibility(),
            "rate_control": self.__set_advanced_mode_visibility(),
            "crf_value": self.__set_advanced_mode_visibility(),
            "video_quality": self.__set_advanced_mode_visibility(),
            "use_auto_bitrate": self.__set_advanced_mode_visibility(),
            "bitrate": self.__set_advanced_mode_visibility(),
            "max_bitrate": self.__set_advanced_mode_visibility(),
            "audio_mode": self.__set_advanced_mode_visibility(),
            "audio_language": self.__set_advanced_mode_visibility(),
            "audio_codec": self.__set_advanced_mode_visibility(),
            "audio_bitrate": self.__set_advanced_mode_visibility(),
            "audio_channels": self.__set_advanced_mode_visibility(),
            "downmix_multichannel": self.__set_advanced_mode_visibility(),
            "copy_subtitles": self.__set_advanced_mode_visibility(),
            "subtitle_format": self.__set_advanced_mode_visibility(),
            "preserve_hdr": self.__set_advanced_mode_visibility(),
            "enable_two_pass": self.__set_advanced_mode_visibility(),
            "auto_crop": self.__set_advanced_mode_visibility(),
            "use_scene_detection": self.__set_advanced_mode_visibility(),
            "dry_run": self.__set_advanced_mode_visibility(),
            "test_encode_duration": self.__set_advanced_mode_visibility(),
            "skip_10bit_files": self.__set_advanced_mode_visibility(),
        }

    def __set_easy_mode_visibility(self, setting_key):
        """Show Easy mode settings only in Easy mode"""
        values = {**self.form_settings.get(setting_key, {})}
        config_mode = self.get_setting('config_mode')
        if config_mode != 'easy':
            values["display"] = 'hidden'
        return values

    def __set_output_container_visibility(self):
        """Show output_container in Easy and Advanced modes, hide in Expert mode"""
        values = {**self.form_settings.get("output_container", {})}
        config_mode = self.get_setting('config_mode')
        if config_mode == 'expert':
            values["display"] = 'hidden'
        return values

    def __set_expert_mode_visibility(self, setting_key):
        """Show Expert mode settings only in Expert mode"""
        values = {**self.form_settings.get(setting_key, {})}
        config_mode = self.get_setting('config_mode')
        if config_mode != 'expert':
            values["display"] = 'hidden'
        return values

    def __set_advanced_mode_visibility(self):
        """Show advanced settings only in Advanced mode"""
        values = {}
        config_mode = self.get_setting('config_mode')
        if config_mode != 'advanced':
            values["display"] = 'hidden'
        return values


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def ensure_pciutils_installed():
    """Ensure pciutils (lspci) is installed for GPU detection"""
    try:
        result = subprocess.run(['which', 'lspci'], capture_output=True, timeout=5)
        if result.returncode != 0:
            logger.warning("lspci not found, attempting to install pciutils...")
            install_result = subprocess.run(['apt-get', 'update'], capture_output=True, timeout=30)
            if install_result.returncode == 0:
                subprocess.run(['apt-get', 'install', '-y', 'pciutils'], capture_output=True, timeout=60)
                logger.info("pciutils installed successfully")
            else:
                logger.warning("Could not install pciutils, GPU detection may fail")
    except Exception as e:
        logger.debug(f"Error checking/installing pciutils: {e}")


def detect_gpu_generation(device_id):
    """Map AMD device ID to architecture generation"""
    device_id = device_id.lower()

    # RDNA 3.5 (Radeon 800M series - Ryzen AI)
    rdna35_ids = ['15bf', '15c8', '15d8', '15e5']

    # RDNA 3 (RX 7000 series, Radeon 700M/780M)
    rdna3_ids = ['744c', '7448', '743f', '15bf', '150e']

    # RDNA 2 (RX 6000 series, Radeon 600M)
    rdna2_ids = ['163f', '1638', '73bf', '73df', '73ef', '73ff']

    # RDNA (RX 5000 series)
    rdna1_ids = ['731f', '7340', '7341', '734f']

    # GCN 5 (Vega)
    gcn5_ids = ['687f', '6863', '6867']

    if device_id in rdna35_ids:
        return 'rdna3.5'
    elif device_id in rdna3_ids:
        return 'rdna3'
    elif device_id in rdna2_ids:
        return 'rdna2'
    elif device_id in rdna1_ids:
        return 'rdna1'
    elif device_id in gcn5_ids:
        return 'gcn5'

    return 'unknown'


def get_amd_gpu_capabilities():
    """Detect AMD GPU generation and capabilities"""
    caps = {
        'detected': False,
        'generation': 'unknown',
        'model': 'Unknown AMD GPU',
        'device_id': None,
        'supports_hevc_10bit': False,
        'supports_av1_encode': False,
        'supports_av1_decode': False,
        'max_hevc_profile': 'main',
    }

    try:
        ensure_pciutils_installed()
        result = subprocess.run(['lspci', '-nn'], capture_output=True, text=True, timeout=5)

        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if any(word in line.lower() for word in ['vga', 'display']) and \
                   any(word in line.lower() for word in ['amd', 'ati', 'radeon']):

                    # Extract device ID
                    match = re.search(r'\[([0-9a-f]{4}):([0-9a-f]{4})\]', line)
                    if match:
                        caps['detected'] = True
                        caps['device_id'] = match.group(2)
                        caps['generation'] = detect_gpu_generation(caps['device_id'])

                        # Extract model name
                        model_match = re.search(r'VGA.*?:\s*(.+?)\s*\[', line)
                        if model_match:
                            caps['model'] = model_match.group(1).strip()

                        # Set capabilities based on generation
                        if caps['generation'] in ['rdna3.5', 'rdna3', 'rdna2']:
                            caps['supports_hevc_10bit'] = True
                            caps['supports_av1_encode'] = True
                            caps['supports_av1_decode'] = True
                            caps['max_hevc_profile'] = 'main10'
                        elif caps['generation'] == 'rdna1':
                            caps['supports_hevc_10bit'] = False
                            caps['supports_av1_decode'] = False
                            caps['max_hevc_profile'] = 'main'

                        logger.info(f"AMD GPU detected: {caps['model']} (Generation: {caps['generation']})")
                        break

    except Exception as e:
        logger.debug(f"Error detecting GPU capabilities: {e}")

    return caps


def detect_amd_gpu():
    """Detect AMD GPU and available encoders"""
    gpu_info = {
        'detected': False,
        'render_device': '/dev/dri/renderD128',
        'has_amf': False,
        'has_vaapi': False,
        'capabilities': {}
    }

    try:
        # Get detailed capabilities
        gpu_info['capabilities'] = get_amd_gpu_capabilities()
        gpu_info['detected'] = gpu_info['capabilities']['detected']

        # Check for render devices
        if os.path.exists('/dev/dri'):
            render_devices = [f for f in os.listdir('/dev/dri') if f.startswith('renderD')]
            if render_devices:
                gpu_info['render_device'] = f'/dev/dri/{render_devices[0]}'

        # Check FFmpeg encoders
        result = subprocess.run(['ffmpeg', '-encoders'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            if 'h264_amf' in result.stdout:
                gpu_info['has_amf'] = True
            if 'h264_vaapi' in result.stdout:
                gpu_info['has_vaapi'] = True

    except Exception as e:
        logger.debug(f"Error detecting AMD GPU: {e}")

    return gpu_info


def detect_amd_cpu():
    """Detect AMD CPU"""
    cpu_info = {
        'detected': False,
        'cores': 0,
        'model': 'Unknown CPU'
    }

    try:
        with open('/proc/cpuinfo', 'r') as f:
            cpuinfo = f.read()

        if 'AMD' in cpuinfo or 'AuthenticAMD' in cpuinfo:
            cpu_info['detected'] = True
            cpu_info['cores'] = cpuinfo.count('processor')

            model_match = re.search(r'model name\s+:\s+(.+)', cpuinfo)
            if model_match:
                cpu_info['model'] = model_match.group(1).strip()
                logger.info(f"AMD CPU detected: {cpu_info['model']} ({cpu_info['cores']} cores)")

    except Exception as e:
        logger.debug(f"Error detecting AMD CPU: {e}")

    return cpu_info


def detect_source_codec(file_path):
    """Detect video codec from source file"""
    try:
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-select_streams', 'v:0',
             '-show_entries', 'stream=codec_name', '-of', 'default=noprint_wrappers=1:nokey=1',
             file_path],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            codec = result.stdout.strip().lower()
            if codec in ['h264', 'avc']:
                return 'h264'
            elif codec in ['hevc', 'h265']:
                return 'hevc'
            elif codec in ['av1']:
                return 'av1'
    except Exception:
        pass

    return 'h264'


def detect_video_bit_depth(file_path):
    """Detect video bit depth (8-bit, 10-bit, etc.)"""
    try:
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-select_streams', 'v:0',
             '-show_entries', 'stream=pix_fmt', '-of', 'default=noprint_wrappers=1:nokey=1',
             file_path],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            pix_fmt = result.stdout.strip().lower()
            if '10le' in pix_fmt or '10be' in pix_fmt or 'p010' in pix_fmt:
                return 10
            elif '12le' in pix_fmt or '12be' in pix_fmt:
                return 12
            else:
                return 8
    except Exception as e:
        logger.debug(f"Error detecting bit depth: {e}")

    return 8


def detect_source_bitrate(file_path):
    """
    Detect video-only bitrate from source file
    Returns bitrate in bits per second, or 0 if unable to detect

    v2.7.7: Added to prevent CRF mode from exceeding source bitrate
    v2.7.8: Enhanced to calculate from file size/duration when stream bitrate unavailable
    """
    try:
        # First try direct bitrate from stream
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-select_streams', 'v:0',
             '-show_entries', 'stream=bit_rate', '-of', 'default=noprint_wrappers=1:nokey=1',
             file_path],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0 and result.stdout.strip():
            bitrate = int(result.stdout.strip())
            if bitrate > 0:
                return bitrate

        # If stream bitrate not available, calculate from file size and duration
        result = subprocess.run(
            ['ffprobe', '-v', 'error',
             '-show_entries', 'format=size,duration', '-of', 'json',
             file_path],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            format_info = data.get('format', {})
            file_size = int(format_info.get('size', 0))
            duration = float(format_info.get('duration', 0))

            if file_size > 0 and duration > 0:
                # Calculate total bitrate and assume 70% is video
                total_bitrate = (file_size * 8) / duration
                video_bitrate = int(total_bitrate * 0.7)
                return video_bitrate

    except Exception as e:
        logger.debug(f"Error detecting source bitrate: {e}")

    return 0


def get_resolution(file_path):
    """Get video resolution (width, height)"""
    try:
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-select_streams', 'v:0',
             '-show_entries', 'stream=width,height', '-of', 'csv=p=0',
             file_path],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            width, height = map(int, result.stdout.strip().split(','))
            return width, height
    except Exception:
        pass

    return 1920, 1080  # Default


def get_optimal_bitrate(file_path, target_codec):
    """Calculate optimal bitrate based on resolution"""
    try:
        width, height = get_resolution(file_path)
        pixels = width * height

        # HEVC bitrate recommendations (in Mbps)
        if target_codec == 'hevc':
            if pixels <= 1280 * 720:      # 720p
                return "2M", "3M"
            elif pixels <= 1920 * 1080:   # 1080p
                return "4M", "6M"
            elif pixels <= 2560 * 1440:   # 1440p
                return "8M", "12M"
            elif pixels <= 3840 * 2160:   # 4K
                return "15M", "20M"
            else:                          # 8K+
                return "30M", "40M"

        # H.264 requires ~2x bitrate of HEVC for same quality
        elif target_codec == 'h264':
            if pixels <= 1280 * 720:
                return "4M", "6M"
            elif pixels <= 1920 * 1080:
                return "8M", "12M"
            elif pixels <= 2560 * 1440:
                return "16M", "24M"
            elif pixels <= 3840 * 2160:
                return "30M", "40M"
            else:
                return "60M", "80M"

        # AV1 requires ~30% less than HEVC
        elif target_codec == 'av1':
            if pixels <= 1280 * 720:
                return "1.5M", "2.5M"
            elif pixels <= 1920 * 1080:
                return "3M", "5M"
            elif pixels <= 2560 * 1440:
                return "6M", "10M"
            elif pixels <= 3840 * 2160:
                return "12M", "16M"
            else:
                return "24M", "32M"

    except Exception as e:
        logger.debug(f"Error calculating optimal bitrate: {e}")

    return "4M", "6M"  # Default


def detect_hdr_metadata(file_path):
    """Detect HDR format and metadata"""
    try:
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-select_streams', 'v:0',
             '-show_entries', 'stream=color_transfer,color_primaries,color_space',
             '-of', 'json', file_path],
            capture_output=True, text=True, timeout=10
        )

        if result.returncode == 0:
            data = json.loads(result.stdout)
            stream = data.get('streams', [{}])[0]

            transfer = stream.get('color_transfer', 'unknown')
            primaries = stream.get('color_primaries', 'unknown')
            space = stream.get('color_space', 'unknown')

            is_hdr = transfer in ['smpte2084', 'arib-std-b67']

            return {
                'transfer': transfer,
                'primaries': primaries,
                'space': space,
                'is_hdr': is_hdr,
                'hdr_type': 'HDR10' if transfer == 'smpte2084' else ('HLG' if transfer == 'arib-std-b67' else 'SDR')
            }

    except Exception as e:
        logger.debug(f"Error detecting HDR metadata: {e}")

    return None


def detect_crop(file_path, duration=10):
    """Detect black bars using cropdetect filter"""
    try:
        cmd = [
            'ffmpeg', '-i', file_path, '-t', str(duration),
            '-vf', 'cropdetect=24:16:0', '-f', 'null', '-'
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        # Parse output for crop values (format: crop=1920:800:0:140)
        matches = re.findall(r'crop=(\d+):(\d+):(\d+):(\d+)', result.stderr)

        if matches:
            # Use most common crop value
            most_common = Counter(matches).most_common(1)[0][0]
            w, h, x, y = most_common

            # Only return crop if significant (>5% cropped)
            orig_w, orig_h = get_resolution(file_path)
            crop_h = int(h)
            if (orig_h - crop_h) / orig_h > 0.05:
                return f"crop={w}:{h}:{x}:{y}"

    except Exception as e:
        logger.debug(f"Error detecting crop: {e}")

    return None


def get_video_duration(file_path):
    """Get video duration in seconds using ffprobe"""
    try:
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
             '-of', 'default=noprint_wrappers=1:nokey=1', file_path],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            duration_str = result.stdout.strip()
            if duration_str and duration_str != 'N/A':
                return float(duration_str)
    except Exception as e:
        logger.debug(f"Error getting video duration: {e}")

    return 0


def get_encoder(codec, gpu_info, cpu_info, mode, prefer_amf):
    """Get optimal encoder based on hardware and mode"""
    encoder_map = {
        'h264': {'amf': 'h264_amf', 'vaapi': 'h264_vaapi', 'software': 'libx264'},
        'hevc': {'amf': 'hevc_amf', 'vaapi': 'hevc_vaapi', 'software': 'libx265'},
        'av1':  {'amf': None, 'vaapi': 'av1_vaapi', 'software': 'libsvtav1'},
    }

    if codec not in encoder_map:
        return 'libx264', 'cpu'

    encoders = encoder_map[codec]

    # CPU only mode
    if mode == 'cpu_only':
        return encoders['software'], 'cpu'

    # GPU mode
    if mode in ['gpu_only', 'auto']:
        if gpu_info['detected']:
            # Check AV1 support
            if codec == 'av1':
                if gpu_info['capabilities'].get('supports_av1_encode'):
                    return encoders['vaapi'], 'gpu'
                else:
                    logger.info("GPU doesn't support AV1 encoding - falling back to CPU")
                    return encoders['software'], 'cpu'

            # Check AMF/VAAPI preference
            if prefer_amf and gpu_info['has_amf'] and encoders['amf']:
                return encoders['amf'], 'gpu'
            elif gpu_info['has_vaapi']:
                return encoders['vaapi'], 'gpu'

    # Fallback to CPU
    return encoders['software'], 'cpu'


def get_effective_settings(settings_obj):
    """Get effective settings (apply preset if enabled, or Easy/Expert mode)"""
    config_mode = settings_obj.get_setting('config_mode')

    # EASY MODE: Use optimal defaults with hardware selection
    if config_mode == 'easy':
        easy_hardware = settings_obj.get_setting('easy_hardware')
        easy_quality = settings_obj.get_setting('easy_quality')

        # Map easy_hardware to encoding_mode
        hardware_map = {
            'auto': 'auto',
            'gpu': 'gpu_only',
            'cpu': 'cpu_only',
        }

        # Quality presets for Easy Mode
        quality_presets = {
            'fast': {
                'rate_control': 'vbr',
                'use_auto_bitrate': True,
                'crf_value': '26',
                'video_quality': 'speed',
                'target_codec': 'hevc',
            },
            'balanced': {
                'rate_control': 'vbr',
                'use_auto_bitrate': True,
                'crf_value': '23',
                'video_quality': 'balanced',
                'target_codec': 'hevc',
            },
            'quality': {
                'rate_control': 'crf',
                'use_auto_bitrate': False,
                'crf_value': '20',
                'video_quality': 'quality',
                'target_codec': 'hevc',
            },
            'av1_quality': {
                'rate_control': 'crf',
                'use_auto_bitrate': False,
                'crf_value': '18',  # High quality for AV1
                'video_quality': 'quality',
                'target_codec': 'av1',
            },
        }

        quality_settings = quality_presets.get(easy_quality, quality_presets['balanced'])

        easy_defaults = {
            'encoding_mode': hardware_map.get(easy_hardware, 'auto'),
            'target_codec': quality_settings.get('target_codec', 'hevc'),
            'audio_codec': 'copy',  # Copy audio to avoid multi-channel encoding issues
            'audio_bitrate': '192k',
            'audio_mode': 'all',
            'copy_subtitles': True,
            'preserve_hdr': True,
            'auto_crop': True,
            **quality_settings,  # Merge quality settings
        }

        class EasyModeSettings:
            def __init__(self, settings_obj, easy_defaults):
                self._settings = settings_obj
                self._easy = easy_defaults

            def get_setting(self, key):
                if key in self._easy:
                    return self._easy[key]
                return self._settings.get_setting(key)

        return EasyModeSettings(settings_obj, easy_defaults)

    # ADVANCED MODE: Use preset or custom settings
    if not settings_obj.get_setting('use_preset'):
        # Use custom settings as-is
        return settings_obj

    # Get preset and merge with custom overrides
    preset_name = settings_obj.get_setting('preset_profile')
    preset = PRESET_PROFILES.get(preset_name, PRESET_PROFILES['balanced'])

    # Create a wrapper that returns preset values with custom overrides
    class EffectiveSettings:
        def __init__(self, settings_obj, preset):
            self._settings = settings_obj
            self._preset = preset

        def get_setting(self, key):
            # Preset values take precedence when use_preset=True
            if key in self._preset:
                return self._preset[key]
            return self._settings.get_setting(key)

    return EffectiveSettings(settings_obj, preset)


def validate_encoding_params(encoder, encoder_type, file_in, settings, gpu_info):
    """Pre-flight validation before encoding"""
    errors = []
    warnings = []

    # Check 1: 10-bit + GPU
    bit_depth = detect_video_bit_depth(file_in)
    if encoder.endswith('_vaapi') and bit_depth >= 10:
        if not gpu_info['capabilities'].get('supports_hevc_10bit'):
            errors.append(
                f"10-bit source detected but GPU ({gpu_info['capabilities'].get('generation', 'unknown')}) "
                "doesn't support 10-bit HEVC encoding. "
                "Solutions: (1) Enable 'skip_10bit_files', (2) Use CPU mode, (3) Upgrade to RDNA 2+ GPU"
            )

    # Check 2: GPU not detected but GPU mode selected
    mode = settings.get_setting('encoding_mode')
    if mode == 'gpu_only' and not gpu_info['detected']:
        errors.append(
            "GPU-only mode selected but no AMD GPU detected. "
            "Solutions: (1) Check Docker --device=/dev/dri mapping, (2) Use auto/CPU mode"
        )

    # Check 3: AV1 on old GPU
    if encoder == 'av1_vaapi' and not gpu_info['capabilities'].get('supports_av1_encode'):
        errors.append(
            "AV1 encoding requested but GPU doesn't support it (requires RDNA 2+). "
            "Will fallback to CPU (libsvtav1)"
        )

    # Check 4: Two-pass with GPU
    if settings.get_setting('enable_two_pass') and encoder_type == 'gpu':
        warnings.append(
            "Two-pass encoding is enabled but GPU mode doesn't support it. "
            "Two-pass will be ignored for hardware encoders."
        )

    # Check 5: Bitrate sanity check
    if settings.get_setting('rate_control') == 'vbr':
        bitrate_str = settings.get_setting('bitrate')
        try:
            bitrate_val = int(bitrate_str.replace('M', '000000').replace('k', '000'))
            width, height = get_resolution(file_in)
            min_bitrate = (width * height) / 1000

            if bitrate_val < min_bitrate:
                warnings.append(
                    f"Bitrate {bitrate_str} may be too low for {width}x{height}. "
                    f"Recommended at least {int(min_bitrate/1000000)}M"
                )
        except:
            pass

    return errors, warnings


# ============================================================================
# PROGRESS PARSER
# ============================================================================

class FFmpegProgressParser:
    """Parse FFmpeg progress output to calculate completion percentage"""

    def __init__(self, total_duration_seconds, default_parser=None):
        self.total_duration = total_duration_seconds
        self.current_percent = 0
        self.proc_registered = False
        self.default_parser = default_parser

    def parse(self, line_text, pid=None, proc_start_time=None, unset=False):
        """
        Parse FFmpeg progress output.

        Args:
            line_text: FFmpeg output line
            pid: Process ID (for initial registration)
            proc_start_time: Process start time (for initial registration)
            unset: If True, unregister the process (it's completed)

        Returns:
            Dict with 'percent' (as integer), 'paused', 'killed' keys
        """
        # Handle process unregistration (completion)
        if unset:
            if self.default_parser is not None:
                self.default_parser(None, unset=True)
            return {
                'percent': 100,
                'paused': False,
                'killed': False
            }

        # Handle process registration (initial call with pid)
        if pid is not None and not self.proc_registered:
            self.proc_registered = True
            # Call default parser to register PID and start time with worker monitor
            if self.default_parser is not None:
                logger.debug(f"Registering PID {pid} with worker monitor")
                try:
                    self.default_parser(None, pid=pid, proc_start_time=proc_start_time)
                    logger.info(f"Successfully registered PID {pid} for elapsed time tracking")
                except Exception as e:
                    logger.error(f"Failed to register PID with worker monitor: {e}")
            return {
                'percent': 0,
                'paused': False,
                'killed': False
            }

        # Parse FFmpeg time output
        # Example: "frame=123 fps=30 time=00:01:23.45 bitrate=1234kbits/s speed=1.0x"
        if line_text and self.total_duration > 0:
            time_match = re.search(r'time=(\d+):(\d+):(\d+)\.(\d+)', str(line_text))
            if time_match:
                hours = int(time_match.group(1))
                minutes = int(time_match.group(2))
                seconds = int(time_match.group(3))
                centiseconds = int(time_match.group(4))

                current_seconds = hours * 3600 + minutes * 60 + seconds + centiseconds / 100.0
                # Cap at 99% until actually complete (prevents showing 100% too early)
                self.current_percent = min(99, int((current_seconds / self.total_duration) * 100))

                logger.debug(f"FFmpeg progress: {current_seconds:.2f}s / {self.total_duration:.2f}s = {self.current_percent}%")

        # Return percent as INTEGER (required for ETC calculation)
        # Unmanic's worker monitor converts this to string internally
        return {
            'percent': self.current_percent,
            'paused': False,
            'killed': False
        }


# ============================================================================
# FILE VALIDATION & OPTIMIZATION (v2.5.0)
# ============================================================================

def validate_source_file(file_path):
    """
    Validate file before processing to prevent failures

    Checks:
    1. File exists and is not empty (0 bytes)
    2. File can be probed with ffprobe
    3. File has valid duration

    Returns: (is_valid, error_category, error_message)
    """
    # Check 1: File exists
    if not os.path.exists(file_path):
        return False, 'FILE_NOT_FOUND', f"File does not exist: {file_path}"

    # Check 2: File is not empty
    try:
        file_size = os.path.getsize(file_path)
        if file_size == 0:
            return False, 'FILE_CORRUPTED', f"File is 0 bytes (empty): {file_path}"

        # Minimum reasonable size (100KB for video)
        if file_size < 100 * 1024:
            return False, 'FILE_CORRUPTED', f"File suspiciously small ({file_size} bytes): {file_path}"

    except Exception as e:
        return False, 'FILE_ERROR', f"Cannot access file: {e}"

    # Check 3: Can probe with ffprobe
    try:
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-show_entries',
             'format=duration', '-of', 'json', file_path],
            capture_output=True, text=True, timeout=10
        )

        if result.returncode != 0:
            return False, 'FILE_CORRUPTED', f"FFprobe failed (corrupted file): {result.stderr[:200]}"

        # Check 4: Has valid duration
        try:
            data = json.loads(result.stdout)
            duration = float(data.get('format', {}).get('duration', 0))

            if duration <= 0:
                return False, 'FILE_CORRUPTED', f"No valid duration found (corrupted): {file_path}"

            # Too short to be real content (< 1 second)
            if duration < 1.0:
                return False, 'FILE_CORRUPTED', f"Duration too short ({duration}s): {file_path}"

        except (ValueError, KeyError) as e:
            return False, 'FILE_CORRUPTED', f"Invalid ffprobe output: {e}"

    except subprocess.TimeoutExpired:
        return False, 'FILE_TIMEOUT', f"FFprobe timeout (file may be corrupted): {file_path}"

    except Exception as e:
        return False, 'FILE_ERROR', f"Validation error: {e}"

    # All checks passed
    return True, None, None


def is_already_optimal(file_path, settings):
    """
    Check if file is already optimally encoded and doesn't need transcoding

    Returns: (should_skip, reason)
    """
    try:
        # Get target codec
        target_codec = settings.get_setting('target_codec')

        if target_codec == 'copy':
            return False, None

        # Probe file info
        probe_cmd = [
            'ffprobe', '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=codec_name,bit_rate,width,height,pix_fmt',
            '-show_entries', 'format=size,bit_rate,duration',
            '-of', 'json',
            file_path
        ]

        result = subprocess.run(probe_cmd, capture_output=True, text=True, timeout=10)

        if result.returncode != 0:
            return False, None

        data = json.loads(result.stdout)
        video_stream = data.get('streams', [{}])[0]
        format_info = data.get('format', {})

        current_codec = video_stream.get('codec_name', '').lower()

        # v2.7.9: Codec efficiency hierarchy (AV1 > HEVC > H.264)
        # Skip if source codec is MORE efficient than target
        codec_efficiency = {'av1': 3, 'hevc': 2, 'h265': 2, 'h264': 1, 'avc': 1}
        current_efficiency = codec_efficiency.get(current_codec, 0)
        target_efficiency = codec_efficiency.get(target_codec, 0)

        if current_efficiency > target_efficiency:
            return True, f"Source codec {current_codec} is more efficient than target {target_codec}, skipping"

        # v2.7.9: Check if source is already well-compressed (regardless of codec)
        # Skip transcoding files that are already at or below target bitrate
        # Get bitrates
        try:
            # v2.7.6: CRITICAL FIX - Only use video stream bitrate, NOT format bitrate
            # Format bitrate includes audio/subtitles which can be misleading
            current_bitrate = int(video_stream.get('bit_rate', 0))

            # If video stream bitrate is not available, calculate from file
            if current_bitrate == 0:
                # Get file size and duration to calculate average bitrate
                file_size = int(format_info.get('size', 0))
                duration_str = format_info.get('duration', '0')
                try:
                    duration = float(duration_str)
                    if duration > 0 and file_size > 0:
                        # Calculate video-only bitrate (assume video is 70% of total file)
                        # This is a heuristic when stream bitrate is unavailable
                        total_bitrate = (file_size * 8) / duration
                        current_bitrate = int(total_bitrate * 0.7)
                except (ValueError, ZeroDivisionError):
                    pass

            if current_bitrate == 0:
                # Can't determine bitrate, allow transcode
                return False, None

            # Get resolution for optimal bitrate calculation
            width = int(video_stream.get('width', 1920))
            height = int(video_stream.get('height', 1080))
            resolution = f"{width}x{height}"

            # Calculate optimal bitrate for this resolution
            optimal_bitrate = get_optimal_bitrate_for_resolution(resolution, target_codec)

            # v2.7.9: Enhanced logic to skip well-encoded files
            # Skip if bitrate is already at or below target codec's optimal bitrate
            # This prevents re-encoding already efficient H.264 files
            if current_bitrate <= optimal_bitrate * 1.2:
                current_mbps = current_bitrate / 1_000_000
                optimal_mbps = optimal_bitrate / 1_000_000

                if current_bitrate <= optimal_bitrate:
                    reason = f"Already efficiently encoded: {current_codec} at {current_mbps:.1f}Mbps (target {target_codec}: {optimal_mbps:.1f}Mbps)"
                else:
                    reason = f"Already well compressed: {current_codec} at {current_mbps:.1f}Mbps (target {target_codec}: {optimal_mbps:.1f}Mbps)"

                return True, reason

        except (ValueError, KeyError):
            # Can't determine bitrate, continue to check if already target codec
            pass

        # If bitrate check didn't skip, check if already target codec
        if current_codec != target_codec:
            return False, None

        return False, None

    except Exception as e:
        logger.debug(f"Error checking if file is optimal: {e}")
        return False, None


def get_optimal_bitrate_for_resolution(resolution, codec):
    """Get optimal bitrate in bps for a given resolution and codec"""
    # Resolution-based bitrate targets (in Mbps)
    bitrate_map = {
        'hevc': {
            '3840x2160': 15_000_000,  # 4K
            '2560x1440': 8_000_000,   # 1440p
            '1920x1080': 4_000_000,   # 1080p
            '1280x720': 2_000_000,    # 720p
            '854x480': 1_000_000,     # 480p
        },
        'h264': {
            '3840x2160': 25_000_000,
            '2560x1440': 12_000_000,
            '1920x1080': 6_000_000,
            '1280x720': 3_000_000,
            '854x480': 1_500_000,
        },
        'av1': {
            '3840x2160': 10_000_000,
            '2560x1440': 5_000_000,
            '1920x1080': 2_500_000,
            '1280x720': 1_500_000,
            '854x480': 750_000,
        }
    }

    codec_map = bitrate_map.get(codec, bitrate_map['hevc'])

    # Try exact match first
    if resolution in codec_map:
        return codec_map[resolution]

    # Fallback: parse resolution and find closest
    try:
        width, height = map(int, resolution.split('x'))
        pixels = width * height

        # 4K range
        if pixels >= 3840 * 2160 * 0.8:
            return codec_map['3840x2160']
        # 1440p range
        elif pixels >= 2560 * 1440 * 0.8:
            return codec_map['2560x1440']
        # 1080p range
        elif pixels >= 1920 * 1080 * 0.8:
            return codec_map['1920x1080']
        # 720p range
        elif pixels >= 1280 * 720 * 0.8:
            return codec_map['1280x720']
        else:
            return codec_map['854x480']

    except:
        # Default to 1080p
        return codec_map['1920x1080']


# ============================================================================
# PLUGIN HOOKS
# ============================================================================

def on_library_management_file_test(data):
    """Determine if a file should be added to pending tasks"""
    abspath = data.get('path')

    if not abspath:
        return data

    # Check if video file
    video_extensions = ['.mkv', '.mp4', '.avi', '.mov', '.m4v', '.wmv', '.flv', '.webm', '.mpg', '.mpeg', '.m2ts', '.ts']
    file_extension = os.path.splitext(abspath)[1].lower()

    if file_extension not in video_extensions:
        return data

    # ========================================================================
    # v2.5.0: PRE-FLIGHT FILE VALIDATION
    # ========================================================================
    # Validate file before queueing to prevent failures from corrupted/missing files
    is_valid, error_category, error_message = validate_source_file(abspath)

    if not is_valid:
        logger.warning(f"[{error_category}] {error_message}")
        data['add_file_to_pending_tasks'] = False
        return data

    # Get settings
    settings = Settings(library_id=data.get('library_id'))
    effective_settings = get_effective_settings(settings)

    target_codec = effective_settings.get_setting('target_codec')
    skip_10bit = effective_settings.get_setting('skip_10bit_files')

    # ========================================================================
    # v2.5.0: SKIP ALREADY OPTIMAL FILES
    # ========================================================================
    # Check if file is already optimally encoded
    should_skip, skip_reason = is_already_optimal(abspath, effective_settings)

    if should_skip:
        logger.info(f"Skipping optimal file: {skip_reason} - {abspath}")
        data['add_file_to_pending_tasks'] = False
        return data

    # Check if already in target codec
    if target_codec != 'copy':
        try:
            current_codec = detect_source_codec(abspath)

            if current_codec == target_codec:
                # Check bit depth
                bit_depth = detect_video_bit_depth(abspath)

                # Skip 10-bit files if requested
                if skip_10bit and bit_depth >= 10:
                    logger.info(f"File '{abspath}' is {bit_depth}-bit, skipping (skip_10bit_files enabled)")
                    data['add_file_to_pending_tasks'] = False
                    return data

                # Skip if already target codec and same bit depth
                logger.info(f"File '{abspath}' is already {target_codec} {bit_depth}-bit, skipping transcoding")
                data['add_file_to_pending_tasks'] = False
                return data

        except Exception as e:
            logger.debug(f"Error detecting codec for '{abspath}': {e}")

    # Add to pending tasks
    data['add_file_to_pending_tasks'] = True
    logger.debug(f"File '{abspath}' should be added to pending tasks")

    return data


def get_expert_template_command(template):
    """Get FFmpeg command template for Expert mode (v2.7.0)"""
    templates = {
        'gpu_hevc': "ffmpeg -vaapi_device {render_device} -hwaccel vaapi -hwaccel_output_format vaapi -i {input} -c:v hevc_vaapi -qp 23 -c:a aac -b:a 192k {output}",
        'cpu_hevc': "ffmpeg -i {input} -c:v libx265 -crf 20 -preset medium -c:a aac -b:a 192k {output}",
        'gpu_h264': "ffmpeg -vaapi_device {render_device} -hwaccel vaapi -hwaccel_output_format vaapi -i {input} -c:v h264_vaapi -qp 23 -c:a aac -b:a 192k {output}",
        'cpu_h264': "ffmpeg -i {input} -c:v libx264 -crf 20 -preset medium -c:a aac -b:a 192k {output}",
        'av1': "ffmpeg -vaapi_device {render_device} -hwaccel vaapi -hwaccel_output_format vaapi -i {input} -c:v av1_vaapi -qp 30 -c:a aac -b:a 192k {output}",
    }
    return templates.get(template, templates['gpu_hevc'])


def on_worker_process(data):
    """Main worker function - build and execute FFmpeg command"""

    # Get file paths
    file_in = data.get('file_in')
    file_out = data.get('file_out')

    if not file_in or not file_out:
        logger.error("Missing input or output file")
        return data

    # Get settings
    settings_obj = Settings(library_id=data.get('library_id'))
    settings = get_effective_settings(settings_obj)

    # Handle output container format (v2.7.0)
    output_container = settings_obj.get_setting('output_container')
    if output_container != 'same':
        # Change file extension
        import os
        base = os.path.splitext(file_out)[0]
        file_out = f"{base}.{output_container}"
        # CRITICAL: Update data dict so Unmanic knows the correct output path
        data['file_out'] = file_out

    # EXPERT MODE: Use custom FFmpeg command
    config_mode = settings_obj.get_setting('config_mode')
    if config_mode == 'expert':
        expert_template = settings_obj.get_setting('expert_template')
        expert_command = settings_obj.get_setting('expert_command')

        # Use template if not custom
        if expert_template != 'custom':
            expert_command = get_expert_template_command(expert_template)

        if not expert_command or expert_command.strip() == '':
            logger.error("Expert mode enabled but no custom command provided")
            data['exec_command'] = None
            return data

        # Get video info for variable substitution
        video_duration = get_video_duration(file_in)
        width, height = get_resolution(file_in)
        source_codec = detect_source_codec(file_in)

        # Get bitrate estimate
        try:
            file_size = os.path.getsize(file_in)
            bitrate_kbps = int((file_size * 8) / (video_duration * 1000)) if video_duration > 0 else 0
        except:
            bitrate_kbps = 0

        # Detect hardware for variable substitution
        gpu_info = detect_amd_gpu()

        # Variable substitution (v2.7.0: added more variables)
        expert_command = expert_command.replace('{input}', file_in)
        expert_command = expert_command.replace('{output}', file_out)
        expert_command = expert_command.replace('{render_device}', gpu_info.get('render_device', '/dev/dri/renderD128'))
        expert_command = expert_command.replace('{width}', str(width))
        expert_command = expert_command.replace('{height}', str(height))
        expert_command = expert_command.replace('{bitrate}', f"{bitrate_kbps}k")
        expert_command = expert_command.replace('{duration}', str(int(video_duration)))
        expert_command = expert_command.replace('{codec}', source_codec)

        logger.info(f"EXPERT MODE: Using custom command")
        logger.debug(f"Expert command: {expert_command}")

        # Parse command string into list
        import shlex
        data['exec_command'] = shlex.split(expert_command)
        data['command_progress_parser'] = FFmpegProgressParser
        return data

    # Get video info
    video_duration = get_video_duration(file_in)
    bit_depth = detect_video_bit_depth(file_in)
    width, height = get_resolution(file_in)

    logger.info(f"Video info: {width}x{height}, {bit_depth}-bit, {video_duration:.1f}s ({video_duration/60:.1f} min)")

    # Detect hardware
    gpu_info = detect_amd_gpu()
    cpu_info = detect_amd_cpu()

    # Get encoding settings
    mode = settings.get_setting('encoding_mode')
    prefer_amf = settings.get_setting('prefer_amf_over_vaapi')
    target_codec = settings.get_setting('target_codec')

    # Determine target codec
    if target_codec == 'copy':
        target_codec = detect_source_codec(file_in)

    # Get encoder
    encoder, encoder_type = get_encoder(target_codec, gpu_info, cpu_info, mode, prefer_amf)

    # Handle 10-bit sources with VAAPI
    if encoder.endswith('_vaapi') and bit_depth >= 10:
        if not gpu_info['capabilities'].get('supports_hevc_10bit'):
            logger.warning(f"GPU doesn't support 10-bit HEVC - falling back to CPU")
            encoder = 'libx265'
            encoder_type = 'cpu'

    logger.info(f"Encoder: {encoder} ({encoder_type}), Mode: {mode}, Codec: {target_codec}")

    # Validate parameters
    errors, warnings = validate_encoding_params(encoder, encoder_type, file_in, settings, gpu_info)

    for warning in warnings:
        logger.warning(warning)

    if errors:
        for error in errors:
            logger.error(error)
        data['exec_command'] = None
        return data

    # Build FFmpeg command
    cmd = ['ffmpeg', '-hide_banner', '-loglevel', 'info']

    # Hardware acceleration setup (before input)
    if encoder.endswith('_vaapi'):
        cmd.extend(['-vaapi_device', gpu_info['render_device']])
        cmd.extend(['-hwaccel', 'vaapi'])
        cmd.extend(['-hwaccel_output_format', 'vaapi'])

    # Test mode - limit duration
    test_duration = settings.get_setting('test_encode_duration')
    if test_duration > 0:
        logger.info(f"TEST MODE: Encoding first {test_duration} seconds only")
        cmd.extend(['-t', str(test_duration)])

    # Input file
    cmd.extend(['-i', file_in])

    # Map all streams (excluding attached pictures to avoid encoding errors)
    if settings.get_setting('copy_subtitles') or settings.get_setting('audio_mode') == 'all':
        cmd.extend(['-map', '0:v:0'])  # Map only first video stream
        cmd.extend(['-map', '0:a?'])   # Map all audio streams (? = optional)
        cmd.extend(['-map', '0:s?'])   # Map all subtitle streams (? = optional)

    # Video encoding
    cmd.extend(['-c:v', encoder])

    # Video filters (crop, etc.)
    video_filters = []

    if settings.get_setting('auto_crop'):
        crop_filter = detect_crop(file_in)
        if crop_filter:
            logger.info(f"Auto-crop enabled: {crop_filter}")
            video_filters.append(crop_filter)

    if video_filters:
        filter_str = ','.join(video_filters)
        if encoder.endswith('_vaapi'):
            # VAAPI needs special handling - apply before hwupload
            cmd.extend(['-vf', filter_str])
        else:
            cmd.extend(['-vf', filter_str])

    # Encoder-specific parameters
    if encoder.endswith('_amf'):
        quality = settings.get_setting('video_quality')
        cmd.extend(['-quality', quality, '-usage', 'transcoding'])

    elif encoder.endswith('_vaapi'):
        rate_control = settings.get_setting('rate_control')

        if rate_control == 'crf':
            crf = int(settings.get_setting('crf_value'))
            quality = max(0, min(51, crf))
            cmd.extend(['-global_quality', str(quality)])

            # v2.7.7: Add bitrate cap to prevent CRF from exceeding source bitrate
            source_bitrate = detect_source_bitrate(file_in)
            if source_bitrate > 0:
                # Cap at 1.5x source bitrate to prevent file bloat
                max_bitrate = int(source_bitrate * 1.5)
                max_bitrate_str = f"{max_bitrate}"
                cmd.extend(['-maxrate', max_bitrate_str])
                logger.info(f"CRF mode: Capping bitrate at {max_bitrate / 1_000_000:.1f}Mbps (1.5x source)")
        else:
            cmd.extend(['-rc_mode', 'VBR'])
            cmd.extend(['-qp', '20'])

            # v2.7.7: Add bitrate cap for VBR mode too
            source_bitrate = detect_source_bitrate(file_in)
            if source_bitrate > 0:
                # Cap at 1.5x source bitrate to prevent file bloat
                max_bitrate = int(source_bitrate * 1.5)
                max_bitrate_str = f"{max_bitrate}"
                cmd.extend(['-maxrate', max_bitrate_str])
                logger.info(f"VBR mode: Capping bitrate at {max_bitrate / 1_000_000:.1f}Mbps (1.5x source)")

        # Profile and level
        if encoder == 'hevc_vaapi':
            # Use main10 for 10-bit sources on supported GPUs
            if bit_depth >= 10 and gpu_info['capabilities'].get('supports_hevc_10bit'):
                profile = 'main10'
                logger.info("Using HEVC Main 10 profile for 10-bit encoding")
            else:
                profile = 'main'

            cmd.extend(['-profile:v', profile, '-level', '5.1'])

    elif encoder == 'libx264':
        rate_control = settings.get_setting('rate_control')

        if rate_control == 'crf':
            crf = settings.get_setting('crf_value')
            cmd.extend(['-crf', crf])

        cmd.extend(['-preset', 'medium'])

        if cpu_info['cores'] > 1:
            threads = min(16, cpu_info['cores'])
            cmd.extend(['-threads', str(threads)])

    elif encoder == 'libx265':
        rate_control = settings.get_setting('rate_control')

        if rate_control == 'crf':
            crf = settings.get_setting('crf_value')
            cmd.extend(['-crf', crf])

        cmd.extend(['-preset', 'medium'])

        # x265 parameters
        x265_params = []

        if cpu_info['cores'] > 1:
            pools = min(16, cpu_info['cores'] // 2)
            x265_params.append(f'pools={pools}')

        if settings.get_setting('use_scene_detection'):
            x265_params.extend([
                'scenecut=40',
                'aq-mode=3',
                'aq-strength=1.0',
                'psy-rd=2.0',
                'psy-rdoq=1.0',
            ])

        if x265_params:
            cmd.extend(['-x265-params', ':'.join(x265_params)])

    elif encoder == 'libsvtav1':
        crf = settings.get_setting('crf_value')
        cmd.extend(['-crf', crf, '-preset', '6'])

    # Bitrate (for VBR/CBR modes with hardware encoders)
    if settings.get_setting('rate_control') in ['vbr', 'cbr'] and encoder.endswith(('_amf', '_vaapi')):
        if settings.get_setting('use_auto_bitrate'):
            bitrate, max_bitrate = get_optimal_bitrate(file_in, target_codec)
            logger.info(f"Auto-selected bitrate: {bitrate} (max: {max_bitrate}) for {width}x{height}")
        else:
            bitrate = settings.get_setting('bitrate')
            max_bitrate = settings.get_setting('max_bitrate')

        cmd.extend(['-b:v', bitrate, '-maxrate', max_bitrate])

    # HDR metadata
    if settings.get_setting('preserve_hdr'):
        hdr_info = detect_hdr_metadata(file_in)
        if hdr_info and hdr_info['is_hdr']:
            logger.info(f"HDR content detected: {hdr_info['hdr_type']}")

            if encoder.endswith('_vaapi'):
                cmd.extend([
                    '-color_primaries', hdr_info['primaries'],
                    '-color_trc', hdr_info['transfer'],
                    '-colorspace', hdr_info['space'],
                ])
            elif encoder == 'libx265':
                x265_hdr = [
                    f"colorprim={hdr_info['primaries']}",
                    f"transfer={hdr_info['transfer']}",
                    f"colormatrix={hdr_info['space']}",
                    "hdr10=1",
                ]
                # Append to existing params or create new
                existing_params = next((i for i, x in enumerate(cmd) if x == '-x265-params'), None)
                if existing_params:
                    cmd[existing_params + 1] += ':' + ':'.join(x265_hdr)
                else:
                    cmd.extend(['-x265-params', ':'.join(x265_hdr)])

    # Audio encoding
    audio_mode = settings.get_setting('audio_mode')
    audio_codec = settings.get_setting('audio_codec')

    if audio_mode == 'all':
        if audio_codec == 'copy':
            cmd.extend(['-c:a', 'copy'])
        else:
            audio_bitrate = settings.get_setting('audio_bitrate')

            if settings.get_setting('downmix_multichannel'):
                # Downmix to stereo
                cmd.extend(['-c:a', audio_codec, '-ac', '2', '-b:a', audio_bitrate])
            else:
                # Use per-stream encoding to handle multi-channel properly
                # For AAC with 5.1/multi-channel, use higher bitrate and specify channel layout
                cmd.extend(['-c:a', audio_codec])
                # Use filter to ensure proper channel layout for multi-channel audio
                cmd.extend(['-b:a:0', audio_bitrate])  # Per-stream bitrate
                # Add channel layout specification for AAC to avoid "Unsupported channel layout" error
                if audio_codec == 'aac':
                    cmd.extend(['-channel_layout:a', '0'])  # Auto-detect from input

    elif audio_mode == 'first':
        cmd.extend(['-map', '0:a:0'])
        cmd.extend(['-c:a', audio_codec if audio_codec != 'copy' else 'copy'])

    elif audio_mode == 'language':
        lang = settings.get_setting('audio_language')
        cmd.extend(['-map', f'0:a:m:language:{lang}?'])
        cmd.extend(['-c:a', audio_codec if audio_codec != 'copy' else 'copy'])

    # Subtitles
    if settings.get_setting('copy_subtitles'):
        sub_format = settings.get_setting('subtitle_format')
        if sub_format == 'copy':
            cmd.extend(['-c:s', 'copy'])
        else:
            cmd.extend(['-c:s', sub_format])

    # Output options
    cmd.extend(['-movflags', '+faststart'])
    cmd.extend(['-y', file_out])

    # Dry run mode
    if settings.get_setting('dry_run'):
        logger.info("=" * 80)
        logger.info("DRY RUN MODE - Command preview:")
        logger.info(" ".join(cmd))
        logger.info("=" * 80)
        data['exec_command'] = None
        return data

    # Set command
    data['exec_command'] = cmd

    # Progress parser
    if video_duration > 0:
        default_parser = data.get('command_progress_parser')
        progress_parser = FFmpegProgressParser(video_duration, default_parser)
        data['command_progress_parser'] = progress_parser.parse
        logger.info("FFmpeg progress parser enabled")

    # Worker log
    if 'worker_log' in data:
        data['worker_log'].append(f"[AMD] Encoder: {encoder} ({encoder_type})")
        data['worker_log'].append(f"[AMD] Resolution: {width}x{height}, {bit_depth}-bit")
        if video_duration > 0:
            data['worker_log'].append(f"[AMD] Duration: {video_duration/60:.1f} minutes")

    return data
