#!/bin/bash
set -e

echo "=== AutoDrama 완전 설치 시작 ==="

apt-get update

echo "[1] vLLM 0.6.6.post1 설치..."
pip install "vllm==0.6.6.post1" --extra-index-url https://download.pytorch.org/whl/cu124 --break-system-packages

echo "[2] torch & torchaudio 2.5.1 설치..."
pip install torch==2.5.1 --extra-index-url https://download.pytorch.org/whl/cu124 --break-system-packages
pip install torchaudio==2.5.1 --extra-index-url https://download.pytorch.org/whl/cu124 --break-system-packages

echo "[3] CosyVoice 설치..."
cd /workspace
rm -rf CosyVoice
git clone --recursive https://github.com/FunAudioLLM/CosyVoice.git
cd CosyVoice
grep -v -E 'torch|grpcio' requirements.txt > req_fix.txt
pip install -r req_fix.txt --break-system-packages
pip install onnxruntime soundfile jieba numpy==1.26.4 --break-system-packages

echo "[4] AutoDrama clone..."
cd /workspace
rm -rf AutoDrama
git clone https://github.com/joosungmin1212-del/AutoDrama.git

echo "[5] 기본 패키지 설치..."
pip install pyyaml ffmpeg-python huggingface_hub hf_transfer --break-system-packages

echo "[6] 모델 캐시 폴더 생성..."
mkdir -p /workspace/huggingface_cache

echo "[7] Qwen2.5-32B-AWQ 다운로드..."
huggingface-cli download Qwen/Qwen2.5-32B-Instruct-AWQ --local-dir /workspace/huggingface_cache/Qwen2.5-32B-AWQ --local-dir-use-symlinks False

echo "=== 설치 완료! ==="
