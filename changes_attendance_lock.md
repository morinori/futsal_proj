# 출석 즉시 마감 기능 변경 요청

## 목표
관리자 일정 관리 > 경기 목록에서 "수정" 시 출석 마감을 즉시 닫을 수 있는 옵션을 추가하고, 출석 페이지에서도 해당 상태를 명확히 안내합니다.

## 현재 구현 상태

### 데이터 모델
- `matches` 테이블에 `attendance_lock_minutes` 컬럼 (INTEGER, DEFAULT 0)
- 현재 허용 값: 0, 30, 60, 90 (분)
  - 0 = 제한 없음 (항상 변경 가능)
  - 30/60/90 = 경기 시작 N분 전에 마감

### 현재 검증 로직 (`utils/validators.py:38-46`)
```python
attendance_lock_minutes = data.get('attendance_lock_minutes')
if attendance_lock_minutes is not None:
    if not isinstance(attendance_lock_minutes, int):
        errors.append("출석 마감 시간은 정수여야 합니다.")
    elif attendance_lock_minutes < 0 or attendance_lock_minutes > 180:
        errors.append("출석 마감 시간은 0~180분 범위여야 합니다.")
    elif attendance_lock_minutes % 30 != 0:
        errors.append("출석 마감 시간은 30분 단위여야 합니다.")
```

### 현재 잠금 확인 로직 (`services/attendance_service.py:18-56`)
```python
def is_attendance_locked(self, match_id: int, *, now: Optional[datetime] = None) -> bool:
    # 출석 마감 시간이 0이면 제한 없음
    if match.get('attendance_lock_minutes', 0) == 0:
        return False

    # 과거 경기는 항상 잠금
    if match_datetime < now:
        return True

    # 마감 시간 계산
    lock_minutes = match.get('attendance_lock_minutes', 0)
    lock_datetime = match_datetime - timedelta(minutes=lock_minutes)

    # 현재 시간이 마감 시간을 지났는지 확인
    return now >= lock_datetime
```

### UI 드롭다운 옵션
#### 경기 추가 폼 (`ui/pages/schedule.py:89-96`)
```python
lock_options = {
    "제한 없음": 0,
    "경기 30분 전": 30,
    "경기 60분 전": 60,
    "경기 90분 전": 90
}
```

#### 경기 수정 폼 (`ui/pages/schedule.py:374-390`)
동일한 옵션 구조

### 출석 페이지 UI (`ui/pages/attendance.py:377-412`)
- `is_locked` 확인 후 잠금 메시지 표시
- 현재 로직: `lock_minutes > 0`일 때만 마감 시간 정보 표시
- 잠금 상태일 때: "🔒 **출석 변경 마감됨**" 또는 "🔒 **출석 변경 마감**: 경기 시작 시간이 임박하여..."

## 요구사항: 즉시 마감 기능 추가

### 비즈니스 요구사항
- **사용 시나리오**: 관리자가 경기 확정 후 즉시 출석을 마감하고 더 이상 변경을 허용하지 않고 싶을 때
- **값 표현**: `-1` = 즉시 마감 (시간과 관계없이 항상 잠금)
- **권한**: 관리자만 설정 가능 (현재 `schedule.py`는 이미 `require_admin_access()` 적용)

## 상세 변경 사항

### 1. `utils/validators.py` - 검증 로직 수정

**파일**: `utils/validators.py:38-46`

**현재 코드**:
```python
elif attendance_lock_minutes < 0 or attendance_lock_minutes > 180:
    errors.append("출석 마감 시간은 0~180분 범위여야 합니다.")
elif attendance_lock_minutes % 30 != 0:
    errors.append("출석 마감 시간은 30분 단위여야 합니다.")
```

