# Dependency Version Matrix

**Last Updated**: 2025-01-22
**Verified for**: vLLM 0.6.6.post1 + Qwen2.5-72B-Instruct-AWQ

## ✅ Verified Working Configuration

This configuration has been researched and verified from vLLM 0.6.6.post1 official requirements and Qwen2.5 model card recommendations.

### Core Dependencies

| Package | Version | Source | Notes |
|---------|---------|--------|-------|
| **Python** | 3.11+ | - | Required for all components |
| **CUDA** | 12.4+ | - | GPU acceleration required |

### PyTorch Stack

| Package | Version | Source | Critical Notes |
|---------|---------|--------|----------------|
| **torch** | 2.5.1+cu124 | vLLM official | Must match CUDA 12.4 |
| **torchvision** | 0.20.1+cu124 | vLLM official | **CRITICAL**: Required by vLLM 0.6.6.post1 |
| **torchaudio** | 2.5.1+cu124 | - | For audio processing |

⚠️ **IMPORTANT**: torchvision 0.20.1 is **required** by vLLM 0.6.6.post1. Missing this package causes `operator torchvision::nms does not exist` errors.

### HuggingFace Ecosystem

| Package | Version | Source | Dependency Chain |
|---------|---------|--------|------------------|
| **transformers** | 4.45.2 | vLLM official | Fixed to prevent auto-upgrades |
| **tokenizers** | >=0.19.1,<0.24.0 | vLLM official + transformers runtime | vLLM requires >=0.19.1, transformers 4.45.2 runtime requires 0.22.x-0.23.x |
| **huggingface-hub** | >=0.34.0,<1.0.0 | transformers 4.45.2 runtime | **Runtime requirement changed** from >=0.23.0 |
| **hf-transfer** | >=0.1.0,<1.0.0 | - | Fast model downloads |

#### 🔴 Known Dependency Drift Issue

**transformers 4.45.2** has **different requirements at install-time vs runtime**:

- **Install-time** (2024-10): `tokenizers>=0.20,<0.21`, `huggingface-hub>=0.23,<0.30`
- **Runtime** (2025-01): `tokenizers>=0.22.0,<=0.23.0`, `huggingface-hub>=0.34.0,<1.0`

**Solution**: Use broader version ranges that satisfy both:
- `tokenizers>=0.19.1,<0.24.0` (covers vLLM 0.19.1+ and transformers 0.22.x-0.23.x)
- `huggingface-hub>=0.34.0,<1.0.0` (satisfies runtime requirements)

### LLM Inference

| Package | Version | Source | Notes |
|---------|---------|--------|-------|
| **vllm** | 0.6.6.post1 | - | AWQ support for Qwen 72B |
| **xformers** | 0.0.28.post3 | vLLM official | Memory-efficient attention |
| **numpy** | >=1.26.0,<2.0.0 | vLLM requirement | vLLM incompatible with numpy 2.x |

### Image Generation

| Package | Version | Source | Notes |
|---------|---------|--------|-------|
| **diffusers** | >=0.27.0,<0.30.0 | - | SDXL Lightning support, avoid 0.30+ (requires numpy 2.x) |
| **accelerate** | >=0.20.0,<1.0.0 | - | Model acceleration |
| **safetensors** | >=0.4.0,<1.0.0 | - | Safe model serialization |
| **invisible-watermark** | >=0.2.0,<1.0.0 | - | SDXL watermarking |

### Audio Processing

| Package | Version | Source | Notes |
|---------|---------|--------|-------|
| **TTS** | >=0.22.0,<0.23.0 | - | Coqui TTS (Korean voice synthesis) |
| **whisper-ctranslate2** | >=0.4.3,<1.0.0 | - | Korean STT (CTranslate2 backend) |

⚠️ **IMPORTANT**:
- Do **NOT** use `faster-whisper` - it requires `tokenizers<0.16` which conflicts with transformers 4.45.2
- **Coqui TTS** requires Python 3.10 or 3.11 (no Python 3.12 wheels available)

### Utilities

| Package | Version | Source | Notes |
|---------|---------|--------|-------|
| **pyyaml** | >=6.0,<7.0 | - | Config file parsing |
| **ffmpeg-python** | >=0.2.0,<0.3.0 | - | Video processing wrapper |
| **Pillow** | >=10.0.0,<11.0.0 | - | Image processing |
| **tqdm** | >=4.66.0,<5.0.0 | - | Progress bars |

## 🚫 Incompatible Packages

| Package | Reason | Alternative |
|---------|--------|-------------|
| **Python 3.12** | Coqui TTS has no Python 3.12 wheels | Use Python 3.10 or 3.11 |
| **faster-whisper** | Requires `tokenizers<0.16` | Use `whisper-ctranslate2>=0.4.3` |
| **numpy 2.x** | vLLM incompatible | Pin to `numpy>=1.26.0,<2.0.0` |
| **diffusers 0.30+** | Requires numpy 2.x | Pin to `diffusers>=0.27.0,<0.30.0` |

## 🔧 Installation Order

**CRITICAL**: Install in this exact order to avoid conflicts:

1. **System packages** (FFmpeg, git)
2. **PyTorch stack** (torch, torchvision, torchaudio) with `--extra-index-url`
3. **All other packages** from requirements.txt

```bash
# Step 1: System
apt-get update && apt-get install -y ffmpeg git

# Step 2: PyTorch (MUST be first)
pip install --break-system-packages \
  torch==2.5.1 \
  torchvision==0.20.1 \
  torchaudio==2.5.1 \
  --extra-index-url https://download.pytorch.org/whl/cu124

# Step 3: Everything else
pip install --break-system-packages -r requirements.txt
```

