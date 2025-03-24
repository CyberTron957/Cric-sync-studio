# Cricket Video Editor

A web application for creating synchronized cricket highlight reels with music. The application allows users to mark important moments in cricket videos and automatically extracts clips synced to beats in the provided music track.

## Features

- Upload cricket video footage and music tracks
- Video player with controls for precise navigation
- Mark timestamps of important moments
- Automatic beat detection in music
- Create clips synced to music beats
- Download the final highlight reel

## Requirements

- Python 3.7+
- FFmpeg (must be installed and available in PATH)
- Required Python packages (see requirements.txt)

## Installation

1. Clone the repository
2. Install FFmpeg (if not already installed)
3. Install Python dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

1. Run the application:
   ```
   python app.py
   ```
2. Open your browser and go to `http://localhost:5000`
3. Upload a cricket video and music file
4. Mark timestamps of important moments in the video
5. Create and download your highlight reel

## Keyboard Shortcuts

While using the editor:
- **Space**: Play/Pause video
- **M**: Mark timestamp
- **A/Left Arrow**: Jump back 5 seconds
- **D/Right Arrow**: Jump forward 5 seconds
- **J**: Jump back 30 seconds
- **K**: Jump forward 30 seconds
- **+/-**: Change playback speed
- **R**: Remove last marker

## License

MIT License 