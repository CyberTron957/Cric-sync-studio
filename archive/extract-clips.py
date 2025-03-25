import cv2
import subprocess
import sys
import os
import hashlib

def detect_beats(music_file):
    """Detect beats in the music file and return the average beat duration"""
    try:
        import librosa
        import scipy
        y, sr = librosa.load(music_file)
        
        # Use librosa's own hann window function instead of scipy's
        tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
        
        if len(beat_frames) > 1:
            beat_times = librosa.frames_to_time(beat_frames, sr=sr)
            beat_intervals = [beat_times[i+1] - beat_times[i] for i in range(len(beat_times)-1)]
            return sum(beat_intervals) / len(beat_intervals)
        return 0.4285  # Default
    except Exception as e:
        print(f"Error detecting beats: {str(e)}")
        print("Using default beat duration")
        return 0.4285  # Default beat duration

def get_video_hash(video_path):
    """Generate a hash for the video file to check for duplicates"""
    hasher = hashlib.md5()
    with open(video_path, 'rb') as f:
        buf = f.read()
        hasher.update(buf)
    return hasher.hexdigest()

def display_progress_bar(current, total, bar_length=50):
    """Display a progress bar in the terminal"""
    percent = int(100 * (current / total))
    arrow = '=' * int(bar_length * percent / 100)
    spaces = ' ' * (bar_length - len(arrow))
    
    sys.stdout.write(f"\r[{arrow}{spaces}] {percent}%")
    sys.stdout.flush()

def process_with_progress(video_path, timestamps, beat_duration, output_file, music_path):
    """Process the video with a progress bar"""
    print("Processing clips:")
    total_clips = len(timestamps)
    
    temp_clips = []
    for i, timestamp in enumerate(timestamps):
        start_time = max(0, timestamp - 0.1)
        temp_clip = f"temp_clip_{i}.mp4"
        
        # Extract each clip with FFmpeg
        cmd = (
            f'ffmpeg -i "{video_path}" -ss {start_time} -t {beat_duration} '
            f'-c:v libx264 -an -y "{temp_clip}" -loglevel error'
        )
        subprocess.run(cmd, shell=True)
        temp_clips.append(temp_clip)
        
        display_progress_bar(i + 1, total_clips)
    
    # Create a file list for FFmpeg
    with open("clips_list.txt", "w") as f:
        for clip in temp_clips:
            f.write(f"file '{clip}'\n")
    
    # Combine all clips
    print("\nCombining clips with music...")
    cmd = (
        f'ffmpeg -f concat -safe 0 -i clips_list.txt -i "{music_path}" '
        f'-c:v copy -c:a aac -shortest "{output_file}" -y -loglevel error'
    )
    subprocess.run(cmd, shell=True)
    
    # Clean up temporary files
    for clip in temp_clips:
        if os.path.exists(clip):
            os.remove(clip)
    if os.path.exists("clips_list.txt"):
        os.remove("clips_list.txt")
        
    print(f"\nFinal reel with music created at: {output_file}")

import cv2
import subprocess
import sys
import os
import hashlib
import json
import argparse

# ... existing code ...

def save_timestamps(timestamps, video_path):
    """Save timestamps to a JSON file"""
    filename = os.path.splitext(os.path.basename(video_path))[0] + "_timestamps.json"
    data = {
        "video_path": video_path,
        "timestamps": timestamps
    }
    with open(filename, 'w') as f:
        json.dump(data, f)
    print(f"Timestamps saved to {filename}")
    return filename

def load_timestamps(filename):
    """Load timestamps from a JSON file"""
    try:
        with open(filename, 'r') as f:
            data = json.load(f)
        print(f"Loaded {len(data['timestamps'])} timestamps for video: {data['video_path']}")
        return data['video_path'], data['timestamps']
    except Exception as e:
        print(f"Error loading timestamps: {str(e)}")
        return None, []

