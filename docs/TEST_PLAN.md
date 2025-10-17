# Test Plan

## 테스트 범위
- 관리자 인증, 경기/출석, 동영상 업로드, 재정 관리, 뉴스/갤러리 UI.
- Docker 기반 배포 스크립트(`run.sh`)의 기본 동작 확인.
- 민감 데이터가 커밋되지 않도록 `.gitignore` 확인.

## 테스트 유형
- **단위 테스트 (pytest)**
  - `services/attendance_service.py`: 출석 생성/상태 변경/요약.
  - `services/attendance_service.is_attendance_locked`: 잠금 시나리오(과거 경기, 마감 전/후, 잘못된 시간 데이터) 검증.
  - `services/video_service.py`: `validate_uploaded_file`, `transcode_to_hls` 실패 케이스 모킹.
  - `services/auth_service.py`: bcrypt 검증, 비밀번호 변경.
  - `services/match_service.py`: `attendance_lock_minutes` 검증 범위 및 저장 확인.
  - `services/news_service.py`: 소식 생성/수정 시 검증 오류 처리와 Repository 호출 여부.
- **통합 테스트 (수동/스크립트)**
 1. `./run.sh restart` 후 `docker logs --tail 50 futsal-team-platform`으로 초기 관리자 비밀번호를 확인해 안전한 곳에 기록한 뒤 로그인 → 출석/경기/재정 페이지 접근.
  2. 테스트용 동영상 업로드 → HLS 변환 완료 여부 확인 (`uploads/videos/hls/{id}`).
  3. 갤러리 필터(특정 경기/정보 없음) 동작 확인.
  4. 경기 추가/수정 시 출석 마감 옵션을 각각 선택하고, 설정된 시간 이후 일반 계정에서 출석 버튼이 잠기는지 확인.
  5. 뉴스 관리 페이지에서 소식 수정 → 리스트 갱신 및 고정 토글 회귀 테스트.
  6. 대시보드/일정에서 출석 페이지로 이동한 뒤, 세션 상태가 유지되어 동일 경기가 선택되는지 확인.
- **보안 회귀 테스트**
  - 세션 URL 파라미터를 조작해도 관리자 권한이 부여되지 않아야 함.
  - 동영상 메타데이터의 `r_frame_rate`에 악성 문자열을 넣어도 예외 처리되어야 함.
  - JS 삽입 시 사용자 입력이 그대로 스크립트에 주입되지 않는지 확인.

## 데이터 및 픽스처
- 단위 테스트는 인메모리 SQLite (`sqlite3.connect(':memory:')`) 또는 임시 파일 사용.
- 샘플 관리자 계정/선수/경기 데이터는 `database/migrations.py`의 초기화 함수를 활용. 생성된 관리자 비밀번호는 매번 랜덤이며 DB에는 bcrypt 해시만 저장되므로 컨테이너 부팅 직후 `docker logs futsal-team-platform`으로 출력된 값을 확보한다.
- 동영상 테스트 시 작은 샘플 파일(수 초 길이)을 사용하고, 테스트 후 `uploads/` 정리.

## 종료 기준
- 서비스 레이어 단위 테스트 커버리지 80% 이상.
- `docs/vuln.md`에 기록된 취약점에 대한 회귀 테스트 통과.
- `./run.sh restart` 시 앱이 정상 부팅하고 주요 페이지가 오류 없이 열릴 것.
- 문서(`docs/CHANGELOG.md`, `docs/QUESTIONS.md`)가 최신 상태.
