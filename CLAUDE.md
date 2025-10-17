# CLAUDE.md

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
- `services/match_service.py`: 경기 생성/수정 시 `attendance_lock_minutes` 검증과 저장을 담당.
- `services/attendance_service.py`: `is_attendance_locked`로 출석 변경 가능 여부를 판별하고 UI에 전달.
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
5. **기능별 스펙 초안**: `docs/attendance_lock_spec.md`, `docs/attendance_match_autoselect_spec.md` – 출석 마감 정책과 드롭다운 동기화 구현 참고.

위 문서들을 차례대로 확인한 뒤 개발을 시작하면 토큰 사용량을 최소화하면서도 최신 지침을 준수할 수 있습니다.

## 5. 금지/주의 패턴 요약

- 쿼리 파라미터로 세션/권한을 복원하지 않습니다 (`app.py` URL 복원 금지).
- 동영상 메타데이터를 `eval`·`exec`로 실행하지 않습니다 (`services/video_service.py`).
- JS 텍스트에 직접 값 삽입하지 말고 반드시 `json.dumps` 등으로 직렬화합니다.
- SQL은 항상 파라미터 바인딩을 사용합니다 (`LIMIT` 포함).
- 민감 데이터(업로드, DB, 세션 파일)는 커밋하지 않습니다 (.gitignore 유지).
- 출석 마감 시간을 우회하거나 관리자 전용 예외 로직을 일반 사용자에게 노출하지 않습니다.

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
4. 출석 마감/드롭다운 동기화 기능이 신규 구현물에 영향을 주는지 수동 확인합니다.
5. 테스트 계획(`docs/TEST_PLAN.md`)을 갱신하거나 새로운 테스트를 추가합니다.
6. 문서 업데이트 후 `docs/CHANGELOG.md`에 주요 변경 사항을 기록합니다.

## 8. Streamlit 개발 시 주의사항 및 고려사항

### 8.1 Streamlit Tabs 렌더링 동작 이해

**문제**: Streamlit의 `st.tabs()`는 모든 탭을 동시에 렌더링하므로, 각 탭에서 세션 상태를 변경하면 예상치 못한 덮어쓰기가 발생할 수 있습니다.

**증상 사례** (`attendance.py` 2025-10-17 이슈):
- 개인별 출석 탭에서 선수를 선택해도 페이지가 렌더링되지 않음
- 탭 함수 내부에서 `st.session_state["attendance_active_tab"]`을 설정했으나, 세 탭이 모두 렌더링되면서 마지막 탭("team")이 값을 덮어씀
- 결과적으로 탭 전환 감지 로직이 항상 "다른 탭에서 왔다"고 판단하여 선수 선택을 초기화

**해결 방법**:
```python
# ❌ 잘못된 방법: 각 탭 함수 내부에서 설정
def _render_personal_attendance_tab(self):
    st.session_state["attendance_active_tab"] = "personal"  # 다른 탭이 덮어씀
    # ...

# ✅ 올바른 방법: 각 `with tab` 블록에서 직접 설정
def render(self):
    tab1, tab2, tab3 = st.tabs(["👤 개인별", "📅 경기별", "🏆 팀"])

    with tab1:
        st.session_state["attendance_active_tab"] = "personal"
        self._render_personal_attendance_tab()

    with tab2:
        st.session_state["attendance_active_tab"] = "match"
        self._render_match_attendance_tab()
```

**교훈**:
- Streamlit tabs는 모든 `with tab` 블록을 순차적으로 실행하므로, 각 블록 내에서 상태를 설정해야 현재 활성 탭을 정확히 추적할 수 있습니다.
- 탭 함수 내부에서 세션 상태를 변경하면 모든 탭이 동일한 상태를 공유하게 되어 의도와 다른 동작이 발생합니다.

### 8.2 Selectbox 상태 관리 및 리렌더링

**문제**: Streamlit selectbox는 `key`로 세션 상태와 연동되지만, 초기 렌더링 시 상태가 없으면 첫 번째 옵션을 자동 선택합니다.

