#!/bin/bash

# Install LLVM 18 for better AMD GPU support
echo "**** Installing LLVM 18 for AMD GPU support ****"

# Add LLVM repository
wget -qO - https://apt.llvm.org/llvm-snapshot.gpg.key | gpg --dearmor --output /usr/share/keyrings/llvm-snapshot.gpg
echo "deb [signed-by=/usr/share/keyrings/llvm-snapshot.gpg] https://apt.llvm.org/jammy/ llvm-toolchain-jammy-18 main" | tee /etc/apt/sources.list.d/llvm.list

# Update package lists
apt-get update

# Install LLVM 18
apt-get install -y llvm-18 libllvm18

# Set environment variables
echo "export LLVM_VERSION=18" >> /etc/environment

echo "**** LLVM 18 installation complete ****"