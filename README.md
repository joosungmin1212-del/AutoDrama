# AutoDrama - 자동 드라마 생성 시스템

제목만 입력하면 2시간 분량 한국 드라마 영상을 자동으로 생성합니다.

## 프로젝트 개요

50~80대 한국 여성을 타겟으로 하는 유튜브 오디오 드라마를 자동으로 생성하는 AI 파이프라인입니다.

- **입력**: 드라마 제목 (예: "할머니의 비밀 일기장")
- **출력**: 2시간 분량 완성 영상 (MP4)
- **소요 시간**: 약 11-13분 (GPU 환경)
- **비용**: $0.77/편 (RunPod 기준)

## 주요 기능

- 📝 **자동 대본 생성**: Qwen 2.5 72B AWQ를 사용한 고품질 한국어 드라마 대본
- 🎨 **이미지 생성**: SDXL Lightning을 사용한 빠른 이미지 생성 (4 steps)
- 🎤 **음성 합성**: Coqui TTS를 사용한 자연스러운 한국어 음성
- 📝 **자막 생성**: Whisper large-v3를 사용한 정확한 자막
- 🎬 **영상 합성**: FFmpeg을 사용한 전문가급 비디오 편집

## 기술 스택

### LLM
- **모델**: Qwen/Qwen2.5-72B-Instruct-AWQ
- **프레임워크**: vLLM 0.6.6.post1
- **최적화**: 72B 전용 파라미터 튜닝 (temperature, top_p, top_k, repetition_penalty)

### 이미지 생성
- **모델**: ByteDance/SDXL-Lightning
- **설정**: 4 inference steps, guidance_scale 0.0
- **최적화**: xFormers memory efficient attention

### TTS
- **모델**: Coqui TTS (tts_models/ko/cv/vits)
- **언어**: 한국어 전용
- **특징**: 자연스러운 음성 합성

### STT
- **모델**: Whisper large-v3 (whisper-ctranslate2)
- **언어**: 한국어

## 시스템 요구사항

### GPU 환경 (필수)
- **GPU**: NVIDIA 40GB+ (A100, H100 권장)
- **VRAM**: 최소 40GB
  - vLLM (Qwen 72B AWQ): ~18-20GB
  - SDXL Lightning: ~6-8GB
  - Coqui TTS: ~2-3GB
  - Whisper: ~3-4GB
- **CUDA**: 12.4+
- **Python**: 3.10 or 3.11 (Coqui TTS requires Python ≤3.11)

### 로컬 환경
- **시스템 RAM**: 64GB+ 권장
- **디스크 공간**: 200GB+
  - 모델 캐시: ~160GB
  - 출력 파일: 영상당 ~2GB

## 설치

### 1. 저장소 클론
```bash
git clone https://github.com/joosungmin1212-del/AutoDrama.git
cd AutoDrama
```

### 2. 의존성 설치 (GPU 환경)
```bash
# 전체 설정 자동화 스크립트 (RunPod/Lambda Labs 등)
bash setup_complete.sh
```

또는 수동 설치:
```bash
pip install -r requirements.txt
```

### 3. 설정 파일 확인
`config.yaml` 파일에서 경로 확인:
- 모델 캐시 디렉토리
- 출력 디렉토리
- LLM/이미지/TTS 파라미터

## 사용 방법

### 기본 실행
```bash
python main.py
```

제목 입력 프롬프트가 나오면 원하는 드라마 제목을 입력하세요.

예:
```
제목을 입력하세요: 할머니의 비밀 일기장
```

### 테스트 실행
```bash
# Outline만 테스트
python test_outline.py "할머니의 비밀 일기장"

# Part 생성 테스트
python test_part_v3.py "할머니의 비밀 일기장"
```

## 파이프라인 단계

| Phase | 작업 | 소요 시간 |
|-------|------|----------|
| 1 | Outline 생성 + 검증 | 1.0분 |
| 2 | Hook 생성 | 0.3분 |
| 3 | Hook 이미지 프롬프트 | 0.5분 |
| 4 | Hook 이미지 생성 | 0.8분 |
| 5 | Parts 1-4 생성 (순차 + Context) | 2.5분 |
| 6 | Main 이미지 프롬프트 | 0.6분 |
| 7 | Main 이미지 생성 | 2.0분 |
| 8 | TTS 생성 (병렬) | 1.5분 |
| 9 | Subtitle 생성 (병렬) | 1.5분 |
| 10 | Video 합성 (병렬) | 1.0분 |

**총 소요 시간**: 약 11-13분

## 출력 구조

