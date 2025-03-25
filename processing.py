import os
import json
import time
import threading
import uuid
import subprocess
import librosa
import tempfile
import re

# Global dictionary to store task progress
tasks = {}

# Aspect ratio definitions
ASPECT_RATIOS = {
    'original': None,  # Keep original aspect ratio
    '16:9': (16, 9),
    '9:16': (9, 16),
    '1:1': (1, 1),
    '4:3': (4, 3),
    '1:1_in_9:16': 'special'  # Special case for 1:1 with 9:16 enclosure
}

# Text position definitions
TEXT_POSITIONS = {
    'top': {'x': '(w-text_w)/2', 'y': '20'},
    'bottom': {'x': '(w-text_w)/2', 'y': 'h-th-20'},
    'top_left': {'x': '20', 'y': '20'},
    'top_right': {'x': 'w-tw-20', 'y': '20'},
    'bottom_left': {'x': '20', 'y': 'h-th-20'},
    'bottom_right': {'x': 'w-tw-20', 'y': 'h-th-20'},
    'center': {'x': '(w-text_w)/2', 'y': '(h-text_h)/2'}
}

# Default text style
DEFAULT_TEXT_STYLE = {
    'font': 'Arial',
    'fontsize': 24,
    'fontcolor': 'white',
    'borderw': 2,
    'bordercolor': 'black'
}

def sanitize_text(text):
    """Sanitize text for FFmpeg command line"""
    # Replace single quotes with escaped single quotes
    text = text.replace("'", "'\\''")
    # Remove any characters that could cause issues
    text = re.sub(r'[^\w\s.,;:!?\'"\-+=]', '', text)
    return text

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

def get_video_dimensions(video_path):
    """Get video dimensions using FFprobe"""
    try:
        cmd = (
            f'ffprobe -v error -select_streams v:0 -show_entries stream=width,height '
            f'-of csv=p=0:s=x "{video_path}"'
        )
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"ffprobe command failed: {result.stderr}")
        
        dimensions = result.stdout.strip().split('x')
        return int(dimensions[0]), int(dimensions[1])
    except Exception as e:
        print(f"Error getting video dimensions: {str(e)}")
        return None, None

def calculate_crop_params(width, height, aspect_ratio):
    """Calculate crop parameters based on video dimensions and target aspect ratio"""
    if aspect_ratio is None:
        # Keep original aspect ratio
        return None
    
    if aspect_ratio == 'special':
        # Special case: 1:1 with 9:16 enclosure
        # This means creating a 1:1 crop centered in a 9:16 frame with black padding
        if width >= height:
            # Landscape or square video - crop to a square first
            new_width = height
            new_height = height
            x_offset = int((width - new_width) / 2)
            y_offset = 0
            
            # Calculate padding for 9:16 aspect ratio
            square_to_vertical = new_width * 16 / 9  # Calculate the height needed for 9:16
            padding = int((square_to_vertical - new_height) / 2)
            
            return {
                'crop': f"crop={new_width}:{new_height}:{x_offset}:{y_offset}",
                'pad': f"pad={new_width}:{int(square_to_vertical)}:0:{padding}:black"
            }
        else:
            # Portrait video - check if it's already close to 9:16
            current_ratio = height / width
            target_ratio = 16 / 9
            
            if abs(current_ratio - target_ratio) < 0.1:
                # Already close to 9:16, just crop to square in the center
                new_width = width
                new_height = width
                x_offset = 0
                y_offset = int((height - new_height) / 2)
                
                return {
                    'crop': f"crop={new_width}:{new_height}:{x_offset}:{y_offset}",
                    'pad': None  # No padding needed, it already fits 9:16
                }
            else:
                # Not 9:16, crop to square and add padding
                new_width = width
                new_height = width
                x_offset = 0
                y_offset = int((height - new_height) / 2)
                
                # Calculate padding for 9:16 aspect ratio
                square_to_vertical = new_width * 16 / 9  # Calculate the height needed for 9:16
                padding = int((square_to_vertical - new_height) / 2)
                
                return {
                    'crop': f"crop={new_width}:{new_height}:{x_offset}:{y_offset}",
                    'pad': f"pad={new_width}:{int(square_to_vertical)}:0:{padding}:black"
                }
    
    # Standard aspect ratio calculation
    target_ratio = aspect_ratio[0] / aspect_ratio[1]
    current_ratio = width / height
    
    if current_ratio > target_ratio:
        # Video is wider than target, crop width
        new_width = int(height * target_ratio)
        new_height = height
        x_offset = int((width - new_width) / 2)
        y_offset = 0
    else:
        # Video is taller than target, crop height
        new_width = width
        new_height = int(width / target_ratio)
        x_offset = 0
        y_offset = int((height - new_height) / 2)
    
    return {
        'crop': f"crop={new_width}:{new_height}:{x_offset}:{y_offset}",
        'pad': None
    }

