# 작당모의 프로젝트

제목 입력 → 2시간 한국 드라마 영상 자동 생성

## 프로젝트 개요

50~80대 한국 여성을 타겟으로 하는 유튜브 오디오 드라마를 자동으로 생성하는 AI 파이프라인입니다.

- **입력**: 드라마 제목
- **출력**: 2시간 분량 완성 영상 (MP4)
- **소요 시간**: 약 23분 (RunPod A100 80GB 기준)
- **비용**: $0.77/편

## 주요 기능

- 📝 **자동 대본 생성**: Llama 3.1 70B를 사용한 50,000자 대본 생성
- 🎨 **이미지 생성**: FLUX.1-dev를 사용한 고품질 드라마 이미지 (20장)
- 🎤 **음성 합성**: Coqui TTS (VITS)를 사용한 자연스러운 한국어 음성 생성
- 📝 **자막 생성**: Faster-Whisper를 사용한 정확한 자막
- 🎬 **영상 합성**: FFmpeg을 사용한 전문가급 비디오 편집

## 시스템 요구사항

### RunPod 환경
- GPU: A100 80GB SXM ($2/시간)
- Network Volume: 160GB ($16/월)
- OS: Ubuntu 24.04
- Python: 3.11+

### 로컬 환경
- Python 3.11 이상
- CUDA 지원 GPU (권장)
- 충분한 디스크 공간 (모델 캐시 160GB + 출력 파일)

## 설치

1. **저장소 클론**
```bash
git clone https://github.com/계정/작당모의.git
cd 작당모의
```

2. **가상환경 생성 및 활성화**
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

3. **의존성 설치**
```bash
pip install -r requirements.txt
```

4. **설정 파일 수정**
`config.yaml` 파일을 열어 환경에 맞게 수정합니다:
- 모델 경로
- 출력 디렉토리
- GPU 설정 등

## 사용 방법

### 기본 실행

```bash
python main.py
```

제목을 입력하면 자동으로 파이프라인이 실행됩니다.

### 출력 구조

```
/workspace/outputs/제목/
├── outline.json              # 전체 개요
├── metadata.json             # 메타데이터
├── hook/
│   ├── hook.txt              # 훅 대본 (500자)
│   ├── image_prompts.json    # 이미지 프롬프트
│   └── images/               # 5장
└── main/
    ├── part1.txt             # Part 1 대본
    ├── part1_summary.txt     # Part 1 요약
    ├── part2.txt             # Part 2 대본
    ├── part2_summary.txt     # Part 2 요약
    ├── part3.txt             # Part 3 대본
    ├── part3_summary.txt     # Part 3 요약
    ├── part4.txt             # Part 4 대본
    ├── main_full.txt         # 전체 대본 (49,500자)
    ├── main_audio.mp3        # 114분 오디오
    ├── main_subtitles.srt    # 자막
    ├── main_video.mp4        # 최종 영상 (1.87GB)
    ├── image_prompts.json    # 이미지 프롬프트
    └── images/               # 15장
```

## 파이프라인 단계

1. **Phase 1**: Outline 생성 (1.5분)
2. **Phase 2**: Hook 생성 (2분)
3. **Phase 3-6**: Part 1-4 생성 (10분)
4. **Phase 7**: 이미지 프롬프트 생성 (1.5분)
5. **Phase 8**: 이미지 생성 + Main TTS 병렬 처리 (5분)
6. **Phase 9**: 자막 생성 (1.5분)
7. **Phase 10**: Main 영상 합성 (3분)
8. **Phase 11**: 백업 및 정리 (0.1분)

**총 소요 시간**: 약 23분

## 프로젝트 구조

```
작당모의/
├── requirements.txt          # Python 패키지 의존성
├── config.yaml               # 설정 파일
├── main.py                   # 메인 실행 파일
├── prompts/                  # 프롬프트 모듈
│   ├── outline.py            # 개요 생성
│   ├── hook.py               # 훅 생성
│   ├── part.py               # Part 1-4 생성
│   ├── hook_images.py        # Hook 이미지 프롬프트
│   └── main_images.py        # Main 이미지 프롬프트
├── pipeline/                 # 파이프라인 모듈
│   ├── llm.py                # LLM 호출
│   ├── image_gen.py          # 이미지 생성
│   ├── tts.py                # TTS 생성
│   ├── subtitle.py           # 자막 생성
│   └── video.py              # 비디오 합성
└── utils/                    # 유틸리티 모듈
    ├── file_utils.py         # 파일 입출력
    └── logger.py             # 로깅
```

## 개발 상태

현재 이 프로젝트는 **보일러플레이트 단계**입니다.

### 완료된 항목
- ✅ 프로젝트 구조
- ✅ 프롬프트 모듈 (5개)
- ✅ 유틸리티 함수
- ✅ 메인 파이프라인 골격

### 구현 필요 항목
- ⏳ LLM 호출 (`pipeline/llm.py`)
- ⏳ 이미지 생성 (`pipeline/image_gen.py`)
- ⏳ TTS 생성 (`pipeline/tts.py`)
- ⏳ 자막 생성 (`pipeline/subtitle.py`)
- ⏳ 비디오 합성 (`pipeline/video.py`)

각 파일에는 상세한 TODO 주석과 구현 예시가 포함되어 있습니다.

## 라이선스

MIT License

## 참고 문서

- `workflow.md`: 전체 워크플로우 상세 설명
- `prompt.md`: 5개 프롬프트 전문

## 기여

이슈와 PR을 환영합니다!