## 🛡️ Auto-Repair Logic

`setup_complete.sh` includes automatic conflict detection and repair:

### 1. numpy Version Check
```bash
if numpy >= 2.0.0:
    downgrade to numpy>=1.26.0,<2.0.0
```

### 2. huggingface-hub Version Check
```bash
if huggingface-hub < 0.34.0:
    upgrade to huggingface-hub>=0.34.0,<1.0.0
```

### 3. tokenizers Version Check
```bash
if tokenizers < 0.19.1:
    upgrade to tokenizers>=0.19.1,<0.24.0
```

### 4. diffusers Version Check
```bash
if diffusers >= 0.30.0:
    downgrade to diffusers>=0.27.0,<0.30.0
```

### 5. distutils Conflicts (blinker)
```bash
pip install --ignore-installed TTS>=0.22.0
```

## 📊 VRAM Requirements

| Component | VRAM Usage | Notes |
|-----------|------------|-------|
| **vLLM (Qwen 72B AWQ)** | ~18-20GB | 4-bit quantization, TP=1 |
| **SDXL Lightning** | ~6-8GB | 4-step inference |
| **Coqui TTS** | ~2-3GB | Korean voice synthesis |
| **Whisper large-v3** | ~3-4GB | Korean STT |
| **System overhead** | ~5-10GB | PyTorch, CUDA, etc. |
| **Total** | **~40-50GB** | **80GB GPU recommended** (A100 80GB, H100) |

### Minimum Configuration
- **GPU**: NVIDIA A100 40GB or equivalent
- **System RAM**: 64GB+
- **Disk**: 200GB+ (models: ~160GB, outputs: ~2GB per video)

## ⚠️ Known Issues

### Issue 1: Dependency Drift
**Problem**: transformers 4.45.2 requirements change between install-time and runtime
**Solution**: Use broader version ranges in requirements.txt (already implemented)

### Issue 2: torchvision Missing
**Problem**: vLLM 0.6.6.post1 requires torchvision but doesn't list it explicitly
**Error**: `RuntimeError: operator torchvision::nms does not exist`
**Solution**: Explicitly install torchvision 0.20.1 with torch (already implemented)

### Issue 3: distutils blinker
**Problem**: RunPod has system-installed blinker 1.4 via distutils
**Error**: `Cannot uninstall blinker 1.4 - It is a distutils installed project`
**Solution**: Auto-detect and remove distutils blinker, then retry installation
**Implementation**:
```bash
# Step 3: Attempt normal installation first
if ! pip install --break-system-packages -r requirements.txt; then
    # If blinker conflict detected, remove distutils version
    if grep -q "Cannot uninstall blinker"; then
        rm -rf /usr/lib/python3*/dist-packages/blinker*
        # Retry installation
        pip install --break-system-packages -r requirements.txt
    fi
fi
```
**Advantages**:
- Maintains full dependency resolution (no `--ignore-installed` needed)
- PyTorch not reinstalled (preserves CUDA version)
- Only activates when actual conflict occurs

### Issue 4: AWQ + Tensor Parallelism
**Problem**: Qwen2.5-72B-AWQ unstable with TP>1
**Solution**: Always use TP=1 in vLLM config (default in our setup)

## 🔍 Verification Commands

After installation, verify critical packages:

```bash
# Check versions
pip show numpy torch torchvision transformers tokenizers huggingface-hub vllm xformers

# Test imports
python3 -c "import torch; print(f'PyTorch: {torch.__version__}')"
python3 -c "import torch; print(f'CUDA: {torch.cuda.is_available()}')"
python3 -c "import transformers; print(f'Transformers: {transformers.__version__}')"
python3 -c "import vllm; print(f'vLLM: {vllm.__version__}')"

# Test VRAM
nvidia-smi
```

## 📚 References

1. **vLLM 0.6.6.post1 Official Requirements**
   - Source: https://github.com/vllm-project/vllm/blob/v0.6.6.post1/requirements.txt
   - Date: 2024-10

2. **Qwen2.5-72B-Instruct-AWQ Model Card**
   - Source: https://huggingface.co/Qwen/Qwen2.5-72B-Instruct-AWQ
   - Requirements: transformers>=4.37.0, vLLM>=0.4.3

3. **transformers 4.45.2 Runtime Requirements**
   - Source: Observed from actual runtime errors (2025-01)
   - tokenizers>=0.22.0,<=0.23.0
   - huggingface-hub>=0.34.0,<1.0

4. **vLLM GitHub Issues**
   - AWQ + TP issues: https://github.com/vllm-project/vllm/issues
   - Qwen2.5-VL-AWQ compatibility: v0.8.x has known issues

## 🔄 Update History

| Date | Change | Reason |
|------|--------|--------|
| 2025-01-22 | Initial version matrix | Document verified working configuration |
| 2025-01-22 | Added torchvision 0.20.1 | Fix vLLM operator error |
| 2025-01-22 | Updated tokenizers to >=0.19.1,<0.24.0 | Fix dependency drift |
| 2025-01-22 | Updated huggingface-hub to >=0.34.0 | Fix runtime requirement |
| 2025-01-22 | Pinned xformers to 0.0.28.post3 | vLLM official requirement |
| 2025-01-22 | Added blinker auto-removal logic | Fix distutils conflict without --ignore-installed |

---

**Maintained by**: AutoDrama Project
**Repository**: https://github.com/joosungmin1212-del/AutoDrama
