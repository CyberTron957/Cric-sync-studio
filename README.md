# Cricket Video Editor

A web application for creating synchronized cricket highlight reels with music. The application allows users to mark important moments in cricket videos and automatically extracts clips synced to beats in the provided music track.

## Features

- Upload cricket video footage and music tracks
- Video player with controls for precise navigation
- Mark timestamps of important moments
- Automatic beat detection in music
- Create clips synced to music beats
- Original audio from video clips is preserved along with music
- Import and export timestamps for reuse
- Trim audio files after uploading
- Option to use original video audio instead of music
- Video cropping in multiple aspect ratios (16:9, 9:16, 1:1, 4:3)
- Special 1:1 crop with 9:16 enclosure (square video centered in vertical format)
- Preview processed videos before downloading

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
   or use the provided script:
   ```
   ./run.sh
   ```
2. Open your browser and go to `http://localhost:5000`
3. Upload a cricket video and (optionally) a music file
4. Optionally import timestamps from a previous session
5. Mark timestamps of important moments in the video
6. Trim the music file if needed
7. Choose an aspect ratio for the output video
8. Choose to use only original audio (no music) if desired
9. Create your highlight reel
10. Preview the processed video to ensure it meets your requirements
11. Download the final highlight reel

## Aspect Ratio Options

The application offers several aspect ratio options for output videos:
- **Original**: Keep the original video aspect ratio
- **Landscape (16:9)**: Standard widescreen format
- **Portrait (9:16)**: Vertical video format for mobile/social media
- **Square (1:1)**: Square video for platforms like Instagram
- **Classic (4:3)**: Traditional TV format
- **Square in Vertical (1:1 in 9:16)**: Square video centered in a 9:16 frame with black padding

All cropping operations maintain the center of the frame by default.

## Audio Options

When creating highlights with music, the application:
- Preserves the original audio from each video clip
- Mixes it with the background music at equal volume levels
- Provides an option to use only the original audio without any music

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

## Timestamp Import/Export

The application supports importing and exporting timestamps in the following formats:
- **JSON**: JSON files with a "timestamps" array
- **TXT**: Plain text files with one timestamp per line (seconds or MM:SS format)

## License

MIT License 