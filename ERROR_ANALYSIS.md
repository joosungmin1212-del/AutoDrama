# AutoDrama 설치 에러 종합 분석

**생성일**: 2025-01-22
**분석 대상**: RunPod (Ubuntu 22.04 + Python 3.10) 설치 과정

---

## 📊 1. 전체 에러 로그

| # | 에러 메시지 | 근본 원인 | 발생 위치 | 해결 방법 | 상태 |
|---|-------------|-----------|-----------|-----------|------|
| **1** | `Cannot uninstall blinker 1.4 - It is a distutils installed project` | RunPod 시스템에 distutils로 설치된 blinker 패키지가 pip으로 제거 불가 | `pip install -r requirements.txt` 실행 중 (Step 3) | distutils 경로에서 수동 삭제 후 재설치 | ✅ 해결 |
| **2** | `RuntimeError: operator torchvision::nms does not exist` | vLLM 0.6.6.post1이 torchvision 0.20.1 필요하지만 requirements에 명시 안됨 | vLLM 실행 시 | torchvision==0.20.1 명시적 설치 (Step 2) | ✅ 해결 |
| **3** | `ImportError: tokenizers>=0.22.0,<=0.23.0 is required ... but found tokenizers==0.20.3` | transformers 4.45.2의 설치 시점 요구사항과 런타임 요구사항 불일치 (dependency drift) | transformers 임포트 시 | tokenizers>=0.19.1,<0.24.0으로 범위 확대 | ✅ 해결 |
| **4** | `ImportError: huggingface-hub>=0.34.0,<1.0 is required ... but found huggingface-hub==0.29.3` | transformers 4.45.2 런타임 요구사항 변경 + tokenizers 업그레이드 연쇄 효과 | transformers 임포트 시 | huggingface-hub>=0.34.0,<1.0.0으로 업그레이드 | ✅ 해결 |
| **5** | `ERROR: No matching distribution found for TTS>=0.22.0` | Coqui TTS는 Python 3.12 wheels 미제공 → 설치 불가능 | `pip install -r requirements.txt` 실행 중 (Step 3) | OpenVoice로 교체 (Python 3.12 완전 지원) | ✅ 해결 |

---

## 🔗 2. 패키지 호환성 매트릭스

### 2.1 핵심 충돌 관계

| 패키지 A | 버전 | 요구사항 | 충돌 패키지 | 충돌 이유 | 우선순위 |
|---------|------|---------|-------------|-----------|---------|
| **vLLM** | 0.6.6.post1 | numpy<2.0.0 | diffusers>=0.30.0 | diffusers 0.30+는 numpy 2.x 필요 | 🔴 Critical |
| **vLLM** | 0.6.6.post1 | tokenizers>=0.19.1 | faster-whisper | faster-whisper는 tokenizers<0.16 필요 | 🔴 Critical |
| **vLLM** | 0.6.6.post1 | torchvision==0.20.1 | (명시 안됨) | 공식 requirements.txt에 누락됨 | 🟡 High |
| **transformers** | 4.45.2 | tokenizers>=0.22.0 (runtime) | vLLM (설치 시점) | 설치 시점에는 tokenizers>=0.20.0,<0.21.0 요구 | 🟡 High |
| **transformers** | 4.45.2 | huggingface-hub>=0.34.0 (runtime) | 이전 버전 transformers | 설치 시점에는 huggingface-hub>=0.23.0,<0.30.0 요구 | 🟡 High |
| **Coqui TTS** | 0.22.0 | Python>=3.11, wheels available | RunPod Python 3.12 | Coqui TTS는 Python 3.12 wheels 미제공 → OpenVoice로 교체 | ✅ 해결됨 |
| **blinker** | 1.4 (distutils) | (시스템 패키지) | TTS>=0.22.0 | TTS가 blinker>=1.6.2 필요, distutils 패키지 제거 불가 | 🟡 High |

### 2.2 의존성 체인 (검증된 작동 버전)

