# Security Vulnerabilities & Remediation Guidance

## Deployment Workflow (Docker + Streamlit)
- 수정은 호스트의 `/futsal_proj` 소스에서 진행하며, 컨테이너는 `run.sh`에서 `-v /futsal_proj:/app` 볼륨을 통해 동일 디렉터리를 사용합니다. 코드 저장 즉시 컨테이너에도 반영됩니다.
- 현재 운영은 단일 컨테이너(`run.sh`) 기준이며 docker compose는 사용하지 않습니다. compose 템플릿이 필요하면 `ops/` 내 별도 검토 후 도입하세요.
- 의존성(Dockerfile, ffmpeg, requirements 등)을 변경했을 때만 `./run.sh rebuild`로 새 이미지를 만든 뒤 자동으로 컨테이너를 띄우세요. 구성 파일(Nginx 포함)은 이번 수정으로 손댈 필요가 없습니다.
- 코드만 바꾼 경우 `./run.sh restart`로 컨테이너를 재시작하거나, 바로 `docker logs --tail 50 futsal-team-platform`으로 런타임 로그를 확인해 세션/업로드 플로우가 정상인지 검증합니다.
- 빠른 로컬 테스트는 `python -m venv .venv && source .venv/bin/activate`, `pip install -r requirements.txt`, `streamlit run app.py` 순으로 진행하고, 운영 데이터(`uploads/`, `futsal.db`)와 테스트 데이터를 분리해 관리하세요.

## 1. Unauthorized Admin Session Restoration (`app.py:545`)
- **Issue**: Admin session is recreated purely from query parameters. Any crafted URL with `restore_session=1` grants admin rights.
- **Remediation**:
  - Reject all session restoration attempts that are not backed by a signed, server-generated token. Store the token server-side (DB or secure cookie) and validate it before mutating `st.session_state`.
  - Remove the code path that reads `admin_id`, `admin_username`, `admin_name`, and `admin_role` from `st.query_params`. Only trust data loaded from the official session store (`utils.session_utils`).
  - Add regression coverage: attempt to hit the app with forged query params and confirm admin features remain inaccessible.

## 2. Untrusted `eval` on FFprobe Metadata (`services/video_service.py:103`)
- **Issue**: `eval(video_stream.get('r_frame_rate', '0/1'))` executes untrusted input from uploaded videos.
- **Remediation**:
  - Parse the frame rate via `fractions.Fraction(video_stream['r_frame_rate']).numerator / denominator` or split on `'/'`. Avoid `eval` entirely.
  - Harden `get_video_info` with try/except for missing or malformed strings so it falls back to a safe default instead of executing arbitrary code.
  - Add tests that pass crafted metadata to confirm the parser rejects malicious values.

## 3. Unsafe Embedding of Session Data in JavaScript (`ui/components/auth.py:40-46`)
- **Issue**: Session values are inserted into inline JS without escaping, enabling XSS when admin names/usernames contain quotes.
- **Remediation**:
  - Serialize the payload with `json.dumps` (e.g., `sessionStorage.setItem('admin_session', JSON.stringify(payload))`) so characters are properly escaped.
  - Alternatively, inject the JSON as a `<script type="application/json">` block and read it via DOM APIs.
  - Test with usernames containing quotes/backticks to ensure the markup remains valid.

## 4. Raw `LIMIT` String Interpolation (`database/repositories.py:790`)
- **Issue**: `query += f" LIMIT {limit}"` concatenates unvalidated values into SQL, opening a future injection vector.
- **Remediation**:
  - Guard `limit` (e.g., `limit = max(1, min(int(limit), 100))`) and use parameter binding: `query += " LIMIT ?"` with `(limit,)`.
  - Confirm all call sites pass integer literals or sanitized values; add defensive assertions if needed.
  - Extend repository tests to cover the `limit` path and catch accidental string inputs.