def create_text_overlay_filter(text, position, style=None):
    """Create FFmpeg drawtext filter for text overlay"""
    if not text:
        return None
    
    # Get position coordinates
    pos = TEXT_POSITIONS.get(position, TEXT_POSITIONS['bottom'])
    
    # Merge provided style with defaults
    style = style or {}
    text_style = {**DEFAULT_TEXT_STYLE, **style}
    
    # Sanitize text
    safe_text = sanitize_text(text)
    
    # Build the drawtext filter
    filter_text = (
        f"drawtext=text='{safe_text}'"
        f":fontfile=/System/Library/Fonts/Supplemental/{text_style['font']}.ttf"
        f":fontsize={text_style['fontsize']}"
        f":fontcolor={text_style['fontcolor']}"
        f":borderw={text_style['borderw']}"
        f":bordercolor={text_style['bordercolor']}"
        f":x={pos['x']}:y={pos['y']}"
        f":box=1:boxcolor=black@0.5"
    )
    
    return filter_text

def process_video(session_id, task_id, keep_original_audio=False, crop_option='original', text_overlays=None):
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
        
        # Get video dimensions for crop calculation
        width, height = get_video_dimensions(video_path)
        if width is None or height is None:
            update_progress(task_id, 0, "failed", "Could not determine video dimensions")
            return False
        
        # Get aspect ratio configuration
        aspect_ratio = ASPECT_RATIOS.get(crop_option)
        crop_params = calculate_crop_params(width, height, aspect_ratio) if aspect_ratio else None
        
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
                
                # Build the FFmpeg command based on crop option
                if crop_params:
                    # Extract video clip with its original audio and apply cropping
                    video_filters = []
                    
                    # Add crop filter if it exists
                    if crop_params.get('crop'):
                        video_filters.append(crop_params['crop'])
                    
                    # Add padding filter if it exists (for special 1:1 in 9:16 case)
                    if crop_params.get('pad'):
                        video_filters.append(crop_params['pad'])
                    
                    # Join all filters with comma
                    filter_chain = ','.join(video_filters)
                    
                    video_cmd = (
                        f'ffmpeg -i "{video_path}" -ss {start_time} -t {clip_duration} '
                        f'-vf "{filter_chain}" -c:v libx264 -c:a aac -y "{temp_clip}" -loglevel error'
                    )
                else:
                    # No cropping, just extract with original dimensions
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
            
            update_progress(task_id, 80, "processing", "Applying text overlays and finalizing output")
            
            # Output file paths
            output_dir = "processed"
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
                
            # Add crop info to filename
            crop_suffix = f"_{crop_option.replace(':', '_')}" if crop_option != 'original' else ""
            output_file = os.path.join(output_dir, f"{session_id}{crop_suffix}_output.mp4")
            
            # Prepare for text overlay
            temp_combined = os.path.join(temp_dir, "combined.mp4")
            
            # Combine clips with appropriate audio
            if keep_original_audio:
                # Just concatenate clips with their original audio
                concat_cmd = (
                    f'ffmpeg -f concat -safe 0 -i "{clips_list}" '
                    f'-c copy "{temp_combined}" -y -loglevel error'
                )
            else:
                # Combine clips (with their original audio) and add music as a separate track
                concat_cmd = (
                    f'ffmpeg -f concat -safe 0 -i "{clips_list}" -i "{music_path}" '
                    f'-filter_complex "[0:a][1:a]amix=inputs=2:duration=longest:weights=0.5 0.5[a]" '
                    f'-map 0:v -map "[a]" -c:v copy -c:a aac -shortest '
                    f'"{temp_combined}" -y -loglevel error'
                )
            
            subprocess.run(concat_cmd, shell=True)
            
            # Apply text overlays if provided
            if text_overlays and len(text_overlays) > 0:
                text_filters = []
                
                for overlay in text_overlays:
                    if overlay.get('text'):
                        text_filter = create_text_overlay_filter(
                            overlay.get('text', ''),
                            overlay.get('position', 'bottom'),
                            overlay.get('style', {})
                        )
                        if text_filter:
                            text_filters.append(text_filter)
                
                if text_filters:
                    # Apply all text overlays to the combined video
                    text_filter_chain = ','.join(text_filters)
                    text_cmd = (
                        f'ffmpeg -i "{temp_combined}" -vf "{text_filter_chain}" '
                        f'-c:v libx264 -c:a copy -y "{output_file}" -loglevel error'
                    )
                    subprocess.run(text_cmd, shell=True)
                else:
                    # No text filters, just copy the combined file
                    os.rename(temp_combined, output_file)
            else:
                # No text overlays, just use the combined file
                os.rename(temp_combined, output_file)
            
            # Update session data with output file
            session_data['output_file'] = output_file
            session_data['crop_option'] = crop_option
            if text_overlays:
                session_data['text_overlays'] = text_overlays
            with open(session_file, 'w') as f:
                json.dump(session_data, f)
            
            update_progress(task_id, 100, "completed", "Video processing completed")
            
            return True
    except Exception as e:
        update_progress(task_id, 0, "failed", f"Error: {str(e)}")
        return False

def process_video_task(session_id, keep_original_audio=False, crop_option='original', text_overlays=None):
    """Start a background task to process a video"""
    task_id = str(uuid.uuid4())
    
    # Initialize task progress
    update_progress(task_id, 0, "starting", "Starting video processing")
    
    # Start processing in a background thread
    thread = threading.Thread(target=process_video, args=(session_id, task_id, keep_original_audio, crop_option, text_overlays))
    thread.daemon = True
    thread.start()
    
    return task_id 