# README.md

이 문서는 Claude Code가 이 리포지토리에서 작업을 시작할 때 반드시 읽어야 하는 요약 가이드입니다. 실행 방법과 필수 문서 링크만 담고 있으니, 필요한 세부 내용은 아래에서 안내하는 추가 문서를 참고하세요.

## 1. 빠른 실행 요약

- **기본 진입점**: 항상 `./run.sh`를 사용해 Docker 컨테이너를 관리합니다.
  - `./run.sh` → 컨테이너가 없으면 새로 생성, 있으면 재사용합니다 (`-v /futsal_proj:/app`으로 코드 동기화).
  - `./run.sh restart` → 컨테이너 재시작.
  - `./run.sh rebuild` → Dockerfile/의존성이 바뀌었을 때 새 이미지 빌드 후 실행.
- **로컬 빠른 테스트** (선택): `python -m venv .venv && source .venv/bin/activate`, `pip install -r requirements.txt`, `streamlit run app.py`.
- **데이터 경로**: `uploads/`, `futsal.db`, `team_platform.db`는 민감 데이터이므로 건드리기 전 항상 백업 지침을 확인합니다.

## 2. 배포 및 운영 흐름

1. 로컬 코드 수정 → `./run.sh restart`로 즉시 반영 확인 (볼륨 마운트 덕분에 재빌드 필요 없음).
2. 의존성/Dockerfile 변경 → `./run.sh rebuild` (컨테이너 삭제 → 이미지 빌드 → 시작).
3. 로그 확인 → `docker logs --tail 50 futsal-team-platform` 또는 `./run.sh logs`.
4. 운영 데이터 직접 수정 전에는 `docs/vuln.md`와 `claude_guardrails.md`의 보안 지침을 반드시 확인합니다.

## 3. 리포지토리 레이아웃 핵심

- `app.py`: Streamlit 엔트리. UI/페이지 라우팅과 세션 복원을 담당합니다.
- `ui/`: 페이지(`ui/pages/`)와 컴포넌트(`ui/components/`) 모듈.
- `services/`: 비즈니스 로직 계층.
- `database/`: 리포지토리, 모델, 마이그레이션.
- `config/settings.py`: 업로드 정책, DB 경로 등 설정.
- `utils/`: 인증, 검증, 포매터, 파일 보안 등 공통 함수.
- `docs/`: Codex CLI가 생산한 설계/테스트/안전 문서 (`SPEC.md`, `INTERFACES.md`, `TEST_PLAN.md`, `vuln.md` 등).
- `.codex/`: Codex 에이전트 프로필(`AGENT.md`), 가드레일 사본(`instructions.md`).
- `claude_guardrails.md`: Claude Code가 실제 구현 시 따라야 할 규칙.

## 4. 참고해야 할 문서

1. **보안 / 취약점**: `docs/vuln.md` – URL 기반 세션 복원 금지, ffprobe `eval` 제거, JS 삽입 보안, SQL `LIMIT` 파라미터화 등.
2. **운영 가드레일**: `claude_guardrails.md` – docker compose 금지, run.sh 기반 운영, git 워크플로, 보안 규칙.
3. **Codex 설계 메모**: `.codex/AGENT.md` – 요구사항 분석, 문서 산출물 작성 흐름.
4. **추가 산출물**: `docs/SPEC.md`, `docs/INTERFACES.md`, `docs/TEST_PLAN.md`, `docs/ROADMAP.md`, `docs/QUESTIONS.md`, `docs/CHANGELOG.md` – 필요 시 최신화.

위 문서들을 차례대로 확인한 뒤 개발을 시작하면 토큰 사용량을 최소화하면서도 최신 지침을 준수할 수 있습니다.

## 5. 금지/주의 패턴 요약

- 쿼리 파라미터로 세션/권한을 복원하지 않습니다 (`app.py` URL 복원 금지).
- 동영상 메타데이터를 `eval`·`exec`로 실행하지 않습니다 (`services/video_service.py`).
- JS 텍스트에 직접 값 삽입하지 말고 반드시 `json.dumps` 등으로 직렬화합니다.
- SQL은 항상 파라미터 바인딩을 사용합니다 (`LIMIT` 포함).
- 민감 데이터(업로드, DB, 세션 파일)는 커밋하지 않습니다 (.gitignore 유지).

세부 근거는 `docs/vuln.md`와 `claude_guardrails.md`에 기록되어 있으니 수정 시 교차 참조하세요.

## 6. Git 워크플로

- `git init` → `git remote add origin git@github.com:morinori/futsal_proj.git` → `git branch -M main`이 기본 셋업입니다.
- 커밋 전 `.gitignore`에 DB/업로드/세션/.claude가 포함돼 있는지 확인하고, 변경 사항은 `git status`와 `git diff`로 점검합니다.
- `git add`, `git commit`, `git push -u origin main` 순으로 반영합니다.
- 보안 규칙이나 가이드 문서를 수정했으면 같은 커밋에 `docs/vuln.md`와 `claude_guardrails.md`도 포함하고 커밋 메시지에 언급합니다.

## 7. 다음 단계 체크리스트

1. `docs/vuln.md`에서 수정 대상 취약점이 여전히 열려 있는지 확인하고 해결 여부를 기록합니다.
2. `claude_guardrails.md`에서 새로운 규칙이 필요한지 검토합니다.
3. 변경 사항을 구현한 뒤 `./run.sh restart`로 즉시 확인하고, 필요하면 `./run.sh rebuild`로 재배포합니다.
4. 테스트 계획(`docs/TEST_PLAN.md`)을 갱신하거나 새로운 테스트를 추가합니다.
5. 문서 업데이트 후 `docs/CHANGELOG.md`에 주요 변경 사항을 기록합니다.

---
Claude Code는 위 순서를 기준으로 작업하며, 추가 정보가 필요할 때만 세부 문서를 열람하세요. 항상 `./run.sh`와 보안 가드레일을 먼저 확인하는 것을 잊지 마세요.
