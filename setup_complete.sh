#!/bin/bash
set -e

echo "========================================"
echo "AutoDrama Full Installation"
echo "Qwen2.5-32B-AWQ + vLLM + SDXL Lightning"
echo "========================================"
echo ""

apt-get update

# ============================================
# 1) Core Dependencies (충돌 방지 순서)
# ============================================
echo "[1/9] Installing Core Python packages..."
pip install --break-system-packages \
  "numpy>=1.26.0,<2.0.0" \
  "pyyaml>=6.0" \
  "ffmpeg-python>=0.2.0"

# ============================================
# 2) HuggingFace Ecosystem (버전 고정)
# ============================================
echo "[2/9] Installing HuggingFace ecosystem..."
pip install --break-system-packages \
  "huggingface-hub>=0.23.0,<0.30.0" \
  "hf-transfer>=0.1.0" \
  "transformers==4.45.2" \
  "tokenizers==0.20.3"

# ============================================
# 3) PyTorch 2.5.1 + cu124
# ============================================
echo "[3/9] Installing PyTorch 2.5.1 + CUDA 12.4..."
pip install --break-system-packages \
  torch==2.5.1 \
  torchaudio==2.5.1 \
  --extra-index-url https://download.pytorch.org/whl/cu124

# ============================================
# 4) vLLM 0.6.6.post1
# ============================================
echo "[4/9] Installing vLLM 0.6.6.post1..."
pip install --break-system-packages "vllm==0.6.6.post1"

# ============================================
# 5) STT - whisper-ctranslate2
# ============================================
echo "[5/9] Installing whisper-ctranslate2..."
pip install --break-system-packages "whisper-ctranslate2>=0.4.3"

# ============================================
# 6) TTS - Coqui TTS
# ============================================
echo "[6/9] Installing TTS (Coqui)..."
pip install --break-system-packages "TTS>=0.22.0"

# ============================================
# 7) Image Generation - SDXL Lightning
# ============================================
echo "[7/9] Installing diffusers + SDXL Lightning dependencies..."
pip install --break-system-packages \
  "diffusers>=0.27.0" \
  "accelerate>=0.20.0" \
  "safetensors>=0.4.0" \
  "invisible-watermark>=0.2.0" \
  "xformers>=0.0.23"

# ============================================
# 8) Utilities
# ============================================
echo "[8/9] Installing utilities..."
pip install --break-system-packages \
  "Pillow>=10.0.0" \
  "tqdm>=4.66.0"

# ============================================
# 9) Model Cache & Download
# ============================================
echo "[9/9] Setting up model cache and downloading Qwen2.5-32B-AWQ..."

mkdir -p /workspace/huggingface_cache
mkdir -p /workspace/models/whisper
mkdir -p /workspace/models/sdxl
mkdir -p /workspace/output

# Qwen2.5-32B-AWQ 다운로드
echo "Downloading Qwen2.5-32B-AWQ (this may take a while)..."
huggingface-cli download Qwen/Qwen2.5-32B-Instruct-AWQ \
  --local-dir /workspace/huggingface_cache/Qwen2.5-32B-AWQ \
  --local-dir-use-symlinks False

# SDXL Lightning 다운로드 (optional, 첫 실행 시 자동 다운로드됨)
echo "SDXL Lightning will be downloaded on first use."

# ============================================
# 10) Cleanup & Verification
# ============================================
echo ""
echo "============================================"
echo "Installation Complete!"
echo "============================================"
echo ""
echo "Installed package versions:"
pip show vllm torch transformers tokenizers numpy huggingface-hub diffusers whisper-ctranslate2 TTS | grep -E "Name|Version"

echo ""
echo "✓ vLLM 0.6.6.post1"
echo "✓ Torch 2.5.1 + cu124"
echo "✓ Transformers 4.45.2"
echo "✓ Tokenizers 0.20.3"
echo "✓ whisper-ctranslate2"
echo "✓ diffusers + SDXL Lightning"
echo "✓ TTS (Coqui)"
echo ""
echo "Model cache: /workspace/huggingface_cache"
echo "Output directory: /workspace/output"
echo ""
echo "Ready to run AutoDrama! 🎬"