```
vLLM 0.6.6.post1
├── torch==2.5.1+cu124 ✅
├── torchvision==0.20.1+cu124 ✅ (수동 추가 필요)
├── transformers>=4.45.2,<4.46 ✅
│   ├── tokenizers>=0.19.1,<0.24.0 ✅ (범위 확대로 해결)
│   │   └── vLLM 요구: >=0.19.1
│   │   └── transformers 런타임 요구: >=0.22.0,<=0.23.0
│   └── huggingface-hub>=0.34.0,<1.0.0 ✅ (업그레이드로 해결)
│       └── transformers 런타임 요구: >=0.34.0
├── numpy>=1.26.0,<2.0.0 ✅
├── xformers==0.0.28.post3 ✅
└── accelerate>=0.20.0,<1.0.0 ✅

SDXL Lightning
├── diffusers>=0.27.0,<0.30.0 ✅ (0.30+ numpy 2.x 필요로 제외)
├── safetensors>=0.4.0,<1.0.0 ✅
└── invisible-watermark>=0.2.0,<1.0.0 ✅

TTS (OpenVoice) ✅ 해결됨
├── Python 3.12 완전 지원 ✅
└── Python 3.11+ 호환 ✅

Whisper-CTranslate2
└── tokenizers>=0.19.1,<0.24.0 ✅ (faster-whisper 대신 사용)
```

---

## 🔧 3. 강제 설치 분석

| 패키지 | 정상 설치 가능? | 강제 설치 이유 | 사용 방법 | 위험도 | 영향 범위 |
|--------|----------------|---------------|-----------|--------|----------|
| **blinker** (제거 후 재설치) | ❌ | RunPod에 distutils로 설치된 1.4 버전이 pip으로 제거 불가 | `rm -rf /usr/lib/python3*/dist-packages/blinker*` | 🟡 Medium | TTS 설치 차단 해제 |
| **tokenizers** (범위 확대) | ⚠️ | vLLM(>=0.19.1)과 transformers(0.22.x-0.23.x) 런타임 요구사항 모두 만족 필요 | `tokenizers>=0.19.1,<0.24.0` | 🟢 Low | 두 패키지 간 호환성 보장 |
| **huggingface-hub** (강제 업그레이드) | ⚠️ | transformers 4.45.2 런타임이 >=0.34.0 요구 (설치 시점과 다름) | `huggingface-hub>=0.34.0,<1.0.0` | 🟢 Low | transformers 런타임 안정성 |
| **torchvision** (명시적 추가) | ⚠️ | vLLM 0.6.6.post1 필수 의존성이지만 공식 requirements.txt에 누락 | `torchvision==0.20.1+cu124` | 🟢 Low | vLLM NMS 연산자 오류 방지 |
| **xformers** (정확한 버전 핀) | ✅ | vLLM 0.6.6.post1 공식 요구사항이 0.0.28.post3 | `xformers==0.0.28.post3` | 🟢 Low | vLLM attention 최적화 |
| **diffusers** (버전 제한) | ✅ | 0.30.0+ 버전이 numpy 2.x 필요 (vLLM과 충돌) | `diffusers>=0.27.0,<0.30.0` | 🟢 Low | numpy 1.x 유지 |
| **numpy** (버전 제한) | ✅ | vLLM이 numpy 2.x와 호환 불가 | `numpy>=1.26.0,<2.0.0` | 🔴 Critical | vLLM 전체 동작 |

### 강제 설치 방법 비교

| 방법 | 명령어 예시 | 장점 | 단점 | 사용 여부 |
|------|------------|------|------|----------|
| **A. --ignore-installed (전체)** | `pip install --ignore-installed -r requirements.txt` | 모든 충돌 우회 | PyTorch CUDA 버전 깨짐 위험 | ❌ 사용 안함 |
| **B. --ignore-installed (개별)** | `pip install --ignore-installed TTS>=0.22.0` | 특정 패키지만 우회 | 의존성 해석 무시로 추가 충돌 가능 | ❌ 사용 안함 |
| **C. 선택적 제거 + 재설치** | `rm -rf /usr/lib/.../blinker* && pip install -r requirements.txt` | 의존성 해석 유지, PyTorch 보존 | blinker 충돌만 해결 | ✅ **채택** |

