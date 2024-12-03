# MD2Video

MD2Video is a Python application that automatically converts Markdown blog posts into narrated videos. It processes Markdown content, generates XML scripts, and creates videos with text overlays, background music, and automated speech synthesis.

## Features

- Converts Markdown posts to narrated videos automatically
- Generates intermediate XML script files that can be manually edited
- Supports custom backgrounds
- Text-to-speech synthesis in multiple languages (default: Italian)
- CLI interface for easy operation
- Configurable video and audio settings
- Docker support for easy deployment

## Installation

### Prerequisites

- Docker and Docker Compose
- Git

### Basic Installation

1. Clone the repository:
```bash
git clone https://github.com/MatteoAdamo82/md2video.git
cd md2video
```

2. Create a `.env` file from the template:
```bash
cp .env.example .env
```

3. Build and start the Docker container:
```bash
docker-compose build
docker-compose up -d
```

### Manual Installation (Without Docker)

1. Install system dependencies:
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y ffmpeg fonts-dejavu python3-tk

# macOS
brew install ffmpeg
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
.\venv\Scripts\activate   # Windows
```

3. Install Python dependencies:
```bash
pip install -r requirements.txt
pip install -e ".[test]"  # If you want to run tests
```

## Configuration

The application uses environment variables for configuration. Key settings in `.env`:

```ini
# Directory paths
CONTENT_DIR=./content        # Location of Markdown posts
SCRIPT_DIR=./video_scripts   # Where XML scripts are saved
OUTPUT_DIR=./video_output    # Where videos are saved

# Video settings
VIDEO_WIDTH=1920             # Video width in pixels
VIDEO_HEIGHT=1080            # Video height in pixels
VIDEO_FPS=24                 # Frames per second
VIDEO_BITRATE=4000k          # Video bitrate

# Audio settings
AUDIO_FPS=44100              # Audio sample rate
AUDIO_BITRATE=192k           # Audio bitrate
SPEECH_LANG=it               # Text-to-speech language
```

### Development \ Test Environment
```ini
# Environment
APP_ENV=dev

# Development TTS Settings
DEV_TTS_PROVIDER=gtts # Uses Google TTS
DEV_TTS_LANG=it
```

### Production Environment
```ini
# Environment
APP_ENV=prod

# Production TTS Settings
PROD_TTS_PROVIDER=azure   # Uses Azure Speech Services
PROD_TTS_LANG=it-IT
AZURE_SPEECH_KEY=your_key_here
AZURE_SPEECH_REGION=westeurope
AZURE_VOICE_NAME=it-IT-IsabellaNeural
```

## Usage

### Interactive CLI Commands

1. Launch interactive CLI:
```bash
docker-compose run --rm md2video
```

Once inside the CLI interface:

1. `script` - Generate XML scripts from recent Markdown posts
2. `video` - Generate videos from existing XML scripts
3. `generate` - Generate both scripts and videos from posts
4. `help` - Show available commands
5. `quit` - Exit the program

### Environment-based Execution (Default configuration)

- Development mode uses Google TTS for simpler testing and development
- Production mode uses Azure Speech Services for higher quality output
- Switch between environments by setting `APP_ENV` in your .env file

Example production setup:
```bash
# Set production environment
echo "APP_ENV=prod" > .env

# Add Azure credentials
echo "AZURE_SPEECH_KEY=your_key" >> .env
echo "AZURE_SPEECH_REGION=westeurope" >> .env

# Run the application
docker-compose run --rm md2video
```

### Direct CLI commands:

1. Generate XML scripts from Markdown posts:
```bash
docker-compose run --rm md2video script
```

2Generate video from an existing XML script:
```bash
docker-compose run --rm md2video video
```

3. Generate both scripts and videos in one command:
```bash
docker-compose run --rm md2video generate
```

### Clean up Docker environment:
```bash
docker-compose down --remove-orphans
```

## Project Structure

```
md2video/
├── content/                       # Input Markdown posts
├── src/
│   ├── tts/                       # TTS providers implementation
│   │   ├── providers/
│   │   │   ├── base.py
│   │   │   ├── gtts.py
│   │   │   └── azure.py
│   │   └── factory.py
│   ├── processors/                # Main processors
│   │   ├── blog_processor.py
│   │   ├── script_processor.py
│   │   └── video_processor.py
│   ├── config.py                   # Configuration management
│   ├── cli.py                     # CLI interface
│   └── video_generator.py         # Video generator
├── video_output/                  # Generated videos
│   ├── assets/                    # Custom backgrounds
│   ├── temp/                      # Temporary files
│   └── videos/                    # Final videos
├── video_scripts/                 # Generated XML scripts
└── tests/                         # Test files
```

## Development

### Running Tests

1. Run all tests with coverage:
```bash
docker-compose run --rm test
```

2. Run specific test files:
```bash
docker-compose run --rm md2video pytest tests/test_blog_processor.py
```

3. Run tests with specific markers:
```bash
docker-compose run --rm md2video pytest -m "not slow"
```

### Test Coverage

The test suite includes unit tests for all major components:
- `test_blog_processor.py`: Tests for Markdown processing
- `test_script_processor.py`: Tests for XML script generation
- `test_video_processor.py`: Tests for video generation
- `test_base_processor.py`: Tests for base processor functionality
- `test_video_generator.py`: Tests for the main generator class

### XML Script Format

The application generates and processes XML scripts in the following format:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<script version="1.0">
    <metadata>
        <title>Video Title</title>
        <url>https://example.com/post</url>
        <date>2024-11-20</date>
    </metadata>
    <content>
        <section level="1" type="intro" background="intro_bg.png">
            <heading>Introduction</heading>
            <speech pause="0.5">Introduction text</speech>
        </section>
    </content>
</script>
```

## Custom Backgrounds

1. Supported formats: PNG, JPG
2. Recommended dimensions: 1920x1080 pixels
3. Place background images in: `video_output/assets/`
4. Reference in XML using: `background="image_name.png"`

## Troubleshooting

### Common Issues

1. **FFmpeg Missing**
```bash
# Install FFmpeg
sudo apt-get install ffmpeg  # Ubuntu/Debian
brew install ffmpeg         # macOS
```

2. **Permission Issues**
```bash
# Fix directory permissions
sudo chown -R $USER:$USER content video_output video_scripts
```

3. **Memory Issues**
```bash
# Adjust Docker memory limit in docker-compose.yml
services:
  md2video:
    mem_limit: 2g
```

### Logging

- Logs are written to console and `video_output/md2video.log`
- Set `LOG_LEVEL` in `.env` to adjust verbosity (DEBUG, INFO, WARNING, ERROR)

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Run tests to ensure they pass
4. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
5. Push to the branch (`git push origin feature/AmazingFeature`)
6. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Uses `gTTS` or `Azure Speech Services` for text-to-speech synthesis
- Uses `moviepy` for video processing
- Uses `python-frontmatter` for Markdown processing