**변경 후**:
```python
elif attendance_lock_minutes < -1 or attendance_lock_minutes > 180:
    errors.append("출석 마감 시간은 -1 또는 0~180분 범위여야 합니다.")
elif attendance_lock_minutes != -1 and attendance_lock_minutes % 30 != 0:
    errors.append("출석 마감 시간은 -1(즉시 마감) 또는 30분 단위여야 합니다.")
```

**보안 고려사항**:
- 정수형 체크는 유지 (SQL 인젝션 방지)
- 범위 제한 유지 (비정상 값 방지)

### 2. `services/attendance_service.py` - 잠금 로직 수정

**파일**: `services/attendance_service.py:18-56`

**현재 코드** (line 34-36):
```python
# 출석 마감 시간이 0이면 제한 없음
if match.get('attendance_lock_minutes', 0) == 0:
    return False
```

**변경 후**:
```python
lock_minutes = match.get('attendance_lock_minutes', 0)

# -1이면 즉시 마감 (항상 잠금)
if lock_minutes == -1:
    return True

# 출석 마감 시간이 0이면 제한 없음
if lock_minutes == 0:
    return False
```

**위치**: `is_attendance_locked()` 메서드 내부, 경기 정보 조회 직후

**논리 순서**:
1. `-1` 체크 → True 반환 (즉시 마감)
2. `0` 체크 → False 반환 (제한 없음)
3. 과거 경기 체크 → True 반환
4. 마감 시간 계산 및 비교

### 3. `ui/pages/schedule.py` - 드롭다운 옵션 추가

#### 3.1 경기 추가 폼 수정

**파일**: `ui/pages/schedule.py:89-96`

**현재 코드**:
```python
lock_options = {
    "제한 없음": 0,
    "경기 30분 전": 30,
    "경기 60분 전": 60,
    "경기 90분 전": 90
}
```

**변경 후**:
```python
lock_options = {
    "제한 없음": 0,
    "바로 마감": -1,
    "경기 30분 전": 30,
    "경기 60분 전": 60,
    "경기 90분 전": 90
}
```

#### 3.2 경기 수정 폼 수정

**파일**: `ui/pages/schedule.py:374-390`

**현재 코드** (line 374-382):
```python
lock_options = {
    "제한 없음": 0,
    "경기 30분 전": 30,
    "경기 60분 전": 60,
    "경기 90분 전": 90
}
current_lock_minutes = match.get('attendance_lock_minutes', 0)
current_lock_label = next((k for k, v in lock_options.items() if v == current_lock_minutes), "제한 없음")
```

**변경 후**:
```python
lock_options = {
    "제한 없음": 0,
    "바로 마감": -1,
    "경기 30분 전": 30,
    "경기 60분 전": 60,
    "경기 90분 전": 90
}
current_lock_minutes = match.get('attendance_lock_minutes', 0)
current_lock_label = next((k for k, v in lock_options.items() if v == current_lock_minutes), "제한 없음")
```

**주의사항**:
- 드롭다운 순서: "제한 없음" → "바로 마감" → 시간 기반 옵션
- 기존 경기 수정 시 `-1` 값이 올바르게 선택되도록 `next()` 로직 확인

### 4. `ui/pages/attendance.py` - 출석 페이지 UI 개선

**파일**: `ui/pages/attendance.py:377-412`

**현재 코드** (line 380-394):
```python
if match_info:
    from datetime import datetime, timedelta, timezone
    lock_minutes = match_info.get('attendance_lock_minutes', 0)

    if lock_minutes > 0:
        # ... 마감 시간 계산 및 표시
        st.info(f"**출석 마감 시간**: {lock_datetime.strftime('%m월 %d일 %H:%M')}")

        if is_locked:
            st.error("🔒 **출석 변경 마감됨**")
        else:
            # ... 남은 시간 표시
```

