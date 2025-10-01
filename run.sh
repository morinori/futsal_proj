#!/bin/bash

# 옵션 처리
case "$1" in
    "rebuild"|"--rebuild")
        echo "🔄 리빌드 모드 실행..."
        exec ./rebuild.sh
        exit 0
        ;;
    "restart"|"--restart")
        echo "🔄 컨테이너 재시작 중..."
        docker restart futsal-team-platform
        echo "✅ 재시작 완료!"
        docker logs --tail 20 futsal-team-platform
        exit 0
        ;;
    "stop"|"--stop")
        echo "🛑 컨테이너 중지 중..."
        docker stop futsal-team-platform
        echo "✅ 중지 완료!"
        exit 0
        ;;
    "logs"|"--logs")
        echo "📋 로그 출력 (Ctrl+C로 종료)..."
        docker logs -f futsal-team-platform
        exit 0
        ;;
    "reset"|"--reset")
        echo "🗑️ 컨테이너 삭제 후 재생성..."
        docker stop futsal-team-platform 2>/dev/null
        docker rm futsal-team-platform 2>/dev/null
        # 새로 생성으로 계속 진행
        ;;
esac

# 컨테이너가 실행 중인지 확인
if docker ps -q -f name=futsal-team-platform | grep -q .; then
    echo "✅ Futsal 앱이 이미 실행 중입니다."
    echo ""
    echo "사용 가능한 명령:"
    echo "  ./run.sh restart  - 재시작"
    echo "  ./run.sh stop     - 중지"
    echo "  ./run.sh logs     - 로그 보기"
    echo "  ./run.sh rebuild  - 리빌드"
    echo "  ./run.sh reset    - 삭제 후 재생성"
    exit 0
fi

# 중지된 컨테이너가 있으면 재시작
if docker ps -aq -f name=futsal-team-platform | grep -q .; then
    echo "🔄 기존 컨테이너 재시작 중..."
    docker start futsal-team-platform
    echo "✅ 재시작 완료!"
    docker logs --tail 20 futsal-team-platform
    exit 0
fi

# 컨테이너가 없으면 새로 생성
echo "🚀 새 컨테이너 생성 중..."
docker run -d \
  --name futsal-team-platform \
  -p 8501:8501 \
  -v /futsal_proj/futsal.db:/app/futsal.db \
  -v /futsal_proj/uploads:/app/uploads \
  --restart unless-stopped \
  --log-driver json-file \
  --log-opt max-size=10m \
  --log-opt max-file=3 \
  futsal-team-platform

if [ $? -eq 0 ]; then
    echo "✅ Futsal 앱이 시작되었습니다!"
    echo ""
    echo "📍 접속 주소: http://localhost:8501"
    echo ""
    echo "최근 로그:"
    sleep 2
    docker logs --tail 20 futsal-team-platform
else
    echo "❌ 컨테이너 시작 실패!"
    exit 1
fi
