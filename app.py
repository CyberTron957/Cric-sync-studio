from flask import Flask, render_template, request, redirect, url_for, send_from_directory, jsonify
import os
import hashlib
import json
import uuid
from werkzeug.utils import secure_filename

# Create upload folder
UPLOAD_FOLDER = 'uploads'
PROCESSED_FOLDER = 'processed'
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mp3', 'wav', 'json', 'txt'}

# Create directories if they don't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PROCESSED_FOLDER'] = PROCESSED_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max upload size

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_video_hash(video_path):
    """Generate a hash for the video file to check for duplicates"""
    hasher = hashlib.md5()
    with open(video_path, 'rb') as f:
        buf = f.read(65536)  # Read in 64k chunks
        while len(buf) > 0:
            hasher.update(buf)
            buf = f.read(65536)
    return hasher.hexdigest()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'video' not in request.files:
        return jsonify({'error': 'Missing video file'}), 400
    
    video_file = request.files['video']
    
    if video_file.filename == '':
        return jsonify({'error': 'No video file selected'}), 400
    
    if not allowed_file(video_file.filename):
        return jsonify({'error': 'Video file type not allowed'}), 400
    
    # Check if music file is provided
    has_music = 'music' in request.files and request.files['music'].filename != ''
    
    # Generate unique IDs for the files
    video_id = str(uuid.uuid4())
    
    # Save the video file
    video_filename = secure_filename(video_file.filename)
    video_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{video_id}_{video_filename}")
    video_file.save(video_path)
    
    # Process music file if provided
    music_path = None
    music_filename = None
    if has_music:
        music_file = request.files['music']
        if not allowed_file(music_file.filename):
            return jsonify({'error': 'Music file type not allowed'}), 400
        
        music_id = str(uuid.uuid4())
        music_filename = secure_filename(music_file.filename)
        music_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{music_id}_{music_filename}")
        music_file.save(music_path)
    
    # Create session data
    session_id = str(uuid.uuid4())
    session_data = {
        'session_id': session_id,
        'video_path': video_path,
        'video_filename': video_filename,
        'timestamps': []
    }
    
    # Add music data if provided
    if music_path:
        session_data['music_path'] = music_path
        session_data['music_filename'] = music_filename
    
    # Check for imported timestamps
    if 'timestamps' in request.files and request.files['timestamps'].filename != '':
        timestamps_file = request.files['timestamps']
        if allowed_file(timestamps_file.filename):
            # Save timestamps file
            ts_filename = secure_filename(timestamps_file.filename)
            ts_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{session_id}_{ts_filename}")
            timestamps_file.save(ts_path)
            
            # Parse timestamps based on file extension
            ext = ts_filename.rsplit('.', 1)[1].lower()
            try:
                if ext == 'json':
                    with open(ts_path, 'r') as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            session_data['timestamps'] = data
                        elif 'timestamps' in data and isinstance(data['timestamps'], list):
                            session_data['timestamps'] = data['timestamps']
                            # Check for durations if available
                            if 'durations' in data and isinstance(data['durations'], list):
                                session_data['durations'] = data['durations']
                elif ext == 'txt':
                    timestamps = []
                    with open(ts_path, 'r') as f:
                        for line in f:
                            line = line.strip()
                            try:
                                # Try parsing as seconds
                                timestamp = float(line)
                                timestamps.append(timestamp)
                            except ValueError:
                                # Try parsing as MM:SS format
                                try:
                                    parts = line.split(':')
                                    if len(parts) == 2:
                                        minutes, seconds = parts
                                        timestamp = int(minutes) * 60 + float(seconds)
                                        timestamps.append(timestamp)
                                except ValueError:
                                    # Skip lines that can't be parsed
                                    pass
                    session_data['timestamps'] = timestamps
            except Exception as e:
                print(f"Error parsing timestamps file: {str(e)}")
    
    # Save session data to a file
    with open(f"session_{session_id}.json", 'w') as f:
        json.dump(session_data, f)
    
    return jsonify({
        'success': True,
        'session_id': session_id,
        'redirect': url_for('editor', session_id=session_id)
    })

@app.route('/editor/<session_id>')
def editor(session_id):
    # Check if session exists
    session_file = f"session_{session_id}.json"
    if not os.path.exists(session_file):
        return redirect(url_for('index'))
    
    # Load session data
    with open(session_file, 'r') as f:
        session_data = json.load(f)
    
    # Prepare template data
    template_data = {
        'session_id': session_id,
        'video_filename': session_data['video_filename'],
        'has_timestamps': len(session_data.get('timestamps', [])) > 0,
        'has_music': 'music_filename' in session_data
    }
    
    if 'music_filename' in session_data:
        template_data['music_filename'] = session_data['music_filename']
    
    return render_template('editor.html', **template_data)

@app.route('/video/<session_id>')
def get_video(session_id):
    # Check if session exists
    session_file = f"session_{session_id}.json"
    if not os.path.exists(session_file):
        return jsonify({'error': 'Session not found'}), 404
    
    # Load session data
    with open(session_file, 'r') as f:
        session_data = json.load(f)
    
    video_path = session_data['video_path']
    directory = os.path.dirname(video_path)
    filename = os.path.basename(video_path)
    
    return send_from_directory(directory, filename)

@app.route('/music/<session_id>')
def get_music(session_id):
    # Check if session exists
    session_file = f"session_{session_id}.json"
    if not os.path.exists(session_file):
        return jsonify({'error': 'Session not found'}), 404
    
    # Load session data
    with open(session_file, 'r') as f:
        session_data = json.load(f)
    
    if 'music_path' not in session_data:
        return jsonify({'error': 'No music file in session'}), 404
    
    music_path = session_data['music_path']
    directory = os.path.dirname(music_path)
    filename = os.path.basename(music_path)
    
    return send_from_directory(directory, filename)

