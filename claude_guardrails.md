# Claude Code Guardrails

## Overview
- Use this document to track coding standards, security rules, and mandatory checks for implementation tasks.
- All contributors must follow these rules to maintain code quality, security, and consistency.
- Reference `CLAUDE.md` for architectural context and update both files when guardrails change.

---

## 📋 Table of Contents
1. [Coding Standards](#coding-standards)
2. [Security Rules](#security-rules)
3. [Streamlit Best Practices](#streamlit-best-practices)
4. [Database Rules](#database-rules)
5. [Testing Requirements](#testing-requirements)
6. [Deployment Guidelines](#deployment-guidelines)
7. [File Structure Rules](#file-structure-rules)
8. [Review Workflow](#review-workflow)

---

## 1. Coding Standards

### 1.1 Python Style

**Required**:
- [ ] **타입 힌트**: 모든 함수에 파라미터 및 리턴 타입 명시
  ```python
  # ✅ Good
  def get_player(player_id: int) -> Optional[Dict[str, Any]]:
      ...

  # ❌ Bad
  def get_player(player_id):
      ...
  ```

- [ ] **Docstring**: 공개 함수/클래스에 Google 스타일 docstring 작성
  ```python
  # ✅ Good
  def update_attendance(match_id: int, player_id: int) -> Dict[str, Any]:
      """선수의 출석 상태를 업데이트합니다.

      Args:
          match_id: 경기 ID
          player_id: 선수 ID

      Returns:
          성공 여부와 메시지를 포함한 딕셔너리
      """
  ```

- [ ] **줄 길이**: 최대 100자 (PEP 8 권장 120자 이하)
- [ ] **임포트 순서**: 표준 라이브러리 → 서드파티 → 로컬 모듈
- [ ] **네이밍 컨벤션**:
  - 함수/변수: `snake_case`
  - 클래스: `PascalCase`
  - 상수: `UPPER_SNAKE_CASE`

### 1.2 Error Handling

**Required**:
- [ ] **명시적 예외 처리**: `except Exception` 금지, 구체적 예외 타입 사용
  ```python
  # ✅ Good
  try:
      result = int(value)
  except (ValueError, TypeError) as e:
      logger.error(f"Invalid value: {e}")
      return None

  # ❌ Bad
  try:
      result = int(value)
  except:
      pass
  ```

- [ ] **로깅**: 에러 발생 시 항상 로깅
  ```python
  except ValueError as e:
      logger.error(f"Validation failed: {e}", exc_info=True)
  ```

- [ ] **일관된 리턴 타입**: Service 계층은 `Dict[str, Any]` 형태로 성공/실패 반환
  ```python
  return {
      'success': bool,
      'message': str,
      'data': Optional[Any]
  }
  ```

---

## 2. Security Rules

### 2.1 Critical Prohibitions (🔴 절대 금지)

**NEVER**:
- [ ] ❌ `eval()` 또는 `exec()` 사용 금지
  ```python
  # ❌ NEVER DO THIS
  eval(user_input)
  exec(config_string)

  # ✅ Use safe alternatives
  json.loads(user_input)
  ast.literal_eval(safe_expression)
  ```

- [ ] ❌ `subprocess.run(..., shell=True)` 금지
  ```python
  # ❌ NEVER
  subprocess.run(f"ffmpeg -i {user_file}", shell=True)

  # ✅ Use list arguments
  subprocess.run(['ffmpeg', '-i', user_file], shell=False)
  ```

- [ ] ❌ SQL 쿼리에 f-string 또는 format() 사용 금지
  ```python
  # ❌ NEVER
  query = f"SELECT * FROM users WHERE id = {user_id}"
  query = "SELECT * FROM users LIMIT {}".format(limit)

  # ✅ Always use parameterized queries
  query = "SELECT * FROM users WHERE id = ?"
  db_manager.execute_query(query, (user_id,))
  ```

- [ ] ❌ URL 파라미터로 세션/권한 복원 금지
  ```python
  # ❌ NEVER
  if query_params.get("admin"):
      st.session_state["is_admin"] = True

  # ✅ Use server-side session only
  # Authentication via services/auth_service.py only
  ```

- [ ] ❌ 하드코딩된 비밀정보 금지
  ```python
  # ❌ NEVER
  API_KEY = "sk-1234567890abcdef"
  PASSWORD = "admin123"

  # ✅ Use environment variables
  API_KEY = os.getenv("API_KEY")
  ```

### 2.2 Input Validation (필수)

**Required**:
- [ ] **모든 사용자 입력 검증**: `utils/validators.py` 사용
  ```python
  # ✅ Good
  validation_result = validate_match_data(form_data)
  if not validation_result.is_valid:
      return {'success': False, 'message': ', '.join(validation_result.errors)}
  ```

- [ ] **파일 업로드 다층 검증**:
  1. 확장자 화이트리스트
  2. Magic byte 검증
  3. 파일 크기 제한
  4. Path traversal 방지
  ```python
  # utils/file_security.py 패턴 준수
  ```

- [ ] **SQL 파라미터 바인딩**: 100% 파라미터 바인딩 사용
  ```python
  # ✅ ALWAYS
  query = "SELECT * FROM matches WHERE id = ?"
  execute_query(query, (match_id,))

  # LIMIT도 파라미터화
  query = "... LIMIT ?"
  execute_query(query, (limit,))
  ```

### 2.3 Session Management

**Required**:
- [ ] **서버 사이드 세션만 사용**: `st.session_state` 전용
- [ ] **sessionStorage/localStorage 금지**: JavaScript 세션 저장 금지
- [ ] **세션 타임아웃 체크**: `utils/auth_utils.py` 패턴 준수 (30분)
- [ ] **권한 검증**: 모든 관리자 기능에서 `is_admin_logged_in()` 체크

---

## 3. Streamlit Best Practices

### 3.1 Session State Management

**CRITICAL** (CLAUDE.md Section 8 기반):

- [ ] **Tabs 렌더링 이해**: `with tab` 블록에서 직접 상태 설정
  ```python
  # ❌ WRONG - 모든 탭이 동시 렌더링되어 덮어씀
  def _render_tab(self):
      st.session_state["active_tab"] = "personal"

  # ✅ CORRECT - with 블록에서 직접 설정
  with tab1:
      st.session_state["active_tab"] = "personal"
      self._render_tab()
  ```

- [ ] **Selectbox index 명시**: 현재 선택 유지를 위해 index 파라미터 사용
  ```python
  # ✅ Good
  current = st.session_state.get("player", "")
  try:
      idx = options.index(current)
  except ValueError:
      idx = 0

  st.selectbox("선수", options, index=idx, key="player")
  ```

- [ ] **버튼 상태 직접 설정 금지**: Streamlit은 버튼 상태를 ephemeral로 관리
  ```python
  # ❌ NEVER - Exception 발생
  st.session_state.my_button = True
  st.button("Click", key="my_button")
  ```

- [ ] **조건부 초기화**: 중복 초기화 방지
  ```python
  # ✅ Good
  if 'key' not in st.session_state:
      st.session_state['key'] = default_value
  ```

### 3.2 Caching

**Required**:
- [ ] **자주 조회되는 데이터 캐싱**: `@st.cache_data` 사용
  ```python
  @st.cache_data(ttl=300)  # 5분 캐시
  def get_all_players() -> List[Dict[str, Any]]:
      return player_service.get_all_players()
  ```

- [ ] **데이터베이스 연결 캐싱**: `@st.cache_resource` 사용
  ```python
  @st.cache_resource
  def get_db_connection():
      return DatabaseManager()
  ```

- [ ] **캐시 무효화**: 데이터 변경 시 `st.cache_data.clear()` 호출

### 3.3 Performance

**Recommended**:
- [ ] **불필요한 리렌더링 방지**: 조건부 렌더링 활용
- [ ] **대용량 데이터 페이지네이션**: 한 번에 20-50개 항목만 표시
- [ ] **이미지 최적화**: 썸네일 크기 제한 (640px)

---

## 4. Database Rules

### 4.1 Query Patterns

**Required**:
- [ ] **Repository 패턴 준수**: 모든 DB 접근은 `database/repositories.py` 경유
- [ ] **Service 레이어 분리**: 비즈니스 로직은 `services/*.py`에만
- [ ] **파라미터 바인딩**: 모든 쿼리에서 `?` 플레이스홀더 사용
  ```python
  # ✅ Good
  query = "INSERT INTO matches (...) VALUES (?, ?, ?)"
  execute_query(query, (field_id, match_date, match_time))
  ```

- [ ] **JOIN으로 N+1 방지**: 관련 데이터는 단일 쿼리로 조회
  ```python
  # ✅ Good
  SELECT m.*, f.name as field_name
  FROM matches m
  JOIN fields f ON f.id = m.field_id
  ```

### 4.2 Transactions

**Required**:
- [ ] **원자성 보장**: 여러 테이블 수정 시 트랜잭션 사용
- [ ] **롤백 처리**: 예외 발생 시 명시적 롤백

### 4.3 Data Integrity

**Required**:
- [ ] **Dataclass 사용**: `database/models.py` 모델 사용
- [ ] **타입 검증**: Repository에서 Dict 반환 시 타입 일관성 유지

---

## 5. Testing Requirements

### 5.1 Unit Tests

**Required**:
- [ ] **Service 계층 테스트**: 새 서비스 함수마다 pytest 테스트 작성
  ```python
  # tests/test_services/test_attendance_service.py
  def test_attendance_lock_before_deadline():
      """마감 전에는 잠금 안 됨"""
      service = AttendanceService()
      result = service.is_attendance_locked(match_id=1, now=test_time)
      assert result is False
  ```

- [ ] **커버리지 목표**: 80% 이상
  ```bash
  pytest --cov=services --cov-report=html
  ```

- [ ] **엣지 케이스**: 경계값, null, 빈 값 테스트

### 5.2 Security Regression Tests

**Required** (docs/vuln.md 기준):
- [ ] **eval/exec 부재 검증**
  ```python
  def test_no_eval_in_codebase():
      result = subprocess.run(['grep', '-r', 'eval(', 'services/'], capture_output=True)
      assert result.returncode != 0
  ```

- [ ] **SQL 인젝션 방지 검증**
- [ ] **파일 업로드 보안 검증**
- [ ] **세션 관리 보안 검증**

### 5.3 Integration Tests

**Recommended**:
- [ ] **브라우저 테스트**: Playwright로 UI 플로우 검증
- [ ] **Docker 통합 테스트**: `./run.sh restart` 후 동작 확인

---

## 6. Deployment Guidelines

### 6.1 Pre-Deployment Checklist

**Required**:
- [ ] `./run.sh restart`로 로컬 검증 완료
- [ ] `docker logs --tail 50 futsal-team-platform`에서 에러 없음 확인
- [ ] `.gitignore`에 민감 데이터 제외 확인 (*.db, uploads/, .env)
- [ ] 보안 회귀 테스트 통과 (docs/vuln.md 체크리스트)
- [ ] 테스트 커버리지 80% 이상 유지

### 6.2 Deployment Flow

**Standard Process**:
1. **코드 변경만**: `./run.sh restart` (볼륨 마운트로 즉시 반영)
2. **의존성 변경**: `./run.sh rebuild` (Dockerfile, requirements.txt)
3. **설정 변경**: Nginx 설정 수정 시 `futsal.nginx.conf` 확인

**Prohibited**:
- [ ] ❌ `docker-compose.yml` 추가 금지 (ops/ 워크플로우 문서화 필요)
- [ ] ❌ 수동 `docker run` 명령 금지 (`run.sh` 사용)

### 6.3 Configuration Management

**Required**:
- [ ] **환경변수 사용**: 민감 정보는 `.env` 파일
- [ ] **설정 중앙화**: `config/settings.py`에서 관리
- [ ] **기본값 제공**: 모든 설정에 안전한 기본값

---

## 7. File Structure Rules

### 7.1 New File Guidelines

**Required**:
- [ ] **Layer 준수**: 적절한 디렉토리에 파일 생성
  - UI 코드 → `ui/pages/` 또는 `ui/components/`
  - 비즈니스 로직 → `services/`
  - 데이터 접근 → `database/repositories.py`
  - 유틸리티 → `utils/`

- [ ] **테스트 파일**: 동일 구조로 `tests/` 아래 생성
  ```
  services/attendance_service.py
  → tests/test_services/test_attendance_service.py
  ```

- [ ] **문서 파일**: `docs/` 또는 `claudedocs/`에 분리
- [ ] **임시 스크립트**: `scripts/` 디렉토리 (커밋 전 검토)

### 7.2 Naming Conventions

**Required**:
- [ ] **파일명**: `snake_case.py`
- [ ] **모듈 import**: 상대 경로 금지, 절대 경로 사용
  ```python
  # ✅ Good
  from services.attendance_service import attendance_service

  # ❌ Bad
  from ..services.attendance_service import attendance_service
  ```

---

## 8. Review Workflow

### 8.1 Code Review Checklist

**Before Commit**:
- [ ] 모든 TODO/FIXME 제거 또는 이슈 등록
- [ ] 타입 힌트 및 docstring 작성
- [ ] `grep -r "eval\|exec" .` 검증 (결과 없어야 함)
- [ ] `grep -r "shell=True" .` 검증 (결과 없어야 함)
- [ ] `git status`로 불필요한 파일 제외 확인

**Before Pull Request**:
- [ ] 테스트 실행: `pytest --cov=services`
- [ ] 로컬 배포 검증: `./run.sh restart`
- [ ] 문서 업데이트 (CHANGELOG.md, QUESTIONS.md)
- [ ] 이 가드레일 체크리스트 준수 확인

### 8.2 Documentation Updates

**When to Update**:
- [ ] **CLAUDE.md**: 아키텍처, 실행 방법, 주의사항 변경 시
- [ ] **docs/vuln.md**: 새로운 보안 취약점 발견/해결 시
- [ ] **docs/CHANGELOG.md**: 주요 기능 추가/변경 시
- [ ] **this file**: 새로운 규칙/패턴 도입 시

---

## 9. Quick Reference

### Security Quick Check
```bash
# 보안 패턴 검증 (모두 0건이어야 함)
grep -r "eval(" . --include="*.py" | wc -l
grep -r "exec(" . --include="*.py" | wc -l
grep -r "shell=True" . --include="*.py" | wc -l
grep -r "f\".*LIMIT" . --include="*.py" | wc -l
```

### Testing Quick Check
```bash
# 테스트 실행 및 커버리지
pytest --cov=services --cov-report=term-missing

# 특정 서비스 테스트
pytest tests/test_services/test_attendance_service.py -v
```

### Deployment Quick Check
```bash
# 로컬 검증
./run.sh restart
docker logs --tail 50 futsal-team-platform

# 데이터베이스 백업 (배포 전)
cp team_platform.db ~/backup/team_platform_$(date +%Y%m%d).db
```

---

## 10. Enforcement

- **Mandatory**: 섹션 1, 2, 4, 5.1, 6.1 (보안, 코드 품질, DB, 테스트)
- **Strongly Recommended**: 섹션 3, 5.2, 7 (Streamlit, 회귀 테스트, 파일 구조)
- **Recommended**: 섹션 5.3, 6.3 (통합 테스트, 설정 관리)

**Violation Consequences**:
- Critical violations (Section 2.1) → 즉시 수정 필수
- Standard violations → PR 리뷰에서 지적 및 수정 요청

---

**Last Updated**: 2025-12-07
**Version**: 2.0
**Maintainer**: Development Team
