#!/bin/bash

echo "🗑️  동영상 데이터 초기화 시작..."

# Docker 컨테이너 이름
CONTAINER_NAME="futsal-streamlit"

# 1. 데이터베이스에서 videos 테이블 데이터 삭제
echo "📊 데이터베이스에서 동영상 레코드 삭제 중..."
docker exec $CONTAINER_NAME python3 -c "
import sqlite3
conn = sqlite3.connect('/app/team_platform.db')
cur = conn.cursor()
cur.execute('DELETE FROM videos')
conn.commit()
affected = cur.rowcount
conn.close()
print(f'삭제된 레코드: {affected}개')
"

# 2. 동영상 파일 삭제
echo "📁 동영상 원본 파일 삭제 중..."
docker exec $CONTAINER_NAME rm -rf /app/uploads/videos/original/*
docker exec $CONTAINER_NAME ls /app/uploads/videos/original/ 2>/dev/null || echo "원본 파일 디렉토리 정리 완료"

# 3. HLS 변환 파일 삭제
echo "🎬 HLS 변환 파일 삭제 중..."
docker exec $CONTAINER_NAME rm -rf /app/uploads/videos/hls/*
docker exec $CONTAINER_NAME ls /app/uploads/videos/hls/ 2>/dev/null || echo "HLS 파일 디렉토리 정리 완료"

# 4. 썸네일 삭제
echo "🖼️  썸네일 파일 삭제 중..."
docker exec $CONTAINER_NAME rm -rf /app/uploads/thumbnails/*
docker exec $CONTAINER_NAME ls /app/uploads/thumbnails/ 2>/dev/null || echo "썸네일 디렉토리 정리 완료"

echo ""
echo "✅ 동영상 데이터 초기화 완료!"
echo ""
echo "📊 현재 상태 확인:"

# 데이터베이스 확인
docker exec $CONTAINER_NAME python3 -c "
import sqlite3
conn = sqlite3.connect('/app/team_platform.db')
cur = conn.cursor()
cur.execute('SELECT COUNT(*) FROM videos')
count = cur.fetchone()[0]
conn.close()
print(f'  - 동영상 레코드: {count}개')
"

# 파일 개수 확인
echo "  - 원본 파일: $(docker exec $CONTAINER_NAME find /app/uploads/videos/original -type f 2>/dev/null | wc -l)개"
echo "  - HLS 디렉토리: $(docker exec $CONTAINER_NAME find /app/uploads/videos/hls -maxdepth 1 -mindepth 1 -type d 2>/dev/null | wc -l)개"
echo "  - 썸네일: $(docker exec $CONTAINER_NAME find /app/uploads/thumbnails -type f 2>/dev/null | wc -l)개"

echo ""
echo "🎉 초기화가 완료되었습니다!"