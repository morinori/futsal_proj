# Changelog

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
