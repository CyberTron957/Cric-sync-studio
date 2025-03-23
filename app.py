from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import cv2
import subprocess
import librosa
import numpy as np
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['TEMP_FOLDER'] = 'temp'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size

# Ensure upload directory exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    print(f"Creating upload directory: {app.config['UPLOAD_FOLDER']}")
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Ensure temp directory exists
if not os.path.exists(app.config['TEMP_FOLDER']):
    print(f"Creating temp directory: {app.config['TEMP_FOLDER']}")
    os.makedirs(app.config['TEMP_FOLDER'])
    
print(f"Upload directory: {os.path.abspath(app.config['UPLOAD_FOLDER'])}")
print(f"Temp directory: {os.path.abspath(app.config['TEMP_FOLDER'])}")

ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mp3', 'wav'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def detect_beats(music_file):
    """Detect beats in the music file and return the average beat duration"""
    try:
        y, sr = librosa.load(music_file)
        tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
        if len(beat_frames) > 1:
            beat_times = librosa.frames_to_time(beat_frames, sr=sr)
            beat_intervals = [beat_times[i+1] - beat_times[i] for i in range(len(beat_times)-1)]
            return sum(beat_intervals) / len(beat_intervals)
        return 0.4285  # Default
    except Exception as e:
        print(f"Error in beat detection: {e}")
        return 0.4285  # Default beat duration

def process_video(video_path, music_path, timestamps, output_path):
    """Process video clips and combine them with music"""
    try:
        # Detect beat duration from music
        beat_duration = detect_beats(music_path)
        print(f"Detected beat duration: {beat_duration}")
        
        # Use the app's temp folder
        temp_dir = app.config['TEMP_FOLDER']
        os.makedirs(temp_dir, exist_ok=True)
        
        # Extract clips
        print("Processing clips:")
        temp_clips = []
        for i, timestamp in enumerate(timestamps):
            start_time = max(0, float(timestamp) - 0.1)
            temp_clip = os.path.join(temp_dir, f"temp_clip_{i}.mp4")
            print(f"Extracting clip {i+1}/{len(timestamps)} at {start_time:.2f}s")
            
            # Extract clip using FFmpeg
            cmd = f'ffmpeg -i "{video_path}" -ss {start_time} -t {beat_duration} -c:v libx264 -an -y "{temp_clip}" -loglevel error'
            print(f"Command: {cmd}")
            subprocess.run(cmd, shell=True)
            
            if not os.path.exists(temp_clip):
                print(f"ERROR: Clip extraction failed for {temp_clip}")
                return False
                
            # Store the actual path, not relative to uploads
            temp_clips.append(os.path.abspath(temp_clip))
        
        # Create a file list for FFmpeg
        list_path = os.path.join(temp_dir, "clips_list.txt")
        print(f"Creating clips list at {list_path}")
        with open(list_path, "w") as f:
            for clip in temp_clips:
                f.write(f"file '{clip}'\n")
        
        # Combine all clips
        print("\nCombining clips with music...")
        cmd = f'ffmpeg -f concat -safe 0 -i "{list_path}" -i "{music_path}" -c:v copy -c:a aac -shortest "{output_path}" -y -loglevel error'
        print(f"Command: {cmd}")
        subprocess.run(cmd, shell=True)
        
        if not os.path.exists(output_path):
            print(f"ERROR: Failed to create output video: {output_path}")
            return False
        
        print(f"\nFinal reel with music created at: {output_path}")
        
        # Clean up temporary files (but keep the directory)
        for clip in temp_clips:
            if os.path.exists(clip):
                os.remove(clip)
        if os.path.exists(list_path):
            os.remove(list_path)
            
        return True
    except Exception as e:
        import traceback
        print(f"Error processing video: {e}")
        print(traceback.format_exc())
        return False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'video' not in request.files and 'audio' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    result = {}
    
    if 'video' in request.files:
        video = request.files['video']
        if video and allowed_file(video.filename):
            video_filename = secure_filename(video.filename)
            video_path = os.path.join(app.config['UPLOAD_FOLDER'], video_filename)
            video.save(video_path)
            result['video'] = video_filename
    
    if 'audio' in request.files:
        audio = request.files['audio']
        if audio and allowed_file(audio.filename):
            audio_filename = secure_filename(audio.filename)
            audio_path = os.path.join(app.config['UPLOAD_FOLDER'], audio_filename)
            audio.save(audio_path)
            result['audio'] = audio_filename
    
    return jsonify(result)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/process_video', methods=['POST'])
def process_video_endpoint():
    data = request.json
    timestamps = data.get('timestamps', [])
    video_file = data.get('video_file', '')
    audio_file = data.get('audio_file', '')
    
    if not timestamps or not video_file or not audio_file:
        return jsonify({'error': 'Missing required data'}), 400
    
    # Use absolute paths to avoid any path confusion
    video_path = os.path.abspath(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(video_file)))
    audio_path = os.path.abspath(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(audio_file)))
    output_filename = f'final_{secure_filename(video_file)}'
    output_path = os.path.abspath(os.path.join(app.config['UPLOAD_FOLDER'], output_filename))
    
    print(f"Processing video:")
    print(f"Video file: {video_file}")
    print(f"Video path: {video_path}")
    print(f"Audio file: {audio_file}")
    print(f"Audio path: {audio_path}")
    print(f"Output: {output_filename}")
    print(f"Output path: {output_path}")
    print(f"Timestamps ({len(timestamps)}): {timestamps}")
    
    # Verify files exist
    if not os.path.exists(video_path):
        return jsonify({'error': f'Video file not found: {video_path}'}), 400
    if not os.path.exists(audio_path):
        return jsonify({'error': f'Audio file not found: {audio_path}'}), 400
    
    # Process the video
    if process_video(video_path, audio_path, timestamps, output_path):
        return jsonify({
            'status': 'success',
            'output_file': output_filename
        })
    else:
        return jsonify({'error': 'Failed to process video'}), 500

@app.route('/save_timestamps', methods=['POST'])
def save_timestamps():
    data = request.json
    timestamps = data.get('timestamps', [])
    video_file = data.get('video_file', '')
    
    print(f"Saved timestamps for {video_file}: {timestamps}")
    return jsonify({'status': 'success', 'timestamps': timestamps})

if __name__ == '__main__':
    app.run(debug=True, port=5100) 