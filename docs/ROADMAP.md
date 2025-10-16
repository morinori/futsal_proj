# Product & Engineering Roadmap

## Near Term (0-1 month)
- 세션 복원 로직 개선: 서명된 토큰 기반 구현 검토 (`docs/vuln.md` 참조).
- 동영상 업로드 자동 테스트 작성 및 실패 시 롤백 처리 보완.
- `pytest` 기반 서비스 단위 테스트 기본 세트 작성.
- `docs/QUESTIONS.md`에 남아 있는 보안/운영 이슈 답변 정리.
- 출석 마감 기능에 대한 관리자 예외 정책 설계(권한 분리, 경고 메시지 조정).
- 뉴스 수정 이력/작성자 감사 로그 요구 여부 결정.

## Mid Term (1-3 months)
- 동영상 HLS 다중 화질(480p 추가) 및 CDN 캐시 전략 검토.
- 관리자 감사 로그(Audit log) 테이블 도입, 주요 행위 기록.
- UI 리팩토링: 공통 컴포넌트 분리 및 다국어 지원 준비.
- CI 파이프라인 구축: lint/pytest/도커 빌드 자동화.
- 출석 마감 알림(푸시/이메일) 및 일정 연동 검토.

## Long Term (3+ months)
- 모바일 앱 또는 PWA 연동으로 출석/알림 푸시 기능 도입.
- 실시간 경기/출석 업데이트(WebSocket 기반) 검토.
- 외부 인증(예: OAuth) 연계로 팀원 셀프 등록 플로우 확장.

## Tracking
- 관련 이슈는 GitHub Projects 또는 `docs/QUESTIONS.md`에 기록하고, 완료 시 `docs/CHANGELOG.md`에 반영.