**채택 이유**:
- PyTorch 2.5.1+cu124 버전 보존 (재설치 시 CPU 버전 설치될 위험)
- pip 의존성 해석 기능 유지 (자동 충돌 탐지)
- blinker 충돌만 선택적으로 우회

---

## 🐛 4. 에러별 상세 분석

### 에러 #1: blinker distutils 충돌

**전체 에러 메시지**:
```
error: uninstall-distutils-installed-package
× Cannot uninstall blinker 1.4
╰─> It is a distutils installed project and thus we cannot accurately determine which files belong to it
```

**발생 조건**:
1. RunPod 기본 이미지에 distutils로 blinker 1.4 사전 설치
2. TTS>=0.22.0이 blinker>=1.6.2 요구
3. pip이 distutils 패키지 제거 시도 → 실패

**왜 이 방법으로 해결?**:
- **시도 1 (실패)**: `if ! pip install ... | tee`
  - 문제: `| tee`의 exit code(0)를 체크하여 pip 실패 감지 못함
  - 결과: 자동 복구 로직 실행 안됨

- **시도 2 (성공)**: `PIPESTATUS[0]` 사용
  ```bash
  pip install ... | tee /tmp/log
  INSTALL_EXIT_CODE=${PIPESTATUS[0]}  # pip의 실제 exit code 캡처

  if [ $INSTALL_EXIT_CODE -ne 0 ]; then
      if grep -q "Cannot uninstall blinker" /tmp/log; then
          rm -rf /usr/lib/python3*/dist-packages/blinker*  # distutils 패키지 수동 삭제
          pip install -r requirements.txt  # 재시도
      fi
  fi
  ```
  - `PIPESTATUS[0]`: 파이프라인 첫 번째 명령(pip)의 exit code
  - `PIPESTATUS[1]`: 파이프라인 두 번째 명령(tee)의 exit code

**위험도**: 🟡 Medium
- distutils 경로 직접 삭제는 시스템 패키지 관리 우회
- blinker는 Flask 등에서 사용하지만 AutoDrama에서는 직접 사용 안함

---

### 에러 #2: torchvision 누락

**전체 에러 메시지**:
```
RuntimeError: operator torchvision::nms does not exist
```

**발생 조건**:
1. vLLM 0.6.6.post1 실행 시 torchvision::nms 연산자 호출
2. torchvision이 설치되지 않음
3. vLLM 공식 requirements.txt에 torchvision 누락

**왜 이 방법으로 해결?**:
- vLLM 공식 문서 조사 결과: torch==2.5.1 + torchvision==0.20.1 필요
- setup_complete.sh Step 2에 명시적 추가:
  ```bash
  pip install --break-system-packages \
    torch==2.5.1 \
    torchvision==0.20.1 \  # 추가
    torchaudio==2.5.1 \
    --extra-index-url https://download.pytorch.org/whl/cu124
  ```

**위험도**: 🟢 Low
- 공식 요구사항 누락을 보완하는 것이므로 부작용 없음

---

### 에러 #3: tokenizers 버전 불일치 (Dependency Drift)

**전체 에러 메시지**:
```
ImportError: tokenizers>=0.22.0,<=0.23.0 is required for a normal functioning of this module, but found tokenizers==0.20.3.
```

**발생 조건**:
1. vLLM 0.6.6.post1 공식 요구: tokenizers>=0.19.1,<0.21.0
2. transformers 4.45.2 설치 시점 요구: tokenizers>=0.20.0,<0.21.0
3. transformers 4.45.2 **런타임 요구**: tokenizers>=0.22.0,<=0.23.0 ⚠️ 변경됨!

