#!/bin/bash

# 脚本配置：发生错误时立即退出，使用未定义变量时报错，管道出错时终止脚本
set -e
set -u
set -o pipefail

# 更新系统软件包索引
echo "Updating system package index..."
sudo apt update

# 安装 Spacemit 所需依赖与工具包
echo "Installing required packages..."
sudo apt install -y \
  spacemit-ollama-toolkit \
  portaudio19-dev \
  python3-dev \
  libopenblas-dev \
  ffmpeg \
  python3-venv \
  python3-spacemit-ort

# 设置下载目录
MODEL_DIR=~/models
mkdir -p $MODEL_DIR
cd $MODEL_DIR

# 下载并创建 Qwen2.5 0.5B 模型
wget -c https://archive.spacemit.com/spacemit-ai/gguf/Qwen2.5-0.5B-Instruct-Q4_0.gguf --no-check-certificate
wget -c https://archive.spacemit.com/spacemit-ai/modelfile/qwen2.5:0.5b.modelfile --no-check-certificate
ollama create qwen2.5:0.5b -f qwen2.5:0.5b.modelfile

# 下载并创建 Qwen2.5 0.5B-FC 模型
wget -c https://archive.spacemit.com/spacemit-ai/gguf/qwen2.5-0.5b-f16-elephant-fc-Q4_0.gguf --no-check-certificate
wget -c https://archive.spacemit.com/spacemit-ai/modelfile/qwen2.5-0.5b-elephant-fc.modelfile --no-check-certificate
ollama create qwen2.5-0.5b-elephant-fc -f qwen2.5-0.5b-elephant-fc.modelfile

# 删除模型目录
cd ~
rm -rf $MODEL_DIR

echo "All dependencies installed successfully."

