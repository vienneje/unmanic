#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    unmanic.system.py

    Written by:               Josh.5 <jsunnex@gmail.com>
    Date:                     05 Mar 2021, (11:00 PM)

    Copyright:
           Copyright (C) Josh Sunnex - All Rights Reserved

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
           OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE
           OR OTHER DEALINGS IN THE SOFTWARE.

"""
from unmanic.libs.logs import UnmanicLogging
from unmanic.libs.singleton import SingletonType


class System(object, metaclass=SingletonType):
    devices = {}
    ffmpeg = {}
    platform = {}
    python_version = {}

    def __init__(self, *args, **kwargs):
        self.logger = UnmanicLogging.get_logger(name=__class__.__name__)

    def __get_python_info(self):
        """
        Return a string of the python version

        :return:
        """
        import sys
        if not self.python_version:
            self.python_version = "{0}.{1}.{2}.{3}.{4}".format(*sys.version_info)
        return self.python_version

    def __get_devices_info(self):
        """
        Return a dictionary of device information

        :return:
        """
        import cpuinfo
        if not self.devices:
            self.devices = {
                "cpu_info": cpuinfo.get_cpu_info(),
                "gpu_info": self.__get_gpu_info(),
            }
        return self.devices

    def __get_gpu_info(self):
        """
        Return a list of GPU information including hardware acceleration capabilities
        
        :return:
        """
        gpu_info = []
        
        try:
            # Import hardware acceleration handle to get device information
            from unmanic.libs.unffmpeg.hardware_acceleration_handle import HardwareAccelerationHandle
            
            # Create a dummy file probe for hardware acceleration handle
            hw_handle = HardwareAccelerationHandle(None)
            
            # Get all available hardware acceleration devices
            hw_devices = hw_handle.get_hwaccel_devices()
            
            for device in hw_devices:
                gpu_data = {
                    "type": device.get('hwaccel', 'unknown'),
                    "vendor": device.get('vendor', 'unknown'),
                    "model": device.get('model', 'unknown'),
                    "driver": device.get('driver', 'unknown'),
                    "device_path": device.get('hwaccel_device', 'unknown'),
                    "device_name": device.get('device_name', 'unknown'),
                    "capabilities": self.__get_gpu_capabilities(device)
                }
                gpu_info.append(gpu_data)
                
        except Exception as e:
            self.logger.warning("Failed to get GPU information: {}".format(str(e)))
            
        return gpu_info

    def __get_gpu_capabilities(self, device):
        """
        Get hardware acceleration capabilities for a specific GPU device
        
        :param device: Device information dictionary
        :return: Dictionary of capabilities
        """
        capabilities = {
            "decoding": [],
            "encoding": [],
            "formats": []
        }
        
        hw_type = device.get('hwaccel', 'unknown')
        vendor = device.get('vendor', 'unknown')
        
        # Define capabilities based on hardware type and vendor
        if hw_type == 'cuda':
            capabilities["decoding"] = ['h264', 'hevc', 'vp8', 'vp9', 'av1']
            capabilities["encoding"] = ['h264_nvenc', 'hevc_nvenc', 'av1_nvenc']
            capabilities["formats"] = ['nv12', 'p010', 'yuv420p']
            
        elif hw_type == 'vaapi':
            if vendor == 'AMD':
                capabilities["decoding"] = ['h264', 'hevc', 'vp8', 'vp9', 'av1']
                capabilities["encoding"] = ['h264_vaapi', 'hevc_vaapi', 'av1_vaapi', 'vp9_vaapi', 'h264_amf', 'hevc_amf', 'av1_amf']
                capabilities["formats"] = ['nv12', 'p010', 'yuv420p']
            elif vendor == 'Intel':
                capabilities["decoding"] = ['h264', 'hevc', 'vp8', 'vp9', 'av1']
                capabilities["encoding"] = ['h264_vaapi', 'hevc_vaapi', 'av1_vaapi', 'vp9_vaapi']
                capabilities["formats"] = ['nv12', 'p010', 'yuv420p']
            else:
                # Generic VAAPI capabilities
                capabilities["decoding"] = ['h264', 'hevc', 'vp8', 'vp9']
                capabilities["encoding"] = ['h264_vaapi', 'hevc_vaapi']
                capabilities["formats"] = ['nv12', 'yuv420p']
        
        return capabilities

    def __get_platform_info(self):
        """
        Return a dictionary of device information

        :return:
        """
        import platform
        if not self.platform:
            self.platform = platform.uname()
        return self.platform

    def info(self):
        """
        Returns a dictionary of system information

        :return:
        """
        info = {
            "devices":  self.__get_devices_info(),
            "platform": self.__get_platform_info(),
            "python":   self.__get_python_info(),
        }
        return info


if __name__ == "__main__":
    import json
    import sys
    import os

    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    print(project_dir)
    sys.path.append(project_dir)
    system = System()
    print(json.dumps(system.info(), indent=2))
