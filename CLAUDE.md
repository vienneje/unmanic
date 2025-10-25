# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Unmanic is a library optimizer for automated video transcoding. This is a **fork optimized for AMD Ryzen AI processors** with enhanced hardware acceleration support through VAAPI and AMF encoders.

**Tech Stack:**
- Backend: Python 3.8+ (Tornado web framework, Peewee ORM with SQLite)
- Frontend: Vue.js/Quasar (in submodule at `unmanic/webserver/frontend`)
- Video Processing: FFmpeg with hardware acceleration (Jellyfin FFmpeg 7)
- Deployment: Docker (Ubuntu 22.04/24.04 base images)

## Key Architecture

### Core Components

**Service Layer (`unmanic/service.py`)**
- Main entry point (`unmanic` command)
- Manages lifecycle of: TaskQueue, TaskHandler, PostProcessor, Foreman, LibraryScanner, EventMonitor, UIServer

**Workers (`unmanic/libs/workers.py`)**
- Execute transcoding tasks via FFmpeg
- Critical: Contains recent ETC (Estimated Time to Completion) bug fixes for elapsed time calculation
- Progress tracking parses FFmpeg output for real-time status updates

**Task Management**
- `taskqueue.py`: Queue management for pending files
- `taskhandler.py`: Orchestrates worker execution
- `foreman.py`: Manages worker pools and resource allocation
- `postprocessor.py`: Handles file cleanup and library updates after transcoding

**Hardware Acceleration (`unmanic/libs/unffmpeg/hardware_acceleration_handle.py`)**
- Auto-detects AMD/Intel/NVIDIA GPUs via `lspci`
- Configures VAAPI/AMF/NVENC encoder parameters
- Device path resolution for `/dev/dri/renderD*` devices

**Plugin System (`unmanic/libs/unplugins/`)**
- Plugin executor with child process isolation
- Settings management via `PluginSettings` base class
- Plugin types in `plugin_types/` subdirectory
- Plugins installed in local library or `plugins/` for development

**Database (`unmanic/libs/unmodels/`)**
- Peewee ORM models for tasks, libraries, plugins, workers
- Migrations managed via `peewee_migrate` (see `libs/db_migrate.py`)

**Web API (`unmanic/webserver/`)**
- RESTful API via Tornado handlers
- API v2: `/api/v2/` endpoints in `api_v2/` directory
- WebSocket support for real-time updates (`websocket.py`)
- Frontend served from `public/` (built from submodule)

### AMD-Specific Enhancements

**GPU Detection (`unmanic/libs/system.py`)**
- `System.devices['gpu_info']` contains AMD GPU detection via `lspci`
- Identifies render devices and VAAPI capabilities

**AMD Transcode Plugin v2 (`plugins/transcode_amd_v2/plugin.py`)**
- **v2.4.0 (Latest):** Comprehensive edition with 24+ new features
- GPU capability detection (RDNA 3.5/3/2/1, GCN5)
- 10-bit HEVC support with auto-profile (main/main10)
- Preset profiles (Fast/Balanced/Quality/Archive)
- HDR metadata preservation (HDR10/HLG)
- Multi-audio and subtitle handling
- Resolution-based bitrate optimization
- CRF quality mode and AV1 codec support
- Auto-crop, scene detection, dry-run mode
- Auto/GPU/CPU encoding modes with intelligent fallback
- Recent fixes: All 10-bit encoding issues resolved (v2.3.2+)
- Auto-installs dependencies like `pciutils`

**Docker Images**
- Base: `lsiobase/ubuntu:jammy` or `lsiobase/ubuntu:noble`
- AMD-optimized: `viennej/unmanic-amd:latest`
- Includes: Jellyfin FFmpeg 7, LLVM 21, Mesa VA-API drivers
- Device mapping: `--device=/dev/dri:/dev/dri` required

## Common Commands

### Development Setup

```bash
# Clone with submodules
git submodule update --init --recursive

# Option 1: Docker Development
devops/run_docker.sh --debug --hw=amd --cpus=1

# Option 2: Local venv Development
python3 -m venv venv
source venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt -r requirements-dev.txt
python3 -m pip install --editable .

# Build frontend
devops/frontend_install.sh
```

### Testing

```bash
# Setup tests (first time only)
tests/scripts/setup_tests.sh

# Linting
pycodestyle ./

# Unit tests
pytest --log-cli-level=INFO

# Single test file
pytest --log-cli-level=INFO tests/test_<TEST_NAME>.py

# Debug mode
pytest --log-cli-level=DEBUG -s

# Docker test environment
docker-compose -f docker/docker-compose-test.yml up --force-recreate
docker exec --workdir=/app unmanic-testenv pytest --log-cli-level=INFO
```

### Building

```bash
# Build Python package
python3 -m build --no-isolation --skip-dependency-check --wheel
python3 -m build --no-isolation --skip-dependency-check --sdist

# Build Docker image
docker build -f docker/Dockerfile.amd -t viennej/unmanic-amd:latest .

# Build with FFmpeg 7
docker build -f docker/Dockerfile.amd-ffmpeg7 -t viennej/unmanic-amd:ffmpeg7 .

# Ubuntu 24.04 (Noble) build
docker build -f docker/Dockerfile.noble -t viennej/unmanic-amd:noble .
```

### Database Migrations

```bash
# Wrapper script for peewee-migrate CLI
devops/migrations.sh --help

# Create migration
devops/migrations.sh create <migration_name>

# Run migrations
devops/migrations.sh migrate
```

### Running

