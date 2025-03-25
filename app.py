from flask import Flask, render_template, request, redirect, url_for, send_from_directory, jsonify, session, flash
import os
import hashlib
import json
import uuid
import sqlite3
from werkzeug.utils import secure_filename
from functools import wraps
from datetime import datetime

# Create upload folder
UPLOAD_FOLDER = 'uploads'
PROCESSED_FOLDER = 'processed'
USER_DB = 'user_database.db'
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mp3', 'wav', 'json', 'txt'}

# Create directories if they don't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PROCESSED_FOLDER'] = PROCESSED_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max upload size
app.secret_key = os.environ.get('SECRET_KEY', 'cricket_video_editor_secret_key')  # Secret key for sessions

# Initialize user database
def init_db():
    conn = sqlite3.connect(USER_DB)
    cursor = conn.cursor()
    
    # Check if users table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
    table_exists = cursor.fetchone() is not None
    
    if not table_exists:
        # Create users table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            subscription_type TEXT DEFAULT 'free',
            subscription_status TEXT DEFAULT 'active',
            subscription_end_date TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
    else:
        # Check if subscription_type column exists
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'subscription_type' not in columns:
            # Add subscription_type column if it doesn't exist
            cursor.execute('ALTER TABLE users ADD COLUMN subscription_type TEXT DEFAULT "free"')
        
        if 'subscription_status' not in columns:
            # Add subscription_status column if it doesn't exist
            cursor.execute('ALTER TABLE users ADD COLUMN subscription_status TEXT DEFAULT "active"')
        
        if 'subscription_end_date' not in columns:
            # Add subscription_end_date column if it doesn't exist
            cursor.execute('ALTER TABLE users ADD COLUMN subscription_end_date TIMESTAMP')
    
    # Create user_sessions table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        session_id TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    # Create subscription_history table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS subscription_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        subscription_type TEXT NOT NULL,
        start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        end_date TIMESTAMP,
        payment_status TEXT,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    conn.commit()
    conn.close()

# Initialize the database when app starts
init_db()

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

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

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validate input
        if not username or not email or not password:
            flash('All fields are required', 'danger')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('register.html')
        
        # Hash the password
        password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
        
        # Connect to database
        conn = sqlite3.connect(USER_DB)
        cursor = conn.cursor()
        
        # Check if username or email already exists
        cursor.execute('SELECT id FROM users WHERE username = ? OR email = ?', (username, email))
        if cursor.fetchone():
            conn.close()
            flash('Username or email already exists', 'danger')
            return render_template('register.html')
        
        # Insert new user
        try:
            cursor.execute(
                'INSERT INTO users (username, email, password) VALUES (?, ?, ?)',
                (username, email, password_hash)
            )
            conn.commit()
            
            # Get the user ID for session
            cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
            user_id = cursor.fetchone()[0]
            
            # Log the user in
            session['user_id'] = user_id
            session['username'] = username
            
            conn.close()
            
            # Redirect to subscription selection
            return redirect(url_for('select_subscription'))
            
        except Exception as e:
            conn.close()
            flash(f'An error occurred: {str(e)}', 'danger')
            return render_template('register.html')
        
    return render_template('register.html')

@app.route('/select_subscription', methods=['GET', 'POST'])
@login_required
def select_subscription():
    if request.method == 'POST':
        plan = request.form.get('plan')
        
        if plan not in ['free', 'pro']:
            flash('Invalid plan selected', 'danger')
            return redirect(url_for('select_subscription'))
        
        # Connect to database
        conn = sqlite3.connect(USER_DB)
        cursor = conn.cursor()
        
        try:
            # Update user's subscription
            cursor.execute('''
                UPDATE users 
                SET subscription_type = ?, subscription_status = 'active'
                WHERE id = ?
            ''', (plan, session['user_id']))
            
            # Record subscription in history
            cursor.execute('''
                INSERT INTO subscription_history (user_id, subscription_type, payment_status)
                VALUES (?, ?, ?)
            ''', (session['user_id'], plan, 'completed' if plan == 'free' else 'pending'))
            
            conn.commit()
            
            if plan == 'pro':
                # For pro plan, redirect to payment page
                return redirect(url_for('payment'))
            else:
                # For free plan, redirect to home
                flash('Welcome to Cricket Video Editor! Your free account is ready.', 'success')
                return redirect(url_for('index'))
                
        except Exception as e:
            conn.rollback()
            flash(f'An error occurred: {str(e)}', 'danger')
            return redirect(url_for('select_subscription'))
        finally:
            conn.close()
    
    return render_template('subscription.html')

