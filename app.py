from flask import Flask, render_template, request, redirect, url_for, send_from_directory, jsonify
import os
import hashlib
import json
import uuid
from werkzeug.utils import secure_filename

# Create upload folder
UPLOAD_FOLDER = 'uploads'
PROCESSED_FOLDER = 'processed'
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mp3', 'wav'}

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
    if 'video' not in request.files or 'music' not in request.files:
        return jsonify({'error': 'Missing video or music file'}), 400
    
    video_file = request.files['video']
    music_file = request.files['music']
    
    if video_file.filename == '' or music_file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if not allowed_file(video_file.filename) or not allowed_file(music_file.filename):
        return jsonify({'error': 'File type not allowed'}), 400
    
    # Generate unique IDs for the files
    video_id = str(uuid.uuid4())
    music_id = str(uuid.uuid4())
    
    # Save the files
    video_filename = secure_filename(video_file.filename)
    music_filename = secure_filename(music_file.filename)
    
    video_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{video_id}_{video_filename}")
    music_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{music_id}_{music_filename}")
    
    video_file.save(video_path)
    music_file.save(music_path)
    
    # Create session data
    session_id = str(uuid.uuid4())
    session_data = {
        'session_id': session_id,
        'video_path': video_path,
        'music_path': music_path,
        'video_filename': video_filename,
        'music_filename': music_filename,
        'timestamps': []
    }
    
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
    
    return render_template('editor.html', 
                          session_id=session_id,
                          video_filename=session_data['video_filename'],
                          music_filename=session_data['music_filename'])

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

@app.route('/process_video', methods=['POST'])
def process_video():
    data = request.get_json()
    session_id = data.get('session_id')
    
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
    
    # Start processing in a background task
    from processing import process_video_task
    task_id = process_video_task(session_id)
    
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