**변경 후**:
```python
if match_info:
    from datetime import datetime, timedelta, timezone
    lock_minutes = match_info.get('attendance_lock_minutes', 0)

    if lock_minutes == -1:
        # 즉시 마감 특별 안내
        st.warning("⚠️ **관리자 즉시 마감**: 이 경기는 관리자에 의해 출석이 즉시 마감되었습니다.")
        st.error("🔒 **출석 변경 불가**")
    elif lock_minutes > 0:
        # ... 기존 시간 기반 마감 로직 유지
        KST = timezone(timedelta(hours=9))
        now = datetime.now(timezone.utc).astimezone(KST).replace(tzinfo=None)
        match_datetime = datetime.strptime(f"{match_info['match_date']} {match_info['match_time']}", "%Y-%m-%d %H:%M")
        lock_datetime = match_datetime - timedelta(minutes=lock_minutes)

        st.info(f"**출석 마감 시간**: {lock_datetime.strftime('%m월 %d일 %H:%M')}")

        if is_locked:
            st.error("🔒 **출석 변경 마감됨**")
        else:
            remaining = lock_datetime - now
            hours, remainder = divmod(int(remaining.total_seconds()), 3600)
            minutes, _ = divmod(remainder, 60)
            st.success(f"✅ **변경 가능** (남은 시간: {hours}시간 {minutes}분)")
```

**현재 코드** (line 411-412):
```python
if is_locked:
    st.warning("🔒 **출석 변경 마감**: 경기 시작 시간이 임박하여 출석 상태를 변경할 수 없습니다.")
```

**변경 후**:
```python
if is_locked:
    if match_info and match_info.get('attendance_lock_minutes') == -1:
        st.warning("🔒 **출석 변경 마감**: 관리자가 출석을 즉시 마감했습니다.")
    else:
        st.warning("🔒 **출석 변경 마감**: 경기 시작 시간이 임박하여 출석 상태를 변경할 수 없습니다.")
```

**UI/UX 개선사항**:
- 즉시 마감 시 다른 색상/아이콘으로 구분 (warning + error)
- 명확한 사유 표시 ("관리자 즉시 마감")
- 기존 시간 기반 마감과 메시지 차별화

## 데이터베이스 영향도
- **스키마 변경**: 없음 (기존 `attendance_lock_minutes INTEGER` 컬럼 사용)
- **마이그레이션**: 불필요
- **기존 데이터**: 영향 없음 (기존 0, 30, 60, 90 값 유지)

## 보안 검토

### 권한 제어
- ✅ `ui/pages/schedule.py`는 이미 `require_admin_access()` 적용
- ✅ 일반 사용자는 출석 페이지에서 읽기만 가능
- ✅ `-1` 값 설정은 관리자 전용 페이지에서만 가능

### 입력 검증
- ✅ `validators.py`에서 정수형 강제 (SQL 인젝션 방지)
- ✅ 범위 제한 (`-1` 또는 `0~180`)
- ✅ 파라미터 바인딩 사용 (Repository 계층)

### 참고 문서
- `docs/vuln.md`: SQL 파라미터 바인딩, 입력 검증 규칙
- `claude_guardrails.md`: 보안 규칙, 권한 검증 필수

## 테스트 계획

### 단위 테스트
1. **`utils/validators.py`**
   - `-1` 값 허용 확인
   - `-2`, `181` 등 비정상 값 거부 확인
   - `30, 60, 90` 기존 값 여전히 허용 확인

2. **`services/attendance_service.py`**
   - `is_attendance_locked(match_id)` 테스트
     - `attendance_lock_minutes = -1` → `True` 반환
     - `attendance_lock_minutes = 0` → `False` 반환
     - `attendance_lock_minutes = 30`, 현재 시간 = 경기 20분 전 → `True`
     - `attendance_lock_minutes = 30`, 현재 시간 = 경기 40분 전 → `False`

3. **`services/match_service.py`**
   - `create_match(attendance_lock_minutes=-1)` 성공 확인
   - `update_match(attendance_lock_minutes=-1)` 성공 확인

### 통합 테스트
1. **경기 생성 플로우**
   - 관리자 로그인 → 경기 추가 → "바로 마감" 선택 → 저장 → DB 확인

