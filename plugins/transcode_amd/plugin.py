#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    plugins.transcode_amd.plugin.py

    Written by:               viennej <viennej@github.com>
    Date:                     2025-01-27

    Copyright:
           Copyright (C) viennej - All Rights Reserved

           Permission is hereby granted, free of charge, to any person obtaining a copy
           of this software and associated documentation files (the "Software"), to deal
           in the Software without restriction, including without limitation the rights
           to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
           copies of the Software, and to permit persons to whom the Software is
           furnished to do so, subject to the following conditions:

           The above copyright notice and this permission notice shall be included in all
           copies or substantial portions of the Software.

           THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
           EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
           MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
           IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
           DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
           OTHERWISE, ARISING FROM OR IN CONNECTION WITH THE SOFTWARE OR THE USE
           OR OTHER DEALINGS IN THE SOFTWARE.

"""

import os
import subprocess
import json
import re
from typing import Dict, List, Optional


# Plugin metadata
__title__ = "Transcode AMD"
__author__ = "viennej"
__version__ = "1.0.0"
__description__ = "AMD Hardware Acceleration Transcoding Plugin"
__icon__ = ""


def detect_amd_gpu() -> Dict:
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
                capabilities['has_vaapi'] = True
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
        pass
    
    return capabilities


def get_optimal_encoder(codec: str, capabilities: Dict, settings: Dict) -> tuple:
    """Get optimal encoder and parameters for codec"""
    prefer_amf = settings.get('prefer_amf_over_vaapi', True)
    
    encoder_map = {
        'h264': {
            'amf': ('h264_amf', ['-quality', settings.get('video_quality', 'balanced')]),
            'vaapi': ('h264_vaapi', ['-qp', '23']),
            'software': ('libx264', ['-preset', 'medium', '-crf', '23'])
        },
        'hevc': {
            'amf': ('hevc_amf', ['-quality', settings.get('video_quality', 'balanced')]),
            'vaapi': ('hevc_vaapi', ['-qp', '25']),
            'software': ('libx265', ['-preset', 'medium', '-crf', '25'])
        },
        'av1': {
            'amf': ('av1_amf', ['-quality', settings.get('video_quality', 'balanced')]),
            'vaapi': ('av1_vaapi', ['-qp', '30']),
            'software': ('libsvtav1', ['-preset', '7'])
        },
        'vp9': {
            'vaapi': ('vp9_vaapi', ['-qp', '30']),
            'software': ('libvpx-vp9', ['-crf', '30', '-b:v', '0'])
        }
    }
    
    if codec not in encoder_map:
        return ('libx264', ['-preset', 'medium', '-crf', '23'])
    
    codec_encoders = encoder_map[codec]
    
    # Choose encoder based on capabilities
    if prefer_amf and capabilities['has_amf'] and 'amf' in codec_encoders:
        return codec_encoders['amf']
    elif capabilities['has_vaapi'] and 'vaapi' in codec_encoders:
        return codec_encoders['vaapi']
    else:
        return codec_encoders.get('software', ('libx264', ['-preset', 'medium', '-crf', '23']))


def detect_source_codec(file_path: str) -> str:
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
            # Map codec names
            if codec in ['h264', 'avc']:
                return 'h264'
            elif codec in ['hevc', 'h265']:
                return 'hevc'
            elif codec == 'av1':
                return 'av1'
            elif codec == 'vp9':
                return 'vp9'
    except Exception:
        pass
    
    return 'h264'  # Default


def on_worker_process(data):
    """
    Main plugin function for AMD hardware transcoding
    
    The 'data' object includes:
        file_in                 - String, the source file to be processed
        file_out                - String, the destination output file
        exec_command            - Array, the FFmpeg command to execute
        command_progress_parser - Function, progress parser for FFmpeg output
        worker_log              - Array, log lines for the frontend
    
    Returns:
        data - Modified data object with FFmpeg command
    """
    import logging
    
    # Setup logging
    logger = logging.getLogger("Unmanic.Plugin.transcode_amd")
    
    # Get settings (would come from plugin settings in real implementation)
    settings = {
        'prefer_amf_over_vaapi': data.get('prefer_amf_over_vaapi', True),
        'video_quality': data.get('video_quality', 'balanced'),
        'bitrate': data.get('bitrate', '2M'),
        'max_bitrate': data.get('max_bitrate', '4M'),
        'audio_bitrate': data.get('audio_bitrate', '128k'),
        'fallback_to_software': data.get('fallback_to_software', True)
    }
    
    # Get file paths
    file_in = data.get('file_in')
    file_out = data.get('file_out')
    
    if not file_in or not file_out:
        logger.error("Missing input or output file")
        return data
    
    # Detect AMD capabilities
    capabilities = detect_amd_gpu()
    logger.info(f"AMD GPU detected: {capabilities['gpu_detected']}")
    logger.info(f"VAAPI available: {capabilities['has_vaapi']}")
    logger.info(f"AMF available: {capabilities['has_amf']}")
    
    # Detect source codec
    source_codec = detect_source_codec(file_in)
    logger.info(f"Source codec: {source_codec}")
    
    # Get optimal encoder
    encoder, encoder_params = get_optimal_encoder(source_codec, capabilities, settings)
    logger.info(f"Selected encoder: {encoder}")
    
    # Build FFmpeg command
    cmd = ['ffmpeg', '-i', file_in]
    
    # Add hardware acceleration if using VAAPI
    if encoder.endswith('_vaapi'):
        cmd.extend(['-hwaccel', 'vaapi'])
        cmd.extend(['-hwaccel_device', capabilities['render_device']])
        cmd.extend(['-hwaccel_output_format', 'vaapi'])
    
    # Add video encoding
    cmd.extend(['-c:v', encoder])
    cmd.extend(encoder_params)
    
    # Add bitrate for hardware encoders
    if encoder.endswith('_amf') or encoder.endswith('_vaapi'):
        cmd.extend(['-b:v', settings['bitrate']])
        cmd.extend(['-maxrate', settings['max_bitrate']])
    
    # Add audio encoding
    cmd.extend(['-c:a', 'aac', '-b:a', settings['audio_bitrate']])
    
    # Add output settings
    cmd.extend(['-y', file_out])
    
    # Set command in data
    data['exec_command'] = cmd
    
    # Log command
    logger.info(f"FFmpeg command: {' '.join(cmd)}")
    data['worker_log'].append(f"Using encoder: {encoder}")
    data['worker_log'].append(f"AMD GPU: {'Detected' if capabilities['gpu_detected'] else 'Not detected'}")
    
    return data