@app.route('/payment')
@login_required
def payment():
    # Get user's subscription info
    conn = sqlite3.connect(USER_DB)
    cursor = conn.cursor()
    cursor.execute('SELECT subscription_type FROM users WHERE id = ?', (session['user_id'],))
    subscription_type = cursor.fetchone()[0]
    conn.close()
    
    if subscription_type != 'pro':
        flash('Invalid subscription type', 'danger')
        return redirect(url_for('select_subscription'))
    
    # TODO: Integrate with payment processor (e.g., Stripe)
    # For now, we'll just show a placeholder payment page
    return render_template('payment.html')

def check_subscription_limits(user_id):
    """Check if user has reached their subscription limits"""
    conn = sqlite3.connect(USER_DB)
    cursor = conn.cursor()
    
    # Get user's subscription type
    cursor.execute('SELECT subscription_type FROM users WHERE id = ?', (user_id,))
    subscription_type = cursor.fetchone()[0]
    
    # Get user's project count
    cursor.execute('''
        SELECT COUNT(DISTINCT session_id) 
        FROM user_sessions 
        WHERE user_id = ?
    ''', (user_id,))
    project_count = cursor.fetchone()[0]
    
    conn.close()
    
    # Check limits based on subscription type
    if subscription_type == 'free' and project_count >= 3:
        return False, "You've reached the limit of 3 projects for the free plan. Upgrade to Pro for more projects!"
    
    return True, None

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        # Validate input
        if not username or not password:
            flash('Username and password are required', 'danger')
            return render_template('login.html')
        
        # Hash the password
        password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
        
        # Connect to database
        conn = sqlite3.connect(USER_DB)
        cursor = conn.cursor()
        
        # Find user
        cursor.execute('SELECT id, username FROM users WHERE username = ? AND password = ?', 
                      (username, password_hash))
        user = cursor.fetchone()
        
        if user:
            # Set session
            session['user_id'] = user[0]
            session['username'] = user[1]
            
            # Record the login session in the database
            session_id = str(uuid.uuid4())
            cursor.execute('INSERT INTO user_sessions (user_id, session_id) VALUES (?, ?)',
                          (user[0], session_id))
            conn.commit()
            
            conn.close()
            
            # Get the next URL if provided
            next_url = request.args.get('next', url_for('index'))
            
            flash('Login successful!', 'success')
            return redirect(next_url)
        else:
            conn.close()
            flash('Invalid username or password', 'danger')
            return render_template('login.html')
        
    return render_template('login.html')

@app.route('/logout')
def logout():
    # Clear session
    session.pop('user_id', None)
    session.pop('username', None)
    flash('You have been logged out successfully', 'success')
    return redirect(url_for('index'))

