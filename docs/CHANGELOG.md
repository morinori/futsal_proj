# Changelog

## 2025-11-27
- **달력 월 이동 기능 구현 완료 (대안 방식)**
  - RFC: `docs/RFCs/streamlit-calendar-dateset-bridge.md` 목표 달성 (다른 방식)
  - 목표: 달력의 prev/next 버튼으로 월 이동 시 경기가 즉시 표시
  - 결과: ✅ **구현 성공** (범위 쿼리 방식)
  - 핵심 아이디어:
    - RFC 원안: datesSet 이벤트로 월 변경 감지 → Python이 새 데이터 전송 (통신 필요)
    - 실제 구현: ±1년 범위 데이터를 초기에 한 번에 전송 → FullCalendar가 클라이언트 사이드 필터링 (통신 불필요)
  - 코드 변경:
    - `database/repositories.py`: `MatchRepository.get_in_date_range(start_date, end_date)` 메서드 추가 (날짜 범위 쿼리)
    - `services/match_service.py`: `get_matches_in_range(start_date, end_date)` 메서드 추가 (범위 쿼리 래핑)
    - `ui/components/calendar.py`:
      - 기존 `get_monthly_matches(year, month)` 대신 `get_matches_in_range(2024-01-01, 2026-12-31)` 사용
      - 모든 경기를 FullCalendar에 전달, 클라이언트 사이드에서 자동 필터링
      - `initialDate`로 현재 월 표시, prev/next 클릭 시 즉시 해당 월 경기 표시
  - 성능 측정 (실제 Docker 환경):
    - 현재 12경기: 0.08ms 쿼리, 1.5KB 메모리, 5KB 브라우저 전송
    - 3년 150경기: 1.00ms 쿼리, 18.75KB 메모리, 65KB 브라우저 전송
    - 10년 500경기: 3.33ms 쿼리, 62.50KB 메모리, 218KB 브라우저 전송
    - 비교: jQuery.js(90KB), 평균 웹 이미지(100-500KB)보다 작음
  - 장점:
    - ✅ 포크/빌드 불필요
    - ✅ Python-Calendar 통신 불필요
    - ✅ 무한루프 리스크 없음
    - ✅ RFC 원안보다 더 빠름 (1회 쿼리 vs 월마다 쿼리)
    - ✅ 유지보수 용이
  - 브라우저 테스트 검증:
    - November 2025 (4경기) → October 2025 (5경기) → September 2025 (6경기) 모두 즉시 표시 확인
    - prev/next 버튼 정상 작동, Python rerun 없이 클라이언트 사이드 렌더링

## 2025-11-25
- **RFC 종료: 달력 월 이동 기능 구현 불가 판정**
  - RFC: `docs/RFCs/calendar-multi-month-view.md`
  - 목표: 달력의 prev/next 버튼으로 월 이동 시 경기 목록도 함께 업데이트
  - 결과: ❌ **구현 불가** (기술적 제약)
  - 근거:
    - `streamlit-calendar` 라이브러리가 prev/next 버튼 클릭 이벤트를 Streamlit Python 코드로 전달하지 않음
    - 작동하는 콜백: `eventClick`, `dateClick`만 확인
    - 미작동 콜백: `datesSet`, `eventsSet` (설정해도 `calendar_result`에 포함 안 됨)
    - 달력 내부 상태(현재 표시 중인 월)를 Python에서 읽을 방법 없음
  - 시도한 방안:
    1. datesSet/eventsSet 콜백 활성화 → 실패
    2. dateClick의 view 정보 활용 → prev/next 버튼에서는 미발생
    3. 동적 key를 통한 컴포넌트 재마운트 → 트리거 부재
    4. Streamlit 버튼으로 네비게이션 추가 → 기술적으로 작동하나 RFC 요구사항과 다름
  - 대안: 월 이동이 필요한 경우 "일정 관리" 페이지의 월별 필터 사용
  - 코드 변경: 없음 (원상 복구됨)