2. **경기 수정 플로우**
   - 관리자 로그인 → 기존 경기 수정 → "바로 마감" 선택 → 저장 → DB 확인
   - 기존 `-1` 값 경기 수정 시 드롭다운에 "바로 마감" 선택 확인

3. **출석 페이지 표시**
   - `-1` 경기의 출석 페이지 접속 → 즉시 마감 메시지 확인
   - 버튼 비활성화 확인

4. **출석 변경 차단**
   - `-1` 경기에서 출석 상태 변경 시도 → 실패 확인
   - `update_player_status()` → `False` 반환 확인

### 회귀 테스트
- 기존 `0, 30, 60, 90` 값 경기들의 동작 확인
- 과거 경기 잠금 로직 정상 동작 확인
- 시간 계산 로직 영향 없음 확인

## 검증 방법

### 수동 테스트 시나리오

#### 시나리오 1: 즉시 마감 경기 생성
1. 관리자 로그인
2. "📅 일정 관리" → "➕ 경기 추가" 탭
3. 경기 정보 입력, "출석 마감" → "바로 마감" 선택
4. "경기 추가" 버튼 클릭
5. **예상 결과**: 성공 메시지, 경기 생성됨
6. DB 확인: `SELECT attendance_lock_minutes FROM matches WHERE id = ?` → `-1`

#### 시나리오 2: 기존 경기를 즉시 마감으로 변경
1. 관리자 로그인
2. "📅 일정 관리" → "📋 경기 목록" 탭
3. 기존 경기 선택 → "✏️ 수정" 버튼
4. "출석 마감" → "바로 마감" 선택
5. 저장
6. **예상 결과**: 성공 메시지, DB에 `-1` 저장됨

#### 시나리오 3: 출석 페이지에서 즉시 마감 안내 확인
1. 시나리오 1 또는 2로 `-1` 경기 생성
2. 출석 페이지 접속 (관리자 또는 일반 사용자)
3. 해당 경기 선택
4. **예상 결과**:
   - "⚠️ **관리자 즉시 마감**: 이 경기는 관리자에 의해 출석이 즉시 마감되었습니다."
   - "🔒 **출석 변경 불가**"
   - 상태 변경 버튼 비활성화

#### 시나리오 4: 출석 변경 시도 차단
1. 시나리오 3 상태에서 출석 버튼 클릭
2. **예상 결과**: 버튼 비활성화로 클릭 불가

#### 시나리오 5: 기존 마감 옵션 회귀 테스트
1. "경기 30분 전" 옵션으로 경기 생성
2. 출석 페이지에서 마감 시간 정보 정상 표시 확인
3. 경기 40분 전 → 변경 가능
4. 경기 20분 전 → 변경 불가

### 로그 확인
```bash
docker logs --tail 50 futsal-team-platform
```
- 검증 에러 없음 확인
- DB 쿼리 정상 실행 확인

## 문서 업데이트

### 1. `docs/CHANGELOG.md`
**추가 항목** (2025-10-16):
```markdown
## 2025-10-16
- 출석 마감에 "바로 마감"(-1) 옵션 추가하여 관리자가 시간과 관계없이 즉시 출석을 마감할 수 있도록 개선.
  - `utils/validators.py`: -1 값 허용
  - `services/attendance_service.py`: -1 값 즉시 잠금 로직 추가
  - `ui/pages/schedule.py`: 경기 추가/수정 폼에 "바로 마감" 드롭다운 옵션 추가
  - `ui/pages/attendance.py`: 즉시 마감 상태 특별 안내 메시지 표시
```

