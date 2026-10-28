# 2.5D 숏츠 파일럿: 인물 없는 3D 세트

## 현재 상태

**세트 생성 스크립트와 렌더 파이프라인을 작성했습니다. 최종 이미지 제작은 아직 완료되지 않았습니다.**

요청한 공식 Blender 4.2 LTS 독립 실행 파일의 배포 경로는 이 실행 환경에서 차단됩니다.

- 실제 조회 URL: `https://download.blender.org/release/Blender4.2/`
- 실제 오류: `URLError: <urlopen error Tunnel connection failed: 403 Forbidden>`
- 오류 위치: 상속된 환경 프록시의 HTTPS CONNECT 단계. Blender 원본 서버의 HTTP 응답은 받지 못했습니다.
- 설치된 독립 실행 파일: Blender 4.3.2. 최종 산출물 렌더에 사용하지 않았습니다. 해당 빌드에서는 OIDN 설정 시 `enum "OPENIMAGEDENOISE" not found in ()` 오류도 확인했습니다.
- 별도 확보했던 공식 PyPI `bpy` 4.2.23 LTS는 백그라운드 모드와 OIDN을 지원합니다. 이를 사용한 S1 저해상도 시안 2장과 S1/S2 `.blend` 초안이 로컬에 있습니다. 실행 경로 대체 승인이 확인되지 않아 **이 경로의 실행과 렌더는 중단했습니다.**
- S2 첫 시안 렌더 도중 프로세스를 종료했습니다. 최종 PNG 8장과 룩시트 4장은 생성하지 않았습니다.
- `metadata/runtime_provenance.json`은 이미 실행된 대체 런타임의 이력이며, 요청한 독립 실행 파일 경로를 완료했다는 의미가 아닙니다.

초안 `.blend`와 무시된 `previews/`는 보존하되 검수 완료 산출물로 취급하지 않습니다. `metadata/validation.json`은 실제 존재하는 파일과 누락 항목을 구분합니다.

## 세트 설계

| 세트 | 생성 스크립트 | 구성 |
| --- | --- | --- |
| S1 | `scripts/scene_s1.py` | 회색 레골리스, 기하학적 발자국, 일반형 착륙선, 검은 하늘과 절차적 지구, 낮은 태양 |
| S2 | `scripts/scene_s2.py` | 1971년형 청록색 콘솔 12개, 빈 CRT, 아날로그 계기·스위치·전화·빈 의자, 중앙 통로 |
| S3 | `scripts/scene_s3.py` | 홈이 있는 아이언 헤드, 호젤, 긴 금속 샤프트, 달 먼지, 낮은 카메라 |
| S4 | `scripts/scene_s4.py` | 실제 크기 골프공 2개, 공마다 기하학적 딤플 360개, 발자국과 작은 돌 |

사람, 얼굴, 로고, 문구, 국기 또는 식별 가능한 임무 표식을 만들지 않습니다. 텍스처·지구·재질·마모·지형은 모두 절차적으로 생성하며 외부 이미지가 필요하지 않습니다. 각 세트는 최종 카메라 A/B와 룩시트용 추가 시점 C/D를 정의합니다. 하단 중앙을 합성용으로 비우도록 설계했으며, 최종 이미지를 실제 열어 확인해야 합니다.

## 요청된 공식 실행 경로

공식 호스트 접근이 정상 허용되는 실행 환경에서 다음을 실행합니다. 다운로드 스크립트는 공식 HTTPS 배포와 공식 SHA256 목록만 사용합니다. 실패하면 다른 경로로 자동 전환하지 않습니다. 현재 환경에서는 다운로드의 성공을 검증하지 못했습니다.

```bash
cd /workspace/TEELOUNGE_SET1
bash 25d-pilot/scripts/download_blender.sh 4.2.23
```

이후 `/workspace/.tools/blender-official/blender-4.2.23-linux-x64/blender`를 사용합니다. 아래는 **승인된 독립 실행 파일이 준비된 뒤 실행할 명령**이며 현재 완료 기록이 아닙니다.

