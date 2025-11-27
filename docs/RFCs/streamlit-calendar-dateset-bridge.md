# streamlit-calendar datesSet 브릿지 패치 가이드

> ✅ **목표 달성 (2025-11-27): 대안 방식으로 해결 완료**
>
> - 원래 목적: FullCalendar prev/next 월 이동을 Streamlit으로 전달해 DB 재조회 트리거 확보
> - 실제 구현: 범위 쿼리 방식 (±1년 데이터를 초기에 한 번에 로드)
> - 결과: **포크/빌드 불필요**, Python-Calendar 통신 불필요, RFC 원안보다 더 빠름
> - 상세: `docs/CHANGELOG.md` 2025-11-27 항목 참조

## ⚠️ 이 문서는 참고용으로 보관됨

아래 내용은 datesSet 이벤트를 추가하는 원래 방안이며, 실제로는 **구현되지 않았습니다**.
대신 클라이언트 사이드 필터링 방식으로 동일한 목표를 달성했습니다.

---

## 원래 제안 내용 (미구현)

- 목적: FullCalendar prev/next 월 이동을 Streamlit으로 전달해 DB 재조회 트리거 확보 (무한 rerun 없이 `viewMonth`/`viewType`만 전달).
- 대상: `streamlit-calendar` 프론트엔드 소스(예: `frontend/src/index.tsx` 또는 `Calendar.tsx`) 커스터마이징 후 빌드·패키징.

## 1) 사전 백업/브랜치
- `git checkout -b feature/calendar-dateset-bridge`
- 원본 태그: `git tag streamlit-calendar-vanilla` (또는 소스 zip/tar 백업)

## 2) JS 브릿지 추가 (루프 방지 포함)
FullCalendar 인스턴스 생성 직후 추가:

```ts
let initialized = false;
let lastMonth: string | null = null;

calendar.on('datesSet', (info) => {
  const cur = info.view?.currentStart?.toISOString().slice(0, 7); // YYYY-MM
  if (!initialized) { initialized = true; lastMonth = cur; return; } // 최초 렌더 무시
  if (!cur || cur === lastMonth) return; // 월 변화 없으면 무시
  lastMonth = cur;
  Streamlit.setComponentValue({ viewMonth: cur, viewType: info.view?.type });
});
```

- payload 최소화(`viewMonth`, `viewType`)로 불필요 rerun 감소.
- 필요 시 `eventClick`/`dateClick` 기존 브릿지는 그대로 유지.

## 3) 파이썬 사용 패턴(참고)
- `calendar_result.get("viewMonth")`가 세션 `calendar_year/month`와 다를 때만 세션 업데이트 후 `st.rerun()`.
- 동일 월이면 아무 것도 하지 않아 rerun 루프 차단.

## 4) 빌드·패키징

```bash
npm install
npm run build          # 라이브러리 빌드 스크립트 기준
python -m build        # dist/streamlit_calendar-*.whl 생성
```

- 서비스 설치: `pip install dist/streamlit_calendar-*.whl`
- 또는 `requirements.txt`에 포크 URL/버전 고정(`git+https://...@tag#egg=streamlit-calendar`)

## 5) 검증 체크리스트
- prev/next 클릭 시 파이썬에 `{viewMonth: 'YYYY-MM'}` 도달 여부 로그 확인.
- 동일 월 반복 클릭/초기 렌더에서 무한 rerun 없는지 확인.
- 기존 `eventClick`/`dateClick` 동작 유지 확인.
- 월 변경 후 DB 재조회 → 달력/요약 데이터가 이동한 월을 반영하는지 수동 확인.

## 6) 리스크/완화
- 무한 rerun: 프런트 가드+백엔드 “변화 시에만 갱신” 로직으로 완화.
- 포크 관리: 태그/버전 핀으로 재현성 확보.
- DOM/옵션 변경 영향: 기존 옵션/스타일 손대지 않음.

## 7) 롤백
- `pip install streamlit-calendar==원본버전` 또는 원본 태그 체크아웃 후 재빌드.
- 서비스 `requirements.txt`를 원본 버전으로 복구.
