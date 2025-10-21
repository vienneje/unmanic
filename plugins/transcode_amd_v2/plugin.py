#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    transcode_amd

    AMD Hardware Acceleration Transcoding Plugin
    
    Automatically detects and uses AMD CPU and GPU hardware for video transcoding.
    Supports AMF, VAAPI GPU encoders and optimized CPU software encoding.
"""

import os
import subprocess
import logging
import re

from unmanic.libs.unplugins.settings import PluginSettings

# Configure logging
logger = logging.getLogger("Unmanic.Plugin.transcode_amd")


class Settings(PluginSettings):
    settings = {
        "encoding_mode": "auto",  # Auto mode: prefer GPU, fallback to CPU
        "prefer_amf_over_vaapi": False,  # Default to VAAPI (AMF library not in Jellyfin FFmpeg)
        "target_codec": "hevc",  # HEVC for maximum space savings
        "video_quality": "balanced",
        "bitrate": "4M",  # Optimized bitrate for quality (4M avg, 6M max)
        "max_bitrate": "6M",
        "audio_codec": "aac",
        "audio_bitrate": "192k",  # Higher quality audio
        "audio_channels": "2"  # Stereo output
    }
    
    form_settings = {
        "encoding_mode": {
            "label": "Encoding Mode",
            "input_type": "select",
            "select_options": [
                {
                    "value": "auto",
                    "label": "Auto - Prefer GPU, fallback to CPU",
                },
                {
                    "value": "gpu_only",
                    "label": "GPU Only - Force hardware acceleration",
                },
                {
                    "value": "cpu_only",
                    "label": "CPU Only - Force software encoding",
                },
            ],
        },
        "prefer_amf_over_vaapi": {
            "label": "Prefer AMF over VAAPI (when using GPU)",
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
        "video_quality": {
            "label": "Video Quality (for hardware encoders)",
            "input_type": "select",
            "select_options": [
                {
                    "value": "speed",
                    "label": "Speed - Fastest encoding",
                },
                {
                    "value": "balanced",
                    "label": "Balanced - Recommended",
                },
                {
                    "value": "quality",
                    "label": "Quality - Best quality",
                },
            ],
        },
        "bitrate": {
            "label": "Video Bitrate (e.g., 2M, 5M, 10M)",
        },
        "max_bitrate": {
            "label": "Max Video Bitrate (e.g., 4M, 8M, 15M)",
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
                    "label": "Copy (no re-encode)",
                },
            ],
        },
        "audio_bitrate": {
            "label": "Audio Bitrate (e.g., 128k, 192k, 256k)",
        },
        "audio_channels": {
            "label": "Audio Channels (e.g., 2 for stereo, 6 for 5.1)",
        },
    }


def ensure_pciutils_installed():
    """Ensure pciutils (lspci) is installed for GPU detection"""
    try:
        # Check if lspci exists
        result = subprocess.run(['which', 'lspci'], capture_output=True, timeout=5)
        if result.returncode != 0:
            logger.warning("lspci not found, attempting to install pciutils...")
            # Try to install pciutils
            install_result = subprocess.run(
                ['apt-get', 'update'], 
                capture_output=True, 
                timeout=30
            )
            if install_result.returncode == 0:
                subprocess.run(
                    ['apt-get', 'install', '-y', 'pciutils'],
                    capture_output=True,
                    timeout=60
                )
                logger.info("pciutils installed successfully")
            else:
                logger.warning("Could not install pciutils, GPU detection may fail")
    except Exception as e:
        logger.debug(f"Error checking/installing pciutils: {e}")


def detect_amd_gpu():
    """Detect AMD GPU and available encoders"""
    gpu_info = {
        'detected': False,
        'render_device': '/dev/dri/renderD128',
        'has_amf': False,
        'has_vaapi': False
    }
    
    try:
        # Ensure pciutils is installed for lspci command
        ensure_pciutils_installed()
        
        # Check for AMD GPU via lspci
        result = subprocess.run(['lspci'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if any(word in line.lower() for word in ['vga', 'display']):
                    if any(word in line.lower() for word in ['amd', 'ati', 'radeon']):
                        gpu_info['detected'] = True
                        logger.info(f"AMD GPU detected: {line.strip()}")
                        break
        
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
        'cores': 0
    }
    
    try:
        with open('/proc/cpuinfo', 'r') as f:
            cpuinfo = f.read()
            
        if 'AMD' in cpuinfo or 'AuthenticAMD' in cpuinfo:
            cpu_info['detected'] = True
            cpu_info['cores'] = cpuinfo.count('processor')
            
            model_match = re.search(r'model name\s+:\s+(.+)', cpuinfo)
            if model_match:
                logger.info(f"AMD CPU detected: {model_match.group(1).strip()}")
        
    except Exception as e:
        logger.debug(f"Error detecting AMD CPU: {e}")
    
    return cpu_info


def get_encoder(codec, gpu_info, cpu_info, mode, prefer_amf):
    """Get optimal encoder based on hardware and mode"""
    encoder_map = {
        'h264': {'amf': 'h264_amf', 'vaapi': 'h264_vaapi', 'software': 'libx264'},
        'hevc': {'amf': 'hevc_amf', 'vaapi': 'hevc_vaapi', 'software': 'libx265'}
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
            if prefer_amf and gpu_info['has_amf']:
                return encoders['amf'], 'gpu'
            elif gpu_info['has_vaapi']:
                return encoders['vaapi'], 'gpu'
    
    # Fallback to CPU
    return encoders['software'], 'cpu'


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
    except Exception:
        pass
    
    return 'h264'


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


class FFmpegProgressParser:
    """Parse FFmpeg progress output to calculate completion percentage"""
    
    def __init__(self, total_duration_seconds):
        self.total_duration = total_duration_seconds
        self.current_percent = 0
        self.proc_registered = False
    
    def parse(self, line_text, pid=None, proc_start_time=None, unset=False):
        """
        Parse FFmpeg progress output.
        
        Args:
            line_text: FFmpeg output line
            pid: Process ID (for initial registration)
            proc_start_time: Process start time (for initial registration)
            unset: If True, unregister the process (it's completed)
        
        Returns:
            Dict with 'percent' (as string), 'paused', 'killed' keys
        """
        # Handle process unregistration (completion)
        if unset:
            return {
                'percent': '100',
                'paused': False,
                'killed': False
            }
        
        # Handle process registration (initial call with pid)
        if pid is not None and not self.proc_registered:
            self.proc_registered = True
            return {
                'percent': '0',
                'paused': False,
                'killed': False
            }
        
        # Parse FFmpeg output for time information
        # Example: "frame=  123 fps= 30 time=00:01:23.45 bitrate=1234.5kbits/s speed=1.02x"
        if line_text and self.total_duration > 0:
            # Look for time= in the output (format: HH:MM:SS.MS or SS.MS)
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
        
        # Return percent as STRING (Unmanic expects string format)
        return {
            'percent': str(self.current_percent),
            'paused': False,
            'killed': False
        }


def on_worker_process(data):
    """
    Runner function - Transcode video with AMD hardware acceleration
    
    The 'data' object argument includes:
        exec_command            - A command that Unmanic should execute.
        command_progress_parser - A function that Unmanic can use to parse progress.
        file_in                 - The source file to be processed.
        file_out                - The destination output file.
        original_file_path      - The absolute path to the original file.
        repeat                  - Boolean, should this runner be executed again.
    
    :param data:
    :return:
    """
    
    # Get settings
    settings = Settings()
    
    # Get file paths
    file_in = data.get('file_in')
    file_out = data.get('file_out')
    
    if not file_in or not file_out:
        logger.error("Missing input or output file")
        return data
    
    # Get video duration for progress tracking
    video_duration = get_video_duration(file_in)
    if video_duration > 0:
        logger.info(f"Video duration: {video_duration:.2f} seconds ({video_duration/60:.2f} minutes)")
    else:
        logger.warning("Could not determine video duration - progress tracking may be limited")
    
    # Detect hardware
    gpu_info = detect_amd_gpu()
    cpu_info = detect_amd_cpu()
    
    # Get settings
    mode = settings.get_setting('encoding_mode')
    prefer_amf = settings.get_setting('prefer_amf_over_vaapi')
    target_codec = settings.get_setting('target_codec')
    
    # Determine target codec
    if target_codec == 'copy':
        target_codec = detect_source_codec(file_in)
    
    # Get encoder
    encoder, encoder_type = get_encoder(target_codec, gpu_info, cpu_info, mode, prefer_amf)
    
    logger.info(f"Mode: {mode}, Encoder: {encoder} ({encoder_type})")
    
    # Build FFmpeg command
    cmd = ['ffmpeg', '-hide_banner', '-loglevel', 'info']
    
    # Add hardware acceleration for VAAPI (MUST come before -i input)
    if encoder.endswith('_vaapi'):
        cmd.extend(['-vaapi_device', gpu_info['render_device']])
        cmd.extend(['-hwaccel', 'vaapi'])
        cmd.extend(['-hwaccel_output_format', 'vaapi'])
    
    # Add input file
    cmd.extend(['-i', file_in])
    
    # Add video encoding
    cmd.extend(['-c:v', encoder])
    
    # Add encoder-specific parameters
    if encoder.endswith('_amf'):
        quality = settings.get_setting('video_quality')
        cmd.extend(['-quality', quality])
        cmd.extend(['-usage', 'transcoding'])  # transcoding, webcam, lowlatency, ultralowlatency
    elif encoder.endswith('_vaapi'):
        # VAAPI optimized settings for quality
        cmd.extend(['-rc_mode', 'VBR'])  # Variable bitrate mode
        cmd.extend(['-qp', '20'])  # Lower QP = higher quality
        # Add profile and level for HEVC
        if encoder == 'hevc_vaapi':
            cmd.extend(['-profile:v', 'main', '-level', '5.1'])
    elif encoder == 'libx264':
        cmd.extend(['-preset', 'medium', '-crf', '23'])
        # libx264 can use all cores efficiently
        if cpu_info['cores'] > 1:
            threads = min(16, cpu_info['cores'])  # Cap at 16 for stability
            cmd.extend(['-threads', str(threads)])
    elif encoder == 'libx265':
        cmd.extend(['-preset', 'medium', '-crf', '25'])
        # libx265 uses frame pools, limit to avoid errors
        if cpu_info['cores'] > 1:
            pools = min(16, cpu_info['cores'] // 2)  # Use half cores for pools
            cmd.extend(['-x265-params', f'pools={pools}'])
    
    # Add bitrate for hardware encoders
    if encoder.endswith(('_amf', '_vaapi')):
        bitrate = settings.get_setting('bitrate')
        max_bitrate = settings.get_setting('max_bitrate')
        cmd.extend(['-b:v', bitrate, '-maxrate', max_bitrate])
    
    # Add audio encoding
    audio_codec = settings.get_setting('audio_codec')
    if audio_codec == 'copy':
        cmd.extend(['-c:a', 'copy'])
    else:
        audio_bitrate = settings.get_setting('audio_bitrate')
        audio_channels = settings.get_setting('audio_channels')
        cmd.extend(['-c:a', audio_codec, '-b:a', audio_bitrate])
        if audio_channels:
            cmd.extend(['-ac', audio_channels])
    
    # Add movflags for better streaming/playback support
    cmd.extend(['-movflags', '+faststart'])
    
    # Add output
    cmd.extend(['-y', file_out])
    
    # Set command
    data['exec_command'] = cmd
    
    # Set up custom FFmpeg progress parser for accurate progress tracking and ETC
    if video_duration > 0:
        progress_parser = FFmpegProgressParser(video_duration)
        data['command_progress_parser'] = progress_parser.parse
        logger.info("FFmpeg progress parser enabled - progress bar and ETC will be available")
    else:
        # Fallback: let Unmanic use default parser (limited functionality)
        logger.warning("Using default progress parser - progress tracking may be limited")
    
    # Log to worker
    if 'worker_log' in data:
        data['worker_log'].append(f"[AMD] Mode: {mode}, Encoder: {encoder} ({encoder_type})")
        if video_duration > 0:
            data['worker_log'].append(f"[AMD] Video duration: {video_duration/60:.2f} minutes")
    
    return data
