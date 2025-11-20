#!/bin/bash
set -e

echo "=== AutoDrama Full Install (Qwen2.5-32B-AWQ Edition) ==="

apt-get update

echo "[1] 기본 패키지 설치..."
pip install pyyaml ffmpeg-python huggingface_hub hf_transfer --break-system-packages

echo "[2] PyTorch 2.5.1 설치..."
pip install torch==2.5.1 --extra-index-url https://download.pytorch.org/whl/cu124 --break-system-packages

echo "[3] vLLM 0.6.6 설치..."
pip install vllm==0.6.6.post1 --break-system-packages

echo "[4] torchaudio 설치..."
pip install torchaudio==2.5.1 --extra-index-url https://download.pytorch.org/whl/cu124 --break-system-packages

echo "[5-0] PyAV / faster-whisper 빌드를 위한 시스템 패키지 설치..."
apt-get install -y \
  pkg-config \
  ffmpeg \
  libavformat-dev \
  libavdevice-dev \
  libavfilter-dev \
  libavcodec-dev \
  libavutil-dev \
  libswscale-dev \
  libswresample-dev

echo "[5] faster-whisper 설치..."
pip install faster-whisper==0.10.0 --break-system-packages

echo "[6] XTTS 설치..."
pip install TTS==0.22.0 --break-system-packages

echo "[7] CosyVoice 제거..."
rm -rf /workspace/CosyVoice || true

echo "[8] 모델 캐시 폴더 생성..."
mkdir -p /workspace/huggingface_cache

echo "[9] Qwen2.5-32B-AWQ 사전 다운로드..."
huggingface-cli download Qwen/Qwen2.5-32B-Instruct-AWQ \
  --local-dir /workspace/huggingface_cache/Qwen2.5-32B-AWQ \
  --local-dir-use-symlinks False

echo "=== 설치 완료 ==="
