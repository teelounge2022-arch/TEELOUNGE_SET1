# 티라운지 — 달에 남은 골프공

완성본은 `output/teelounge_moon_golf_1080x1920.mp4`입니다. 34초, 1080×1920, 30fps의 세로형 2.5D 일러스트 모션그래픽입니다.

## 이야기

1971년 아폴로 14호의 앨런 셰퍼드가 달에서 골프공 두 개를 친 실제 기록을 소재로 삼았습니다. 도구와 한 손 스윙은 일러스트로 재구성했으며, 비거리나 실제 인물의 대사는 만들어 넣지 않았습니다. 달 중력 비교는 비거리 배율을 뜻하지 않습니다.

## 포함 파일

- `output/teelounge_moon_golf_1080x1920.mp4`: H.264 / AAC, 1080×1920, 30fps, 34초
- `output/poster.png`: 첫 장면 포스터
- `script_ko.md`: 한국어 대본과 사실 범위·참조 링크
- `storyboard.json`: 7장면 편집 구성 및 타이밍
- `narration_ko.srt`: 내레이션 녹음용 문장별 편집 가이드
- `audio/music_sfx.wav`: 직접 합성한 배경음악·전환음·골프 타격음, 48kHz 스테레오
- `scripts/illustrations.py`: 투명 레이어 일러스트 원본 생성
- `scripts/make_video.py`: 시차·캐릭터 포즈·도구·공·자막 애니메이션과 영상 인코딩
- `scripts/audio_bed.py`: 음악·효과음 재현 스크립트
- `metadata/`: 실제 빌드·음량·영상 검수·스킬 설치 정보

이번 완성본은 **자막·음악·효과음 버전**이며 녹음된 음성 내레이션은 포함하지 않습니다. 내레이션 대본과 문장별 가이드를 별도로 제공합니다. SRT의 타이밍은 녹음에 맞춘 단어 정렬 결과가 아닙니다.

## 제작 방식과 검수

원본 벡터·음영 일러스트를 전경·인물·도구·지형·원경으로 분리하고, 서로 다른 속도의 시차와 확대·회전·스윙 동작을 합성했습니다. Pillow와 FFmpeg로 렌더했으며 이 영상의 제작 중 Blender 런타임은 실행하지 않았습니다. 앞선 정지 세트 작업의 미승인 대체 런타임을 사용하지 않았습니다.

완성 MP4에서 주요 장면을 직접 추출해 자막·오브젝트 잘림, 빈 화면, 가독성을 확인했습니다. 전체 영상의 디코딩, 해상도·프레임 수·길이, 음원 클리핑과 음량도 검사합니다. 실제 결과는 `metadata/quality_report.json`에 기록합니다. 음악과 일러스트는 절차적으로 새로 제작했으며 기존 영상·타인의 음원을 가져오지 않았습니다.

공유된 Google Drive HOOK 폴더는 이 클라우드의 목적지 네트워크 정책 때문에 HTTPS CONNECT 단계에서 403으로 차단됐습니다. 따라서 ZIP 내부 작업지시서·기존 대본·사운드를 열거나 참고했다고 주장하지 않습니다. 현재 영상은 제공된 주제 방향에 맞춰 독립적으로 제작한 파일럿입니다. Drive 업로드는 수행하지 않았습니다.

## 재생성

Python 3, Pillow 12.3.0, NumPy 2.3.5, SciPy 1.17.0, FFmpeg 및 Noto Sans CJK 폰트가 필요합니다. 별도의 온라인 서비스는 사용하지 않습니다.

```bash
cd /workspace/TEELOUNGE_SET1
python3 25d-pilot/video/scripts/audio_bed.py
python3 25d-pilot/video/scripts/make_video.py
```

특정 시점의 이미지만 확인하려면 `--preview-frame 16.4`를 사용합니다. 중간 검수 이미지는 `review/`, 진행 로그는 `logs/`에 저장되며 Git에 포함하지 않습니다.

## Blender Skills 설치

별도 요청한 `EL4CTEO/blender-skills`의 22개 스킬을 이 클라우드의 Codex 사용자 경로와 `/workspace/.agents/skills`에 설치했습니다. 소스 커밋은 `71d031dab8bc6729504d11a78cbe91945401045f`이며 저장소 검증 도구가 `OK`를 반환했습니다. 이 묶음은 Blender 5.2 LTS 이상 기준이고, 설치 과정에서 Blender 실행 파일은 변경하지 않았습니다.