@app.route('/save_timestamps', methods=['POST'])
def save_timestamps():
    data = request.get_json()
    session_id = data.get('session_id')
    timestamps = data.get('timestamps', [])
    
    if not session_id:
        return jsonify({'error': 'No session ID provided'}), 400
    
    # Check if session exists
    session_file = f"session_{session_id}.json"
    if not os.path.exists(session_file):
        return jsonify({'error': 'Session not found'}), 404
    
    # Load session data
    with open(session_file, 'r') as f:
        session_data = json.load(f)
    
    # Update timestamps
    session_data['timestamps'] = timestamps
    
    # Save updated session data
    with open(session_file, 'w') as f:
        json.dump(session_data, f)
    
    return jsonify({'success': True})

@app.route('/export_timestamps/<session_id>')
def export_timestamps(session_id):
    # Check if session exists
    session_file = f"session_{session_id}.json"
    if not os.path.exists(session_file):
        return jsonify({'error': 'Session not found'}), 404
    
    # Load session data
    with open(session_file, 'r') as f:
        session_data = json.load(f)
    
    # Check if timestamps exist
    if not session_data.get('timestamps'):
        return jsonify({'error': 'No timestamps to export'}), 400
    
    # Create export file
    export_data = {
        'timestamps': session_data['timestamps']
    }
    
    # Add durations if available
    if 'durations' in session_data:
        export_data['durations'] = session_data['durations']
    
    # Create exports folder if it doesn't exist
    exports_dir = os.path.join(app.config['PROCESSED_FOLDER'], 'exports')
    os.makedirs(exports_dir, exist_ok=True)
    
    # Save export file
    export_path = os.path.join(exports_dir, f"timestamps_{session_id}.json")
    with open(export_path, 'w') as f:
        json.dump(export_data, f)
    
    return send_from_directory(exports_dir, f"timestamps_{session_id}.json", as_attachment=True)

@app.route('/trim_audio', methods=['POST'])
def trim_audio():
    data = request.get_json()
    session_id = data.get('session_id')
    start_time = data.get('start_time', 0)
    duration = data.get('duration', 0)
    
    if not session_id:
        return jsonify({'error': 'No session ID provided'}), 400
    
    if duration <= 0:
        return jsonify({'error': 'Invalid duration'}), 400
    
    # Check if session exists
    session_file = f"session_{session_id}.json"
    if not os.path.exists(session_file):
        return jsonify({'error': 'Session not found'}), 404
    
    # Load session data
    with open(session_file, 'r') as f:
        session_data = json.load(f)
    
    # Check if music file exists
    if 'music_path' not in session_data:
        return jsonify({'error': 'No music file in session'}), 400
    
    # Generate trimmed audio file
    original_music_path = session_data['music_path']
    trimmed_music_id = str(uuid.uuid4())
    trimmed_filename = f"trimmed_{trimmed_music_id}.aac"
    trimmed_path = os.path.join(app.config['UPLOAD_FOLDER'], trimmed_filename)
    
    # Import the trim_audio_file function
    from processing import trim_audio_file
    
    # Trim the audio file
    success = trim_audio_file(original_music_path, trimmed_path, start_time, duration)
    
    if not success:
        return jsonify({'error': 'Failed to trim audio file'}), 500
    
    # Update session data with new music file
    session_data['music_path'] = trimmed_path
    session_data['music_filename'] = f"Trimmed {session_data['music_filename']}"
    session_data['music_trimmed'] = True
    session_data['music_trim_info'] = {
        'original_path': original_music_path,
        'start_time': start_time,
        'duration': duration
    }
    
    # Save updated session data
    with open(session_file, 'w') as f:
        json.dump(session_data, f)
    
    return jsonify({
        'success': True,
        'trimmed_path': url_for('get_music', session_id=session_id)
    })

@app.route('/process_video', methods=['POST'])
def process_video():
    data = request.get_json()
    session_id = data.get('session_id')
    keep_original_audio = data.get('keep_original_audio', False)
    
    if not session_id:
        return jsonify({'error': 'No session ID provided'}), 400
    
    # Check if session exists
    session_file = f"session_{session_id}.json"
    if not os.path.exists(session_file):
        return jsonify({'error': 'Session not found'}), 404
    
    # Load session data
    with open(session_file, 'r') as f:
        session_data = json.load(f)
    
    # Check if timestamps are available
    if not session_data.get('timestamps'):
        return jsonify({'error': 'No timestamps marked'}), 400
    
    # Check if we have music when not using original audio only
    if not keep_original_audio and 'music_path' not in session_data:
        return jsonify({'error': 'No music file available for synchronization'}), 400
    
    # Start processing in a background task
    from processing import process_video_task
    task_id = process_video_task(session_id, keep_original_audio)
    
    return jsonify({
        'success': True,
        'task_id': task_id,
        'message': 'Video processing started'
    })

@app.route('/check_progress/<task_id>')
def check_progress(task_id):
    # Import the get_task_progress function from processing
    from processing import get_task_progress
    
    # Get the progress data
    progress_data = get_task_progress(task_id)
    
    return jsonify(progress_data)

@app.route('/download/<session_id>')
def download_video(session_id):
    # Check if processed file exists
    output_file = os.path.join(app.config['PROCESSED_FOLDER'], f"{session_id}_output.mp4")
    
    if not os.path.exists(output_file):
        return jsonify({'error': 'Processed file not found'}), 404
    
    return send_from_directory(app.config['PROCESSED_FOLDER'], f"{session_id}_output.mp4", as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)  