@app.route('/profile')
@login_required
def profile():
    # Get user info from database
    conn = sqlite3.connect(USER_DB)
    cursor = conn.cursor()
    
    # Get user profile along with subscription info
    cursor.execute('''
        SELECT username, email, created_at, subscription_type, subscription_status, subscription_end_date 
        FROM users WHERE id = ?
    ''', (session['user_id'],))
    user_data = cursor.fetchone()
    
    # Get user's projects
    cursor.execute('''
        SELECT session_id FROM user_sessions 
        WHERE user_id = ? 
        ORDER BY created_at DESC
    ''', (session['user_id'],))
    
    sessions = []
    for row in cursor.fetchall():
        session_file = f"session_{row[0]}.json"
        if os.path.exists(session_file):
            with open(session_file, 'r') as f:
                try:
                    session_data = json.load(f)
                    sessions.append({
                        'session_id': row[0],
                        'video_filename': session_data.get('video_filename', 'Unknown'),
                        'has_music': 'music_filename' in session_data,
                        'timestamp_count': len(session_data.get('timestamps', []))
                    })
                except:
                    pass
    
    # Get subscription history
    cursor.execute('''
        SELECT subscription_type, start_date, end_date, payment_status
        FROM subscription_history
        WHERE user_id = ?
        ORDER BY start_date DESC
    ''', (session['user_id'],))
    subscription_history = cursor.fetchall()
    
    conn.close()
    
    # Calculate project limit and usage based on subscription
    subscription_type = user_data[3] if user_data[3] else 'free'
    project_limit = get_subscription_limit(subscription_type, 'projects')
    project_count = len(sessions)
    
    # Calculate usage percentage - handle case where limit is very large
    if project_limit > 1000000:  # Effectively unlimited
        project_usage_percent = min(100, project_count)
    else:
        project_usage_percent = min(100, int(project_count / project_limit * 100)) if project_limit > 0 else 100
    
    return render_template('profile.html', 
                          user=user_data, 
                          sessions=sessions, 
                          subscription_history=subscription_history,
                          project_limit=project_limit,
                          project_count=project_count,
                          project_usage_percent=project_usage_percent)

# New function to get subscription limits
def get_subscription_limit(subscription_type, limit_type):
    """Get the limit value for a specific subscription type and limit type"""
    limits = {
        'free': {
            'projects': 3,
            'video_length': 120,  # 2 minutes in seconds
            'resolution': '720p',
            'aspect_ratios': ['original', '16:9'],
            'watermark': True
        },
        'pro': {
            'projects': 20,
            'video_length': 600,  # 10 minutes in seconds
            'resolution': '1080p',
            'aspect_ratios': ['original', '16:9', '9:16', '1:1', '4:3', '1:1_in_9:16'],
            'watermark': False
        },
        'premium': {
            'projects': 9999999,  # Effectively unlimited
            'video_length': 9999999,  # Effectively unlimited
            'resolution': '4k',
            'aspect_ratios': ['original', '16:9', '9:16', '1:1', '4:3', '1:1_in_9:16'],
            'watermark': False
        }
    }
    
    subscription = limits.get(subscription_type, limits['free'])
    return subscription.get(limit_type, limits['free'][limit_type])

@app.route('/')
def index():
    return render_template('index.html')

# Add a route middleware to enforce login for all pages except login/register
@app.before_request
def require_login():
    # Public routes that don't require login
    public_routes = ['login', 'register', 'static', 'index']
    
    # Check if the route is public or if user is logged in
    if request.endpoint not in public_routes and 'user_id' not in session:
        flash('Please log in to access this feature.', 'warning')
        return redirect(url_for('login', next=request.path))

