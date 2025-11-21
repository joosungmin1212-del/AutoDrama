#!/bin/bash
set -e

echo "========================================"
echo "AutoDrama Full Installation"
echo "Qwen2.5-72B-AWQ + vLLM + SDXL Lightning"
echo "========================================"
echo ""
echo "This script will install all dependencies in the correct order"
echo "to avoid version conflicts. Estimated time: 10-15 minutes"
echo ""

# ============================================
# Step 1: System Dependencies
# ============================================
echo "[1/6] Updating system packages..."
apt-get update -qq

echo "[1/6] Installing FFmpeg and system dependencies..."
apt-get install -y -qq ffmpeg git

# ============================================
# Step 2: PyTorch (MUST install first)
# ============================================
echo "[2/6] Installing PyTorch 2.5.1 + CUDA 12.4..."
echo "       (This must be installed before other packages)"

pip install --break-system-packages \
  torch==2.5.1 \
  torchaudio==2.5.1 \
  --extra-index-url https://download.pytorch.org/whl/cu124

# Verify PyTorch installation
python3 -c "import torch; print(f'✓ PyTorch {torch.__version__} installed')"
python3 -c "import torch; print(f'✓ CUDA available: {torch.cuda.is_available()}')"

# ============================================
# Step 3: Install ALL other dependencies from requirements.txt
# ============================================
echo "[3/6] Installing all Python dependencies from requirements.txt..."
echo "       This will automatically resolve version conflicts"

# Use pip's dependency resolver with requirements.txt as single source of truth
pip install --break-system-packages -r requirements.txt

# ============================================
# Step 4: Verify Critical Package Versions
# ============================================
echo "[4/6] Verifying critical package versions..."

# Function to check package version
check_version() {
    local package=$1
    local constraint=$2
    local version=$(pip show "$package" 2>/dev/null | grep "^Version:" | awk '{print $2}')

    if [ -z "$version" ]; then
        echo "✗ $package: NOT INSTALLED"
        return 1
    else
        echo "✓ $package: $version $constraint"
    fi
}

# Critical version checks
echo ""
echo "Dependency Validation:"
check_version "numpy" "(must be <2.0.0 for vLLM)"
check_version "torch" "(2.5.1+cu124)"
check_version "vllm" "(0.6.6.post1)"
check_version "transformers" "(4.45.2)"
check_version "tokenizers" "(0.20.3)"
check_version "huggingface-hub" "(must be <1.0)"
check_version "diffusers" "(must be <0.30.0)"
check_version "TTS" "(>=0.22.0)"
check_version "whisper-ctranslate2" "(>=0.4.3)"
check_version "xformers" "(>=0.0.23)"

# Additional validation
echo ""
echo "Checking for known conflicts..."

NUMPY_VERSION=$(pip show numpy 2>/dev/null | grep "^Version:" | awk '{print $2}')
if [[ "$NUMPY_VERSION" == 2.* ]]; then
    echo "✗ CRITICAL: numpy $NUMPY_VERSION detected (vLLM requires <2.0.0)"
    echo "   Run: pip install --force-reinstall 'numpy>=1.26.0,<2.0.0'"
    exit 1
fi

HF_HUB_VERSION=$(pip show huggingface-hub 2>/dev/null | grep "^Version:" | awk '{print $2}')
if [[ "$HF_HUB_VERSION" == 1.* ]]; then
    echo "✗ CRITICAL: huggingface-hub $HF_HUB_VERSION detected (transformers requires <1.0)"
    echo "   Run: pip install --force-reinstall 'huggingface-hub>=0.23.0,<0.30.0'"
    exit 1
fi

DIFFUSERS_VERSION=$(pip show diffusers 2>/dev/null | grep "^Version:" | awk '{print $2}')
if [[ "$DIFFUSERS_VERSION" == 0.3* ]] || [[ "$DIFFUSERS_VERSION" == 0.4* ]]; then
    echo "✗ WARNING: diffusers $DIFFUSERS_VERSION may require numpy 2.x"
    echo "   Recommended: diffusers <0.30.0"
fi

echo ""
echo "✓ All critical packages validated!"