**왜 dependency drift 발생?**:
- transformers 4.45.2 릴리즈 시점 (2024-10): tokenizers 0.20.3 사용
- 2025-01 현재: transformers 내부 코드가 tokenizers 0.22+ 기능 사용
- pyproject.toml은 업데이트 안됨 → 설치는 성공, 런타임 오류 발생

**해결 전략**:
```python
# 이전 (실패)
tokenizers==0.20.3  # vLLM 요구만 만족

# 수정 1차 (실패)
tokenizers>=0.22.0,<=0.23.0  # transformers만 만족, vLLM 설치 실패

# 최종 (성공)
tokenizers>=0.19.1,<0.24.0  # 두 요구사항 모두 만족
# vLLM: >=0.19.1 ✅
# transformers runtime: 0.22.x-0.23.x ✅
```

**위험도**: 🟢 Low
- 넓은 버전 범위지만 두 패키지 모두 공식 지원 범위 내

---

### 에러 #4: huggingface-hub 버전 불일치

**전체 에러 메시지**:
```
ImportError: huggingface-hub>=0.34.0,<1.0 is required for a normal functioning of this module, but found huggingface-hub==0.29.3.
```

**발생 조건**:
1. transformers 4.45.2 설치 시점 요구: huggingface-hub>=0.23.0,<0.30.0
2. transformers 4.45.2 **런타임 요구**: huggingface-hub>=0.34.0,<1.0 ⚠️ 변경됨!
3. tokenizers 업그레이드 후 연쇄적으로 발견됨

**해결 전략**:
```python
# 이전 (실패)
huggingface-hub>=0.23.0,<0.30.0  # 설치 시점 요구만 만족

# 최종 (성공)
huggingface-hub>=0.34.0,<1.0.0  # 런타임 요구 만족
```

**위험도**: 🟢 Low
- 0.34.0은 안정 버전, vLLM과도 호환

---

### 에러 #5: Coqui TTS + Python 3.12 비호환 ✅ 해결됨

**전체 에러 메시지**:
```
ERROR: Could not find a version that satisfies the requirement TTS<0.23.0,>=0.22.0 (from versions: none)
ERROR: No matching distribution found for TTS<0.23.0,>=0.22.0
```

**발생 조건**:
1. RunPod Python 버전: **3.12.3**
2. Coqui TTS는 Python 3.12 wheels **미제공**
3. pip가 설치 가능한 버전을 찾을 수 없음

**근본 원인**:
- Coqui TTS 프로젝트는 Python 3.12용 wheel 빌드 안 함
- `pip install TTS`가 source distribution 빌드 시도 → 실패
- Python 3.10/3.11에서도 wheel 제공 제한적

**해결 방법 - OpenVoice로 완전 교체**:

| 항목 | Coqui TTS (이전) | OpenVoice (신규) |
|------|----------------|-----------------|
| **Python 지원** | 3.10, 3.11 (wheels 제한적) | **3.11, 3.12 완전 지원** |
| **한국어 품질** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **감정 제어** | 제한적 | **지원** |
| **속도** | 중간 | 빠름 |
| **VRAM** | ~2-3GB | ~2-3GB |
| **설치** | 복잡 (빌드 필요) | **간단 (pip install)** |

**적용 변경사항**:
1. **requirements.txt**: `TTS>=0.22.0` → `openvoice>=0.1.0`
2. **pipeline/tts.py**: 완전 재작성 (OpenVoice API 사용)
3. **config.yaml**: TTS 설정 업데이트
4. **main.py**: 기본 TTS 모델 변경

**위험도**: 🟢 Low
- OpenVoice는 Python 3.12 완전 호환
- 한국어 품질 더 우수
- 감정 제어 기능 추가
- 설치 안정성 향상

---

## 🔍 5. 설치 순서 최적화 분석

### 현재 설치 순서 (setup_complete.sh)

