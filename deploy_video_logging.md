# 비디오 로깅 시스템 배포 가이드

## 변경사항 요약

### 1. 클라이언트 측 로깅
- 비디오 플레이어에 상세한 이벤트 로깅 추가
- 재생 시작, 에러, 버퍼링 등 모든 이벤트 추적
- Beacon API로 서버에 로그 전송 (페이지 닫혀도 전송 보장)

### 2. 서버 측 로그 수집
- Flask 기반 로그 API 추가 (포트 8502)
- SQLite 데이터베이스에 로그 저장
- IP 주소, User Agent, 타임스탬프 등 메타데이터 수집

### 3. 관리자 로그 뷰어
- 📊 비디오 로그 페이지 추가 (관리자 전용)
- 로그 레벨, 비디오, 시간 범위 필터
- 통계 요약 및 에러 로그 하이라이트
- 페이징 지원 (50개씩)

## 배포 순서

### 1. 의존성 설치

```bash
# 컨테이너 내부에서
pip install flask flask-cors
```

### 2. 데이터베이스 마이그레이션

video_logs 테이블이 자동으로 생성됩니다 (init_complete_db() 실행 시).

기존 데이터베이스에 추가하려면:

```bash
docker exec futsal-team-platform python3 << 'EOF'
import sqlite3
from config.settings import db_config

conn = sqlite3.connect(db_config.DB_PATH)
cur = conn.cursor()

# video_logs 테이블 생성
cur.execute("""
    CREATE TABLE IF NOT EXISTS video_logs(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        video_id INTEGER NOT NULL,
        level TEXT CHECK(level IN ('info','warn','error')) DEFAULT 'info',
        event_type TEXT NOT NULL,
        message TEXT NOT NULL,
        details TEXT DEFAULT NULL,
        user_agent TEXT DEFAULT NULL,
        ip_address TEXT DEFAULT NULL,
        timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
        url TEXT DEFAULT NULL,
        FOREIGN KEY(video_id) REFERENCES videos(id)
    );
""")

# 인덱스 생성
cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_video_logs_video_id
    ON video_logs(video_id);
""")

cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_video_logs_timestamp
    ON video_logs(timestamp DESC);
""")

cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_video_logs_level
    ON video_logs(level);
""")

conn.commit()
conn.close()
print("✅ video_logs 테이블 생성 완료")
EOF
```

### 3. Nginx 설정 업데이트

```bash
# Nginx 설정 파일 복사
docker cp /futsal_proj/futsal.nginx.conf <nginx_container>:/etc/nginx/conf.d/futsal.conf

# Nginx 재시작
docker exec <nginx_container> nginx -s reload
```

### 4. Docker 이미지 재빌드 및 컨테이너 재시작

```bash
cd /futsal_proj

# 기존 컨테이너 중지 및 삭제
docker stop futsal-team-platform
docker rm futsal-team-platform

# 이미지 재빌드
docker build -t futsal-team-platform .

# 컨테이너 재시작 (포트 8502 추가)
docker run -d \
  --name futsal-team-platform \
  -p 8501:8501 \
  -p 8502:8502 \
  -v /futsal_proj/futsal.db:/app/futsal.db \
  -v /futsal_proj/uploads:/app/uploads \
  futsal-team-platform
```

## 로그 확인 방법

### 1. 웹 UI (관리자 전용)
- 관리자로 로그인
- 사이드바에서 "📊 비디오 로그" 선택
- 필터 및 통계 확인

### 2. 데이터베이스 직접 조회

```bash
docker exec futsal-team-platform sqlite3 /app/futsal.db << 'EOF'
.mode column
.headers on

-- 최근 에러 로그
SELECT
    video_id,
    event_type,
    message,
    timestamp
FROM video_logs
WHERE level = 'error'
ORDER BY timestamp DESC
LIMIT 10;

-- 비디오별 에러 건수
SELECT
    v.title,
    COUNT(*) as error_count
FROM video_logs vl
JOIN videos v ON vl.video_id = v.id
WHERE vl.level = 'error'
GROUP BY v.title
ORDER BY error_count DESC;
EOF
```

### 3. Flask API 로그 확인

```bash
# Flask 프로세스 로그
docker logs futsal-team-platform | grep "video log API"
```

### 4. Nginx 액세스 로그

```bash
# HLS 파일 요청 확인
docker exec <nginx_container> tail -f /var/log/nginx/access.log | grep "\.m3u8\|\.ts"
```

## 모니터링 쿼리

### 재생 성공률

```sql
SELECT
    video_id,
    COUNT(*) as total_attempts,
    SUM(CASE WHEN event_type = 'play' THEN 1 ELSE 0 END) as successful_plays,
    ROUND(SUM(CASE WHEN event_type = 'play' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as success_rate
FROM video_logs
WHERE event_type IN ('player_init', 'play', 'playback_error')
GROUP BY video_id;
```

### 에러 패턴 분석

```sql
SELECT
    json_extract(details, '$.code') as error_code,
    json_extract(details, '$.message') as error_message,
    COUNT(*) as occurrence_count
FROM video_logs
WHERE level = 'error' AND details IS NOT NULL
GROUP BY error_code, error_message
ORDER BY occurrence_count DESC;
```

### 사용자 에이전트 분석

```sql
SELECT
    CASE
        WHEN user_agent LIKE '%Mobile%' THEN 'Mobile'
        WHEN user_agent LIKE '%Tablet%' THEN 'Tablet'
        ELSE 'Desktop'
    END as device_type,
    COUNT(*) as view_count,
    SUM(CASE WHEN level = 'error' THEN 1 ELSE 0 END) as error_count
FROM video_logs
GROUP BY device_type;
```

## 트러블슈팅

### 로그가 수집되지 않는 경우

1. Flask API 실행 확인
```bash
docker exec futsal-team-platform ps aux | grep video_log_api
```

2. 포트 8502 접근 확인
```bash
curl http://localhost:8502/health
```

3. Nginx 프록시 설정 확인
```bash
docker exec <nginx_container> nginx -t
```

### 데이터베이스 오류

```bash
# 테이블 존재 확인
docker exec futsal-team-platform sqlite3 /app/futsal.db ".tables" | grep video_logs

# 테이블 구조 확인
docker exec futsal-team-platform sqlite3 /app/futsal.db ".schema video_logs"
```

## 성능 고려사항

- 로그는 비동기로 전송되어 플레이어 성능에 영향 없음
- 인덱스로 빠른 조회 보장
- 페이징으로 대용량 로그 처리
- 오래된 로그 주기적 정리 권장 (예: 90일 이상)

```sql
-- 90일 이상 된 로그 삭제
DELETE FROM video_logs
WHERE timestamp < datetime('now', '-90 days');
```