@app.route('/process_payment', methods=['POST'])
@login_required
def process_payment():
    # TODO: Integrate with actual payment processor
    # For now, we'll just simulate a successful payment
    
    conn = sqlite3.connect(USER_DB)
    cursor = conn.cursor()
    
    try:
        # Update subscription history
        cursor.execute('''
            UPDATE subscription_history 
            SET payment_status = 'completed'
            WHERE user_id = ? AND subscription_type = 'pro' AND payment_status = 'pending'
            AND id = (SELECT MAX(id) FROM subscription_history WHERE user_id = ? AND subscription_type = 'pro')
        ''', (session['user_id'], session['user_id']))
        
        conn.commit()
        
        flash('Payment successful! Welcome to the Pro plan.', 'success')
        return redirect(url_for('index'))
        
    except Exception as e:
        conn.rollback()
        flash(f'An error occurred: {str(e)}', 'danger')
        return redirect(url_for('payment'))
    finally:
        conn.close()

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'video' not in request.files:
        return jsonify({'error': 'Missing video file'}), 400
    
    video_file = request.files['video']
    
    if video_file.filename == '':
        return jsonify({'error': 'No video file selected'}), 400
    
    if not allowed_file(video_file.filename):
        return jsonify({'error': 'Video file type not allowed'}), 400
    
    # Check subscription limits if user is logged in
    if 'user_id' in session:
        can_upload, error_message = check_subscription_limits(session['user_id'])
        if not can_upload:
            return jsonify({'error': error_message}), 403
    
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
    
    # If user is logged in, associate this session with their account
    if 'user_id' in session:
        try:
            conn = sqlite3.connect(USER_DB)
            cursor = conn.cursor()
            cursor.execute('INSERT INTO user_sessions (user_id, session_id) VALUES (?, ?)',
                          (session['user_id'], session_id))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error associating session with user: {str(e)}")
    
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
@login_required
def process_video():
    data = request.get_json()
    session_id = data.get('session_id')
    keep_original_audio = data.get('keep_original_audio', False)
    crop_option = data.get('crop_option', 'original')
    text_overlays = data.get('text_overlays', [])
    
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
    
    # Get user's subscription type
    conn = sqlite3.connect(USER_DB)
    cursor = conn.cursor()
    cursor.execute('SELECT subscription_type FROM users WHERE id = ?', (session['user_id'],))
    user_data = cursor.fetchone()
    conn.close()
    
    subscription_type = user_data[0] if user_data and user_data[0] else 'free'
    
    # Calculate total video length based on timestamps
    timestamps = session_data.get('timestamps', [])
    total_video_length = sum(session_data.get('durations', [1] * len(timestamps)))
    
    # Check video length limit
    max_video_length = get_subscription_limit(subscription_type, 'video_length')
    if total_video_length > max_video_length:
        return jsonify({
            'error': f'Your {subscription_type} plan allows videos up to {max_video_length/60:.1f} minutes. Your project is {total_video_length/60:.1f} minutes. Please upgrade your plan or reduce the number of clips.'
        }), 403
    
    # Check aspect ratio limit
    allowed_ratios = get_subscription_limit(subscription_type, 'aspect_ratios')
    if crop_option not in allowed_ratios:
        return jsonify({
            'error': f'Your {subscription_type} plan does not support the {crop_option} aspect ratio. Please upgrade to access all aspect ratios.'
        }), 403
    
    # Check if crop option is valid
    from processing import ASPECT_RATIOS
    if crop_option not in ASPECT_RATIOS:
        return jsonify({'error': 'Invalid crop option'}), 400
    
    # Validate text overlays
    from processing import TEXT_POSITIONS
    valid_text_overlays = []
    for overlay in text_overlays:
        if not isinstance(overlay, dict) or 'text' not in overlay:
            continue
            
        valid_overlay = {
            'text': overlay.get('text', '').strip(),
            'position': overlay.get('position', 'bottom')
        }
        
        # Validate position
        if valid_overlay['position'] not in TEXT_POSITIONS:
            valid_overlay['position'] = 'bottom'
            
        # Get style if provided
        if 'style' in overlay and isinstance(overlay['style'], dict):
            valid_overlay['style'] = overlay['style']
            
        # Add to valid overlays if text is not empty
        if valid_overlay['text']:
            valid_text_overlays.append(valid_overlay)
    
    # Add watermark based on subscription
    require_watermark = get_subscription_limit(subscription_type, 'watermark')
    
    # Get appropriate resolution based on subscription
    resolution = get_subscription_limit(subscription_type, 'resolution')
    
    # Store subscription info and limits in session data for processing
    session_data['subscription_info'] = {
        'type': subscription_type,
        'watermark': require_watermark,
        'resolution': resolution
    }
    
    # Save updated session data
    with open(session_file, 'w') as f:
        json.dump(session_data, f)
    
    # Start processing in a background task
    from processing import process_video_task
    task_id = process_video_task(
        session_id, 
        keep_original_audio, 
        crop_option, 
        valid_text_overlays, 
        require_watermark=require_watermark,
        resolution=resolution
    )
    
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
    # Check if session exists
    session_file = f"session_{session_id}.json"
    if not os.path.exists(session_file):
        return jsonify({'error': 'Session not found'}), 404
    
    # Load session data
    with open(session_file, 'r') as f:
        session_data = json.load(f)
    
    # Check if output_file is directly specified in session
    if 'output_file' in session_data:
        output_file = session_data['output_file']
        if os.path.exists(output_file):
            return send_from_directory(
                os.path.dirname(output_file), 
                os.path.basename(output_file), 
                as_attachment=True
            )
    
    # Fallback: try to find file with crop option if specified
    crop_option = session_data.get('crop_option', 'original')
    crop_suffix = f"_{crop_option.replace(':', '_')}" if crop_option != 'original' else ""
    output_file = os.path.join(app.config['PROCESSED_FOLDER'], f"{session_id}{crop_suffix}_output.mp4")
    
    if not os.path.exists(output_file):
        # Try the original filename as last resort
        output_file = os.path.join(app.config['PROCESSED_FOLDER'], f"{session_id}_output.mp4")
        if not os.path.exists(output_file):
            return jsonify({'error': 'Processed file not found'}), 404
    
    return send_from_directory(
        app.config['PROCESSED_FOLDER'], 
        os.path.basename(output_file), 
        as_attachment=True
    )

