# 🎬 작당모의 프로젝트 - 최종 워크플로우

---

## 📋 프로젝트 최종 스펙

**목표**: 제목 입력 → 2시간 한국 드라마 영상 자동 생성

**타겟**: 50~80대 한국 여성

**제작 시간**:

- RunPod 자동: 23분
- 로컬 수동: 6분
- 합계: 29분

**제작 비용**: $0.77/개 (RunPod만)

**Volume 유지**: $16/월 (모델 재다운 불필요)

---

## 🏗️ 인프라

### RunPod 환경

```
GPU: A100 80GB SXM ($2/시간)
Network Volume: 160GB ($16/월, 계속 유지)
OS: Ubuntu 24.04
Python: 3.11+
작업 경로: /workspace/

```

### Volume 내 모델 (한 번 다운, 계속 사용)

```
/workspace/huggingface_cache/
├─ meta-llama/Llama-3.1-70B-Instruct (140GB)
├─ black-forest-labs/FLUX.1-dev (12GB)
├─ CosyVoice-300M (3GB)
└─ faster-whisper-large-v3 (3GB)

총: 158GB

```

### 코드 저장 (Git)

```
GitHub: github.com/계정/작당모의

/workspace/작당모의/
├─ requirements.txt
├─ prompts/
│   ├─ outline.py
│   ├─ hook.py
│   ├─ part.py (통합)
│   ├─ hook_images.py
│   └─ main_images.py
├─ pipeline/
│   ├─ llm.py
│   ├─ image_gen.py
│   ├─ tts.py
│   ├─ subtitle.py
│   └─ video.py
└─ main.py

```

---

## 📂 대본 구조 (총 50,000자)

```
개요 (3,000자)
└─ 전체 스토리 청사진

훅 (500자):
└─ 클라이맥스 장면, 후킹

메인 (49,500자):
├─ Part 1 (12,500자) - 훅 직후 시작, 이야기의 시작
├─ Part 2 (12,500자) - 갈등 심화
├─ Part 3 (12,500자) - 클라이맥스, 진실 폭로
└─ Part 4 (12,000자) - 해소, 감동, 결말

```

---

## 🎨 이미지 구조 (총 20장)

```
훅: 5장
메인: 15장 (Part 1-4)

```

---

## 🔄 전체 워크플로우

```
[사용자 입력]
   ↓
제목 입력
   ↓
━━━━━━━━━━━━━━━━━━━━━━━━━━━
[RunPod 자동 파이프라인] 23분
━━━━━━━━━━━━━━━━━━━━━━━━━━━
   ├─ Phase 1: 개요 생성 (1.5분)
   ├─ Phase 2: 훅 생성 (2분)
   ├─ Phase 3: Part 1 생성 + 요약 (2.5분)
   ├─ Phase 4: Part 2 생성 + 요약 (2.5분)
   ├─ Phase 5: Part 3 생성 + 요약 (2.5분)
   ├─ Phase 6: Part 4 생성 (2.5분)
   ├─ Phase 7: 이미지 프롬프트 (1.5분)
   ├─ Phase 8: 이미지 생성 + Main TTS 병렬 (5분)
   ├─ Phase 9: 자막 생성 (1.5분)
   ├─ Phase 10: Main 영상 합성 (3분)
   └─ Phase 11: 백업 (0.1분)
   ↓
Google Drive 자동 백업
   ↓
━━━━━━━━━━━━━━━━━━━━━━━━━━━
[로컬 작업] 6분
━━━━━━━━━━━━━━━━━━━━━━━━━━━
   ├─ 다운로드 (1분)
   ├─ Vrew로 Hook 편집 (4분)
   └─ 최종 합성 (1분)
   ↓
hook_final.mp4
  +
구독영상.mp4 (별도 제작)
  +
main_video.mp4
  =
final_video.mp4 (120분)
   ↓
YouTube 업로드

```

---

## 🚀 RunPod 파이프라인 상세

---

### Phase 1: 개요 생성 (1.5분)

**목적**: 50,000자 스토리 청사진

**입력:**

- 제목

