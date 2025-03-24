document.addEventListener('DOMContentLoaded', function() {
    // Get DOM elements
    const videoPlayer = document.getElementById('video-player');
    const playPauseBtn = document.getElementById('play-pause');
    const currentTimeEl = document.getElementById('current-time');
    const durationEl = document.getElementById('duration');
    const progressBar = document.querySelector('.video-progress .progress-bar');
    const videoProgress = document.querySelector('.video-progress');
    const markBtn = document.getElementById('mark-timestamp');
    const removeLastBtn = document.getElementById('remove-last');
    const saveTimestampsBtn = document.getElementById('save-timestamps');
    const createVideoBtn = document.getElementById('create-video');
    const jumpBack5Btn = document.getElementById('jump-back-5');
    const jumpForward5Btn = document.getElementById('jump-forward-5');
    const jumpBack30Btn = document.getElementById('jump-back-30');
    const jumpForward30Btn = document.getElementById('jump-forward-30');
    const speedOptions = document.getElementById('speed-options');
    const speedIndicator = document.getElementById('speed-indicator');
    const timestampsContainer = document.getElementById('timestamps-container');
    const noTimestamps = document.getElementById('no-timestamps');
    const timestampCount = document.getElementById('timestamp-count');
    const processingModal = new bootstrap.Modal(document.getElementById('processingModal'));
    const processingProgressBar = document.querySelector('#processingModal .progress-bar');
    const processingMessage = document.getElementById('processing-message');
    const processingComplete = document.getElementById('processing-complete');
    const downloadBtn = document.getElementById('download-btn');
    
    // Session ID from the data attribute
    const sessionId = document.body.dataset.sessionId;
    
    // Timestamps array
    let timestamps = [];
    
    // Initialize video player
    videoPlayer.addEventListener('loadedmetadata', function() {
        updateDurationDisplay();
        videoPlayer.volume = 0.8;
    });
    
    // Play/Pause functionality
    playPauseBtn.addEventListener('click', togglePlayPause);
    videoPlayer.addEventListener('click', togglePlayPause);
    
    // Update time display and progress bar
    videoPlayer.addEventListener('timeupdate', function() {
        updateTimeDisplay();
        updateProgressBar();
    });
    
    // Progress bar click to seek
    videoProgress.addEventListener('click', function(e) {
        const rect = videoProgress.getBoundingClientRect();
        const pos = (e.clientX - rect.left) / rect.width;
        videoPlayer.currentTime = pos * videoPlayer.duration;
    });
    
    // Jump buttons
    jumpBack5Btn.addEventListener('click', () => seekRelative(-5));
    jumpForward5Btn.addEventListener('click', () => seekRelative(5));
    jumpBack30Btn.addEventListener('click', () => seekRelative(-30));
    jumpForward30Btn.addEventListener('click', () => seekRelative(30));
    
    // Mark timestamp button
    markBtn.addEventListener('click', addTimestamp);
    
    // Remove last timestamp button
    removeLastBtn.addEventListener('click', removeLastTimestamp);
    
    // Save timestamps button
    saveTimestampsBtn.addEventListener('click', saveTimestamps);
    
    // Create video button
    createVideoBtn.addEventListener('click', startVideoProcessing);
    
    // Playback speed options
    speedOptions.addEventListener('click', function(e) {
        if (e.target.tagName === 'A') {
            const speed = parseFloat(e.target.dataset.speed);
            videoPlayer.playbackRate = speed;
            speedIndicator.textContent = `${speed}x`;
            
            // Update active item
            const items = speedOptions.querySelectorAll('a');
            items.forEach(item => item.classList.remove('active'));
            e.target.classList.add('active');
            
            e.preventDefault();
        }
    });
    
    // Keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // Don't trigger shortcuts if user is typing in an input field
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
            return;
        }
        
        switch (e.key) {
            case ' ':  // Space
                togglePlayPause();
                e.preventDefault();
                break;
            case 'm':
            case 'M':
                addTimestamp();
                break;
            case 'ArrowLeft':
            case 'a':
            case 'A':
                seekRelative(-5);
                break;
            case 'ArrowRight':
            case 'd':
            case 'D':
                seekRelative(5);
                break;
            case 'j':
            case 'J':
                seekRelative(-30);
                break;
            case 'k':
            case 'K':
                seekRelative(30);
                break;
            case '+':
            case '=':
                increaseSpeed();
                break;
            case '-':
            case '_':
                decreaseSpeed();
                break;
            case 'r':
            case 'R':
                removeLastTimestamp();
                break;
        }
    });
    
    // Functions
    
    function togglePlayPause() {
        if (videoPlayer.paused) {
            videoPlayer.play();
            playPauseBtn.innerHTML = '<i class="fas fa-pause"></i>';
        } else {
            videoPlayer.pause();
            playPauseBtn.innerHTML = '<i class="fas fa-play"></i>';
        }
    }
    
    function updateTimeDisplay() {
        currentTimeEl.textContent = formatTime(videoPlayer.currentTime);
    }
    
    function updateDurationDisplay() {
        durationEl.textContent = formatTime(videoPlayer.duration);
    }
    
    function updateProgressBar() {
        const percent = (videoPlayer.currentTime / videoPlayer.duration) * 100;
        progressBar.style.width = `${percent}%`;
    }
    
    function formatTime(seconds) {
        const minutes = Math.floor(seconds / 60);
        seconds = Math.floor(seconds % 60);
        return `${minutes}:${seconds.toString().padStart(2, '0')}`;
    }
    
    function seekRelative(seconds) {
        videoPlayer.currentTime = Math.max(0, Math.min(videoPlayer.duration, videoPlayer.currentTime + seconds));
    }
    
    function increaseSpeed() {
        const speeds = [0.25, 0.5, 0.75, 1, 1.25, 1.5, 2];
        const currentSpeed = videoPlayer.playbackRate;
        const currentIndex = speeds.indexOf(currentSpeed);
        
        if (currentIndex < speeds.length - 1) {
            const newSpeed = speeds[currentIndex + 1];
            videoPlayer.playbackRate = newSpeed;
            speedIndicator.textContent = `${newSpeed}x`;
            
            // Update active item
            const items = speedOptions.querySelectorAll('a');
            items.forEach(item => {
                if (parseFloat(item.dataset.speed) === newSpeed) {
                    item.classList.add('active');
                } else {
                    item.classList.remove('active');
                }
            });
        }
    }
    
    function decreaseSpeed() {
        const speeds = [0.25, 0.5, 0.75, 1, 1.25, 1.5, 2];
        const currentSpeed = videoPlayer.playbackRate;
        const currentIndex = speeds.indexOf(currentSpeed);
        
        if (currentIndex > 0) {
            const newSpeed = speeds[currentIndex - 1];
            videoPlayer.playbackRate = newSpeed;
            speedIndicator.textContent = `${newSpeed}x`;
            
            // Update active item
            const items = speedOptions.querySelectorAll('a');
            items.forEach(item => {
                if (parseFloat(item.dataset.speed) === newSpeed) {
                    item.classList.add('active');
                } else {
                    item.classList.remove('active');
                }
            });
        }
    }
    
    function addTimestamp() {
        const time = videoPlayer.currentTime;
        timestamps.push(time);
        updateTimestampsList();
        addMarkerToProgress(time);
    }
    
    function removeLastTimestamp() {
        if (timestamps.length > 0) {
            timestamps.pop();
            updateTimestampsList();
            updateMarkersOnProgress();
        }
    }
    
    function updateTimestampsList() {
        // Update count
        timestampCount.textContent = timestamps.length;
        
        // Show/hide no timestamps message
        if (timestamps.length === 0) {
            noTimestamps.classList.remove('d-none');
        } else {
            noTimestamps.classList.add('d-none');
        }
        
        // Clear existing items
        const items = timestampsContainer.querySelectorAll('.timestamp-item');
        items.forEach(item => item.remove());
        
        // Add new items
        timestamps.forEach((time, index) => {
            const item = document.createElement('div');
            item.className = 'timestamp-item';
            item.innerHTML = `
                <span>${index + 1}. ${formatTime(time)}</span>
                <button class="btn btn-sm btn-outline-danger" data-index="${index}">
                    <i class="fas fa-times"></i>
                </button>
            `;
            
            const deleteBtn = item.querySelector('button');
            deleteBtn.addEventListener('click', function() {
                timestamps.splice(index, 1);
                updateTimestampsList();
                updateMarkersOnProgress();
            });
            
            timestampsContainer.appendChild(item);
        });
    }
    
    function addMarkerToProgress(time) {
        updateMarkersOnProgress();
    }
    
    function updateMarkersOnProgress() {
        // Remove existing markers
        const markers = videoProgress.querySelectorAll('.marker');
        markers.forEach(marker => marker.remove());
        
        // Add new markers
        timestamps.forEach(time => {
            const percent = (time / videoPlayer.duration) * 100;
            const marker = document.createElement('div');
            marker.className = 'marker';
            marker.style.left = `${percent}%`;
            marker.setAttribute('data-time', formatTime(time));
            videoProgress.appendChild(marker);
        });
    }
    
    function saveTimestamps() {
        fetch('/save_timestamps', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                session_id: sessionId,
                timestamps: timestamps
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Timestamps saved successfully');
            } else {
                alert('Error saving timestamps: ' + data.error);
            }
        })
        .catch(error => {
            alert('Error saving timestamps: ' + error.message);
        });
    }
    
    function startVideoProcessing() {
        // Check if we have any timestamps
        if (timestamps.length === 0) {
            alert('Please mark at least one timestamp before creating a highlight reel');
            return;
        }
        
        // Save timestamps first
        fetch('/save_timestamps', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                session_id: sessionId,
                timestamps: timestamps
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Start video processing
                return fetch('/process_video', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        session_id: sessionId
                    })
                });
            } else {
                throw new Error('Error saving timestamps: ' + data.error);
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Show processing modal
                processingProgressBar.style.width = '0%';
                processingMessage.textContent = 'Starting video processing...';
                processingComplete.classList.add('d-none');
                processingModal.show();
                
                // Start polling for progress
                const taskId = data.task_id;
                pollProcessingProgress(taskId);
            } else {
                alert('Error starting video processing: ' + data.error);
            }
        })
        .catch(error => {
            alert('Error: ' + error.message);
        });
    }
    
    function pollProcessingProgress(taskId) {
        const interval = setInterval(() => {
            fetch(`/check_progress/${taskId}`)
                .then(response => response.json())
                .then(data => {
                    processingProgressBar.style.width = `${data.progress}%`;
                    processingMessage.textContent = data.message;
                    
                    if (data.status === 'completed') {
                        clearInterval(interval);
                        processingComplete.classList.remove('d-none');
                        downloadBtn.href = `/download/${sessionId}`;
                    } else if (data.status === 'failed') {
                        clearInterval(interval);
                        processingMessage.textContent = `Error: ${data.message}`;
                        processingMessage.classList.add('text-danger');
                    }
                })
                .catch(error => {
                    console.error('Error polling progress:', error);
                });
        }, 1000);
    }
}); 