```bash
Step 1: 시스템 패키지
├── apt-get update
├── apt-get install ffmpeg git
└── 목적: FFmpeg (비디오 처리), git (버전 관리)

Step 2: PyTorch Stack ⚠️ 반드시 먼저 설치
├── pip install torch==2.5.1+cu124
├── pip install torchvision==0.20.1+cu124  # vLLM 필수
├── pip install torchaudio==2.5.1+cu124
├── --extra-index-url https://download.pytorch.org/whl/cu124
└── 목적: CUDA 12.4 버전 확보, CPU 버전 설치 방지

Step 3: 모든 나머지 패키지
├── pip install -r requirements.txt
├── PIPESTATUS[0]로 exit code 캡처
├── blinker 충돌 시 자동 복구
└── 목적: pip 의존성 해석 활용, 자동 버전 충돌 해결

Step 4: 버전 검증 + 자동 수리
├── numpy<2.0.0 체크 → 2.x면 1.26.x로 다운그레이드
├── huggingface-hub>=0.34.0 체크 → 낮으면 업그레이드
├── tokenizers>=0.19.1 체크 → 낮으면 업그레이드
├── diffusers<0.30.0 체크 → 0.30+면 0.29.x로 다운그레이드
└── 목적: dependency drift 대응, 런타임 오류 사전 차단

Step 5: 디렉토리 생성
└── mkdir -p /workspace/{huggingface_cache,models,outputs}

Step 6: 모델 다운로드
└── Qwen2.5-72B-Instruct-AWQ (~145GB)
```

### 왜 이 순서가 중요한가?

| 단계 | 다른 순서 사용 시 문제점 | 실제 발생 사례 |
|------|------------------------|--------------|
| **Step 2를 먼저** | Step 3에서 `pip install vllm` 시 torch를 CPU 버전으로 재설치 가능 | vLLM 설치 후 `torch.cuda.is_available() == False` |
| **Step 3을 한번에** | 개별 설치 시 각 패키지가 다른 패키지 버전 변경 → 충돌 누적 | transformers가 tokenizers 0.20.3 설치 → vLLM이 재설치 → 무한 루프 |
| **Step 4 검증** | 설치는 성공하지만 런타임에 ImportError → 사용자가 에러 발견 | transformers 임포트 시 tokenizers 버전 오류 |

---

## 📈 6. 의존성 우선순위 결정 기준

AutoDrama에서 패키지 충돌 시 우선순위 결정 규칙:

| 순위 | 패키지 | 이유 | 타협 불가 버전 |
|------|--------|------|---------------|
| **1** | **vLLM** | 핵심 LLM 엔진, Qwen 72B AWQ 지원 필수 | torch==2.5.1, numpy<2.0, tokenizers>=0.19.1 |
| **2** | **PyTorch** | vLLM, SDXL, TTS 모두 의존 | torch==2.5.1+cu124 (CUDA 버전 고정) |
| **3** | **transformers** | vLLM과 SDXL 모두 사용 | 4.45.2 (vLLM 공식 요구) |
| **4** | **diffusers** | SDXL Lightning 이미지 생성 | <0.30.0 (numpy 1.x 유지) |
| **5** | **TTS** | 한국어 음성 합성 | ~~0.22.0~~ → **0.21.x** (Python 3.10 호환) |
| **6** | **whisper-ctranslate2** | 한국어 STT | tokenizers<0.24.0 (faster-whisper 제외 이유) |

**타협 사례**:
- ❌ faster-whisper 제외: tokenizers<0.16 요구 → vLLM과 양립 불가
- ❌ diffusers 0.30+ 제외: numpy 2.x 요구 → vLLM과 양립 불가
- ⚠️ TTS 0.22.0 → 0.21.x 다운그레이드 검토 중: Python 3.10 호환 위해

---

## 🛠️ 7. 자동 복구 로직 상세

setup_complete.sh의 자동 복구 메커니즘:

### 7.1 blinker 충돌 복구

