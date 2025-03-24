document.addEventListener('DOMContentLoaded', function() {
    const uploadForm = document.getElementById('video-upload-form');
    const uploadBtn = document.getElementById('upload-btn');
    const uploadText = document.getElementById('upload-text');
    const uploadSpinner = document.getElementById('upload-spinner');
    const uploadProgressDiv = document.getElementById('upload-progress');
    const progressBar = uploadProgressDiv.querySelector('.progress-bar');
    const progressText = document.getElementById('progress-text');
    const uploadErrorDiv = document.getElementById('upload-error');
    const errorMessage = document.getElementById('error-message');
    
    uploadForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Get form data
        const formData = new FormData(uploadForm);
        
        // Check if files are selected
        const videoFile = formData.get('video');
        const musicFile = formData.get('music');
        
        if (!videoFile.name || !musicFile.name) {
            showError('Please select both video and music files.');
            return;
        }
        
        // Show upload progress
        uploadBtn.disabled = true;
        uploadText.textContent = 'Uploading...';
        uploadSpinner.classList.remove('d-none');
        uploadProgressDiv.classList.remove('d-none');
        uploadErrorDiv.classList.add('d-none');
        
        // Simulate upload progress
        let progress = 0;
        const interval = setInterval(function() {
            progress += 5;
            if (progress >= 100) {
                clearInterval(interval);
            }
            progressBar.style.width = progress + '%';
            progressBar.setAttribute('aria-valuenow', progress);
            progressText.textContent = `Uploading files... ${progress}%`;
        }, 300);
        
        // Upload files
        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            // Clear the interval regardless of response
            clearInterval(interval);
            
            if (!response.ok) {
                return response.json().then(data => {
                    throw new Error(data.error || 'Upload failed');
                });
            }
            return response.json();
        })
        .then(data => {
            // Redirect to editor
            if (data.redirect) {
                window.location.href = data.redirect;
            }
        })
        .catch(error => {
            // Show error
            uploadBtn.disabled = false;
            uploadText.textContent = 'Start Editing';
            uploadSpinner.classList.add('d-none');
            uploadProgressDiv.classList.add('d-none');
            showError(error.message);
        });
    });
    
    function showError(message) {
        errorMessage.textContent = message;
        uploadErrorDiv.classList.remove('d-none');
    }
}); 