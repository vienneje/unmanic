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

from unmanic.libs.unplugins.settings import PluginSettings

# Plugin metadata
__title__ = "Transcode AMD"
__author__ = "viennej"
__version__ = "1.0.1"
__description__ = "AMD Hardware Acceleration Transcoding Plugin"
__icon__ = ""


logger = logging.getLogger("Unmanic.Plugin.transcode_amd")


class Settings(PluginSettings):
    settings = {
        "prefer_amf_over_vaapi": True,
        "fallback_to_software": True,
        "video_quality": "balanced",
        "target_codec": "h264",
        "bitrate": "2M",
        "max_bitrate": "4M",
        "audio_codec": "aac",
        "audio_bitrate": "128k"
    }

    def __init__(self, *args, **kwargs):
        super(Settings, self).__init__(*args, **kwargs)
        self.form_settings = {
            "prefer_amf_over_vaapi": {
                "label": "Prefer AMF over VAAPI",
            },
            "fallback_to_software": {
                "label": "Fallback to software encoding",
            },
            "video_quality": {
                "label": "Video Quality (AMF)",
                "input_type": "select",
                "select_options": [
                    {
                        "value": "speed",
                        "label": "Speed",
                    },
                    {
                        "value": "balanced",
                        "label": "Balanced",
                    },
                    {
                        "value": "quality",
                        "label": "Quality",
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


def detect_amd_gpu():
    """Detect AMD GPU and available hardware acceleration"""
    capabilities = {
        'has_vaapi': False,
        'has_amf': False,
        'render_device': '/dev/dri/renderD128',
        'gpu_detected': False
    }
    
    try:
        # Check for AMD GPU via lspci
        result = subprocess.run(['lspci'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if 'vga' in line.lower() or 'display' in line.lower():
                    if 'amd' in line.lower() or 'ati' in line.lower() or 'radeon' in line.lower():
                        capabilities['gpu_detected'] = True
                        break
        
        # Check for render devices
        if os.path.exists('/dev/dri'):
            render_devices = [f for f in os.listdir('/dev/dri') if f.startswith('renderD')]
            if render_devices:
                capabilities['render_device'] = f'/dev/dri/{render_devices[0]}'
        
        # Check FFmpeg encoders
        result = subprocess.run(['ffmpeg', '-encoders'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            encoders = result.stdout
            if 'h264_amf' in encoders:
                capabilities['has_amf'] = True
            if 'h264_vaapi' in encoders:
                capabilities['has_vaapi'] = True
                
    except Exception as e:
        logger.debug(f"Error detecting AMD GPU: {e}")
    
    return capabilities


def get_optimal_encoder(codec, capabilities, prefer_amf):
    """Get optimal encoder for codec"""
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
        return 'libx264'
    
    codec_encoders = encoder_map[codec]
    
    # Choose encoder based on capabilities
    if prefer_amf and capabilities['has_amf'] and 'amf' in codec_encoders:
        return codec_encoders['amf']
    elif capabilities['has_vaapi'] and 'vaapi' in codec_encoders:
        return codec_encoders['vaapi']
    else:
        return codec_encoders.get('software', 'libx264')


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
    
    # Detect AMD capabilities
    capabilities = detect_amd_gpu()
    logger.info(f"AMD GPU detected: {capabilities['gpu_detected']}")
    logger.info(f"VAAPI: {capabilities['has_vaapi']}, AMF: {capabilities['has_amf']}")
    
    # Determine target codec
    target_codec = settings.get_setting('target_codec')
    if target_codec == 'copy':
        target_codec = detect_source_codec(file_in)
    
    # Get optimal encoder
    prefer_amf = settings.get_setting('prefer_amf_over_vaapi')
    encoder = get_optimal_encoder(target_codec, capabilities, prefer_amf)
    logger.info(f"Selected encoder: {encoder}")
    
    # Build FFmpeg command
    cmd = ['ffmpeg', '-hide_banner', '-loglevel', 'info', '-i', file_in]
    
    # Add hardware acceleration if using VAAPI
    if encoder.endswith('_vaapi'):
        cmd.extend(['-vaapi_device', capabilities['render_device']])
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
        cmd.extend(['-preset', 'medium', '-crf', '23'])
    elif encoder == 'libx265':
        cmd.extend(['-preset', 'medium', '-crf', '25'])
    
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
    data['worker_log'].append(f"[Transcode AMD] Using encoder: {encoder}")
    data['worker_log'].append(f"[Transcode AMD] AMD GPU: {'Detected' if capabilities['gpu_detected'] else 'Not detected'}")
    
    return data
