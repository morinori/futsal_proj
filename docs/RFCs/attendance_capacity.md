# Attendance Capacity Planning

본 문서는 `.codex/AGENTS.md`의 분석 워크플로에 따라 경기별 참석 인원 제한 기능을 구현하기 위한 실행 계획을 구성한다. Claude Code가 실제 개발을 수행할 때 참조할 세부 지침을 제공하며, 구현 착수 전 추가 확인이 필요한 항목을 명시한다.

## 1. 배경 & 목표
- 현재는 경기 생성 시 모든 선수에게 출석 레코드를 생성하고, `attendance_lock_minutes`로만 변경 가능 여부를 제어한다.
- 일부 경기(연습 경기, 소수 정예 훈련 등)는 참석자를 제한해야 하지만, 정원 관리 기능이 없어 운영자가 수동으로 관리해야 한다.
- 목표: 경기별 `참석 정원(attendance_capacity)`을 설정해 정원이 찼을 때 일반 사용자의 참석 전환을 막고, 관리자에게 정원 조정/오버라이드 수단을 제공한다.

## 2. 범위
1. **데이터 계층**
   - `matches` 테이블에 `attendance_capacity INTEGER NULL` 컬럼 추가 (NULL → 제한 없음).
   - `database/models.Match`와 `database/repositories.MatchRepository`(create/update/get 계열)에 새 필드를 반영.
   - 참석자 수 계산 최적화를 위해 `attendance(match_id, status)` 인덱스 추가 고려.
2. **서비스 계층**
   - `AttendanceService.update_player_status`에서 `status='present'`로 전환 시 현재 참석 수(`attendance_repo.count_present(match_id)`)와 정원을 비교.
   - 정원 초과 시 일반 요청은 실패 처리, 관리자 호출 시 `override_capacity=True` 옵션으로 통과 가능하도록 별도 메서드(`update_status_with_override`) 추가.
   - `get_attendance_summary` 결과에 `capacity`, `remaining_slots`를 포함해 UI 재사용.
3. **UI/UX**
   - `ui/pages/schedule.py`: 경기 생성/수정 폼에 “참석 정원” 숫자 입력 추가(`0 또는 빈 값 = 제한 없음`). 저장 시 `match_service`가 범위(예: 0~30) 검증.
   - `ui/pages/attendance.py`: 개인 탭과 경기 탭 상단에 `현재 참석 / 정원 / 잔여` 배지 표시. 잔여 0이면 참석 버튼 비활성화 + 안내 문구 표시.
   - `ui/pages/team_builder.py` 또는 관리자 패널: 정원 대비 참석 현황을 보여주고, 필요 시 정원을 늘리는 버튼/모달 제공.
4. **알림/가드레일**
   - 정원 변경 시 세션 알림(`st.info`)으로 팀원에게 공유.
   - 정원이 찬 상태에서 참석하려는 사용자는 “정원이 가득 찼습니다. 관리자에게 문의하세요.” 메시지를 받음.

## 3. 구현 단계
1. **스키마 업데이트**
   - 새 마이그레이션 파일 작성: `attendance_capacity` 컬럼 추가, 필요한 인덱스 생성.
   - `database/migrations.py`에 기본값 적용 로직(기존 경기는 NULL) 추가.
2. **도메인/레포지토리 갱신**
   - `database/models.Match` dataclass, `match_repo` CRUD 쿼리, `match_service` DTO 업데이트.
   - `attendance_repo`에 `count_present(match_id)` 또는 `get_present_count(match_id)` 메서드 추가.
3. **서비스 로직**
   - `AttendanceService` 내 정원 체크 로직 추가.
   - 관리자 오버라이드용 `update_status_with_override` 작성(추후 감사 로그 연동 가능하도록 확장 포인트 주석).
4. **UI 반영**
   - 경기 생성/수정 폼 UI 변경.
   - 출석 페이지(개인/경기 탭)에서 정원 정보 표시 및 버튼 상태 제어.
   - 관리자 페이지에서 정원 조정/잔여 확인 기능 추가.
5. **검증**
   - `pytest`에 서비스 단위 테스트 추가 (정원 내 성공, 정원 초과 실패, 관리자 오버라이드 성공).
   - Streamlit 수동 테스트: 정원 값 입력 → 여러 사용자로 참석 변경 → 잔여 표시 확인 → 관리자 정원 조정 시 즉시 반영되는지 검증.

## 4. 고려 사항 & 열린 질문
- **대기열 필요성**: 초기 배포는 단순 정원 차단, 추후 “대기자” 상태 도입 여부 결정 필요.
- **정원 알림**: 정원 마감 시 Slack/이메일 등 추가 알림이 필요한지 운영팀 확인.
- **오버라이드 감사**: 운영 정책상 관리자 오버라이드 로그가 필요하면 `attendance_overrides` 테이블을 별도 RFC로 정의.
- **정원 기본값**: 경기 템플릿 또는 구장별 기본 정원을 두어 입력 편의를 높일지 여부.

## 5. 완료 기준
- 경기 생성/수정 화면에서 정원을 설정할 수 있고 DB에 저장된다.
- 정원이 설정된 경기에서 일반 사용자는 잔여가 0일 경우 참석 버튼이 비활성화된다.
- 관리자 계정으로는 정원 초과 참석 처리가 가능하거나 정원을 조정할 수 있다.
- `docs/CHANGELOG.md` 및 관련 문서에 기능 추가 내역이 기록된다.

## 6. 후속 작업
- 감사 로그/대기열 요구가 확정되면 별도 RFC 작성.
- 정원 설정 값이 훈련/친선 등 이벤트 유형과 연동되어야 한다면 `matches` 테이블에 `match_type` 도입 고려.
- CI에 신규 테스트 케이스를 포함시켜 회귀를 방지한다.
