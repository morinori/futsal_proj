# Functional Specification

## 프로젝트 개요
- Streamlit 기반 풋살팀 운영 플랫폼으로 출석, 경기 일정, 선수 관리, 재정, 미디어(사진/동영상) 기능을 제공.
- 관리자(Admin)와 일반 사용자로 역할이 구분되며, 관리자 기능은 로그인 후에만 접근 가능.
- 모든 핵심 기능은 `app.py` → `ui/`(페이지) → `services/`(비즈니스 로직) → `database/`(Repository) 구조로 호출됨.

## 핵심 기능 범위
1. **경기 및 출석 관리**
   - 경기 CRUD, 필드 스케줄링, 경기 생성 시 선수 출석 레코드 자동 생성.
   - 출석 현황(참석/불참/미정) 업데이트 및 요약 지표 제공.
   - 경기별 출석 마감 시간(`attendance_lock_minutes`)을 설정해 일반 사용자의 출석 변경 허용 범위를 제어.
   - 출석 페이지 드롭다운이 세션 상태와 동기화되어 최근에 본 경기를 그대로 표시.
2. **선수 관리 및 통계**
   - 선수 정보 등록/수정/비활성화, 포지션/연락처 관리.
   - 경기별 기록(득점, 어시스트 등)과 출석률 집계.
3. **재정 관리**
   - 수입/지출 등록, 카테고리 분류, 총계 및 지표 제공.
4. **컨텐츠 관리**
   - 뉴스·갤러리 관리, 동영상 업로드/트랜스코딩/갤러리 공개.
   - 업로드 영상은 FFmpeg로 HLS(720p) 변환 후 Nginx를 통해 스트리밍.
   - 관리자 뉴스 관리 페이지에서 소식 등록뿐 아니라 수정/고정 토글을 지원.
5. **관리자 인증**
   - bcrypt 기반 비밀번호 검증, 세션 상태 점검, 드롭다운 메뉴를 통한 페이지 이동.
   - 초기 관리자 계정(`admin`, `captain`, `manager`)은 `database/migrations.py` 실행 시 `secrets.token_urlsafe`로 랜덤 비밀번호가 생성되고 콘솔 로그에 한 번만 출력된다. 배포 후 즉시 `docker logs futsal-team-platform`으로 값을 확인해 안전하게 전달·변경한다.

## 사용자 플로우 요약
1. **관리자 로그인**
   1. `ui/components/auth.py` 로그인 폼 → `services/auth_service.py.login` → `database.repositories.AdminRepository` 확인.
   2. 성공 시 `st.session_state`에 관리자 정보 저장, 사이드바 메뉴 확장.
2. **경기 생성 → 출석 자동 생성**
   1. `ui/pages/schedule.py`에서 경기 생성 요청.
   2. `services/match_service.create_match` → `database.repositories.MatchRepository.create`.
   3. 성공 시 `services/attendance_service.create_attendance_for_match` 호출로 모든 선수 출석 레코드 생성.
3. **동영상 업로드 파이프라인**
   1. `ui/pages/video_upload.py`에서 파일 업로드.
   2. `services/video_service.process_video_complete`에서 저장 → 트랜스코딩 → 썸네일 생성.
   3. `database.repositories.VideoRepository.update_processing_status`로 상태 갱신.
   4. `ui/pages/video_gallery.py`에서 완료된 영상 노출 및 필터링.
4. **출석 마감 설정 및 적용**
   1. `ui/pages/schedule.py`에서 경기 생성/수정 시 "출석 마감" 옵션을 선택한다.
   2. `services/match_service`가 입력을 검증하고 `attendance_lock_minutes` 값을 저장한다.
   3. 출석 페이지에서 `AttendanceService`가 경기 시작 시각과 마감 값을 비교해 변경 가능 여부를 판단한다.
   4. 잠금 시간이 지난 뒤에는 일반 사용자의 상태 변경 버튼이 비활성화되고 안내 메시지가 표출된다.
5. **소식 수정 플로우**
   1. `ui/pages/news_management.py`에서 소식을 선택하면 인라인 편집 폼이 활성화된다.
   2. `services/news_service.update_news`가 입력을 검증한 뒤 Repository를 통해 Row를 갱신한다.
   3. 성공 시 세션 상태를 초기화하고 최신 내용으로 리스트가 갱신된다.

## 비기능 요구사항
- **보안**: URL 파라미터로 세션 복원 금지, 업로드 파일 MIME 체크, SQL 파라미터 바인딩 강제.
- **성능**: 영상 트랜스코딩은 Docker 컨테이너 내부 FFmpeg 사용, HLS 세그먼트는 Nginx가 서빙.
- **신뢰성**: `purge_videos.sh` 등 운영 스크립트 실행 전 백업 필수, `~/backup/20251001_backup.tar.gz` 참고.

## 주요 데이터 모델
- `players`, `matches`, `attendance`, `fields`, `finances`, `news`, `gallery`, `admins`, `videos` 테이블.
- 모든 모델은 `database/models.py` dataclass로 정의되고 Repository에서 Dict 형태로 반환.

## 성공 기준 (Acceptance Criteria)
- 관리자는 로그인 후 사이드바 드롭다운에서 모든 관리자 페이지에 접근 가능해야 한다.
- 경기 생성 시 출석 레코드가 누락 없이 생성되고, 출석 변경이 즉시 반영되어야 한다.
- 경기별 출석 마감 시간이 경과하면 일반 사용자가 상태를 변경할 수 없어야 하며, 관리자는 정책에 따라 예외 처리가 가능해야 한다.
- 동영상 업로드 후 최대 수 분 이내에 HLS 스트리밍이 가능해야 하며, 썸네일이 갤러리에 노출되어야 한다.
- 출석 페이지에서 다른 화면으로 이동 후 돌아와도 사용자가 마지막으로 선택한 경기가 유지되어야 한다.
- 뉴스 관리 페이지에서 소식 제목/내용/카테고리/고정 여부를 수정한 뒤 리스트가 즉시 갱신되어야 한다.
- 보안 가이드(`docs/vuln.md`, `claude_guardrails.md`)의 금지 패턴이 코드베이스에 존재하지 않아야 한다.
