# Changelog

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
