FROM python:3.9-slim

RUN apt-get update && apt-get install -y \
    ffmpeg \
    fonts-dejavu \
    python3-tk \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN pip install -e ".[test]"

CMD ["md2video"]