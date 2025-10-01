#!/bin/bash

echo "🔄 Docker 이미지 재빌드 시작..."

# 기존 컨테이너 중지 및 삭제
if docker ps -q -f name=futsal-team-platform | grep -q .; then
    echo "⏹️  기존 컨테이너 중지 중..."
    docker stop futsal-team-platform
fi

if docker ps -aq -f name=futsal-team-platform | grep -q .; then
    echo "🗑️  기존 컨테이너 삭제 중..."
    docker rm futsal-team-platform
fi

# Docker 이미지 재빌드
echo "🏗️  Docker 이미지 빌드 중 (FFmpeg 포함)..."
docker build -t futsal-team-platform .

if [ $? -eq 0 ]; then
    echo "✅ 빌드 완료!"
    echo ""
    echo "🚀 컨테이너 시작 중..."

    # 새 컨테이너 실행
    docker run -d \
      --name futsal-team-platform \
      -p 8501:8501 \
      -v $(pwd):/app \
      --restart unless-stopped \
      --log-driver json-file \
      --log-opt max-size=10m \
      --log-opt max-file=3 \
      futsal-team-platform

    echo "✅ Futsal 앱이 시작되었습니다!"
    echo "📍 접속 주소: http://localhost:8501"
    echo ""
    echo "📋 FFmpeg 설치 확인:"
    docker exec futsal-team-platform ffmpeg -version | head -n 1
else
    echo "❌ 빌드 실패!"
    exit 1
fi