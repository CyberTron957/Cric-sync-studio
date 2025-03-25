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

def trim_audio_file(input_file, output_file, start_time, duration):
    """Trim an audio file with FFmpeg"""
    try:
        cmd = (
            f'ffmpeg -i "{input_file}" -ss {start_time} -t {duration} '
            f'-c:a aac -b:a 192k -y "{output_file}" -loglevel error'
        )
        subprocess.run(cmd, shell=True)
        return True
    except Exception as e:
        print(f"Error trimming audio: {str(e)}")
        return False

def process_video(session_id, task_id, keep_original_audio=False):
    """Process a video based on session data"""
    try:
        # Load session data
        session_file = f"session_{session_id}.json"
        with open(session_file, 'r') as f:
            session_data = json.load(f)
        
        video_path = session_data['video_path']
        music_path = session_data.get('music_path')
        timestamps = session_data['timestamps']
        
        # Check if we have enough data
        if not timestamps:
            update_progress(task_id, 0, "failed", "No timestamps found")
            return False
        
        if keep_original_audio:
            update_progress(task_id, 10, "processing", "Using original audio from clips")
        else:
            update_progress(task_id, 10, "processing", "Detecting beats in music")
            # Get beat duration from music file
            beat_duration = detect_beats(music_path)
        
        update_progress(task_id, 20, "processing", "Extracting video clips")
        
        temp_clips = []
        total_clips = len(timestamps)
        
        # Create a temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Process each timestamp
            for i, timestamp in enumerate(timestamps):
                start_time = max(0, timestamp - 0.1)
                
                # Determine duration - either from beat or from session data
                if 'durations' in session_data and len(session_data['durations']) > i:
                    clip_duration = session_data['durations'][i]
                elif keep_original_audio:
                    clip_duration = 2.0  # Default duration when using original audio
                else:
                    clip_duration = beat_duration
                    
                temp_clip = os.path.join(temp_dir, f"temp_clip_{i}.mp4")
                
                # Extract video clip with its original audio
                video_cmd = (
                    f'ffmpeg -i "{video_path}" -ss {start_time} -t {clip_duration} '
                    f'-c:v libx264 -c:a aac -y "{temp_clip}" -loglevel error'
                )
                
                subprocess.run(video_cmd, shell=True)
                temp_clips.append(temp_clip)
                
                # Update progress
                progress = 20 + int(60 * ((i + 1) / total_clips))
                update_progress(task_id, progress, "processing", f"Extracting clip {i+1}/{total_clips}")
            
            # Create clips list file
            clips_list = os.path.join(temp_dir, "clips_list.txt")
            with open(clips_list, "w") as f:
                for clip in temp_clips:
                    f.write(f"file '{clip}'\n")
            
            update_progress(task_id, 80, "processing", "Finalizing output")
            
            # Output file paths
            output_dir = "processed"
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
                
            output_file = os.path.join(output_dir, f"{session_id}_output.mp4")
            
            # Combine clips with appropriate audio
            if keep_original_audio:
                # Just concatenate clips with their original audio
                cmd = (
                    f'ffmpeg -f concat -safe 0 -i "{clips_list}" '
                    f'-c copy "{output_file}" -y -loglevel error'
                )
            else:
                # Combine clips (with their original audio) and add music as a separate track
                cmd = (
                    f'ffmpeg -f concat -safe 0 -i "{clips_list}" -i "{music_path}" '
                    f'-filter_complex "[0:a][1:a]amix=inputs=2:duration=longest:weights=0.5 0.5[a]" '
                    f'-map 0:v -map "[a]" -c:v copy -c:a aac -shortest '
                    f'"{output_file}" -y -loglevel error'
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

def process_video_task(session_id, keep_original_audio=False):
    """Start a background task to process a video"""
    task_id = str(uuid.uuid4())
    
    # Initialize task progress
    update_progress(task_id, 0, "starting", "Starting video processing")
    
    # Start processing in a background thread
    thread = threading.Thread(target=process_video, args=(session_id, task_id, keep_original_audio))
    thread.daemon = True
    thread.start()
    
    return task_id 