### 2. `docs/SPEC.md` (선택)
**추가 섹션** (line 40-44 근처):
```markdown
4. **출석 마감 설정 및 적용**
   1. `ui/pages/schedule.py`에서 경기 생성/수정 시 "출석 마감" 옵션을 선택한다.
      - "제한 없음"(0): 항상 변경 가능
      - "바로 마감"(-1): 즉시 마감 (시간과 관계없이)
      - "경기 30/60/90분 전": 시간 기반 마감
   2. `services/match_service`가 입력을 검증하고 `attendance_lock_minutes` 값을 저장한다.
   3. 출석 페이지에서 `AttendanceService`가 경기 시작 시각과 마감 값을 비교해 변경 가능 여부를 판단한다.
   4. 잠금 시간이 지났거나 `-1` 값일 때 일반 사용자의 상태 변경 버튼이 비활성화되고 안내 메시지가 표출된다.
```

### 3. 이 문서 (`changes_attendance_lock.md`)
- 구현 완료 후 `docs/features/attendance_lock_immediate.md`로 이동 (선택)
- 또는 삭제하고 CHANGELOG만 유지

## 배포 절차

### 1. 로컬 개발
```bash
# 코드 수정 후 즉시 반영 확인 (볼륨 마운트 덕분)
./run.sh restart

# 로그 확인
docker logs --tail 50 futsal-team-platform
```

### 2. 수동 테스트
- 위 검증 시나리오 1~5 실행
- 기존 기능 회귀 테스트

### 3. Git 커밋
```bash
git status
git diff

# 변경 파일 확인
# - utils/validators.py
# - services/attendance_service.py
# - ui/pages/schedule.py
# - ui/pages/attendance.py
# - docs/CHANGELOG.md
# - changes_attendance_lock.md (이 파일)

git add utils/validators.py services/attendance_service.py ui/pages/schedule.py ui/pages/attendance.py docs/CHANGELOG.md changes_attendance_lock.md

git commit -m "feat: 출석 즉시 마감 기능 추가 (-1 옵션)

- 관리자가 시간과 관계없이 출석을 즉시 마감할 수 있는 '바로 마감' 옵션 추가
- validators: -1 값 허용, 검증 로직 개선
- attendance_service: -1 값 즉시 잠금 처리
- schedule.py: 경기 추가/수정 폼에 드롭다운 옵션 추가
- attendance.py: 즉시 마감 특별 안내 메시지 표시

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"

git push origin main
```

### 4. 운영 배포
```bash
# 의존성 변경 없으므로 재시작만
./run.sh restart

# 정상 동작 확인
docker logs --tail 100 futsal-team-platform
```

## 롤백 계획

### 롤백 조건
- 검증 실패
- 기존 기능 회귀 발생
- 데이터 무결성 문제

### 롤백 절차
```bash
# Git 롤백
git revert HEAD
git push origin main

# 컨테이너 재시작
./run.sh restart

# 또는 이전 커밋으로 하드 리셋 (주의!)
git reset --hard <previous_commit_hash>
git push -f origin main
```

### 데이터 정리 (필요 시)
```sql
-- -1 값을 0으로 되돌리기 (DB 직접 수정)
UPDATE matches SET attendance_lock_minutes = 0 WHERE attendance_lock_minutes = -1;
```

## 참고 문서
- `CLAUDE.md`: 실행 방법 및 문서 구조
- `docs/vuln.md`: 보안 가이드
- `claude_guardrails.md`: 개발 규칙
- `docs/SPEC.md`: 기능 사양
- `docs/CHANGELOG.md`: 변경 이력

## 구현 체크리스트
- [ ] `utils/validators.py` 수정
- [ ] `services/attendance_service.py` 수정
- [ ] `ui/pages/schedule.py` 경기 추가 폼 수정
- [ ] `ui/pages/schedule.py` 경기 수정 폼 수정
- [ ] `ui/pages/attendance.py` UI 개선
- [ ] 단위 테스트 (가능 시)
- [ ] 통합 테스트 (수동)
- [ ] 회귀 테스트
- [ ] `docs/CHANGELOG.md` 업데이트
- [ ] Git 커밋 및 푸시
- [ ] 운영 배포 및 확인

