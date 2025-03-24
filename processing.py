import os
import json
import time
import threading
import uuid
import subprocess
import librosa
import tempfile

# Global dictionary to store task progress
tasks = {}

def detect_beats(music_file):
    """Detect beats in the music file and return the average beat duration"""
    try:
        y, sr = librosa.load(music_file)
        
        # Use librosa's beat tracking
        tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
        
        if len(beat_frames) > 1:
            beat_times = librosa.frames_to_time(beat_frames, sr=sr)
            beat_intervals = [beat_times[i+1] - beat_times[i] for i in range(len(beat_times)-1)]
            return sum(beat_intervals) / len(beat_intervals)
        return 0.4285  # Default
    except Exception as e:
        print(f"Error detecting beats: {str(e)}")
        return 0.4285  # Default beat duration

def update_progress(task_id, progress, status="processing", message=""):
    """Update the progress of a task"""
    tasks[task_id] = {
        'progress': progress,
        'status': status,
        'message': message,
        'timestamp': time.time()
    }

def get_task_progress(task_id):
    """Get the progress of a task"""
    return tasks.get(task_id, {
        'progress': 0,
        'status': 'unknown',
        'message': 'Task not found',
        'timestamp': time.time()
    })

def process_video(session_id, task_id):
    """Process a video based on session data"""
    try:
        # Load session data
        session_file = f"session_{session_id}.json"
        with open(session_file, 'r') as f:
            session_data = json.load(f)
        
        video_path = session_data['video_path']
        music_path = session_data['music_path']
        timestamps = session_data['timestamps']
        
        # Check if we have enough data
        if not timestamps:
            update_progress(task_id, 0, "failed", "No timestamps found")
            return False
        
        update_progress(task_id, 10, "processing", "Detecting beats in music")
        
        # Get beat duration
        beat_duration = detect_beats(music_path)
        
        update_progress(task_id, 20, "processing", "Extracting video clips")
        
        temp_clips = []
        total_clips = len(timestamps)
        
        # Create a temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Process each timestamp
            for i, timestamp in enumerate(timestamps):
                start_time = max(0, timestamp - 0.1)
                temp_clip = os.path.join(temp_dir, f"temp_clip_{i}.mp4")
                
                # Extract clip with FFmpeg
                cmd = (
                    f'ffmpeg -i "{video_path}" -ss {start_time} -t {beat_duration} '
                    f'-c:v libx264 -an -y "{temp_clip}" -loglevel error'
                )
                subprocess.run(cmd, shell=True)
                temp_clips.append(temp_clip)
                
                # Update progress
                progress = 20 + int(60 * ((i + 1) / total_clips))
                update_progress(task_id, progress, "processing", f"Extracting clip {i+1}/{total_clips}")
            
            # Create clips list file
            clips_list = os.path.join(temp_dir, "clips_list.txt")
            with open(clips_list, "w") as f:
                for clip in temp_clips:
                    f.write(f"file '{clip}'\n")
            
            update_progress(task_id, 80, "processing", "Combining clips with music")
            
            # Output file
            output_dir = "processed"
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
                
            output_file = os.path.join(output_dir, f"{session_id}_output.mp4")
            
            # Combine clips with music
            cmd = (
                f'ffmpeg -f concat -safe 0 -i "{clips_list}" -i "{music_path}" '
                f'-c:v copy -c:a aac -shortest "{output_file}" -y -loglevel error'
            )
            subprocess.run(cmd, shell=True)
            
            # Update session data with output file
            session_data['output_file'] = output_file
            with open(session_file, 'w') as f:
                json.dump(session_data, f)
            
            update_progress(task_id, 100, "completed", "Video processing completed")
            
            return True
    except Exception as e:
        update_progress(task_id, 0, "failed", f"Error: {str(e)}")
        return False

def process_video_task(session_id):
    """Start a background task to process a video"""
    task_id = str(uuid.uuid4())
    
    # Initialize task progress
    update_progress(task_id, 0, "starting", "Starting video processing")
    
    # Start processing in a background thread
    thread = threading.Thread(target=process_video, args=(session_id, task_id))
    thread.daemon = True
    thread.start()
    
    return task_id 