#!/bin/bash
echo "Installing CosyVoice..."
cd /workspace
if [ ! -d "CosyVoice" ]; then
    git clone --recursive https://github.com/FunAudioLLM/CosyVoice.git
fi
cd CosyVoice

# grpcio 제외하고 설치
sed '/grpcio/d' requirements.txt > requirements_nogrpc.txt
pip install -r requirements_nogrpc.txt --break-system-packages

# torchvision 호환 버전 설치
pip install torchvision==0.18.1+cu121 --break-system-packages --extra-index-url https://download.pytorch.org/whl/cu121

echo "CosyVoice installation complete!"