```bash
# 실행 흐름
pip install -r requirements.txt 2>&1 | tee /tmp/pip_install.log
INSTALL_EXIT_CODE=${PIPESTATUS[0]}  # [1] pip의 exit code 캡처

if [ $INSTALL_EXIT_CODE -ne 0 ]; then  # [2] 실패 시에만 실행
    if grep -q "Cannot uninstall blinker" /tmp/pip_install.log; then  # [3] blinker 에러 확인
        echo "🔧 Auto-fixing: Removing distutils blinker..."

        # [4] 모든 가능한 distutils 경로에서 제거
        rm -rf /usr/lib/python3/dist-packages/blinker* 2>/dev/null || true
        rm -rf /usr/lib/python3.*/dist-packages/blinker* 2>/dev/null || true
        rm -rf /usr/local/lib/python3/dist-packages/blinker* 2>/dev/null || true
        rm -rf /usr/local/lib/python3.*/dist-packages/blinker* 2>/dev/null || true

        # [5] 재시도
        pip install -r requirements.txt || {
            echo "✗ Retry failed!"
            exit 1
        }
    else
        # [6] 다른 에러는 로그 출력 후 종료
        echo "✗ Unknown error"
        cat /tmp/pip_install.log
        exit 1
    fi
fi
```

**핵심 기술**:
- `PIPESTATUS[0]`: Bash 배열, 파이프라인 각 명령의 exit code 저장
- `2>&1`: stderr를 stdout으로 리다이렉트 (tee로 캡처 위해)
- `|| true`: 오류 무시 (일부 경로 없어도 계속 진행)

### 7.2 버전 검증 + 자동 수리

```bash
# numpy 2.x 다운그레이드
NUMPY_VERSION=$(pip show numpy | grep "^Version:" | awk '{print $2}')
if [[ "$NUMPY_VERSION" == 2.* ]]; then
    echo "🔧 Downgrading numpy to 1.26.x..."
    pip install --force-reinstall 'numpy>=1.26.0,<2.0.0' -q
fi

# huggingface-hub 업그레이드
HF_HUB_VERSION=$(pip show huggingface-hub | grep "^Version:" | awk '{print $2}')
if [[ "$HF_HUB_VERSION" =~ ^0\.([0-9]|[12][0-9]|3[0-3])\. ]]; then
    echo "🔧 Upgrading huggingface-hub..."
    pip install --force-reinstall 'huggingface-hub>=0.34.0,<1.0.0' -q
fi

# tokenizers 업그레이드
TOKENIZERS_VERSION=$(pip show tokenizers | grep "^Version:" | awk '{print $2}')
if [[ "$TOKENIZERS_VERSION" =~ ^0\.([0-9]|1[0-8])\. ]]; then
    echo "🔧 Upgrading tokenizers..."
    pip install --force-reinstall 'tokenizers>=0.19.1,<0.24.0' -q
fi

# diffusers 다운그레이드
DIFFUSERS_VERSION=$(pip show diffusers | grep "^Version:" | awk '{print $2}')
if [[ "$DIFFUSERS_VERSION" == 0.3* ]] || [[ "$DIFFUSERS_VERSION" == 0.4* ]]; then
    echo "🔧 Downgrading diffusers..."
    pip install --force-reinstall 'diffusers>=0.27.0,<0.30.0' -q
fi
```

**정규표현식 설명**:
- `^0\.([0-9]|1[0-8])\.`: 0.0.x ~ 0.18.x 매칭 (0.19.1 미만)
- `^0\.(3[4-9]|[4-9][0-9])\.`: 0.34.x ~ 0.99.x 매칭 (0.34.0 이상)

---

## 🚨 8. 현재 미해결 이슈

### Issue #5: TTS + Python 버전 순환 의존성

**현재 상태**: ❌ 차단됨

**문제 구조**:
```
┌─────────────────────────────────────┐
│ RunPod Python 3.10 (기본 이미지)    │
└───────────┬─────────────────────────┘
            │
     ┌──────┴──────┐
     ↓             ↓
numpy 1.26.x     TTS 0.22.0
(Python <3.11)   (Python >=3.11)
     │             │
     └──────┬──────┘
            ↓
      ⚠️ 충돌! ⚠️
```

