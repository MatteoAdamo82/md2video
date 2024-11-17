FROM python:3.9-slim

# Installa le dipendenze di sistema necessarie
RUN apt-get update && apt-get install -y \
    ffmpeg \
    fonts-dejavu \
    python3-tk \
    libavcodec-extra \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copia e installa i requisiti
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia il codice sorgente
COPY src/ ./src/

# Crea le directory necessarie
RUN mkdir -p content/posts video_scripts video_output

# Imposta il comando di avvio
CMD ["python", "-m", "src.video_generator"]