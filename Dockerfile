FROM python:3.9-slim

WORKDIR /app

# 시스템 패키지 업데이트 (streamlit-calendar 의존성 + FFmpeg 동영상 처리)
RUN apt-get update && apt-get install -y \
    build-essential \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