@app.route('/crop_options', methods=['GET'])
@login_required
def get_crop_options():
    """Return the available crop options based on subscription level"""
    from processing import ASPECT_RATIOS
    
    # Get user's subscription type
    conn = sqlite3.connect(USER_DB)
    cursor = conn.cursor()
    cursor.execute('SELECT subscription_type FROM users WHERE id = ?', (session['user_id'],))
    user_data = cursor.fetchone()
    conn.close()
    
    subscription_type = user_data[0] if user_data and user_data[0] else 'free'
    
    # Get allowed aspect ratios for this subscription
    allowed_ratios = get_subscription_limit(subscription_type, 'aspect_ratios')
    
    # Define all options
    all_options = [
        {'value': 'original', 'label': 'Original Aspect Ratio', 'requires': 'free'},
        {'value': '16:9', 'label': 'Landscape (16:9)', 'requires': 'free'},
        {'value': '9:16', 'label': 'Portrait (9:16)', 'requires': 'pro'},
        {'value': '1:1', 'label': 'Square (1:1)', 'requires': 'pro'},
        {'value': '4:3', 'label': 'Classic (4:3)', 'requires': 'pro'},
        {'value': '1:1_in_9:16', 'label': 'Square in Vertical (1:1 in 9:16)', 'requires': 'pro'}
    ]
    
    # Filter options based on subscription
    available_options = []
    locked_options = []
    
    for option in all_options:
        if option['value'] in allowed_ratios:
            # Remove the 'requires' field before sending to frontend
            option_copy = option.copy()
            option_copy.pop('requires', None)
            available_options.append(option_copy)
        else:
            # For locked options, keep the requires field to show upgrade prompt
            locked_options.append(option)
    
    return jsonify({
        'success': True,
        'options': available_options,
        'locked_options': locked_options,
        'subscription_type': subscription_type
    })