**증상 사례**:
- 플레이스홀더 옵션("-- 선수를 선택하세요 --")을 첫 번째로 추가했지만, JavaScript로 선택한 값이 Streamlit 세션 상태에 반영되지 않음
- 페이지 리렌더링 시 여전히 플레이스홀더가 선택되어 조건문(`if selected != PLACEHOLDER`)을 통과하지 못함

**해결 방법**:
```python
# ✅ index 파라미터로 현재 선택 유지
PLACEHOLDER_TEXT = "-- 선수를 선택하세요 --"
dropdown_options = [PLACEHOLDER_TEXT] + player_names

# 현재 세션 상태에서 선택된 값 가져오기
current_selection = st.session_state.get("personal_attendance_player", PLACEHOLDER_TEXT)
try:
    default_index = dropdown_options.index(current_selection)
except ValueError:
    default_index = 0  # 기본값: 플레이스홀더

selected_player_name = st.selectbox(
    "👤 누구세요?",
    options=dropdown_options,
    index=default_index,  # 명시적으로 현재 선택 유지
    key="personal_attendance_player"
)
```

**교훈**:
- Streamlit의 `key` 파라미터는 세션 상태와 위젯을 연결하지만, **초기 렌더링 시 `index`를 명시하지 않으면 첫 번째 옵션이 강제 선택**됩니다.
- JavaScript로 DOM을 직접 조작해도 Streamlit 세션 상태는 업데이트되지 않으므로, 반드시 `index`로 상태를 명시적으로 관리해야 합니다.

### 8.3 브라우저 테스트의 중요성

**문제**: 코드 상으로는 정상 작동하는 것처럼 보이지만, 실제 브라우저에서는 렌더링 순서나 상태 관리 이슈로 동작하지 않을 수 있습니다.

**증상 사례**:
- 로그에 에러가 없고 코드 로직도 올바르지만, 브라우저에서 선수 선택 후 페이지가 표시되지 않음
- Playwright를 통한 실제 브라우저 테스트로만 문제를 재현하고 확인 가능

**권장 사항**:
1. **UI 변경 시 반드시 브라우저 테스트 수행**:
   ```bash
   # Playwright MCP 또는 수동 브라우저 확인
   ./run.sh restart
   # http://localhost:8501 접속하여 실제 동작 확인
   ```

2. **디버깅 정보 활용**:
   - 개발 중에는 주석 처리된 디버깅 정보를 활성화하여 세션 상태 확인
   - `st.write(st.session_state)`로 전체 상태 덤프

3. **점진적 검증**:
   - 기능 단위로 작게 나누어 구현 후 즉시 브라우저 확인
   - 복잡한 상태 관리 로직은 단순화한 뒤 점진적으로 추가

### 8.4 세션 상태 초기화 패턴

**문제**: 탭 전환 시 상태를 초기화하려는 로직이 오히려 정상 동작을 방해할 수 있습니다.

**증상 사례**:
- "다른 탭에서 왔을 때만 초기화"하려는 복잡한 로직이 tabs의 동시 렌더링 특성과 충돌
- 조건문이 항상 참이 되어 사용자가 선택한 값이 즉시 초기화됨

**권장 패턴**:
```python
# ❌ 복잡한 탭 전환 감지 로직 지양
previous_tab = st.session_state.get("active_tab")
if previous_tab is not None and previous_tab != "current":
    # 상태 초기화 - 예상치 못한 동작 발생 가능

# ✅ 명시적인 초기화 버튼 제공
if st.button("🔄 선택 초기화"):
    del st.session_state["player_selection"]
    st.rerun()
```

**교훈**:
- **단순함이 최선**: 복잡한 자동 초기화 로직보다 명시적인 사용자 액션(버튼)이 더 안전하고 예측 가능합니다.
- 상태 초기화가 필요하다면 사용자가 명확히 인지할 수 있는 UI 요소를 제공하세요.

---
Claude Code는 위 순서를 기준으로 작업하며, 추가 정보가 필요할 때만 세부 문서를 열람하세요. 항상 `./run.sh`와 보안 가드레일을 먼저 확인하는 것을 잊지 마세요.