**프롬프트:** `prompts/outline.py`

**LLM 설정:**

```python
model = "meta-llama/Llama-3.1-70B-Instruct"
temperature = 0.7
max_tokens = 2000

```

**출력:**

```json
{
  "title": "제목",
  "characters": [...],
  "core_conflict": "...",
  "turning_points": [...],
  "climax": "...",
  "resolution": "...",
  "ending": "...",
  "theme": "...",
  "outline_full": "3,000자 개요"
}

```

**저장:**

```
/workspace/outputs/제목/outline.json

```

---

### Phase 2: 훅 생성 (2분)

**목적**: 클라이맥스 장면 500자

**입력:**

- 제목
- outline_full

**프롬프트:** `prompts/hook.py`

**LLM 설정:**

```python
temperature = 0.8
max_tokens = 1000

```

**출력:**

```
클라이맥스 장면 500자 순수 텍스트

```

**저장:**

```
/workspace/outputs/제목/hook/hook.txt (500자)

```

**중요:**

- ❌ TTS 생성 안 함
- ❌ 구독 멘트 안 넣음
- ❌ 영상 합성 안 함
- ✅ 순수 대본만

---

### Phase 3: Part 1 생성 + 요약 (2.5분)

**목적**: 메인 스토리 시작

**입력:**

- 제목
- outline_full
- (previous_parts 없음 → Part 1 자동 판단)

**프롬프트:** `prompts/part.py` (통합 프롬프트)

**동적 설정:**

```python
part_number = len(previous_parts) + 1  # 0 + 1 = 1
part_instruction = "Part 1을 작성하세요.\n\n전체의 시작~1/4 구간입니다.\n- 훅 직후 자연스럽게 시작\n- 이야기의 처음\n- 주요 인물 소개\n- 사건 발생\n- 갈등의 시작"
target_length = "12,000~13,000자"
climax_dialogue_rule = ""
ending_note = ""

```

**LLM 설정:**

```python
temperature = 0.7
max_tokens = 6000

```

**출력:**

```
Part 1 본문 (12,500자)

===SUMMARY===
Part 1 요약 (500자)

```

**파싱 및 저장:**

```python
parts = text.split("===SUMMARY===")
part1_text = parts[0].strip()
part1_summary = parts[1].strip()

save("part1.txt", part1_text)
save("part1_summary.txt", part1_summary)

```

**저장:**

```
/workspace/outputs/제목/main/part1.txt
/workspace/outputs/제목/main/part1_summary.txt

```

---

### Phase 4: Part 2 생성 + 요약 (2.5분)

**입력:**

- 제목
- outline_full
- previous_parts = [part1_summary]

**동적 설정:**

```python
part_number = 1 + 1 = 2
part_instruction = "Part 2를 작성하세요. 갈등 심화"
target_length = "12,000~13,000자"

```

**출력 및 저장:**

```
/workspace/outputs/제목/main/part2.txt
/workspace/outputs/제목/main/part2_summary.txt

```

---

### Phase 5: Part 3 생성 + 요약 (2.5분)

**입력:**

- previous_parts = [part1_summary, part2_summary]

**동적 설정:**

```python
part_number = 2 + 1 = 3
part_instruction = "Part 3를 작성하세요. 클라이맥스"
climax_dialogue_rule = "클라이맥스에서만 대사 25-30자 허용"

```

**출력 및 저장:**

```
/workspace/outputs/제목/main/part3.txt
/workspace/outputs/제목/main/part3_summary.txt

```

---

### Phase 6: Part 4 생성 (2.5분)

**입력:**

- previous_parts = [part1_summary, part2_summary, part3_summary]

**동적 설정:**

```python
part_number = 3 + 1 = 4
part_instruction = "Part 4를 작성하세요. 결말"
target_length = "11,500~12,500자"
ending_note = ""  # 구독 멘트 추가 안 함

```

**출력:**

```
Part 4 본문 (12,000자)
(요약 생성 안 함 - 마지막이므로)

```

**저장:**

```
/workspace/outputs/제목/main/part4.txt

```

