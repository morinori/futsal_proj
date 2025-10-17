# Interface Inventory

## 서비스 레이어
- `AttendanceService`
  - `create_attendance_for_match(match_id)` : 경기 생성 후 선수별 출석 레코드 생성.
  - `is_attendance_locked(match_id, *, now=None)` : 경기 시작 시각과 `attendance_lock_minutes` 기준으로 잠금 여부 판별.
  - `update_player_status(match_id, player_id, status)` : 출석 상태 변경 (`present|absent|pending`).
  - `get_match_attendance(match_id)` : 관리자용 상세 리스트 반환.
- `MatchService`
  - `create_match(field_id, match_date, match_time, opponent="", attendance_lock_minutes=0)` : 출석 마감 값을 포함한 경기 생성.
  - `update_match(match_id, field_id, match_date, match_time, opponent="", result="", attendance_lock_minutes=0)` : 경기 정보 및 마감 시간 갱신.
  - `delete_match(match_id)` : 경기 삭제.
  - `get_month_schedule(year, month)` : 월별 경기 목록.
- `VideoService`
  - `process_video_complete(uploaded_file, video_id)` : 저장 → 트랜스코딩 → 썸네일까지 전체 파이프라인.
  - `transcode_to_hls(video_path, video_id)` : FFmpeg 호출로 HLS 스트림 생성.
  - `generate_thumbnail(video_path, video_id)` : 썸네일 이미지 생성.
- `AuthService`
  - `login(username, password)` : bcrypt 검증 후 관리자 정보 반환.
  - `get_all_admins()` : 활성 관리자 목록 조회 시 비밀번호 해시를 제거해 반환.
  - `create_admin(...)`, `change_password(...)`, `deactivate_admin(...)` : 관리자 계정 관리.
- `NewsService`
  - `create_news(...)` / `update_news(...)` : 소식 등록·수정 시 입력 검증 및 Repository 호출.
  - `toggle_pinned(news_id)` / `delete_news(news_id)` : 소식 고정 및 삭제.
  - `get_all_news()`, `get_news_by_id(news_id)` 등 조회 유틸.

## 리포지토리 레이어
- `MatchRepository`, `PlayerRepository`, `VideoRepository`, `FinanceRepository`, `AdminRepository` 등 모든 Repository는 `database/connection.py`의 `DatabaseManager`를 사용.
  - `MatchRepository.create(match)` / `update(match)` : `attendance_lock_minutes` 컬럼을 INSERT/UPDATE에 포함.
  - `VideoRepository.get_completed_videos(limit=None)` : 완료된 영상 목록 (limit는 파라미터 바인딩 권장).
  - `VideoRepository.update_processing_status(...)` : 상태/경로/재생시간 업데이트.
  - `NewsRepository.update(news_id, title, content, author, pinned, category)` : 소식 수정.
  - `AdminRepository.create`, `get_by_username`, `get_by_id`, `get_all_active`, `update_last_login`, `update_password`, `deactivate`.
- 규칙: UI/Service는 SQL을 직접 실행하지 않고 Repository를 통해 데이터에 접근해야 한다.

## UI 페이지 & 컴포넌트
- `ui/pages/dashboard.py` : 지표 카드(`ui/components/metrics.py`) 및 요약.
- `ui/pages/attendance.py` : 출석 카드, 상태 변경 버튼, 세션 기반 경기 선택 동기화.
- `ui/pages/video_upload.py` : 업로드 폼, 진행률 UI → `VideoService` 호출.
- `ui/pages/video_gallery.py` : 필터 + 비디오 카드 그리드, `VideoRepository` 조회.
- `ui/pages/schedule.py` : 경기 생성/수정 폼에서 출석 마감 선택.
- `ui/pages/news_management.py` : 소식 등록/수정/삭제 및 고정 토글.
- `ui/components/auth.py` : 로그인 폼, 관리자 드롭다운 (`require_admin_access`).
- `ui/components/calendar.py` : 경기 일정 렌더링, 클릭 이벤트는 출석 페이지로 연결.

## 외부 연동 & 런타임 의존성
- **Streamlit** : UI 프레임워크.
- **FFmpeg/FFprobe** : `subprocess.run`으로 호출, Docker 이미지에 포함.
- **Nginx** : `futsal.nginx.conf`에서 `/uploads/` 라우팅 및 MIME 설정.
- **Docker (`run.sh`)** : 컨테이너 라이프사이클 관리, `/futsal_proj` 볼륨 공유.

## 세션 및 상태
- `st.session_state` 키: `current_page`, `is_admin`, `admin_*`, `admin_menu_expanded`, `last_activity`, `selected_match_id`, `match_select_dropdown`, `personal_match_select_{player_id}` 등.
- 파일 기반 세션(`utils/session_utils.py`)은 백업 용도로 유지되지만 기본 인증 흐름은 Streamlit 세션 중심.
- URL 파라미터 기반 세션 복원은 금지 (`docs/vuln.md` 참고).

## 보안 가드레일 링크
- `docs/vuln.md` : 세션 복원, JS 직삽입, SQL LIMIT 등 취약점 대응.
- `claude_guardrails.md` : docker compose 금지, git 워크플로, 배포 스크립트 사용 규칙.