## 2025-11-20
- 경기별 참석 정원 관리 기능 추가로 운영 편의성 향상.
  - `database/migrations.py`: `matches` 테이블에 `attendance_capacity INTEGER NULL` 컬럼 추가
  - `database/models.py`: `Match` 모델에 `attendance_capacity` 필드 추가
  - `database/repositories.py`:
    - `MatchRepository`: create/update 메서드에 attendance_capacity 반영
    - `AttendanceRepository`: `count_present(match_id)` 메서드 추가 (참석 인원 카운트)
    - `attendance(match_id, status)` 복합 인덱스 생성으로 카운트 성능 최적화
  - `services/match_service.py`: create/update 메서드에 정원 검증 로직 추가 (필수 입력, 1-50명 범위)
  - `services/attendance_service.py`:
    - `update_player_status`: 정원 초과 시 일반 사용자 참석 변경 차단
    - `get_attendance_summary`: capacity, remaining_slots, is_full 정보 추가
    - 관리자는 `is_admin=True` 플래그로 정원 초과 허용
  - `ui/pages/schedule.py`: 경기 생성/수정 폼에 "참석 정원" 필수 입력 필드 추가 (기본값: 20명, 범위: 1-50명)
  - `ui/pages/attendance.py`:
    - 개인별/경기별 출석 탭 모두에 정원 현황 배지 표시 (예: "🎯 참석 정원: 12/15명 (잔여 3석)")
    - 정원 마감 시 "⚠️ **정원 마감**" 경고 메시지 + 참석 버튼 비활성화
    - 출석 상태 변경 응답을 Dict 형태로 처리하여 상세 에러 메시지 제공
  - ADR 문서: `docs/ADRs/2025-11-20-attendance-capacity.md` 참조

## 2025-11-12
- 출석 응답 상태를 세분화해 무응답 선수를 명확히 구분.
  - `database/repositories.py`: 경기 요약 쿼리를 참석/불참/미정/무응답/총원 집계로 재작성.
  - `services/attendance_service.py`: 무응답 카운트와 `has_responded` 플래그를 노출해 UI에서 재사용 가능하도록 확장.
  - `ui/pages/attendance.py`: 요약 메트릭에 무응답 수치를 추가하고, 불참 표시를 응답 여부에 따라 분리, 기본 불참 상태로부터 응답하지 않은 선수는 버튼 재활성화 없이도 구별 가능하도록 UI 제약 개선.

## 2025-10-17
- 개인별 출석 탭에 명시적 선수 선택 플로우 적용하여 실수로 첫 번째 선수를 선택하는 문제 해결.
  - `ui/pages/attendance.py`:
    - 더미 플레이스홀더 옵션("-- 선수를 선택하세요 --") 추가 (Streamlit 1.20 호환)
    - 선수 미선택 시 세부 패널과 액션 버튼 숨김, 안내 메시지 표시
    - 선택된 선수 표시 정보 필 추가 ("선택된 선수: 김선준")
    - 출석 상태 변경 시 확인 메시지 표시 (선수명 → 경기명)
    - Streamlit tabs 렌더링 순서 문제 해결: 각 `with tab` 블록에서 `attendance_active_tab` 직접 설정
    - `index` 파라미터로 드롭다운 선택 상태 유지 및 리렌더링 안정화
  - 스펙 문서: `docs/attendance_personal_tab_spec.md` 참조
  - 모든 기능 요구사항(FR1-FR6)과 승인 기준(AC1-AC4) 충족
  - 브라우저 테스트 완료: 선수 선택 후 출석 페이지 정상 렌더링 확인

## 2025-10-16
- 출석 마감에 "바로 마감"(-1) 옵션 추가하여 관리자가 시간과 관계없이 즉시 출석을 마감할 수 있도록 개선.
  - `utils/validators.py`: -1 값 허용, 검증 로직 개선
  - `services/attendance_service.py`: -1 값 즉시 잠금 로직 추가
  - `ui/pages/schedule.py`: 경기 추가/수정 폼에 "바로 마감" 드롭다운 옵션 추가
  - `ui/pages/attendance.py`: 즉시 마감 상태 특별 안내 메시지 표시
  - `ui/pages/team_builder.py`: 팀 구성 표시 후 저장/불러오기 버튼을 배치해 사용 흐름 개선

## 2025-10-15
- 경기 일정 관리에 출석 마감(`attendance_lock_minutes`) 설정을 도입하고 DB/검증/UI 전반을 갱신.
- 뉴스 관리 페이지에서 소식 수정 워크플로를 지원하도록 Repository·Service·UI를 확장.
- 출석 페이지 드롭다운이 세션 상태와 동기화되어 페이지 이동 시 선택한 경기가 유지되도록 개선.

## 2025-10-01
- Repository 초기화 및 GitHub `main` 브랜치 푸시 완료.
- 문서 구조 정비(`docs/`, `.codex/`)와 보안 가이드(`docs/vuln.md`, `claude_guardrails.md`) 작성.
- `CLAUDE.md`를 간결한 런북 형태로 재작성하여 `run.sh` 기반 실행 및 교차 문서 링크 강조.
- `.gitignore` 업데이트로 DB/업로드/세션/로컬 설정 파일 제외.
- 전체 백업 아카이브 생성: `~/backup/20251001_backup.tar.gz`.

## Guidelines
- Follow Keep a Changelog conventions and list entries chronologically.