**메인 전체 병합:**

```python
main_full = part1 + "\n\n" + part2 + "\n\n" + part3 + "\n\n" + part4
save("main_full.txt", main_full)
# 약 49,500자

```

---

### Phase 7: 이미지 프롬프트 생성 (1.5분)

---

### Phase 7-1: Hook 이미지 프롬프트 (0.7분)

**입력:**

- hook.txt (500자)

**프롬프트:** `prompts/hook_images.py`

**출력:**

```json
{
  "scenes": [
    {
      "index": 0,
      "part": "hook",
      "text_reference": "...",
      "timestamp": 0,
      "duration": 36,
      "description": "...",
      "mood": "tense",
      "prompt": "영어 FLUX 프롬프트"
    },
    ... 총 5개
  ],
  "total_scenes": 5
}

```

**저장:**

```
/workspace/outputs/제목/hook/image_prompts.json

```

---

### Phase 7-2: Main 이미지 프롬프트 (0.8분)

**입력:**

- part1_summary.txt
- part2_summary.txt
- part3_summary.txt
- part4.txt (마지막은 전체)

**프롬프트:** `prompts/main_images.py`

**출력:**

```json
{
  "scenes": [
    {
      "index": 0,
      "part": "part1",
      "position": "start",
      "timestamp": 0,
      "description": "...",
      "mood": "...",
      "prompt": "..."
    },
    ... 총 15개
  ],
  "total_scenes": 15
}

```

**저장:**

```
/workspace/outputs/제목/main/image_prompts.json

```

---

### Phase 8: 병렬 처리 - 이미지 생성 + Main TTS (5분)

**병렬 구조:**

```python
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=2) as executor:
    future_images = executor.submit(generate_all_images)  # 3분
    future_tts = executor.submit(generate_main_tts_only)  # 5분

    images = future_images.result()
    audio = future_tts.result()

# 전체 소요: 5분 (긴 쪽 기준)

```

---

### Thread 1: 이미지 생성 (3분)

**입력:**

- Hook 프롬프트 5개
- Main 프롬프트 15개
- 총 20개

**모델:**

```python
from diffusers import FluxPipeline
pipe = FluxPipeline.from_pretrained("black-forest-labs/FLUX.1-dev")

```

**배치 생성:**

```python
batch_size = 8
# 20개 → 3개 배치 (8, 8, 4)

배치 1: 30초
배치 2: 30초
배치 3: 20초
저장: 30초
─────────
합계: 110초 ≈ 2분

여유: 3분

```

**파일명 규칙:**

```
Hook:
00_hook_001.png
01_hook_002.png
02_hook_003.png
03_hook_004.png
04_hook_005.png

Main:
05_part1_001.png
06_part1_002.png
...
19_part4_003.png

```

**저장:**

```
/workspace/outputs/제목/hook/images/ (5장, 10MB)
/workspace/outputs/제목/main/images/ (15장, 30MB)

```

---

### Thread 2: Main TTS만 생성 (5분)

**중요:**

- ✅ Main (Part 1-4)만 TTS 생성
- ❌ Hook TTS 생성 안 함

**입력:**

- main_full.txt (49,500자)

**모델:**

```python
from cosyvoice.cli.cosyvoice import CosyVoice
cozy = CosyVoice('pretrained_models/CosyVoice-300M')

```

**문장 분리:**

```python
sentences = split_sentences(main_full)
# 49,500자 → 약 820개 문장

```

**배치 TTS:**

```python
batch_size = 10
# 820개 → 82개 배치

배치당 평균: 3.5초
82 배치 × 3.5초 = 287초 ≈ 5분

```

**오디오 병합:**

```python
final_audio = torch.cat(audio_segments, dim=-1)

```

**출력:**

```
파일: main_audio.mp3
길이: 6,840초 (114분)
크기: 145MB
샘플레이트: 22.05kHz

```

**저장:**

```
/workspace/outputs/제목/main/main_audio.mp3

```

---

### Phase 9: 자막 생성 (1.5분)

**목적**: Main 오디오 → 한국어 자막

**입력:**