@app.route('/preview/<session_id>')
def preview_video(session_id):
    """Stream the processed video for preview"""
    # Check if session exists
    session_file = f"session_{session_id}.json"
    if not os.path.exists(session_file):
        return jsonify({'error': 'Session not found'}), 404
    
    # Load session data
    with open(session_file, 'r') as f:
        session_data = json.load(f)
    
    # Get the output file path
    output_file = None
    
    # Check if output_file is directly specified in session
    if 'output_file' in session_data and os.path.exists(session_data['output_file']):
        output_file = session_data['output_file']
    else:
        # Try to find file with crop option if specified
        crop_option = session_data.get('crop_option', 'original')
        crop_suffix = f"_{crop_option.replace(':', '_')}" if crop_option != 'original' else ""
        potential_file = os.path.join(app.config['PROCESSED_FOLDER'], f"{session_id}{crop_suffix}_output.mp4")
        
        if os.path.exists(potential_file):
            output_file = potential_file
        else:
            # Try the original filename as last resort
            potential_file = os.path.join(app.config['PROCESSED_FOLDER'], f"{session_id}_output.mp4")
            if os.path.exists(potential_file):
                output_file = potential_file
    
    if output_file is None:
        return jsonify({'error': 'Processed video not found'}), 404
    
    # Stream the video file for preview
    return send_from_directory(
        os.path.dirname(output_file),
        os.path.basename(output_file)
    )

@app.route('/text_positions', methods=['GET'])
def get_text_positions():
    """Return the available text positions with descriptions"""
    from processing import TEXT_POSITIONS
    
    # Create a list of positions with labels
    positions = [
        {'value': 'top', 'label': 'Top'},
        {'value': 'bottom', 'label': 'Bottom'},
        {'value': 'top_left', 'label': 'Top Left'},
        {'value': 'top_right', 'label': 'Top Right'},
        {'value': 'bottom_left', 'label': 'Bottom Left'},
        {'value': 'bottom_right', 'label': 'Bottom Right'},
        {'value': 'center', 'label': 'Center'}
    ]
    
    return jsonify({
        'success': True,
        'positions': positions
    })

@app.route('/font_options', methods=['GET'])
def get_font_options():
    """Return a list of available font options"""
    # Basic list of common fonts - this could be generated from the system
    fonts = [
        {'value': 'Arial', 'label': 'Arial'},
        {'value': 'Arial-Bold', 'label': 'Arial Bold'},
        {'value': 'TimesNewRomanPSMT', 'label': 'Times New Roman'},
        {'value': 'TimesNewRomanPS-BoldMT', 'label': 'Times New Roman Bold'},
        {'value': 'Georgia', 'label': 'Georgia'},
        {'value': 'Georgia-Bold', 'label': 'Georgia Bold'},
        {'value': 'Verdana', 'label': 'Verdana'},
        {'value': 'Verdana-Bold', 'label': 'Verdana Bold'},
        {'value': 'Comic-Sans-MS', 'label': 'Comic Sans MS'},
        {'value': 'Impact', 'label': 'Impact'}
    ]
    
    return jsonify({
        'success': True,
        'fonts': fonts
    })

@app.route('/cancel_subscription')
@login_required
def cancel_subscription():
    conn = sqlite3.connect(USER_DB)
    cursor = conn.cursor()
    
    try:
        # Update user's subscription status to cancelled
        cursor.execute('''
            UPDATE users 
            SET subscription_status = 'cancelled'
            WHERE id = ?
        ''', (session['user_id'],))
        
        # Record cancellation in subscription history
        cursor.execute('''
            UPDATE subscription_history 
            SET payment_status = 'cancelled', end_date = datetime('now')
            WHERE user_id = ? AND subscription_type = 'pro' AND payment_status = 'completed'
            ORDER BY start_date DESC LIMIT 1
        ''', (session['user_id'],))
        
        conn.commit()
        
        flash('Your subscription has been cancelled. Your Pro features will remain active until the end of your current billing period.', 'info')
        return redirect(url_for('profile'))
        
    except Exception as e:
        conn.rollback()
        flash(f'An error occurred: {str(e)}', 'danger')
        return redirect(url_for('profile'))
    finally:
        conn.close()

@app.route('/renew-subscription')
@login_required
def renew_subscription():
    # Redirect to subscription selection page for renewal
    return redirect(url_for('select_subscription'))

if __name__ == '__main__':
    app.run(debug=True)  