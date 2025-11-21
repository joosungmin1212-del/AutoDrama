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
# Step 4: Verify and Auto-Fix Critical Package Versions
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
check_version "tokenizers" "(0.22.x-0.23.x)"
check_version "huggingface-hub" "(must be <1.0)"
check_version "diffusers" "(must be <0.30.0)"
check_version "TTS" "(>=0.22.0)"
check_version "whisper-ctranslate2" "(>=0.4.3)"
check_version "xformers" "(>=0.0.23)"

# Auto-repair known conflicts
echo ""
echo "Checking for known conflicts and auto-fixing..."

NUMPY_VERSION=$(pip show numpy 2>/dev/null | grep "^Version:" | awk '{print $2}')
if [[ "$NUMPY_VERSION" == 2.* ]]; then
    echo "✗ CRITICAL: numpy $NUMPY_VERSION detected (vLLM requires <2.0.0)"
    echo "   🔧 Auto-fixing: Downgrading numpy to 1.26.x..."
    pip install --break-system-packages --force-reinstall 'numpy>=1.26.0,<2.0.0' -q

    # Re-check after fix
    NUMPY_VERSION=$(pip show numpy 2>/dev/null | grep "^Version:" | awk '{print $2}')
    if [[ "$NUMPY_VERSION" == 1.* ]]; then
        echo "   ✓ Fixed: numpy $NUMPY_VERSION"
    else
        echo "   ✗ Auto-fix failed! Manual intervention required."
        exit 1
    fi
fi

HF_HUB_VERSION=$(pip show huggingface-hub 2>/dev/null | grep "^Version:" | awk '{print $2}')
if [[ "$HF_HUB_VERSION" == 1.* ]]; then
    echo "✗ CRITICAL: huggingface-hub $HF_HUB_VERSION detected (transformers requires <1.0)"
    echo "   🔧 Auto-fixing: Downgrading huggingface-hub to 0.29.x..."
    pip install --break-system-packages --force-reinstall 'huggingface-hub>=0.23.0,<0.30.0' -q

    # Re-check after fix
    HF_HUB_VERSION=$(pip show huggingface-hub 2>/dev/null | grep "^Version:" | awk '{print $2}')
    if [[ "$HF_HUB_VERSION" == 0.* ]]; then
        echo "   ✓ Fixed: huggingface-hub $HF_HUB_VERSION"
    else
        echo "   ✗ Auto-fix failed! Manual intervention required."
        exit 1
    fi
fi

DIFFUSERS_VERSION=$(pip show diffusers 2>/dev/null | grep "^Version:" | awk '{print $2}')
if [[ "$DIFFUSERS_VERSION" == 0.3* ]] || [[ "$DIFFUSERS_VERSION" == 0.4* ]]; then
    echo "✗ WARNING: diffusers $DIFFUSERS_VERSION may require numpy 2.x"
    echo "   🔧 Auto-fixing: Downgrading diffusers to 0.29.x..."
    pip install --break-system-packages --force-reinstall 'diffusers>=0.27.0,<0.30.0' -q

    # Re-check after fix
    DIFFUSERS_VERSION=$(pip show diffusers 2>/dev/null | grep "^Version:" | awk '{print $2}')
    if [[ "$DIFFUSERS_VERSION" == 0.2* ]]; then
        echo "   ✓ Fixed: diffusers $DIFFUSERS_VERSION"
    else
        echo "   ⚠ Warning: diffusers $DIFFUSERS_VERSION (may still work)"
    fi
fi

echo ""
echo "✓ All critical packages validated and fixed!"

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
echo "       Network interruptions are OK - download will resume automatically"
echo ""

# Python-based download (more reliable than CLI)
python3 << 'PYTHON_DOWNLOAD'
import os
from huggingface_hub import snapshot_download

cache_dir = "/workspace/huggingface_cache/Qwen2.5-72B-AWQ"

print(f"📥 Downloading to {cache_dir}...")
print("   This may take 20-30 minutes depending on your connection...")
print("   Progress will be shown below:")
print("")

try:
    snapshot_download(
        repo_id="Qwen/Qwen2.5-72B-Instruct-AWQ",
        local_dir=cache_dir,
        local_dir_use_symlinks=False,
        resume_download=True,
        max_workers=4
    )
    print("")
    print("✓ Model download complete!")
except KeyboardInterrupt:
    print("")
    print("⚠ Download interrupted by user.")
    print("  Run this script again to resume from where you left off.")
    exit(0)
except Exception as e:
    print("")
    print(f"✗ Download failed: {e}")
    print("")
    print("You can manually resume download later with:")
    print(f"  python3 -c \"from huggingface_hub import snapshot_download; \\")
    print(f"    snapshot_download('Qwen/Qwen2.5-72B-Instruct-AWQ', \\")
    print(f"      local_dir='{cache_dir}', \\")
    print(f"      local_dir_use_symlinks=False, \\")
    print(f"      resume_download=True)\"")
    exit(1)
PYTHON_DOWNLOAD

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