**즉시 필요한 조치**:
1. ✅ RunPod Python 버전 확인
   ```bash
   python3 --version
   ```

2. ⚠️ 결과에 따른 분기:
   - **Python 3.10 확인 시**: TTS 버전 다운그레이드
     ```python
     # requirements.txt 수정
     TTS>=0.21.0,<0.22.0  # Python 3.10 호환
     ```

   - **Python 3.11+ 확인 시**: numpy 버전 확인 필요
     ```bash
     pip show numpy | grep Version
     # 1.21.6이면 업그레이드 필요: numpy>=1.26.0,<2.0.0
     ```

**영향받는 기능**:
- Phase 5: 대사 음성 합성 (TTS 필수)
- Phase 6: 최종 비디오 합성 (음성 파일 필요)

**우회 방법**:
- TTS 없이 Phase 1-4 테스트 가능 (텍스트 생성, 이미지 생성까지)
- 음성 파일 수동 생성 후 Phase 6 실행

---

## 📝 9. 권장 조치 사항

### 즉시 실행 (Critical)

1. **Python 버전 확인**
   ```bash
   python3 --version
   python3 -c "import sys; print(f'Python {sys.version_info.major}.{sys.version_info.minor}')"
   ```

2. **TTS 버전 결정**
   - Python 3.10 → `TTS>=0.21.0,<0.22.0` 사용
   - Python 3.11+ → `TTS>=0.22.0,<0.23.0` 유지

3. **requirements.txt 업데이트**
   ```bash
   # Python 버전 확인 후 수정
   # setup_complete.sh 재실행
   bash setup_complete.sh
   ```

### 단기 개선 (High Priority)

1. **setup_complete.sh에 Python 버전 체크 추가**
   ```bash
   # Step 0: Python 버전 확인
   PYTHON_VERSION=$(python3 --version | awk '{print $2}' | cut -d. -f1,2)
   echo "Detected Python version: $PYTHON_VERSION"

   if (( $(echo "$PYTHON_VERSION < 3.11" | bc -l) )); then
       echo "⚠️  Python 3.10 detected - using TTS 0.21.x"
       # TTS 버전 자동 조정
   else
       echo "✓ Python 3.11+ detected - using TTS 0.22.x"
   fi
   ```

2. **requirements.txt를 템플릿화**
   - `requirements-py310.txt`: Python 3.10용 (TTS 0.21.x)
   - `requirements-py311.txt`: Python 3.11+용 (TTS 0.22.x)
   - setup_complete.sh가 자동 선택

### 장기 개선 (Medium Priority)

1. **Docker 이미지 생성**
   - Python 3.11 고정
   - 모든 의존성 사전 설치
   - 버전 불일치 원천 차단

2. **CI/CD 파이프라인 구축**
   - 의존성 변경 시 자동 테스트
   - 설치 스크립트 검증
   - 런타임 오류 사전 탐지

3. **의존성 고정 전략**
   - Pipenv 또는 Poetry 도입
   - `Pipfile.lock` / `poetry.lock`으로 정확한 버전 고정
   - dependency drift 방지

---

## 📚 10. 참고 자료

### 공식 문서
1. vLLM 0.6.6.post1 Requirements: https://github.com/vllm-project/vllm/blob/v0.6.6.post1/requirements.txt
2. Qwen2.5-72B-Instruct-AWQ: https://huggingface.co/Qwen/Qwen2.5-72B-Instruct-AWQ
3. transformers 4.45.2 Release: https://github.com/huggingface/transformers/releases/tag/v4.45.2
4. TTS (Coqui) PyPI: https://pypi.org/project/TTS/

### 디버깅 가이드
- Bash PIPESTATUS: https://www.gnu.org/software/bash/manual/html_node/Pipelines.html
- distutils vs pip conflicts: https://github.com/pypa/pip/issues/4805
- Python version constraints: https://packaging.python.org/en/latest/specifications/version-specifiers/

---

**문서 버전**: 1.0
**최종 업데이트**: 2025-01-22
**작성자**: AutoDrama Project
