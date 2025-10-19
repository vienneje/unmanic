# Unmanic development

The development environment can be configured in 2 ways:

1. Using Docker

2. As a Pip develop installation


Depending on what you are trying to develop, one way may work better than the other.

Regardless of the method you use, you will need to pull in the frontend component and build it.



## Dev env

### Option 1: Docker

Docker is by far the simplest way to develop. You can either pull the latest Docker image, or build
the docker image by following the [Docker documentation](../docker/README.md)

Once you have a Docker image, you can run it using the scripts in the `../devops/` directory.

Examples:
```
# Enable VAAPI (Intel/AMD)
devops/run_docker.sh --debug --hw=vaapi --cpus=1

# Enable AMD GPU specifically
devops/run_docker.sh --debug --hw=amd --cpus=1

# Enable NVIDIA
devops/run_docker.sh --debug --hw=nvidia --cpus=1

# Standard dev env
devops/run_docker.sh --debug
```

The following folders are generated in the Docker environment:

  - `/dev_environment/config` - Contains the containers mutable config data
  - `/dev_environment/library` - A library in which media files can be placed for testing
  - `/dev_environment/cache` - The temporary location used by ffmpeg for converting file formats

### Option 2: Pip

You can also just install the module natively in your home directory in "develop" mode.

Start by creating a venv.
```
python3 -m venv venv
echo 'export HOME_DIR=$(readlink -e ${VIRTUAL_ENV}/../)/dev_environment' >> ./venv/bin/activate
source ./venv/bin/activate
```

Then install the dependencies into that venv
```
python3 -m pip install --upgrade pip
python3 -m pip install --upgrade -r ./requirements.txt -r ./requirements-dev.txt
```

Then install the module:

```
python3 -m pip install --editable .
```

This creates an egg symlink to the project directory for development.

To later uninstall the development symlink:

```
python3 -m pip uninstall unmanic
```

You should now be able to run unmanic from the commandline:
```
# In develop mode this should return "UNKNOWN"
unmanic --version
```



## Building the Frontend

The Unmanic frontend UI exists in a submodule.

Start by pulling the latest changes

```
git submodule update --init --recursive 
```

Once you have done this, run the frontend_install.sh script.

```
devops/frontend_install.sh
```

This will install the NPM modules and build the frontend package. The end result will be located in `unmanic/webserver/public`



## Hardware Acceleration Support

Unmanic supports hardware-accelerated video encoding and decoding through multiple GPU vendors:

### Supported Hardware Acceleration APIs

| Vendor | API | Decoding | Encoding | Notes |
|--------|-----|----------|----------|-------|
| **AMD** | VAAPI | ✅ H.264, HEVC, VP8, VP9, AV1 | ✅ H.264, HEVC, AV1, VP9 | Uses Mesa VAAPI drivers |
| **AMD** | AMF | ❌ | ✅ H.264, HEVC, AV1 | AMD proprietary API (Windows/Linux) |
| **Intel** | VAAPI | ✅ H.264, HEVC, VP8, VP9, AV1 | ✅ H.264, HEVC, AV1, VP9 | Intel Media Driver |
| **NVIDIA** | CUDA/NVENC | ✅ H.264, HEVC, VP8, VP9, AV1 | ✅ H.264, HEVC, AV1 | Proprietary drivers |

### AMD GPU Setup

#### Requirements
- AMD GPU with hardware video encoding support (GCN 2.0+ or RDNA)
- Mesa VAAPI drivers (`mesa-va-drivers`)
- Linux kernel with AMD GPU driver (`amdgpu`)

#### Docker Setup
Use the AMD-specific Docker Compose template:
```bash
# Copy the AMD template
cp docker/docker-compose-amd.yml docker-compose.yml

# Edit docker-compose.yml with your paths and run
docker-compose up -d
```

#### Development Setup
```bash
# For AMD GPU development
devops/run_docker.sh --debug --hw=amd --cpus=1
```

#### Troubleshooting AMD VAAPI

1. **Check GPU detection:**
   ```bash
   # Inside container
   vainfo
   ```

2. **Verify device permissions:**
   ```bash
   # On host
   ls -la /dev/dri/
   # Should show renderD* devices with proper permissions
   ```

3. **Check driver installation:**
   ```bash
   # Inside container
   lspci | grep VGA
   # Should show AMD GPU
   ```

4. **Test encoding:**
   ```bash
   # Inside container
   ffmpeg -f lavfi -i testsrc=duration=10:size=1920x1080:rate=30 -c:v hevc_vaapi -f null -
   ```

### Performance Tuning

#### AMD GPU Optimizations
- Use `RADV_PERFTEST=1` environment variable for performance testing
- Set `AMD_VULKAN_ICD=RADV` for Vulkan applications
- Monitor GPU usage with `radeontop`

#### Encoder Selection Priority
1. **AMD VAAPI**: Best compatibility, works across all AMD GPUs
2. **AMD AMF**: Better performance on newer GPUs, Windows/Linux only
3. **Software**: Fallback for unsupported formats

### Hardware Acceleration Detection

Unmanic automatically detects available hardware acceleration devices and their capabilities. The system information API (`/api/v2/settings/system/configuration`) provides detailed GPU information including:

- Vendor identification (AMD, Intel, NVIDIA)
- Device model and driver information
- Supported codecs and formats
- Hardware acceleration capabilities

This information is used to automatically configure the best available encoder for your hardware.


## Database upgrades

This project uses Peewee migrations for managing the sqlite database.
`devops/migrations.sh` provides a small wrapper for the cli tool. To get started, run:
```
devops/migrations.sh --help
```