```bash
# 저해상도 시안: 구도와 지형, 조명 확인용. 최종 산출물이 아님.
/workspace/.tools/blender-official/blender-4.2.23-linux-x64/blender \
  -b --python-exit-code 1 --python 25d-pilot/scripts/render.py -- \
  --scene ALL --mode preview --threads 4

# 최종 스틸 8장: Cycles CPU, 64 샘플 상한, OpenImageDenoise.
/workspace/.tools/blender-official/blender-4.2.23-linux-x64/blender \
  -b --python-exit-code 1 --python 25d-pilot/scripts/render.py -- \
  --scene ALL --mode final --threads 4 --skip-existing

# 실제 4개 시점의 룩시트 원본: 각 540×960, 64 샘플 상한.
/workspace/.tools/blender-official/blender-4.2.23-linux-x64/blender \
  -b --python-exit-code 1 --python 25d-pilot/scripts/render.py -- \
  --scene ALL --mode look --threads 4 --skip-existing

python3 25d-pilot/scripts/compose_looksheets.py
python3 25d-pilot/scripts/validate_outputs.py
```

`--python-exit-code 1`은 Blender가 Python 예외를 성공 종료로 보고하는 일을 방지합니다. `--skip-existing`은 소스 지문, 런타임 버전, 이미지 크기·비트 수·SHA256과 완료 기록이 모두 일치할 때만 기존 이미지를 재사용합니다. 수정한 카메라만 다시 렌더하려면 `--scene S3 --mode final --camera A`처럼 지정합니다.

렌더 파이프라인은 최종 설정을 가진 `.blend`를 압축 저장합니다. 라이브 프로세스와 렌더 중간 상태를 최종 산출물로 취급하지 않습니다. 최종 카메라 A/B를 각각 출력하고 C/D는 별도 검수 시점으로 저장합니다.

## 최종 산출물 명명 규칙

아래는 **완료 목표 목록**입니다. 존재와 완료 여부는 검증 JSON을 확인해야 합니다.

- `renders/S1_camera_A.png`, `S1_camera_B.png` … `S4_camera_A.png`, `S4_camera_B.png`: 총 8장, 2160×3840, RGB 16비트 PNG
- `scenes/S1.blend` … `S4.blend`: 총 4개, 절차적으로 생성된 편집 가능한 장면
- `lookviews/S1_angle_01.png` … `S4_angle_04.png`: 총 16장, 실제 카메라별 룩시트 소스
- `looksheets/S1_looksheet.png` … `S4_looksheet.png`: 총 4장, 1080×1920, 2×2 무문구 룩시트
- `metadata/`: 실제 렌더 설정·소스 지문·시간·해시·검수 기록
- `scripts/`: 세트 생성, 공식 다운로드, 렌더, 룩시트 합성, 산출물 검증

룩시트의 시점 순서는 왼쪽 위 A, 오른쪽 위 B, 왼쪽 아래 C, 오른쪽 아래 D입니다. 이미지 안에는 제목·번호·라벨을 합성하지 않습니다.

## 최종 검수 절차

1. 공식 4.2 런타임·CPU·OIDN 지원을 확인하고 모든 시안을 렌더합니다.
2. 8개 카메라 이미지를 직접 열어 빈 화면·누락 물체·클리핑·떠 있는 소품·노이즈·합성 공간과 초점을 확인합니다. S1의 지구, S3의 아이언 형상, S4의 두 공과 딤플을 각각 확인합니다.
3. 문제가 있는 세트/카메라만 수정해 다시 렌더합니다. 시안은 최종 고해상도 파일의 검수를 대신하지 않습니다.
4. 최종 8장과 룩시트 4장을 직접 열어 재검수하고 실제 결과를 기록합니다. 검증 스크립트의 수치 검사는 육안 검수를 대신하지 않습니다.
5. 파일과 Git 대용량 제한을 확인하고 새 파일만 커밋·푸시합니다. 원격 브랜치 SHA가 로컬 커밋과 같은지 확인한 뒤 완료를 보고합니다.

## 검증한 범위

- 일반 Python 구문 검사, 렌더·룩시트 CLI 파서 검사, 공식 PyPI 4.2.23의 실제 시안 실행 일부.
- S1 저해상도 시안을 직접 열어 지구가 카메라 A에서 빠지는 문제를 수정했고, A/B 두 장에서 지구를 재확인했습니다.
- 지형의 재질 좌표와 콘솔 마모의 물리 단위 범프를 수정했습니다.
- 나머지 세트의 시각 검수, 최종 고해상도 검수와 룩시트 검수는 **미실행**입니다.
- 렌더 8장·룩시트 4장·최종 `.blend` 4개가 모두 검증될 때까지 작업을 완료로 표시하면 안 됩니다.