- main_audio.mp3 (114분)

**모델:**

```python
from faster_whisper import WhisperModel
whisper = WhisperModel("large-v3", device="cuda")

```

**처리:**

```python
segments, info = whisper.transcribe(
    audio_path,
    language="ko",
    beam_size=5,
    word_timestamps=True,
    vad_filter=True
)

# 114분 오디오
# Whisper 속도: 실시간의 약 80배
# 114 / 80 = 1.4분 ≈ 1.5분

```

**SRT 생성:**

```python
def create_srt_file(segments, output_path):
    srt_content = []
    for seg in segments:
        srt_content.append(f"{seg['index']}")
        srt_content.append(f"{format_timestamp(seg['start'])} --> {format_timestamp(seg['end'])}")
        srt_content.append(seg['text'])
        srt_content.append("")

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(srt_content))

```

**출력:**

```
파일: main_subtitles.srt
크기: 80KB
구간: 약 1,250개
평균 길이: 5.5초/구간

```

**저장:**

```
/workspace/outputs/제목/main/main_subtitles.srt

```

---

### Phase 10: Main 영상 합성 (3분)

**목적**: Main만 영상 합성 (Hook 제외)

**입력:**

- main_audio.mp3 (114분, 145MB)
- main_subtitles.srt (1,250구간, 80KB)
- main/images/ (15장, 30MB)
- main/image_prompts.json

**중요:**

- ✅ Main (Part 1-4)만 합성
- ❌ Hook 합성 안 함
- ❌ 구독 멘트 추가 안 함

**이미지 타임라인 계산:**

```python
# Main 15개 이미지를 114분에 배치
# 각 이미지 약 7.6분씩 (114 / 15)

timeline = [
    {"image": "05_part1_001.png", "start": 0, "duration": 456},
    {"image": "06_part1_002.png", "start": 456, "duration": 456},
    ...
    {"image": "19_part4_003.png", "start": 6384, "duration": 456}
]

```

**FFmpeg 합성:**

```python
# 이미지 시퀀스 리스트
concat_file = "/tmp/images_concat.txt"

# FFmpeg 명령어
ffmpeg_cmd = [
    "ffmpeg", "-y",
    "-f", "concat", "-safe", "0", "-i", concat_file,  # 이미지 시퀀스
    "-i", audio_path,  # 오디오
    "-vf", f"subtitles={subtitle_path}:force_style='...'",  # 자막 오버레이
    "-c:v", "libx264", "-preset", "fast", "-crf", "23",
    "-c:a", "aac", "-b:a", "192k",
    "-r", "24", "-pix_fmt", "yuv420p",
    output_path
]

# 114분 인코딩
# 실시간의 약 38배 속도
# 114 / 38 = 3분

```

**출력:**

```
파일: main_video.mp4
크기: 1.87GB
길이: 114분
해상도: 1280×720 (HD)
프레임레이트: 24fps
비디오: H.264
오디오: AAC 192kbps
자막: 하드코딩 포함

```

**저장:**

```
/workspace/outputs/제목/main/main_video.mp4

```

---

### Phase 11: 백업 및 정리 (0.1분)

**메타데이터 생성:**

```json
{
  "title": "제목",
  "created_at": "2024-11-16T14:23:05",
  "completed_at": "2024-11-16T14:46:05",
  "duration_minutes": 23,
  "status": "completed",
  "script": {
    "outline": 3124,
    "hook": 500,
    "part1": 12500,
    "part2": 12500,
    "part3": 12500,
    "part4": 12000,
    "total": 50000
  },
  "images": {
    "hook": 5,
    "main": 15,
    "total": 20
  },
  "audio": {
    "main_duration_seconds": 6840,
    "file_size_mb": 145
  },
  "video": {
    "main_duration_seconds": 6840,
    "resolution": "1280x720",
    "file_size_gb": 1.87
  },
  "subtitles": {
    "segments": 1250,
    "accuracy": "99.9%"
  }
}

```

**Google Drive 백업:**

```python
rclone sync /workspace/outputs/제목 gdrive:작당모의/outputs/제목
# 비동기 실행

```