```bash
# Run from source
unmanic

# Run with specific config directory
unmanic --config-dir /path/to/config

# Version check (returns "UNKNOWN" in develop mode)
unmanic --version

# Docker
docker run -d --name=unmanic \
  -e PUID=1000 -e PGID=1000 -e TZ=UTC \
  -p 8888:8888 \
  -v /config:/config -v /library:/library -v /cache:/tmp/unmanic \
  --device=/dev/dri:/dev/dri \
  viennej/unmanic-amd:latest
```

## Important Implementation Details

### Progress Tracking & ETC Calculation

**Critical Bug Fix (v2.3.1):**
- ETC calculation requires progress percentage as **string format** (e.g., "75.5%")
- Located in: `unmanic/libs/workers.py`
- FFmpeg output parsing: `time=HH:MM:SS.MS` regex pattern
- Elapsed time calculation: Fixed to use `time.time()` instead of progress updates

**When modifying worker progress:**
- Always return `percent` as string with "%" suffix
- Update both `percent` and `eta` in `data['task_progress']`
- Test ETC display in UI after changes

### Plugin Development

**Plugin Structure:**
```python
from unmanic.libs.unplugins.settings import PluginSettings

class Settings(PluginSettings):
    settings = {"key": "default_value"}
    form_settings = {"key": {"label": "Display Name"}}

def on_worker_process(data):
    """Main plugin execution hook"""
    # Access file: data['file_path']
    # Return dict with 'exec_command', 'command_progress_parser', etc.
```

**Plugin Installation:**
- Development: Place in `plugins/<plugin_name>/plugin.py`
- Production: Install via Web UI (Plugins → Install from file)
- Dependencies: Install in `on_library_management_file_test` hook

### Hardware Acceleration

**AMD GPU Requirements:**
- Kernel driver: `amdgpu`
- Render device: `/dev/dri/renderD128` (or higher)
- Mesa drivers: `mesa-va-drivers`, `libva2`
- Verify: `vainfo` (should list VAAPI profiles)

**FFmpeg Command Pattern (HEVC VAAPI):**
```bash
ffmpeg -vaapi_device /dev/dri/renderD128 \
  -hwaccel vaapi -hwaccel_output_format vaapi \
  -i input.mkv \
  -c:v hevc_vaapi -rc_mode VBR -qp 20 -b:v 4M -maxrate 6M \
  -profile:v main -level 5.1 \
  -c:a aac -b:a 192k \
  -y output.mkv
```

### Frontend Development

**Frontend is a Git submodule:**
- Location: `unmanic/webserver/frontend/`
- Framework: Quasar (Vue 3)
- Build output: `unmanic/webserver/public/`
- Install/build: `devops/frontend_install.sh`

**DO NOT manually edit files in `public/` directory** - they are generated.

### Database Schema

**Key Models (unmanic/libs/unmodels/):**
- `tasks.py`: Pending/active transcode tasks
- `completedtasks.py`: Completed task history
- `libraries.py`: Library configurations
- `librarypluginflow.py`: Plugin execution order per library
- `enabledplugins.py`: Installed plugin metadata
- `workergroups.py` / `workerschedules.py`: Worker pool management

**Migration Pattern:**
1. Modify model in `unmodels/*.py`
2. Run `devops/migrations.sh create migration_name`
3. Edit migration in `unmanic/migrations_v1/`
4. Test: `devops/migrations.sh migrate`

## Code Style

**PEP8 with Exceptions:**
- Max line length: 127 characters (pycodestyle), 200 (flake8)
- Ignored: E722 (bare except), E241 (multiple spaces), W293 (blank line whitespace)
- Run linter before commits: `pycodestyle ./`

**File Headers:**
All new Python files must include the copyright header (see `docs/CONTRIBUTING.md` for template).

## Common Issues

**Frontend not building:**
- Ensure submodule is initialized: `git submodule update --init --recursive`
- Check Node version: Requires Node >=14.17.2, npm >=6.14.13

**GPU not detected:**
- Verify device permissions: `ls -la /dev/dri/`
- Check driver: `lspci | grep VGA`
- Test VAAPI: `docker exec unmanic vainfo`

**ETC not displaying:**
- Check `percent` is returned as string with "%" suffix in worker
- Verify FFmpeg progress parser is enabled
- Inspect logs: Look for "time=" parsing in worker output

**Migration errors:**
- Peewee migrations are in `unmanic/migrations_v1/`
- Use `devops/migrations.sh` wrapper, not raw `pw_migrate`

## File Locations

**Key Entry Points:**
- CLI: `unmanic/service.py:main()`
- Web UI: `unmanic/webserver/main.py`
- Workers: `unmanic/libs/workers.py`

**Configuration:**
- Default: `~/.unmanic/` or `$HOME_DIR/config/`
- Database: `config/unmanic.db`
- Logs: `config/logs/`
- Plugins: `config/plugins/`

**Docker:**
- Config: `/config`
- Library: `/library` (watch path)
- Cache: `/tmp/unmanic` (FFmpeg temp files)

## AMD Fork Specifics

This fork maintains compatibility with upstream Unmanic while adding:

1. **Enhanced AMD GPU support** - VAAPI/AMF encoder optimizations
2. **Custom plugin** - `transcode_amd_v2` with intelligent mode selection
3. **Docker variants** - Ubuntu 22.04 (Mesa 22.x) and 24.04 (Mesa 25.x)
4. **Bug fixes** - ETC calculation, progress tracking, FFmpeg output parsing

**When syncing with upstream:**
- Key files: `unmanic/libs/workers.py`, `unmanic/libs/unffmpeg/hardware_acceleration_handle.py`
- Plugin files: `plugins/transcode_amd_v2/`
- Docker files: `docker/Dockerfile.amd*`, `docker/Dockerfile.noble`

**Docker Hub:** `viennej/unmanic-amd` (tags: `latest`, `noble`, `ffmpeg7`)
