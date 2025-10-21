Unmanic - Library Optimiser (AMD Ryzen AI Enhanced)
===================================================

![UNMANIC - Library Optimiser](https://github.com/unmanic/unmanic/raw/master/logo.png)

> **🚀 This fork is optimized for AMD Ryzen AI processors with integrated Radeon graphics**
> 
> Enhanced with comprehensive AMD hardware acceleration support, including VAAPI and AMF encoders, plus a custom plugin for intelligent CPU/GPU transcoding with optimized HEVC encoding parameters.ng)

<a href='https://ko-fi.com/I2I21F8E1' target='_blank'><img height='26' style='border:0px;height:26px;' src='https://cdn.ko-fi.com/cdn/kofi1.png?v=2' border='0' alt='Buy Me a Coffee at ko-fi.com' /></a>

[![GitHub tag (latest by date)](https://img.shields.io/github/v/tag/unmanic/unmanic?color=009dc7&label=latest%20release&logo=github&logoColor=%23403d3d&style=flat-square)](https://github.com/unmanic/unmanic/releases)
[![GitHub issues](https://img.shields.io/github/issues-raw/unmanic/unmanic?color=009dc7&logo=github&logoColor=%23403d3d&style=flat-square)](https://github.com/unmanic/unmanic/issues?q=is%3Aopen+is%3Aissue)
[![GitHub closed issues](https://img.shields.io/github/issues-closed-raw/unmanic/unmanic?color=009dc7&logo=github&logoColor=%23403d3d&style=flat-square)](https://github.com/unmanic/unmanic/issues?q=is%3Aissue+is%3Aclosed)
[![GitHub pull requests](https://img.shields.io/github/issues-pr-raw/unmanic/unmanic?color=009dc7&logo=github&logoColor=%23403d3d&style=flat-square)](https://github.com/unmanic/unmanic/pulls?q=is%3Aopen+is%3Apr)
[![GitHub closed pull requests](https://img.shields.io/github/issues-pr-closed-raw/unmanic/unmanic?color=009dc7&logo=github&logoColor=%23403d3d&style=flat-square)](https://github.com/unmanic/unmanic/pulls?q=is%3Apr+is%3Ac[![Docker Stars](https://img.shields.io/docker/stars/josh5/unmanic?color=009dc7&logo=docker&logoColor=%23403d3d&style=for-the-badge)](https://hub.docker.com/r/josh5/unmanic)
[![Docker Pulls](https://img.shields.io/docker/pulls/josh5/unmanic?color=009dc7&logo=docker&logoColor=%23403d3d&style=for-the-badge)](https://hub.docker.com/r/josh5/unmanic)
[![Docker Image Size (tag)](https://img.shields.io/docker/image-size/josh5/unmanic/latest?color=009dc7&label=docker%20image%20size&logo=docker&logoColor=%23403d3d&style=for-the-badge)](https://hub.docker.com/r/josh5/unmanic)

## 🎯 AMD-Optimized Docker Images

**Docker Hub:** [`viennej/unmanic-amd`](https://hub.docker.com/r/viennej/unmanic-amd)

```bash
# Pull the latest AMD-optimized image
docker pull viennej/unmanic-amd:latest

# Or use a specific version
docker pull viennej/unmanic-amd:v2.1.8
```

**Available Tags:**
- `latest` - Latest stable build with AMD optimizations
- `latest-enhanced` - Same as latest, includes Jellyfin FFmpeg 7
- `v2.1.8` - Latest version with optimized HEVC encoding
- `ffmpeg7` - FFmpeg 7 base imagesh5/unmanic)




[![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/Unmanic/unmanic/python_lint_and_run_unit_tests.yml?branch=master&style=flat-square&logo=github&logoColor=403d3d&label=Unit%20Tests)](https://github.com/Unmanic/unmanic/actions/workflows/python_lint_and_run_unit_tests.yml?query=branch%3Amaster)
[![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/Unmanic/unmanic/integration_test_and_build_all_packages_ci.yml?branch=master&style=flat-square&logo=github&logoColor=403d3d&label=Package%20Build)](https://github.com/Unmanic/unmanic/actions/workflows/integration_test_and_build_all_packages_ci.yml?query=branch%3Amaster)

[![GitHub license](https://img.shields.io/github/license/unmanic/unmanic?color=009dc7&style=flat-square)]()
---

Unmanic is a simple tool for optimising your file library. You can use it to convert your files into a single, uniform format, manage file movements based on timestamps, or execute custom commands against a file based on its file size.

Simply configure Unmanic pointing it at your library and let it automatically manage that library for you.

Unmanic provides you with the following main functions:

- A scheduler built in to scan your whole library for files that do not conform to your configured file presets. Files found requiring processing are then queued.
- A file/directory monitor. When a file is modified, or a new file is added in your library, Unmanic is able to again test that against your configured file presets. Like the first function, if this file requires processing, it is added to a queue for processing.
- A handler to manage running multiple file manipulation tasks at a time.
- A Web UI to easily configure, manage and monitor the progress of your library optimisation.

You choose how you want your library to be.

Some examples of how you may use Unmanic:

- Transcode video or audio files into a uniform format using FFmpeg.
- Identify (and remove if desired) commercials in DVR recordings shortly after they have completed being recorded.
- Move files from one location to another after a configured period of time.
- Automatically execute FileBot rename files in your library as they are added.
- Compress files older than a specified age.
- Run any custom command against files matching a certain exten### Table Of Contents

[AMD Optimizations](#amd-optimizations)
  * [Container Enhancements](#container-enhancements)
  * [Code Enhancements](#code-enhancements)
  * [AMD Transcode Plugin v2](#amd-transcode-plugin-v2)
  * [Performance Benchmarks](#performance-benchmarks)

[Docker Deployment](#docker-deployment)

[Dependencies](#dependencies)

[Screen-shots](#screen-shots)
  * [Dashboard](#dashboard)
  * [File metrics](#file-metrics)
  * [Installed plugins](#installed-plugins)

[Install and Run](#install-and-run)

[License and Contribution](#license-and-contribution)License and Cont## AMD Optimizations

This fork includes comprehensive optimizations for **AMD Ryzen AI processors** (including Ryzen AI 9 HX PRO 370, Ryzen AI MAX+ 395) with integrated **AMD Radeon graphics** (e.g., Radeon 890M, Radeon 8060S).

### Container Enhancements

The Docker container (`viennej/unmanic-amd`) includes the following optimizations:

#### 1. **Jellyfin FFmpeg 7** with Extended Hardware Acceleration
- Latest Jellyfin FFmpeg build with comprehensive AMD codec support
- Repository: `https://repo.jellyfin.org/ubuntu`
- Package: `jellyfin-ffmpeg7`
- Provides enhanced VAAPI and AMF encoder support

#### 2. **LLVM 21 Compiler Infrastructure**
- Latest LLVM version (21.1.3) for optimal AMD GPU driver support
- Enhanced code generation for AMD RDNA architectures
- Repository: `https://apt.llvm.org/jammy/`
- Packages: `llvm-21`, `llvm-21-dev`, `llvm-21-runtime`, `llvm-21-tools`

#### 3. **Mesa Drivers & VAAPI Libraries**
- `mesa-va-drivers` - Video Acceleration API drivers for AMD GPUs
- `mesa-vdpau-drivers` - VDPAU acceleration
- `libva2`, `libva-drm2` - VA-API core libraries
- `vainfo`, `mesa-utils` - GPU diagnostic tools

#### 4. **Hardware Detection Tools**
- `pciutils` - Auto-installed by plugin for GPU detection
- `lspci` - PCI device enumeration
- `lshw` - Hardware information gathering

#### 5. **Base Image**
- Built on `lsiobase/ubuntu:jammy` (Ubuntu 22.04 LTS)
- Device access: `/dev/dri` for GPU hardware acceleration
- Optimized for both development and production use

### Code Enhancements

#### 1. **AMD GPU Detection** (`unmanic/libs/system.py`)
- Automatic detection of AMD GPUs via `lspci`
- Identification of render devices (`/dev/dri/renderD128`)
- GPU model, vendor ID, and device ID parsing

#### 2. **Hardware Acceleration Handling** (`unmanic/libs/unffmpeg/hardware_acceleration_handle.py`)
- Enhanced VAAPI device detection and configuration
- Optimized FFmpeg argument generation for AMD hardware
- Proper device enumeration and fallback mechanisms

#### 3. **AMD Transcode Plugin v2**

A comprehensive plugin specifically designed for AMD hardware acceleration.

**Features:**
- ✅ **Auto Mode**: Intelligently selects GPU or CPU based on availability
- ✅ **GPU Mode**: Forces VAAPI or AMF hardware acceleration
- ✅ **CPU Mode**: Optimized software encoding with thread management
- ✅ **H.264/HEVC Codecs**: Full support for both codecs
- ✅ **Quality Presets**: Speed, Balanced, Quality modes
- ✅ **Automatic Hardware Detection**: Detects AMD CPUs and GPUs
- ✅ **Progress Tracking**: Real-time progress, percentage, and ETC
- ✅ **Auto-dependency Installation**: Installs `pciutils` if missing

**Plugin File:** [`plugins/transcode_amd_v2/plugin.py`](plugins/transcode_amd_v2/plugin.py)

**Optimized HEVC Encoding Parameters (v2.1.8):**
```bash
ffmpeg -hide_banner -loglevel info \
  -vaapi_device /dev/dri/renderD128 \
  -hwaccel vaapi -hwaccel_output_format vaapi \
  -i "input.mkv" \
  -c:v hevc_vaapi -rc_mode VBR -qp 20 -b:v 4M -maxrate 6M \
  -profile:v main -level 5.1 \
  -c:a aac -b:a 192k -ac 2 \
  -movflags +faststart \
  -y "output.mkv"
```

**Key Parameters:**
- **VBR Rate Control**: Variable bitrate for optimal quality/size ratio
- **QP 20**: High quality (lower = better, range 0-51)
- **4M/6M Bitrate**: Average 4 Mbps, max 6 Mbps
- **HEVC Main Profile, Level 5.1**: Maximum compatibility
- **192k Stereo Audio**: High-quality AAC audio
- **+faststart**: Optimized for streaming (moves metadata to file start)

**Installation:**
1. Download [`transcode_amd_v2-2.1.8.zip`](transcode_amd_v2-2.1.8.zip)
2. Install via Unmanic Web UI: Plugins → Install from file
3. Add to library flow: Libraries → Select Library → Plugin Flow → Add Plugin

### Performance Benchmarks

**Tested on AMD Ryzen AI 9 HX PRO 370 + Radeon 890M:**
- **HEVC VAAPI GPU**: 31.6x realtime (1080p)
- **HEVC CPU (libx265)**: 11x realtime (1080p)
- **H.264 VAAPI GPU**: 32x realtime (1080p)

**Tested on Unraid NAS (AMD GPU):**
- **HEVC VAAPI GPU**: 3.93x realtime (720p)

**File Size Reduction:**
- **H.264 → HEVC**: ~32-48% size reduction
- **Quality**: Maintained with VBR + QP 20

## Docker Deployment

### Quick Start with Docker Compose

```yaml
version: '3'
services:
  unmanic:
    image: viennej/unmanic-amd:latest
    container_name: unmanic
    environment:
      - PUID=1000
      - PGID=1000
      - TZ=Europe/Paris
    volumes:
      - /path/to/config:/config
      - /path/to/library:/library
      - /path/to/cache:/tmp/unmanic
    ports:
      - 8888:8888
    devices:
      - /dev/dri:/dev/dri  # AMD GPU access
    restart: unless-stopped
```

### Manual Docker Run

```bash
docker run -d \
  --name=unmanic \
  -e PUID=1000 \
  -e PGID=1000 \
  -e TZ=Europe/Paris \
  -p 8888:8888 \
  -v /path/to/config:/config \
  -v /path/to/library:/library \
  -v /path/to/cache:/tmp/unmanic \
  --device=/dev/dri:/dev/dri \
  --restart unless-stopped \
  viennej/unmanic-amd:latest
```

### Verify GPU Access

```bash
# Check GPU device inside container
docker exec unmanic ls -l /dev/dri/

# Check VAAPI capabilities
docker exec unmanic vainfo

# Check available FFmpeg encoders
docker exec unmanic ffmpeg -encoders | grep vaapi
```

## Dependencies

 - Python 3.x ([Install](https://www.python.org/downloads/))
 - To install requirements run 'python3 -m pip install -r requirements.txt' from the project root

Since Unmanic can be used for running any commands, you will need to ensure that the required dependencies for those commands are also installed on your system.

**Additional AMD-specific dependencies** (included in Docker image):
 - Jellyfin FFmpeg 7
 - LLVM 21.1.3
 - Mesa VA-API drivers
 - pciutils (for GPU detection)ose commands are also installed on your system.

## Screen-shots

#### Dashboard:
![Screen-shot - Dashboard](./docs/images/unmanic-dashboard-processing-anime.png)
#### File metrics:
![Screen-shot - Desktop](./docs/images/unmanic-file-size-data-panel-anime.png)
#### Installed plugins:
![Screen-shot - Desktop](./docs/images/unmanic-list-installed-plugins.png)

## Install and Run

For up-to-date installation instructions, follow the [Unmanic documentation](https://docs.unmanic.app/docs/).

To run from source:

1) Install the Python dependencies listed above then run:
2) Run:
    ```
    # Ensure the submodules are checked out
    git submodule update --init --recursive
    
    # Build and install the project into your home directory
    python3 ./setup.py install --user
    
    # Run Unmanic
    unmanic
    ```
3) Open your web browser and navigate to http://localhost:8888/

## License and Contribution

This projected is licensed under th GPL version 3. 

Copyright (C) Josh Sunnex - All Rights Reserved

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
 
The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

This project contains libraries imported from external authors.
Please refer to the source of these libraries for more information on their respective licenses.

See [CONTRIBUTING.md](docs/CONTRIBUTING.md) to learn how to contribute to Unmanic.

---
