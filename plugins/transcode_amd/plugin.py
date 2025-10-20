#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    plugins.transcode_amd.plugin.py

    Written by:               viennej <viennej@github.com>
    Date:                     2025-01-27
"""

import os
import subprocess
import logging
import re

from unmanic.libs.unplugins.settings import PluginSettings

# Plugin metadata
__title__ = "Transcode AMD"
__author__ = "viennej"
__version__ = "1.1.0"
__description__ = "AMD Hardware Acceleration Transcoding Plugin - CPU and GPU support"
__icon__ = ""


logger = logging.getLogger("Unmanic.Plugin.transcode_amd")


class Settings(PluginSettings):
    settings = {
        "encoding_mode": "auto",
        "prefer_amf_over_vaapi": True,
        "fallback_to_software": True,
        "video_quality": "balanced",
        "target_codec": "h264",
        "bitrate": "2M",
        "max_bitrate": "4M",
        "audio_codec": "aac",
        "audio_bitrate": "128k",
        "show_capabilities": False
    }

    def __init__(self, *args, **kwargs):
        super(Settings, self).__init__(*args, **kwargs)
        
        # Detect capabilities for info display
        caps = detect_amd_capabilities()
        caps_info = self._format_capabilities_info(caps)
        
        self.form_settings = {
            "encoding_mode": {
                "label": "Encoding Mode",
                "input_type": "select",
                "select_options": [
                    {
                        "value": "auto",
                        "label": "Auto (prefer GPU, fallback to CPU)",
                    },
                    {
                        "value": "gpu_only",
                        "label": "GPU Only (VAAPI/AMF)",
                    },
                    {
                        "value": "cpu_only",
                        "label": "CPU Only (software encoding)",
                    },
                ],
            },
            "prefer_amf_over_vaapi": {
                "label": "Prefer AMF over VAAPI (GPU mode)",
            },
            "fallback_to_software": {
                "label": "Fallback to software encoding on error",
            },
            "show_capabilities": {
                "label": f"AMD Capabilities Detected:\n{caps_info}",
                "sub_setting": True,
            },
            "video_quality": {
                "label": "Video Quality (for hardware encoding)",
                "input_type": "select",
                "select_options": [
                    {
                        "value": "speed",
                        "label": "Speed (fastest)",
                    },
                    {
                        "value": "balanced",
                        "label": "Balanced (recommended)",
                    },
                    {
                        "value": "quality",
                        "label": "Quality (best)",
                    },
                ],
            },
            "target_codec": {
                "label": "Target Codec",
                "input_type": "select",
                "select_options": [
                    {
                        "value": "h264",
                        "label": "H.264/AVC",
                    },
                    {
                        "value": "hevc",
                        "label": "H.265/HEVC",
                    },
                    {
                        "value": "copy",
                        "label": "Copy (same as source)",
                    },
                ],
            },
            "bitrate": {
                "label": "Video Bitrate (e.g., 2M, 5M)",
            },
            "max_bitrate": {
                "label": "Max Video Bitrate (e.g., 4M, 8M)",
            },
            "audio_codec": {
                "label": "Audio Codec",
                "input_type": "select",
                "select_options": [
                    {
                        "value": "aac",
                        "label": "AAC",
                    },
                    {
                        "value": "copy",
                        "label": "Copy",
                    },
                ],
            },
            "audio_bitrate": {
                "label": "Audio Bitrate (e.g., 128k, 256k)",
            },
        }
    
    def _format_capabilities_info(self, caps):
        """Format capabilities info for display"""
        lines = []
        
        # CPU Info
        if caps['cpu']['detected']:
            lines.append(f"🔹 CPU: {caps['cpu']['model']}")
            lines.append(f"  Cores: {caps['cpu']['cores']}")
            if caps['cpu']['features']:
                lines.append(f"  Features: {', '.join(caps['cpu']['features'][:5])}")
        else:
            lines.append("🔹 AMD CPU: Not detected")
        
        lines.append("")
        
        # GPU Info
        if caps['gpu']['detected']:
            lines.append(f"🔹 GPU: {caps['gpu']['model']}")
            lines.append(f"  Vendor ID: {caps['gpu']['vendor_id']}")
            if caps['gpu']['device_id']:
                lines.append(f"  Device ID: {caps['gpu']['device_id']}")
        else:
            lines.append("🔹 AMD GPU: Not detected")
        
        lines.append("")
        
        # Hardware Encoders
        lines.append("🔹 Hardware Encoders:")
        if caps['encoders']['amf']:
            lines.append(f"  AMF: {', '.join(caps['encoders']['amf'])}")
        if caps['encoders']['vaapi']:
            lines.append(f"  VAAPI: {', '.join(caps['encoders']['vaapi'])}")
        if not caps['encoders']['amf'] and not caps['encoders']['vaapi']:
            lines.append("  None detected")
        
        lines.append("")
        
        # Software Encoders
        lines.append("🔹 Software Encoders:")
        if caps['encoders']['software']:
            lines.append(f"  {', '.join(caps['encoders']['software'])}")
        
        return "\n".join(lines)


def detect_amd_cpu():
    """Detect AMD CPU and its features"""
    cpu_info = {
        'detected': False,
        'model': 'Unknown',
        'cores': 0,
        'threads': 0,
        'features': []
    }
    
    try:
        # Check CPU model
        with open('/proc/cpuinfo', 'r') as f:
            cpuinfo = f.read()
            
        # Check if AMD CPU
        if 'AMD' in cpuinfo or 'AuthenticAMD' in cpuinfo:
            cpu_info['detected'] = True
            
            # Get model name
            model_match = re.search(r'model name\s+:\s+(.+)', cpuinfo)
            if model_match:
                cpu_info['model'] = model_match.group(1).strip()
            
            # Count cores and threads
            cpu_info['cores'] = cpuinfo.count('processor')
            
            # Get CPU flags/features
            flags_match = re.search(r'flags\s+:\s+(.+)', cpuinfo)
            if flags_match:
                all_flags = flags_match.group(1).split()
                # Filter for important AMD features
                important_features = ['avx', 'avx2', 'avx512', 'sse4_1', 'sse4_2', 'fma', 'aes']
                cpu_info['features'] = [f for f in all_flags if any(feat in f for feat in important_features)]
        
    except Exception as e:
        logger.debug(f"Error detecting AMD CPU: {e}")
    
    return cpu_info


def detect_amd_gpu():
    """Detect AMD GPU and available hardware acceleration"""
    gpu_info = {
        'detected': False,
        'model': 'Unknown',
        'vendor_id': '',
        'device_id': '',
        'render_device': '/dev/dri/renderD128',
        'driver': 'unknown'
    }
    
    try:
        # Check for AMD GPU via lspci
        result = subprocess.run(['lspci', '-nn'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if 'vga' in line.lower() or 'display' in line.lower():
                    if 'amd' in line.lower() or 'ati' in line.lower() or 'radeon' in line.lower():
                        gpu_info['detected'] = True
                        gpu_info['model'] = line.strip()
                        
                        # Extract vendor and device IDs
                        id_match = re.search(r'\[([0-9a-f]{4}):([0-9a-f]{4})\]', line)
                        if id_match:
                            gpu_info['vendor_id'] = id_match.group(1)
                            gpu_info['device_id'] = id_match.group(2)
                        break
        
        # Check for render devices
        if os.path.exists('/dev/dri'):
            render_devices = [f for f in os.listdir('/dev/dri') if f.startswith('renderD')]
            if render_devices:
                gpu_info['render_device'] = f'/dev/dri/{render_devices[0]}'
        
        # Try to detect driver
        if os.path.exists('/sys/module/amdgpu'):
            gpu_info['driver'] = 'amdgpu'
        elif os.path.exists('/sys/module/radeon'):
            gpu_info['driver'] = 'radeon'
                
    except Exception as e:
        logger.debug(f"Error detecting AMD GPU: {e}")
    
    return gpu_info


def detect_ffmpeg_encoders():
    """Detect available FFmpeg encoders"""
    encoders = {
        'amf': [],
        'vaapi': [],
        'software': []
    }
    
    try:
        result = subprocess.run(['ffmpeg', '-encoders'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            lines = result.stdout.split('\n')
            for line in lines:
                # AMF encoders
                if '_amf' in line:
                    encoder_match = re.search(r'(\w+_amf)', line)
                    if encoder_match:
                        encoders['amf'].append(encoder_match.group(1))
                
                # VAAPI encoders
                elif '_vaapi' in line:
                    encoder_match = re.search(r'(\w+_vaapi)', line)
                    if encoder_match:
                        encoders['vaapi'].append(encoder_match.group(1))
                
                # Software encoders (common ones)
                elif any(enc in line for enc in ['libx264', 'libx265', 'libsvtav1', 'libvpx']):
                    for enc in ['libx264', 'libx265', 'libsvtav1', 'libvpx-vp9']:
                        if enc in line and enc not in encoders['software']:
                            encoders['software'].append(enc)
    
    except Exception as e:
        logger.debug(f"Error detecting encoders: {e}")
    
    return encoders


def detect_amd_capabilities():
    """Detect all AMD hardware capabilities (CPU + GPU)"""
    return {
        'cpu': detect_amd_cpu(),
        'gpu': detect_amd_gpu(),
        'encoders': detect_ffmpeg_encoders()
    }


def get_optimal_encoder(codec, capabilities, mode, prefer_amf):
    """Get optimal encoder for codec based on mode"""
    encoder_map = {
        'h264': {
            'amf': 'h264_amf',
            'vaapi': 'h264_vaapi',
            'software': 'libx264'
        },
        'hevc': {
            'amf': 'hevc_amf',
            'vaapi': 'hevc_vaapi',
            'software': 'libx265'
        }
    }
    
    if codec not in encoder_map:
        return ('libx264', 'cpu')
    
    codec_encoders = encoder_map[codec]
    encoders_available = capabilities['encoders']
    
    # CPU only mode
    if mode == 'cpu_only':
        return (codec_encoders['software'], 'cpu')
    
    # GPU only mode
    if mode == 'gpu_only':
        if prefer_amf and codec_encoders.get('amf') in encoders_available.get('amf', []):
            return (codec_encoders['amf'], 'gpu')
        elif codec_encoders.get('vaapi') in encoders_available.get('vaapi', []):
            return (codec_encoders['vaapi'], 'gpu')
        else:
            # Fallback to CPU if GPU not available
            return (codec_encoders['software'], 'cpu')
    
    # Auto mode (prefer GPU, fallback to CPU)
    if prefer_amf and codec_encoders.get('amf') in encoders_available.get('amf', []):
        return (codec_encoders['amf'], 'gpu')
    elif codec_encoders.get('vaapi') in encoders_available.get('vaapi', []):
        return (codec_encoders['vaapi'], 'gpu')
    else:
        return (codec_encoders['software'], 'cpu')


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
    except Exception as e:
        logger.debug(f"Error detecting codec: {e}")
    
    return 'h264'


def on_worker_process(data):
    """
    Runner function - Transcode video with AMD hardware acceleration
    """
    # Get settings
    settings = Settings(library_id=data.get('library_id'))
    
    # Get file paths
    file_in = data.get('file_in')
    file_out = data.get('file_out')
    
    if not file_in or not file_out:
        logger.error("Missing input or output file")
        return data
    
    # Detect AMD capabilities (CPU + GPU)
    capabilities = detect_amd_capabilities()
    
    # Log detected hardware
    logger.info("=== AMD Hardware Detection ===")
    if capabilities['cpu']['detected']:
        logger.info(f"CPU: {capabilities['cpu']['model']}")
        logger.info(f"CPU Cores: {capabilities['cpu']['cores']}")
    else:
        logger.info("AMD CPU: Not detected")
    
    if capabilities['gpu']['detected']:
        logger.info(f"GPU: {capabilities['gpu']['model']}")
        logger.info(f"GPU Driver: {capabilities['gpu']['driver']}")
    else:
        logger.info("AMD GPU: Not detected")
    
    logger.info(f"Available encoders - AMF: {capabilities['encoders']['amf']}")
    logger.info(f"Available encoders - VAAPI: {capabilities['encoders']['vaapi']}")
    logger.info(f"Available encoders - Software: {capabilities['encoders']['software']}")
    
    # Get encoding mode
    encoding_mode = settings.get_setting('encoding_mode')
    logger.info(f"Encoding mode: {encoding_mode}")
    
    # Determine target codec
    target_codec = settings.get_setting('target_codec')
    if target_codec == 'copy':
        target_codec = detect_source_codec(file_in)
    logger.info(f"Target codec: {target_codec}")
    
    # Get optimal encoder
    prefer_amf = settings.get_setting('prefer_amf_over_vaapi')
    encoder, encoder_type = get_optimal_encoder(target_codec, capabilities, encoding_mode, prefer_amf)
    logger.info(f"Selected encoder: {encoder} (type: {encoder_type})")
    
    # Build FFmpeg command
    cmd = ['ffmpeg', '-hide_banner', '-loglevel', 'info', '-i', file_in]
    
    # Add hardware acceleration if using VAAPI
    if encoder.endswith('_vaapi'):
        render_device = capabilities['gpu']['render_device']
        cmd.extend(['-vaapi_device', render_device])
        cmd.extend(['-hwaccel', 'vaapi'])
        cmd.extend(['-hwaccel_output_format', 'vaapi'])
    
    # Add video encoding
    cmd.extend(['-c:v', encoder])
    
    # Add encoder-specific parameters
    if encoder.endswith('_amf'):
        quality = settings.get_setting('video_quality')
        cmd.extend(['-quality', quality])
        cmd.extend(['-rc', 'vbr'])
    elif encoder.endswith('_vaapi'):
        cmd.extend(['-qp', '23'])
    elif encoder == 'libx264':
        # CPU encoding with optimizations
        cmd.extend(['-preset', 'medium', '-crf', '23'])
        # Use available CPU threads
        if capabilities['cpu']['detected'] and capabilities['cpu']['cores'] > 0:
            threads = max(1, capabilities['cpu']['cores'] - 1)  # Leave one core free
            cmd.extend(['-threads', str(threads)])
    elif encoder == 'libx265':
        cmd.extend(['-preset', 'medium', '-crf', '25'])
        if capabilities['cpu']['detected'] and capabilities['cpu']['cores'] > 0:
            threads = max(1, capabilities['cpu']['cores'] - 1)
            cmd.extend(['-threads', str(threads)])
    
    # Add bitrate for hardware encoders
    if encoder.endswith('_amf') or encoder.endswith('_vaapi'):
        bitrate = settings.get_setting('bitrate')
        max_bitrate = settings.get_setting('max_bitrate')
        cmd.extend(['-b:v', bitrate])
        cmd.extend(['-maxrate', max_bitrate])
    
    # Add audio encoding
    audio_codec = settings.get_setting('audio_codec')
    if audio_codec == 'copy':
        cmd.extend(['-c:a', 'copy'])
    else:
        audio_bitrate = settings.get_setting('audio_bitrate')
        cmd.extend(['-c:a', audio_codec, '-b:a', audio_bitrate])
    
    # Add output settings
    cmd.extend(['-y', file_out])
    
    # Set command in data
    data['exec_command'] = cmd
    
    # Log info
    logger.info(f"FFmpeg command: {' '.join(cmd)}")
    
    # Add user-friendly log messages
    data['worker_log'].append(f"[Transcode AMD] Mode: {encoding_mode}")
    data['worker_log'].append(f"[Transcode AMD] Encoder: {encoder} ({encoder_type.upper()})")
    
    if capabilities['cpu']['detected']:
        data['worker_log'].append(f"[Transcode AMD] CPU: {capabilities['cpu']['model'][:50]}")
    
    if capabilities['gpu']['detected']:
        gpu_name = capabilities['gpu']['model'].split('controller:')[-1].strip() if 'controller:' in capabilities['gpu']['model'] else capabilities['gpu']['model']
        data['worker_log'].append(f"[Transcode AMD] GPU: {gpu_name[:50]}")
    
    return data
