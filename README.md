# Cricket Video Editor (CricSync)

A web application for creating synchronized cricket highlight reels with music. The application allows users to mark important moments in cricket videos and automatically extracts clips synced to beats in the provided music track.

## Features

- User authentication with registration and login
- Freemium subscription model with Free and Pro plans
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
- Text overlay capabilities for adding titles, captions, and annotations

## Subscription Plans

### Free Plan
- Storage: Limited to 3 projects
- Video Length: Up to 2 minutes per highlight reel
- Resolution: Up to 720p export
- Basic Features:
  - Mark timestamps manually
  - Basic video cropping (16:9 only)
- Watermark: cricsync.fun watermark on exported videos

### Pro Plan ($9.99/month)
- Storage: Up to 20 projects
- Video Length: Up to 10 minutes per highlight reel
- Resolution: Up to 1080p export
- All aspect ratio options
- Save custom templates for text/graphics
- Export without watermark
- Import external timestamps

### Premium Plan (Coming Soon - $19.99/month)
- Storage: Unlimited projects
- Video Length: Unlimited length per highlight reel
- Resolution: Up to 4K export
- Premium Features:
  - All Pro features
  - Automatic highlight detection (AI-assisted)
  - Special effects library (slow motion, transitions)
  - Advanced color grading options
  - Team collaboration (share projects with teammates)
  - Batch processing (create multiple videos at once)
  - Custom branding options
  - Priority processing queue

## Requirements

- Python 3.7+
- FFmpeg (must be installed and available in PATH)
- SQLite3 for user database
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
3. Register a new account or log in
4. Choose your subscription plan (Free or Pro)
5. Upload a cricket video and (optionally) a music file
6. Optionally import timestamps from a previous session
7. Mark timestamps of important moments in the video
8. Trim the music file if needed
9. Add text overlays if desired
10. Choose an aspect ratio for the output video (based on your subscription level)
11. Choose to use only original audio (no music) if desired
12. Create your highlight reel
13. Preview the processed video to ensure it meets your requirements
14. Download the final highlight reel

## User Management

- Create an account with username, email, and password
- Access your projects from the profile page
- View subscription status and usage information
- Upgrade from Free to Pro plan at any time
- Cancel or renew subscriptions from the profile page

## Aspect Ratio Options

The application offers several aspect ratio options for output videos based on subscription level:

**Free Plan**:
- **Original**: Keep the original video aspect ratio
- **Landscape (16:9)**: Standard widescreen format

**Pro and Premium Plans**:
- All Free plan options plus:
- **Portrait (9:16)**: Vertical video format for mobile/social media
- **Square (1:1)**: Square video for platforms like Instagram
- **Classic (4:3)**: Traditional TV format
- **Square in Vertical (1:1 in 9:16)**: Square video centered in a 9:16 frame with black padding

All cropping operations maintain the center of the frame by default.

## Text Overlay Options

The application allows adding multiple text overlays to your videos:
- Add titles, captions, scores, or other annotations
- Position text at various locations (top, bottom, corners, center)
- Customize font family, size, and color
- Add optional border/outline to improve readability
- Preview text appearance before applying

You can add different text overlays with different styles positioned at different locations throughout the video.

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