```
output/제목/
├── outline.json              # 전체 개요 (검증됨)
├── metadata.json             # 메타데이터
├── hook/
│   ├── hook.txt              # 훅 대본
│   ├── hook_audio.wav        # 훅 음성
│   ├── hook_subtitles.srt    # 훅 자막
│   ├── hook_video.mp4        # 훅 영상
│   ├── image_prompts.json    # 이미지 프롬프트
│   └── images/               # 5장
└── main/
    ├── part1.txt             # Part 1 대본
    ├── part1_context.json    # Part 1 Context (Part 2 전달용)
    ├── part2.txt             # Part 2 대본
    ├── part2_context.json    # Part 2 Context
    ├── part3.txt             # Part 3 대본
    ├── part3_context.json    # Part 3 Context
    ├── part4.txt             # Part 4 대본
    ├── main_full.txt         # 전체 대본 병합
    ├── main_audio.wav        # 메인 음성 (2시간)
    ├── main_subtitles.srt    # 메인 자막
    ├── main_video.mp4        # 최종 영상 (~2GB)
    ├── image_prompts.json    # 이미지 프롬프트
    └── images/               # 15장
```

## 프로젝트 구조

```
AutoDrama/
├── main.py                   # 메인 파이프라인 (Phase 1-10)
├── config.yaml               # 설정 파일
├── requirements.txt          # Python 의존성
├── setup_complete.sh         # 전체 설치 스크립트
├── test_outline.py           # Outline 테스트
├── test_part_v3.py           # Part 테스트
│
├── prompts/                  # 프롬프트 모듈
│   ├── outline_v2_final.py   # Outline 생성 + 검증
│   ├── part_v3.py            # Part 생성 + 검증
│   ├── hook.py               # Hook 생성
│   ├── hook_images.py        # Hook 이미지 프롬프트
│   └── main_images.py        # Main 이미지 프롬프트
│
├── pipeline/                 # 파이프라인 모듈
│   ├── llm.py                # LLM 엔진 (vLLM + 72B 최적화)
│   ├── image.py              # 이미지 생성 (SDXL Lightning)
│   ├── tts.py                # TTS 생성 (Coqui TTS)
│   ├── subtitle.py           # 자막 생성 (Whisper)
│   └── video.py              # 비디오 합성 (FFmpeg)
│
└── utils/                    # 유틸리티 모듈
    ├── context_generator.py  # Context 생성 + 안전화
    ├── file_utils.py         # 파일 I/O
    └── logger.py             # 로깅
```

## 안정화 기능 (Stabilization)

### 1. JSON 파싱 안정화
- `extract_first_json()`: 중괄호 depth 추적으로 첫 번째 완전한 JSON만 추출
- `clean_json_string()`: UTF-8 BOM, null, None, N/A 자동 제거
- 최대 3회 재시도 (2초 exponential backoff)

### 2. 중국어 오염 방지
- `detect_chinese()`: Unicode \u4e00-\u9fff 범위 감지
- 임계값 5자 이상 시 자동 재시도
- 예상 효과: 중국어 오염 10% → 1% 이하

### 3. Validation 로직
- `validate_outline()`: 7개 필드 검증 + 자동 보정
- `validate_part_text()`: 대사 비율, 중국어, 반복률, 길이 체크
- `sanitize_context()`: Context 필드 안전화 (최대 5개 제한)

### 4. 품질 검증
- 대사 비율 15% 초과 시 경고
- 반복률 10% 초과 시 경고
- 영어 단어 과다 사용 체크
- 실시간 로깅으로 문제 조기 발견

### 5. 72B 최적화 파라미터
```yaml
outline:
  temperature: 0.65
  max_tokens: 7000
  top_p: 0.92
  top_k: 40
  repetition_penalty: 1.13

parts:
  temperature: 0.70
  max_tokens: 5000
  top_p: 0.92
  top_k: 40
  repetition_penalty: 1.13
```

## 개발 상태

### ✅ 완료된 항목
- ✅ 전체 파이프라인 구조
- ✅ Outline 생성 + 검증 (outline_v2_final.py)
- ✅ Part 생성 + 검증 (part_v3.py)
- ✅ Context 생성 + 안전화 (context_generator.py)
- ✅ LLM 엔진 (72B 최적화 + 재시도 로직)
- ✅ 이미지 생성 (SDXL Lightning)
- ✅ TTS 생성 (Coqui)
- ✅ 자막 생성 (Whisper)
- ✅ 비디오 합성 (FFmpeg)
- ✅ 코드 레벨 검증 (100% 통과)

### 📊 예상 성능
- JSON 파싱 실패율: 30% → **5% 이하**
- 중국어 오염: 10% → **1% 이하**
- KeyError 발생: 빈번 → **0건**
- 파이프라인 완료율: 70% → **95%+**

## 라이선스

MIT License

## 기여

이슈와 PR을 환영합니다!

GitHub: https://github.com/joosungmin1212-del/AutoDrama

## 참고 문서

- [STABILIZATION_CHANGES.md](STABILIZATION_CHANGES.md) - 안정화 변경 사항 상세
- [INTEGRATION_SUMMARY.md](INTEGRATION_SUMMARY.md) - 통합 요약
- [test_logs/TEST_REPORT.md](test_logs/TEST_REPORT.md) - 코드 검증 보고서
