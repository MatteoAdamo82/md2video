FROM python:3.9-slim

RUN apt-get update && apt-get install -y \
    ffmpeg \
    fonts-dejavu \
    python3-tk \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
RUN mkdir -p content/posts video_scripts video_output

CMD ["python", "-m", "src.cli"]