# ============================================
# Step 5: Setup Model Cache Directories
# ============================================
echo "[5/6] Setting up model cache directories..."

mkdir -p /workspace/huggingface_cache
mkdir -p /workspace/models/whisper
mkdir -p /workspace/models/sdxl
mkdir -p /workspace/outputs

echo "✓ Directories created:"
echo "  - /workspace/huggingface_cache (HuggingFace models)"
echo "  - /workspace/models/whisper (Whisper models)"
echo "  - /workspace/models/sdxl (SDXL models)"
echo "  - /workspace/outputs (Generated videos)"

# ============================================
# Step 6: Download Qwen2.5-72B-AWQ Model
# ============================================
echo "[6/6] Downloading Qwen2.5-72B-AWQ model..."
echo "       This is a large model (~145GB), may take 20-30 minutes"
echo ""

# Ensure huggingface-cli is available
if ! command -v huggingface-cli &> /dev/null; then
    echo "⚠ huggingface-cli not found in PATH, trying to locate..."

    # Find huggingface-cli in Python site-packages
    HF_CLI_PATH=$(python3 -c "import sys; import os; paths=[os.path.join(p, 'bin', 'huggingface-cli') for p in sys.path if 'site-packages' in p]; print(next((p for p in paths if os.path.exists(p)), ''))" 2>/dev/null)

    if [ -n "$HF_CLI_PATH" ]; then
        echo "✓ Found huggingface-cli at: $HF_CLI_PATH"
        alias huggingface-cli="$HF_CLI_PATH"
    else
        echo "✗ huggingface-cli not found, reinstalling huggingface-hub..."
        pip install --break-system-packages --force-reinstall 'huggingface-hub>=0.23.0,<0.30.0'

        # Try system-wide installation if still not found
        if ! command -v huggingface-cli &> /dev/null; then
            export PATH="$PATH:/usr/local/bin:$HOME/.local/bin"
        fi
    fi
fi

# Download the model
if command -v huggingface-cli &> /dev/null || [ -n "$HF_CLI_PATH" ]; then
    echo "Starting download..."

    # Set environment variable for faster downloads
    export HF_HUB_ENABLE_HF_TRANSFER=1

    # Download with progress
    ${HF_CLI_PATH:-huggingface-cli} download Qwen/Qwen2.5-72B-Instruct-AWQ \
        --local-dir /workspace/huggingface_cache/Qwen2.5-72B-AWQ \
        --local-dir-use-symlinks False

    echo "✓ Qwen2.5-72B-AWQ downloaded successfully!"
else
    echo "⚠ WARNING: Could not find huggingface-cli"
    echo "   Model download skipped. You can download manually later with:"
    echo "   huggingface-cli download Qwen/Qwen2.5-72B-Instruct-AWQ \\"
    echo "     --local-dir /workspace/huggingface_cache/Qwen2.5-72B-AWQ \\"
    echo "     --local-dir-use-symlinks False"
fi

# ============================================
# Installation Complete
# ============================================
echo ""
echo "============================================"
echo "Installation Complete! 🎬"
echo "============================================"
echo ""
echo "Installed Components:"
echo "  ✓ PyTorch 2.5.1 + CUDA 12.4"
echo "  ✓ vLLM 0.6.6.post1 (Qwen 72B AWQ support)"
echo "  ✓ Transformers 4.45.2 + Tokenizers 0.20.3"
echo "  ✓ Diffusers + SDXL Lightning"
echo "  ✓ Coqui TTS (Korean voice synthesis)"
echo "  ✓ Whisper-CTranslate2 (Korean STT)"
echo "  ✓ xFormers (memory-efficient attention)"
echo ""
echo "Model Cache: /workspace/huggingface_cache"
echo "Output Directory: /workspace/outputs"
echo ""
echo "To run AutoDrama:"
echo "  cd /workspace/AutoDrama"
echo "  python main.py"
echo ""
echo "To test individual components:"
echo "  python test_outline.py \"할머니의 비밀 일기장\""
echo "  python test_part_v3.py \"할머니의 비밀 일기장\""
echo ""
echo "Ready to generate 2-hour Korean dramas! 🎭"
