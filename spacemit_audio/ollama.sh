#!/bin/bash

# Script configuration: exit immediately when an error occurs, report an error when using undefined variables, terminate the script when a pipeline error occurs
set -e
set -u
set -o pipefail

# Update system package index
echo "Updating system package index..."
sudo apt update

# Install Spacemit required dependencies and toolkits
echo "Installing required packages..."
sudo apt install -y \
  spacemit-ollama-toolkit \
  portaudio19-dev \
  python3-dev \
  libopenblas-dev \
  ffmpeg \
  python3-venv \
  python3-spacemit-ort

# Set Download Directory
MODEL_DIR=~/models
mkdir -p $MODEL_DIR
cd $MODEL_DIR

# Download and create the Qwen2.5 0.5B model
wget -c https://archive.spacemit.com/spacemit-ai/gguf/Qwen2.5-0.5B-Instruct-Q4_0.gguf --no-check-certificate
wget -c https://archive.spacemit.com/spacemit-ai/modelfile/qwen2.5:0.5b.modelfile --no-check-certificate
ollama create qwen2.5:0.5b -f qwen2.5:0.5b.modelfile

# Download and create the Qwen2.5 0.5B-FC model
wget -c https://archive.spacemit.com/spacemit-ai/gguf/qwen2.5-0.5b-f16-elephant-fc-Q4_0.gguf --no-check-certificate
wget -c https://archive.spacemit.com/spacemit-ai/modelfile/qwen2.5-0.5b-elephant-fc.modelfile --no-check-certificate
ollama create qwen2.5-0.5b-elephant-fc -f qwen2.5-0.5b-elephant-fc.modelfile

# Delete the model directory
cd ~
rm -rf $MODEL_DIR

echo "All dependencies installed successfully."

