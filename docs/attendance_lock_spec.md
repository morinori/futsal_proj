# 출석 잠금 기능 스펙 초안

## 목표
- 경기 시작 `attendance_lock_minutes`분 전에 일반 사용자의 출석 변경을 차단한다.
- 마감 전에는 기존과 동일하게 출석 상태를 변경할 수 있다.
- 기본 단위는 0·30·60·90분 등 30분 간격이며, 기본값은 `0` (제한 없음)이다.

## 데이터베이스 및 모델 변경
- `matches` 테이블에 `attendance_lock_minutes INTEGER NOT NULL DEFAULT 0` 컬럼을 추가한다. (기존 DB에는 `ALTER TABLE` 수행 필요)
- `database/models.py`의 `Match` 데이터 클래스에 `attendance_lock_minutes: int = 0` 필드를 추가한다.
- 초기화/마이그레이션 스크립트에도 새 컬럼을 포함하고, 기존 레코드는 기본값 0으로 채운다.

## 검증 및 서비스 로직
- `utils/validators.validate_match_data`
  - `attendance_lock_minutes`가 `0 <= 값 <= 180` 범위이고 30분 배수인지 검증한다.
- `MatchService.create_match` / `MatchService.update_match`
  - 새 필드를 파라미터로 받고 레포지토리에 전달한다. UI 입력이 없다면 기본값 0을 사용한다.
- `MatchRepository.create` / `MatchRepository.update`
  - INSERT/UPDATE 문에 새 컬럼을 포함한다.
- `AttendanceService`
  - `is_attendance_locked(match_id, *, now=None)` 헬퍼를 추가해 경기 시간과 `attendance_lock_minutes`로 잠금 여부를 계산한다.
  - `update_player_status`에서 잠금 상태면 False 반환 또는 예외를 발생시키고, (선택) 관리자 강제 수정을 허용할지 정책을 분기한다.

## UI 변경
- **일정 관리 페이지 (`ui/pages/schedule.py`)**
  - 경기 추가/수정 폼에 "출석 마감" 선택 박스를 추가한다: `[제한 없음, 경기 30분 전, 60분 전, 90분 전]`.
  - 저장 시 선택 값을 서비스로 전달한다.
- **출석 페이지 (`ui/pages/attendance.py`)**
  - 경기/개인 상세에서 `is_attendance_locked` 결과에 따라 버튼을 비활성화하고 `🔒 출석 변경 마감` 경고를 표시한다.
  - 마감 전에는 기존 동작을 유지한다.

## 경계 조건
- 경기 시각이 과거인 경우 자동으로 잠금 처리한다.
- 시간 정보가 없는 경기(데이터 오류)는 잠금 검사 실패 시 기존 로직을 유지한다.
- 관리자 권한을 구분할 경우 `require_admin_access` 여부를 확인해 예외 허용을 분기한다.

## 테스트 시나리오
- `attendance_lock_minutes`가 0인 경기: 제한 없이 상태 변경 가능.
- 경기 60분 전 마감 설정
  1. 경기 70분 전: 변경 가능
  2. 경기 50분 전: 변경 불가 메시지 및 버튼 비활성화
- 과거 경기: 항상 잠금 상태
- 관리자 예외 허용 시: 일반 사용자/관리자 계정으로 각각 확인

## 추가 고려사항
- 기존 DB에 `ALTER TABLE` 적용 전 백업 권장.
- 마감 메시지를 다국어 지원 시 상수화한다.
- 향후 마감 임박 알림(예: 푸시/이메일) 등 확장 포인트로 활용 가능하다.

## 구현 현황 (2025-10-15)
- `matches` 테이블과 `Match` 데이터 모델에 `attendance_lock_minutes`가 반영되었다.
- 일정 관리 페이지에서 경기 생성/수정 시 마감 시간을 선택할 수 있다.
- `AttendanceService.is_attendance_locked`가 잠금 여부를 판단하고, 출석 페이지 UI가 결과에 따라 버튼을 비활성화한다.
- 관리자 예외 처리와 알림 정책은 미정 상태로 `docs/QUESTIONS.md`에 후속 항목을 기록했다.