def main():
    # Use argparse for better command line argument handling
    parser = argparse.ArgumentParser(description="Video clip extraction tool with music synchronization")
    parser.add_argument("video_path", nargs="?", help="Path to the video file")
    parser.add_argument("music_path", nargs="?", help="Path to the music file")
    parser.add_argument("--beat-duration", type=float, help="Manual beat duration in seconds")
    parser.add_argument("--load-timestamps", help="Load timestamps from a JSON file")
    parser.add_argument("--extract-only", action="store_true", help="Skip marking and extract using loaded timestamps")
    args = parser.parse_args()

    global video_path, music_path, beat_duration
    
    # Initialize variables
    video_path = None
    music_path = None
    beat_duration = 0.4285  # Default
    timestamps = []
    
    # Handle loading timestamps from file
    if args.load_timestamps:
        loaded_video_path, loaded_timestamps = load_timestamps(args.load_timestamps)
        if loaded_video_path:
            video_path = loaded_video_path if not args.video_path else args.video_path
            timestamps = loaded_timestamps
            
            # If extract-only flag is set, skip to extraction
            if args.extract_only and args.music_path:
                music_path = args.music_path
                # Detect beat duration if music path is provided
                beat_duration = detect_beats(music_path)
                if args.beat_duration:
                    beat_duration = args.beat_duration
                    
                output_file = "cricket_reel_with_music.mp4"
                process_with_progress(video_path, timestamps, beat_duration, output_file, music_path)
                return
    
    # Use command line arguments if provided
    if args.video_path:
        video_path = args.video_path
    if args.music_path:
        music_path = args.music_path
        # Use detect_beats function to set beat_duration
        beat_duration = detect_beats(music_path)
        print(f"Detected beat duration: {beat_duration:.2f} seconds")
    if args.beat_duration:
        beat_duration = args.beat_duration

    # Check if video file exists and can be opened
    if not video_path:
        print("Error: No video file specified")
        parser.print_help()
        sys.exit(1)
        
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error: Could not open video file: {video_path}")
        sys.exit(1)

    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps if fps > 0 else 0

    print(f"Video loaded: {os.path.basename(video_path)}")
    print(f"Duration: {duration:.2f} seconds ({total_frames} frames @ {fps:.2f} FPS)")
    print("Controls:")
    print("  SPACE: Mark timestamp")
    print("  a: Jump back 5 seconds")
    print("  d: Jump forward 5 seconds")
    print("  s: Jump back 1 second")
    print("  w: Jump forward 1 second")
    print("  j: Jump back 30 seconds")
    print("  k: Jump forward 30 seconds")
    print("  p: Pause/Resume playback")
    print("  r: Remove last marked timestamp")
    print("  S: Save timestamps to file")
    print("  q: Quit and extract clips")

    # Create a window and set its properties
    cv2.namedWindow("Video", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Video", 960, 540)

    # Enhanced UI during video playback
    position = 0
    paused = False
    playback_speed = 1.0
    show_help = True
    last_time = cv2.getTickCount() / cv2.getTickFrequency()
    
    while position < total_frames:
        current_time = cv2.getTickCount() / cv2.getTickFrequency()
        delta_time = current_time - last_time
        last_time = current_time
        
        # Set the exact frame position
        cap.set(cv2.CAP_PROP_POS_FRAMES, position)
        ret, frame = cap.read()
        if not ret:
            break
        
        current_video_time = position / fps
        total_time = total_frames / fps
        
        # Calculate progress bar
        progress_width = int(frame.shape[1] * 0.8)
        progress_x = int(frame.shape[1] * 0.1)
        progress_y = frame.shape[0] - 50
        progress_height = 10
        
        # Draw progress bar background
        cv2.rectangle(frame, (progress_x, progress_y), 
                     (progress_x + progress_width, progress_y + progress_height), 
                     (50, 50, 50), -1)
        
        # Draw progress indicator
        progress = int(progress_width * (current_video_time / total_time))
        cv2.rectangle(frame, (progress_x, progress_y), 
                     (progress_x + progress, progress_y + progress_height), 
                     (0, 255, 0), -1)
        
        # Add timestamps as markers on the progress bar
        for t in timestamps:
            marker_x = progress_x + int(progress_width * (t / total_time))
            cv2.line(frame, (marker_x, progress_y - 5), 
                    (marker_x, progress_y + progress_height + 5), (0, 255, 255), 2)
        
        # Add time overlay on frame
        cv2.putText(frame, f"Time: {current_video_time:.2f}s / {total_time:.2f}s", (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Show timestamp markers indicator
        if timestamps:
            timestamp_indicator = "Marked: " + " ".join([f"{t:.2f}s" for t in timestamps[-3:]])
            cv2.putText(frame, timestamp_indicator, (10, frame.shape[0] - 70), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            cv2.putText(frame, f"Total markers: {len(timestamps)}", (10, frame.shape[0] - 100), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        
        # Display speed and paused status
        status_text = f"{'PAUSED' if paused else 'Speed: ' + str(playback_speed) + 'x'}"
        cv2.putText(frame, status_text, (frame.shape[1] - 200, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255) if paused else (255, 165, 0), 2)
        
        # Show help overlay if enabled
        if show_help:
            help_y = 70
            help_texts = [
                "SPACE: Mark timestamp", 
                "a/d: Jump ±5 sec", 
                "s/w: Jump ±1 sec",
                "j/k: Jump ±30 sec",
                "p: Pause/Resume",
                "r: Remove last mark",
                "+/-: Change speed",
                "S: Save timestamps",
                "h: Toggle help",
                "q: Quit & extract"
            ]
            
            # Add semi-transparent background for help text
            overlay = frame.copy()
            cv2.rectangle(overlay, (frame.shape[1] - 210, 50), 
                         (frame.shape[1] - 20, help_y + 30*len(help_texts)), 
                         (0, 0, 0), -1)
            cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
            
            for text in help_texts:
                cv2.putText(frame, text, (frame.shape[1] - 200, help_y), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
                help_y += 30
        
        cv2.imshow("Video", frame)
        
        # Process key presses
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord(' '):
            timestamps.append(current_video_time)
            print(f"Marked at {current_video_time:.2f} sec")
        elif key == ord('q'):
            break
        elif key == ord('a'):  # Jump back 5 seconds
            position = max(0, position - int(fps * 5))
            continue
        elif key == ord('d'):  # Jump forward 5 seconds
            position = min(total_frames - 1, position + int(fps * 5))
            continue
        elif key == ord('s'):  # Jump back 1 second
            position = max(0, position - int(fps))
            continue
        elif key == ord('w'):  # Jump forward 1 second
            position = min(total_frames - 1, position + int(fps))
            continue
        elif key == ord('j'):  # Jump back 30 seconds
            position = max(0, position - int(fps * 30))
            continue
        elif key == ord('k'):  # Jump forward 30 seconds
            position = min(total_frames - 1, position + int(fps * 30))
            continue
        elif key == ord('p'):  # Pause/Resume playback
            paused = not paused
            print("Playback " + ("paused" if paused else "resumed"))
            # Reset the timer when unpausing to avoid jumps
            if not paused:
                last_time = cv2.getTickCount() / cv2.getTickFrequency()
        elif key == ord('r'):  # Remove last timestamp
            if timestamps:
                removed = timestamps.pop()
                print(f"Removed timestamp at {removed:.2f} sec")
            else:
                print("No timestamps to remove")
        elif key == ord('S'):  # Save timestamps (capital S)
            filename = save_timestamps(timestamps, video_path)
            print(f"Timestamps saved to {filename}")
        elif key == ord('+') or key == ord('='):  # Increase playback speed
            playback_speed = min(4.0, playback_speed + 0.25)
            print(f"Playback speed: {playback_speed}x")
        elif key == ord('-') or key == ord('_'):  # Decrease playback speed
            playback_speed = max(0.25, playback_speed - 0.25)
            print(f"Playback speed: {playback_speed}x")
        elif key == ord('h'):  # Toggle help overlay
            show_help = not show_help
            
        # Only advance position if not paused
        if not paused:
            # Calculate frames to advance based on playback speed and elapsed time
            frames_to_advance = int(fps * delta_time * playback_speed)
            frames_to_advance = max(1, frames_to_advance)  # Always advance at least 1 frame
            position += frames_to_advance
            
        # Add a small delay to process events and reduce CPU usage
        cv2.waitKey(1)

    cap.release()
    cv2.destroyAllWindows()

    # Use FFmpeg to trim and combine segments with music
    if timestamps and music_path:
        output_file = "cricket_reel_with_music.mp4"
        
        # Ask whether to save timestamps before processing
        if not args.load_timestamps:
            save_timestamps(timestamps, video_path)
        
        # Use the progress-enabled processing function
        process_with_progress(video_path, timestamps, beat_duration, output_file, music_path)
    elif timestamps:
        print("No music file specified. Saving timestamps only.")
        save_timestamps(timestamps, video_path)
    else:
        print("No timestamps marked. No clips extracted.")

if __name__ == "__main__":
    main()