#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    unmanic.hardware_acceleration_handle.py

    Written by:               Josh.5 <jsunnex@gmail.com>
    Date:                     21 Feb 2021, (3:54 PM)

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
import ctypes
import os


class HardwareAccelerationHandle(object):
    """
    HardwareAccelerationHandle

    Determine support for Hardware Acceleration on host
    """

    def __init__(self, file_probe):
        self.file_probe = file_probe
        self.enable_hardware_accelerated_decoding = False
        self.hardware_device = None
        self.video_encoder = None
        self.main_options = []
        self.advanced_options = []

    def get_hwaccel_devices(self):
        """
        Return a list of the hosts compatible decoders

        :return:
        """
        decoders_list = []

        # Check for CUDA decoders
        decoders_list = decoders_list + self.list_available_cuda_decoders()

        # Append any discovered VAAPI decoders
        decoders_list = decoders_list + self.list_available_vaapi_devices()

        # Return the decoder list
        return decoders_list

    def set_hwaccel_args(self):
        self.main_options = []

        # If Unmanic has settings configured for enabling 'HW Decoding', then fetch args based on selected HW type
        if self.hardware_device:
            hwaccel_type = self.hardware_device.get('hwaccel')
            if hwaccel_type is not None:
                if hwaccel_type == 'vaapi':
                    # Return decoder args for VAAPI
                    self.generate_vaapi_main_args()
                elif hwaccel_type == 'cuda':
                    # Return decoder args for NVIDIA CUDA device
                    self.generate_cuda_main_args()
        else:
            # If no hardware decoder is set, then check that there is no need for setting the hardware device for the encoder
            # Eg. The VAAPI encoder still needs to have the '-vaapi_device' main option configured to work even if no decoder
            #   is configured

            # Check if VAAPI video encoder is enabled
            if self.video_encoder and "vaapi" in self.video_encoder.lower():
                # Find the first decoder
                vaapi_devices = self.list_available_vaapi_devices()
                if vaapi_devices:
                    self.hardware_device = vaapi_devices[0]
                    self.generate_vaapi_main_args()
                    # self.main_options = self.main_options + ['-vaapi_device', vaapi_device.get('hwaccel_device')]

    def update_main_options(self, main_options):
        return main_options + self.main_options

    def update_advanced_options(self, advanced_options):
        return advanced_options + self.advanced_options

    def generate_vaapi_main_args(self):
        """
        Generate a list of args for using a VAAPI decoder

        :return:
        """
        # Check if this is an AMD device and use AMD-specific optimizations
        if self.hardware_device and self.hardware_device.get('vendor') == 'AMD':
            return self.generate_amd_vaapi_main_args()
        
        # Check if we are using a VAAPI encoder also...
        if self.video_encoder and "vaapi" in self.video_encoder.lower():
            if self.enable_hardware_accelerated_decoding:
                # Configure args such that when the input may or may not be hardware decodable we can do:
                #   REF: https://trac.ffmpeg.org/wiki/Hardware/VAAPI#Encoding
                self.main_options = [
                    "-init_hw_device", "vaapi=vaapi0:{}".format(self.hardware_device.get('hwaccel_device')),
                    "-hwaccel", "vaapi",
                    "-hwaccel_output_format", "vaapi",
                    "-hwaccel_device", "vaapi0",
                ]
                # Use 'NV12' for hardware surfaces. I would think that 10-bit encoding encoding using
                #   the P010 input surfaces is an advanced feature
                self.advanced_options = [
                    "-filter_hw_device", "vaapi0",
                    "-vf", "format=nv12|vaapi,hwupload",
                ]
            else:
                # Encode only (no decoding)
                #   REF: https://trac.ffmpeg.org/wiki/Hardware/VAAPI#Encode-only (sorta)
                self.main_options = [
                    "-vaapi_device", self.hardware_device.get('hwaccel_device'),
                ]
                # Use 'NV12' for hardware surfaces. I would think that 10-bit encoding encoding using
                #   the P010 input surfaces is an advanced feature
                self.advanced_options = [
                    "-vf", "format=nv12|vaapi,hwupload",
                ]
        else:
            # Decode an input with hardware if possible, output in normal memory to encode with another encoder not vaapi:
            #   REF: https://trac.ffmpeg.org/wiki/Hardware/VAAPI#Decode-only
            self.main_options = [
                "-hwaccel", "vaapi",
                "-hwaccel_device", self.hardware_device.get('hwaccel_device')
            ]

    def generate_amd_vaapi_main_args(self):
        """
        Generate AMD-specific VAAPI arguments with optimizations for AMD GPUs
        
        :return:
        """
        # Check if we are using a VAAPI encoder also...
        if self.video_encoder and "vaapi" in self.video_encoder.lower():
            if self.enable_hardware_accelerated_decoding:
                # AMD-optimized encoding with hardware decoding
                self.main_options = [
                    "-init_hw_device", "vaapi=vaapi0:{}".format(self.hardware_device.get('hwaccel_device')),
                    "-hwaccel", "vaapi",
                    "-hwaccel_output_format", "vaapi",
                    "-hwaccel_device", "vaapi0",
                ]
                # AMD GPUs support both NV12 and P010 formats
                # Use P010 for 10-bit content when available, fallback to NV12
                self.advanced_options = [
                    "-filter_hw_device", "vaapi0",
                    "-vf", "format=nv12|vaapi,hwupload",
                ]
            else:
                # AMD encode-only mode
                self.main_options = [
                    "-vaapi_device", self.hardware_device.get('hwaccel_device'),
                ]
                self.advanced_options = [
                    "-vf", "format=nv12|vaapi,hwupload",
                ]
        else:
            # AMD decode-only mode
            self.main_options = [
                "-hwaccel", "vaapi",
                "-hwaccel_device", self.hardware_device.get('hwaccel_device')
            ]

    def generate_cuda_main_args(self):
        """
        Generate a list of args for using an NVIDIA CUDA decoder

        :return:
        """
        self.main_options = ["-hwaccel", "cuda", "-hwaccel_device", self.hardware_device.get('hwaccel_device')]

    def list_available_cuda_decoders(self):
        """
        Check for the existance of a cuda encoder
        Credit for code:
            https://gist.github.com/f0k/63a664160d016a491b2cbea15913d549

        :return:
        """
        decoders = []

        # Search for cuder libs
        libnames = ('libcuda.so', 'libcuda.dylib', 'cuda.dll')
        for libname in libnames:
            try:
                cuda = ctypes.CDLL(libname)
            except OSError:
                continue
            else:
                break
        else:
            return decoders

        # For the available GPUs found, ensure that there is a cuda device
        nGpus = ctypes.c_int()
        device = ctypes.c_int()
        result = cuda.cuInit(0)
        if result != 0:
            return decoders
        result = cuda.cuDeviceGetCount(ctypes.byref(nGpus))
        if result != 0:
            return decoders

        # Loop over GPUs and list each one individually
        for i in range(nGpus.value):
            result = cuda.cuDeviceGet(ctypes.byref(device), i)
            if result != 0:
                continue
            device_data = {
                'hwaccel':        'cuda',
                'hwaccel_device': "{}".format(i),
            }
            decoders.append(device_data)

        return decoders

    def list_available_vaapi_devices(self):
        """
        Return a list of available VAAPI decoder devices with vendor identification

        :return:
        """
        decoders = []
        dir_path = os.path.join("/", "dev", "dri")

        if os.path.exists(dir_path):
            for device in sorted(os.listdir(dir_path)):
                if device.startswith('render'):
                    device_path = os.path.join("/", "dev", "dri", device)
                    device_info = self.identify_vaapi_device_vendor(device_path)
                    
                    device_data = {
                        'hwaccel':        'vaapi',
                        'hwaccel_device': device_path,
                        'vendor':         device_info.get('vendor', 'unknown'),
                        'model':          device_info.get('model', 'unknown'),
                        'driver':         device_info.get('driver', 'unknown'),
                        'device_name':    device_info.get('device_name', device),
                    }
                    decoders.append(device_data)

        # Return the list of decoders
        return decoders

    def identify_vaapi_device_vendor(self, device_path):
        """
        Identify the vendor and model of a VAAPI device by examining sysfs
        
        :param device_path: Path to the DRM device (e.g., /dev/dri/renderD128)
        :return: Dictionary with vendor, model, driver, and device_name
        """
        device_info = {
            'vendor': 'unknown',
            'model': 'unknown', 
            'driver': 'unknown',
            'device_name': os.path.basename(device_path)
        }
        
        try:
            # First, try to find the corresponding card device by checking all available cards
            # since render device numbers don't always match card numbers
            drm_dir = os.path.join("/", "sys", "class", "drm")
            sysfs_path = None
            
            if os.path.exists(drm_dir):
                # Look for all card devices
                for item in os.listdir(drm_dir):
                    if item.startswith('card') and not '-' in item:  # Skip display outputs
                        card_path = os.path.join(drm_dir, item)
                        if os.path.isdir(card_path):
                            # Check if this card has a render device that matches our path
                            # The render device might be in the device/drm subdirectory
                            device_drm_path = os.path.join(card_path, "device", "drm", os.path.basename(device_path))
                            if os.path.exists(device_drm_path):
                                # Found the matching card, now read its information
                                sysfs_path = card_path
                                break
                
                # Fallback: try the original logic with device number
                if not sysfs_path:
                    device_name = os.path.basename(device_path)
                    if device_name.startswith('renderD'):
                        device_num = device_name[7:]  # Remove 'renderD' prefix
                        sysfs_path = os.path.join("/", "sys", "class", "drm", f"card{device_num}")
                
                if sysfs_path and os.path.exists(sysfs_path):
                    # Read vendor information
                    vendor_file = os.path.join(sysfs_path, "device", "vendor")
                    if os.path.exists(vendor_file):
                        with open(vendor_file, 'r') as f:
                            vendor_id = f.read().strip()
                            # Convert vendor ID to name
                            vendor_map = {
                                '0x1002': 'AMD',      # AMD/ATI
                                '0x8086': 'Intel',    # Intel
                                '0x10de': 'NVIDIA',   # NVIDIA
                            }
                            device_info['vendor'] = vendor_map.get(vendor_id, f'Unknown ({vendor_id})')
                    
                    # Read device information
                    device_file = os.path.join(sysfs_path, "device", "device")
                    if os.path.exists(device_file):
                        with open(device_file, 'r') as f:
                            device_id = f.read().strip()
                            device_info['model'] = f'Device {device_id}'
                    
                    # Read driver information
                    driver_link = os.path.join(sysfs_path, "device", "driver")
                    if os.path.exists(driver_link):
                        driver_path = os.readlink(driver_link)
                        driver_name = os.path.basename(driver_path)
                        device_info['driver'] = driver_name
                        
                        # Map driver names to more readable names
                        driver_map = {
                            'amdgpu': 'AMD GPU Driver',
                            'i915': 'Intel Graphics Driver',
                            'nouveau': 'Nouveau (NVIDIA Open Source)',
                            'nvidia': 'NVIDIA Proprietary Driver',
                        }
                        device_info['driver'] = driver_map.get(driver_name, driver_name)
                    
                    # Try to get more specific model information from modalias
                    modalias_file = os.path.join(sysfs_path, "device", "modalias")
                    if os.path.exists(modalias_file):
                        with open(modalias_file, 'r') as f:
                            modalias = f.read().strip()
                            # Parse modalias for more specific model info
                            if 'amd' in modalias.lower():
                                device_info['vendor'] = 'AMD'
                            elif 'intel' in modalias.lower():
                                device_info['vendor'] = 'Intel'
                            elif 'nvidia' in modalias.lower():
                                device_info['vendor'] = 'NVIDIA'
                                
        except (OSError, IOError, ValueError) as e:
            # If we can't read sysfs, just use defaults
            pass
            
        return device_info


if __name__ == "__main__":
    hw_a = HardwareAccelerationHandle('blah')
    print(hw_a.get_hwaccel_devices())
    for hardware_decoder in hw_a.get_hwaccel_devices():
        hw_a.hardware_device = hardware_decoder
        break
    print(hw_a.args())