**최종 출력 파일 구조:**

```
/workspace/outputs/제목/
├─ outline.json
├─ metadata.json
├─ hook/
│   ├─ hook.txt (500자)
│   ├─ image_prompts.json
│   └─ images/ (5장)
│       ├─ 00_hook_001.png
│       ├─ 01_hook_002.png
│       ├─ 02_hook_003.png
│       ├─ 03_hook_004.png
│       └─ 04_hook_005.png
└─ main/
    ├─ part1.txt
    ├─ part1_summary.txt
    ├─ part2.txt
    ├─ part2_summary.txt
    ├─ part3.txt
    ├─ part3_summary.txt
    ├─ part4.txt
    ├─ main_full.txt (49,500자)
    ├─ main_audio.mp3 (145MB, 114분)
    ├─ main_subtitles.srt (80KB, 1,250구간)
    ├─ main_video.mp4 (1.87GB, 114분) ⭐
    ├─ image_prompts.json
    └─ images/ (15장)
        ├─ 05_part1_001.png
        ├─ 06_part1_002.png
        └─ ... 19_part4_003.png

```

---

## 📥 로컬 작업 (6분)

### 1. 다운로드 (1분)

**Google Drive에서:**

```
다운로드:
├─ hook/hook.txt (500자)
├─ hook/images/ (5장, 10MB)
└─ main/main_video.mp4 (1.87GB)

총: 1.88GB
속도: 30MB/s
시간: 63초 ≈ 1분

```

---

### 2. Vrew로 Hook 편집 (4분)

**작업:**

```
1. Vrew 열기
2. hook.txt 붙여넣기
3. Vrew TTS 생성 (내장)
4. 이미지 5장 타임라인 배치
5. 자막 자동 생성
6. 내보내기 → hook_final.mp4

```

**출력:**

```
hook_final.mp4
- 길이: 약 3-6분 (편집에 따라)
- 크기: 약 50MB

```

**소요:** 4분

---

### 3. 최종 합성 (1분)

**FFmpeg 합성:**

```bash
ffmpeg -i hook_final.mp4 -i 구독영상.mp4 -i main_video.mp4 \
       -filter_complex "[0:v][0:a][1:v][1:a][2:v][2:a]concat=n=3:v=1:a=1" \
       final_video.mp4

```

**구조:**

```
hook_final.mp4 (Vrew 편집, 3-6분)
  +
구독영상.mp4 (너가 만든 것, 약 10초)
  +
main_video.mp4 (RunPod 자동, 114분)
  =
final_video.mp4 (약 120분)

```

**출력:**

```
final_video.mp4
- 길이: 약 120분
- 크기: 약 2GB

```

**소요:** 1분

---

## 📊 최종 정리

### 시간

```
RunPod 자동: 23분
━━━━━━━━━━━━━━━━━━━━━━━
Phase 1: 개요 (1.5분)
Phase 2: 훅 (2분)
Phase 3-6: Part 1-4 (10분)
Phase 7: 이미지 프롬프트 (1.5분)
Phase 8: 이미지 + Main TTS 병렬 (5분)
Phase 9: 자막 (1.5분)
Phase 10: Main 영상 (3분)
Phase 11: 백업 (0.1분)

로컬 수동: 6분
━━━━━━━━━━━━━━━━━━━━━━━
다운로드 (1분)
Vrew Hook 편집 (4분)
최종 합성 (1분)

━━━━━━━━━━━━━━━━━━━━━━━
전체: 29분
━━━━━━━━━━━━━━━━━━━━━━━

```

### 비용

```
RunPod: 23분 / 60 × $2 = $0.77
Google Drive: $16/월 (고정)
━━━━━━━━━━━━━━━━━━━━━━━
영상당: $0.77
월 고정: $16
━━━━━━━━━━━━━━━━━━━━━━━

```

### 프롬프트

```
1. outline.py
2. hook.py
3. part.py (통합 - Part 1,2,3,4 자동 판단)
4. hook_images.py
5. main_images.py

총 5개

```

---

**끝.**