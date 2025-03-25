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
    const exportTimestampsBtn = document.getElementById('export-timestamps');
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
    const keepOriginalAudioCheck = document.getElementById('keep-original-audio-check');
    const processingModal = new bootstrap.Modal(document.getElementById('processingModal'));
    const processingProgressBar = document.querySelector('#processingModal .progress-bar');
    const processingMessage = document.getElementById('processing-message');
    const processingComplete = document.getElementById('processing-complete');
    const downloadBtn = document.getElementById('download-btn');
    const cropOptionSelect = document.getElementById('crop-option');
    const ratioPreview = document.getElementById('ratio-preview');
    
    // Preview video elements
    const previewVideoModal = new bootstrap.Modal(document.getElementById('previewVideoModal'));
    const previewPlayer = document.getElementById('preview-player');
    const previewDownloadBtn = document.getElementById('preview-download-btn');
    
    // Text overlay elements
    const manageTextOverlayBtn = document.getElementById('manage-text-overlay');
    const textOverlayModal = new bootstrap.Modal(document.getElementById('textOverlayModal'));
    const textOverlaysContainer = document.getElementById('text-overlays-container');
    const noOverlays = document.getElementById('no-overlays');
    const addOverlayBtn = document.getElementById('add-overlay');
    const overlayEditor = document.getElementById('overlay-editor');
    const overlayTextInput = document.getElementById('overlay-text');
    const overlayPositionSelect = document.getElementById('overlay-position');
    const overlayFontSelect = document.getElementById('overlay-font');
    const overlayFontsizeInput = document.getElementById('overlay-fontsize');
    const overlayFontcolorInput = document.getElementById('overlay-fontcolor');
    const overlayBordercolorInput = document.getElementById('overlay-bordercolor');
    const overlayBorderwInput = document.getElementById('overlay-borderw');
    const overlayPreviewText = document.getElementById('overlay-preview-text');
    const cancelOverlayEditBtn = document.getElementById('cancel-overlay-edit');
    const saveOverlayBtn = document.getElementById('save-overlay');
    const applyTextOverlaysBtn = document.getElementById('apply-text-overlays');
    const textOverlaySummary = document.getElementById('text-overlay-summary');
    
    // Audio trim elements
    const trimAudioBtn = document.getElementById('trim-audio-btn');
    const trimAudioModal = document.getElementById('trimAudioModal') ? new bootstrap.Modal(document.getElementById('trimAudioModal')) : null;
    const audioPlayer = document.getElementById('audio-player');
    const trimStartInput = document.getElementById('trim-start');
    const trimDurationInput = document.getElementById('trim-duration');
    const trimAudioSubmit = document.getElementById('trim-audio-submit');
    
    // Session ID and flags from the data attributes
    const sessionId = document.body.dataset.sessionId;
    const hasTimestamps = document.body.dataset.hasTimestamps === 'true';
    const hasMusic = document.body.dataset.hasMusic === 'true';
    
    // Timestamps array
    let timestamps = [];
    
    // Text overlays array
    let textOverlays = [];
    let currentEditingIndex = -1;
    let currentVideoFrame = null;
    
    // Default position coordinates (center of the preview)
    let defaultXPercent = 0.5;
    let defaultYPercent = 0.5;
    
    // Initialize video player
    videoPlayer.addEventListener('loadedmetadata', function() {
        updateDurationDisplay();
        videoPlayer.volume = 0.8;
        
        // If we have imported timestamps, load them
        if (hasTimestamps) {
            fetchTimestamps();
        }
        
        // Capture a video frame for text overlay preview
        captureVideoFrame();
    });
    
    // Function to capture video frame for text overlay preview
    function captureVideoFrame() {
        // Use the midpoint of the video for the frame
        const time = videoPlayer.duration / 2;
        
        // Set the video frame URL
        currentVideoFrame = `${window.location.origin}/video_frame/${sessionId}/${time}`;
        
        // Preload the image
        const img = new Image();
        img.src = currentVideoFrame;
    }
    
    // Initialize draggable text
    function initDraggableText() {
        if (!$('#draggable-text-preview').length) return;
        
        // Set the video frame as background
        if (currentVideoFrame) {
            $('#video-frame-img').attr('src', currentVideoFrame);
        }
        
        // Initialize position at center
        const container = $('#drag-preview-container');
        const textElement = $('#draggable-text-preview');
        
        // Set the initial position in the center
        updateTextElementPosition(textElement, defaultXPercent, defaultYPercent);
        
        // Make the text draggable
        textElement.draggable({
            containment: 'parent',
            cursor: 'move',
            drag: function(event, ui) {
                // Calculate percentage position
                const containerWidth = container.width();
                const containerHeight = container.height();
                
                const xPercent = ui.position.left / containerWidth;
                const yPercent = ui.position.top / containerHeight;
                
                // Update position display
                updatePositionDisplay(xPercent, yPercent);
                
                // Save the current position
                defaultXPercent = xPercent;
                defaultYPercent = yPercent;
            }
        });
        
        // Initialize position display
        updatePositionDisplay(defaultXPercent, defaultYPercent);
    }
    
    // Helper function to update text element position
    function updateTextElementPosition(element, xPercent, yPercent) {
        const container = $('#drag-preview-container');
        const x = container.width() * xPercent;
        const y = container.height() * yPercent;
        
        element.css({
            left: x + 'px',
            top: y + 'px'
        });
    }
    
    // Helper function to update position display
    function updatePositionDisplay(xPercent, yPercent) {
        $('#coordinates-display').text(
            `Position: ${Math.round(xPercent * 100)}%, ${Math.round(yPercent * 100)}%`
        );
    }
    
    // Audio trim functionality
    if (trimAudioBtn && hasMusic) {
        trimAudioBtn.addEventListener('click', function() {
            trimAudioModal.show();
        });
        
        if (audioPlayer) {
            audioPlayer.addEventListener('loadedmetadata', function() {
                // Set max duration based on audio length
                const audioDuration = audioPlayer.duration;
                trimDurationInput.max = audioDuration;
                trimDurationInput.value = Math.min(60, audioDuration);
            });
        }
        
        if (trimAudioSubmit) {
            trimAudioSubmit.addEventListener('click', function() {
                const startTime = parseFloat(trimStartInput.value) || 0;
                const duration = parseFloat(trimDurationInput.value) || 60;
                
                if (duration <= 0) {
                    alert('Duration must be greater than 0');
                    return;
                }
                
                // Show processing in the button
                trimAudioSubmit.disabled = true;
                trimAudioSubmit.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Processing...';
                
                // Send trim request
                fetch('/trim_audio', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        session_id: sessionId,
                        start_time: startTime,
                        duration: duration
                    })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Reset button
                        trimAudioSubmit.disabled = false;
                        trimAudioSubmit.innerHTML = 'Trim Music';
                        
                        // Update audio player with new source
                        audioPlayer.src = data.trimmed_path;
                        audioPlayer.load();
                        
                        // Close modal
                        trimAudioModal.hide();
                        
                        // Show success message
                        alert('Music file trimmed successfully!');
                    } else {
                        throw new Error(data.error || 'Failed to trim audio');
                    }
                })
                .catch(error => {
                    // Reset button
                    trimAudioSubmit.disabled = false;
                    trimAudioSubmit.innerHTML = 'Trim Music';
                    
                    // Show error
                    alert('Error: ' + error.message);
                });
            });
        }
    }
    
    // Fetch timestamps from server if they were imported
    function fetchTimestamps() {
        fetch(`/get_timestamps/${sessionId}`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    timestamps = data.timestamps;
                    updateTimestampsList();
                    updateMarkersOnProgress();
                    
                    // Load text overlays if available
                    if (data.text_overlays && data.text_overlays.length > 0) {
                        textOverlays = data.text_overlays;
                        updateTextOverlaySummary();
                    }
                } else {
                    console.error('Error fetching timestamps:', data.error);
                }
            })
            .catch(error => {
                console.error('Error fetching timestamps:', error);
            });
    }
    
    // Export timestamps
    if (exportTimestampsBtn) {
        exportTimestampsBtn.addEventListener('click', function() {
            if (timestamps.length === 0) {
                alert('No timestamps to export');
                return;
            }
            
            // Save timestamps first
            saveTimestamps(true)
                .then(() => {
                    // Open export URL in new window
                    window.open(`/export_timestamps/${sessionId}`, '_blank');
                })
                .catch(error => {
                    alert('Error: ' + error.message);
                });
        });
    }
    
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
    saveTimestampsBtn.addEventListener('click', () => saveTimestamps());
    
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
    
    // Initialize ratio preview
    if (cropOptionSelect) {
        updateRatioPreview(cropOptionSelect.value);
        
        cropOptionSelect.addEventListener('change', function() {
            updateRatioPreview(this.value);
        });
    }
    
    // Text overlay functionality
    if (manageTextOverlayBtn) {
        manageTextOverlayBtn.addEventListener('click', function() {
            textOverlayModal.show();
            // Initialize draggable text when modal is shown
            setTimeout(initDraggableText, 300);
        });
    }
    
    if (addOverlayBtn) {
        addOverlayBtn.addEventListener('click', function() {
            // Reset editor fields for a new overlay
            currentEditingIndex = -1;
            overlayTextInput.value = '';
            overlayFontSelect.value = 'Arial';
            overlayFontsizeInput.value = '24';
            overlayFontcolorInput.value = '#ffffff';
            overlayBordercolorInput.value = '#000000';
            overlayBorderwInput.value = '2';
            
            // Reset position to center
            defaultXPercent = 0.5;
            defaultYPercent = 0.5;
            
            // Update draggable element
            if ($('#draggable-text-preview').length) {
                updateTextElementPosition($('#draggable-text-preview'), defaultXPercent, defaultYPercent);
                updatePositionDisplay(defaultXPercent, defaultYPercent);
                $('#draggable-text-preview').text('Your text here');
            }
            
            // Show editor
            overlayEditor.classList.remove('d-none');
            
            // Focus on text input
            overlayTextInput.focus();
        });
    }
    
    if (cancelOverlayEditBtn) {
        cancelOverlayEditBtn.addEventListener('click', function() {
            overlayEditor.classList.add('d-none');
        });
    }
    
    if (saveOverlayBtn) {
        saveOverlayBtn.addEventListener('click', function() {
            const text = overlayTextInput.value.trim();
            if (!text) {
                alert('Please enter some text for the overlay');
                return;
            }
            
            const overlay = {
                text: text,
                position: 'custom',
                style: {
                    font: overlayFontSelect.value,
                    fontsize: parseInt(overlayFontsizeInput.value),
                    fontcolor: overlayFontcolorInput.value,
                    borderw: parseInt(overlayBorderwInput.value),
                    bordercolor: overlayBordercolorInput.value,
                    x_percent: defaultXPercent,
                    y_percent: defaultYPercent
                }
            };
            
            if (currentEditingIndex >= 0 && currentEditingIndex < textOverlays.length) {
                // Editing existing overlay
                textOverlays[currentEditingIndex] = overlay;
            } else {
                // Adding new overlay
                textOverlays.push(overlay);
            }
            
            // Hide editor and update overlays list
            overlayEditor.classList.add('d-none');
            updateTextOverlaysList();
            updateTextOverlaySummary();
        });
    }
    
    // Initialize text overlay preview updates
    if (overlayTextInput) {
        overlayTextInput.addEventListener('input', function() {
            // Update draggable text preview
            if ($('#draggable-text-preview').length) {
                $('#draggable-text-preview').text(this.value || 'Your text here');
                updateTextStyle();
            }
        });
    }
    
    if (overlayFontSelect) {
        overlayFontSelect.addEventListener('change', updateTextStyle);
    }
    
    if (overlayFontsizeInput) {
        overlayFontsizeInput.addEventListener('input', updateTextStyle);
    }
    
    if (overlayFontcolorInput) {
        overlayFontcolorInput.addEventListener('input', updateTextStyle);
    }
    
    if (overlayBordercolorInput) {
        overlayBordercolorInput.addEventListener('input', updateTextStyle);
    }
    
    if (overlayBorderwInput) {
        overlayBorderwInput.addEventListener('input', updateTextStyle);
    }
    
    if (applyTextOverlaysBtn) {
        applyTextOverlaysBtn.addEventListener('click', function() {
            textOverlayModal.hide();
        });
    }
    
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
    
    function saveTimestamps(silent = false) {
        return new Promise((resolve, reject) => {
            fetch('/save_timestamps', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    session_id: sessionId,
                    timestamps: timestamps,
                    text_overlays: textOverlays
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    if (!silent) {
                        alert('Timestamps and text overlays saved successfully');
                    }
                    resolve(data);
                } else {
                    reject(new Error(data.error || 'Failed to save timestamps and text overlays'));
                }
            })
            .catch(error => {
                reject(error);
            });
        });
    }
    
    function startVideoProcessing() {
        // Check if we have any timestamps
        if (timestamps.length === 0) {
            alert('Please mark at least one timestamp before creating a highlight reel');
            return;
        }
        
        // Get options
        const keepOriginalAudio = keepOriginalAudioCheck && keepOriginalAudioCheck.checked;
        const cropOption = cropOptionSelect ? cropOptionSelect.value : 'original';
        
        // Save timestamps first
        saveTimestamps(true)
        .then(() => {
            // Start video processing
            return fetch('/process_video', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    session_id: sessionId,
                    keep_original_audio: keepOriginalAudio,
                    crop_option: cropOption,
                    text_overlays: textOverlays
                })
            });
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
                        
                        // Setup download button
                        downloadBtn.href = `/download/${sessionId}`;
                        
                        // Add preview button to the processing modal
                        const previewBtn = document.createElement('button');
                        previewBtn.className = 'btn btn-primary me-2';
                        previewBtn.innerHTML = '<i class="fas fa-eye"></i> Preview Video';
                        previewBtn.addEventListener('click', openVideoPreview);
                        
                        // Add preview button before download button
                        if (!document.getElementById('preview-btn')) {
                            previewBtn.id = 'preview-btn';
                            processingComplete.insertBefore(previewBtn, downloadBtn);
                        }
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
    
    // Function to open the video preview modal
    function openVideoPreview() {
        // Set the source of the preview player
        const videoSrc = `/preview/${sessionId}`;
        
        if (previewPlayer) {
            // Clear the previous source
            while (previewPlayer.firstChild) {
                previewPlayer.removeChild(previewPlayer.firstChild);
            }
            
            // Create and add new source element
            const source = document.createElement('source');
            source.src = videoSrc;
            source.type = 'video/mp4';
            previewPlayer.appendChild(source);
            
            // Load and play the video
            previewPlayer.load();
            
            // Setup download button
            if (previewDownloadBtn) {
                previewDownloadBtn.href = `/download/${sessionId}`;
            }
            
            // Show the modal
            previewVideoModal.show();
            
            // Auto-play the preview when ready
            previewPlayer.addEventListener('loadedmetadata', function() {
                previewPlayer.play().catch(e => {
                    console.log('Auto-play prevented by browser:', e);
                });
            });
        }
    }
    
    // Handle closing the preview modal - pause the video
    if (document.getElementById('previewVideoModal')) {
        document.getElementById('previewVideoModal').addEventListener('hidden.bs.modal', function () {
            if (previewPlayer) {
                previewPlayer.pause();
            }
        });
    }
    
    // Function to update the aspect ratio preview
    function updateRatioPreview(option) {
        if (!ratioPreview) return;
        
        // Remove all existing ratio classes
        ratioPreview.classList.remove(
            'ratio-original', 
            'ratio-16-9', 
            'ratio-9-16', 
            'ratio-1-1', 
            'ratio-4-3', 
            'ratio-1-1-in-9-16'
        );
        
        // Add the appropriate class based on selection
        const className = 'ratio-' + option.replace(':', '-').replace('_', '-');
        ratioPreview.classList.add(className);
    }
    
    // Function to update text style for draggable preview
    function updateTextStyle() {
        const textElement = $('#draggable-text-preview');
        if (!textElement.length) return;
        
        const fontSize = overlayFontsizeInput.value + 'px';
        const fontColor = overlayFontcolorInput.value;
        const borderWidth = overlayBorderwInput.value + 'px';
        const borderColor = overlayBordercolorInput.value;
        
        textElement.css({
            'font-size': fontSize,
            'color': fontColor
        });
        
        // Apply text shadow for border effect
        if (parseInt(overlayBorderwInput.value) > 0) {
            textElement.css('text-shadow', `
                0px 0px ${borderWidth} ${borderColor},
                0px 0px ${borderWidth} ${borderColor},
                0px 0px ${borderWidth} ${borderColor},
                0px 0px ${borderWidth} ${borderColor}
            `);
        } else {
            textElement.css('text-shadow', 'none');
        }
        
        // Try to update font family if supported
        try {
            const fontFamily = overlayFontSelect.value.replace(/-/g, ' ');
            textElement.css('font-family', fontFamily);
        } catch (e) {
            console.log('Error setting font family:', e);
        }
    }
    
    // Function to update text overlays list
    function updateTextOverlaysList() {
        // Show/hide no overlays message
        if (textOverlays.length === 0) {
            if (noOverlays) noOverlays.classList.remove('d-none');
        } else {
            if (noOverlays) noOverlays.classList.add('d-none');
        }
        
        // Clear existing overlay items
        const items = textOverlaysContainer.querySelectorAll('.overlay-item');
        items.forEach(item => item.remove());
        
        // Add overlay items
        textOverlays.forEach((overlay, index) => {
            const item = document.createElement('div');
            item.className = 'overlay-item';
            
            // Get position description
            let positionLabel = '';
            if (overlay.position === 'custom' && overlay.style && overlay.style.x_percent !== undefined) {
                positionLabel = `Position: ${Math.round(overlay.style.x_percent * 100)}%, ${Math.round(overlay.style.y_percent * 100)}%`;
            } else {
                positionLabel = `Position: ${overlay.position}`;
            }
            
            item.innerHTML = `
                <div>
                    <div class="overlay-item-text">${overlay.text}</div>
                    <div class="overlay-item-position">${positionLabel}</div>
                </div>
                <div class="overlay-actions">
                    <button class="btn btn-sm btn-outline-primary edit-overlay" data-index="${index}">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-danger delete-overlay" data-index="${index}">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            `;
            
            // Add event listeners
            const editBtn = item.querySelector('.edit-overlay');
            editBtn.addEventListener('click', function() {
                editOverlay(index);
            });
            
            const deleteBtn = item.querySelector('.delete-overlay');
            deleteBtn.addEventListener('click', function() {
                deleteOverlay(index);
            });
            
            textOverlaysContainer.appendChild(item);
        });
    }
    
    // Function to edit an overlay
    function editOverlay(index) {
        if (index < 0 || index >= textOverlays.length) return;
        
        currentEditingIndex = index;
        const overlay = textOverlays[index];
        
        // Set form values
        overlayTextInput.value = overlay.text;
        
        // Set style values if they exist
        if (overlay.style) {
            if (overlay.style.font) overlayFontSelect.value = overlay.style.font;
            if (overlay.style.fontsize) overlayFontsizeInput.value = overlay.style.fontsize;
            if (overlay.style.fontcolor) overlayFontcolorInput.value = overlay.style.fontcolor;
            if (overlay.style.borderw) overlayBorderwInput.value = overlay.style.borderw;
            if (overlay.style.bordercolor) overlayBordercolorInput.value = overlay.style.bordercolor;
            
            // Set position if custom
            if (overlay.position === 'custom' && overlay.style.x_percent !== undefined) {
                defaultXPercent = overlay.style.x_percent;
                defaultYPercent = overlay.style.y_percent;
            }
        }
        
        // Update draggable text preview
        if ($('#draggable-text-preview').length) {
            $('#draggable-text-preview').text(overlay.text);
            updateTextElementPosition($('#draggable-text-preview'), defaultXPercent, defaultYPercent);
            updatePositionDisplay(defaultXPercent, defaultYPercent);
            updateTextStyle();
        }
        
        // Show editor
        overlayEditor.classList.remove('d-none');
        
        // Scroll to editor
        overlayEditor.scrollIntoView({ behavior: 'smooth' });
    }
    
    // Function to delete an overlay
    function deleteOverlay(index) {
        if (index < 0 || index >= textOverlays.length) return;
        
        if (confirm('Are you sure you want to delete this text overlay?')) {
            textOverlays.splice(index, 1);
            updateTextOverlaysList();
            updateTextOverlaySummary();
        }
    }
    
    // Function to update text overlay summary
    function updateTextOverlaySummary() {
        if (!textOverlaySummary) return;
        
        if (textOverlays.length === 0) {
            textOverlaySummary.innerHTML = '<small class="text-muted">No text overlays added</small>';
        } else {
            const count = textOverlays.length;
            textOverlaySummary.innerHTML = `<small class="text-success">${count} text overlay${count !== 1 ? 's' : ''} added</small>`;
        }
    }
    
    // Toggle advanced settings
    if (document.getElementById('toggle-advanced-settings')) {
        document.getElementById('toggle-advanced-settings').addEventListener('click', function() {
            const advancedSettings = document.getElementById('advanced-settings');
            if (advancedSettings.style.display === 'block') {
                advancedSettings.style.display = 'none';
                this.innerHTML = '<i class="fas fa-cog"></i> Advanced Settings';
            } else {
                advancedSettings.style.display = 'block';
                this.innerHTML = '<i class="fas fa-cog"></i> Hide Advanced Settings';
            }
        });
    }
}); 