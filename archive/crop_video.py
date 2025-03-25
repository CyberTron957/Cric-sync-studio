import cv2
import numpy as np

def crop_video_to_aspect_ratio(input_video_path, output_video_path, target_aspect_ratio=(9, 16), scale_factor=1.0):
    cap = cv2.VideoCapture(input_video_path)
    
    if not cap.isOpened():
        print(f"Error: Could not open video file: {input_video_path}")
        return

    # Get original video dimensions
    original_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    original_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    # First crop to 1:1 from the center
    square_size = min(original_width, original_height)
    x_start = (original_width - square_size) // 2
    y_start = (original_height - square_size) // 2

    # Calculate dimensions for 9:16 output with the square in the center
    output_width = square_size  # Width same as the square
    output_height = (output_width * target_aspect_ratio[1]) // target_aspect_ratio[0]
    
    # Calculate padding
    padding_y = (output_height - square_size) // 2
    
    # Process directly with ffmpeg instead of OpenCV for better performance
    try:
        import subprocess
        import os
        
        # Generate a script file with ffmpeg commands
        filter_script = "crop_filter.txt"
        with open(filter_script, "w") as f:
            # Calculate crop values for ffmpeg
            crop_cmd = f"crop={square_size}:{square_size}:{x_start}:{y_start}"
            pad_cmd = f"pad={output_width}:{output_height}:0:{padding_y}:black"
            f.write(f"[0:v] {crop_cmd}, {pad_cmd} [v]")
        
        # Run ffmpeg with the filter script
        cmd = [
            'ffmpeg', '-i', input_video_path, 
            '-filter_complex_script', filter_script,
            '-map', '[v]', 
            '-c:v', 'libx264', '-crf', '23',
            '-preset', 'faster',  # Use faster preset for speed
            output_video_path, '-y'
        ]
        print("Processing with ffmpeg (this should be faster)...")
        subprocess.run(cmd, check=True)
        os.remove(filter_script)
        print(f"Compressed video saved as: {output_video_path}")
        return
    except (ImportError, subprocess.SubprocessError) as e:
        print(f"FFmpeg failed, falling back to OpenCV: {e}")
        # Continue with OpenCV method if ffmpeg fails
    
    # Define codec and create VideoWriter object with compression
    fourcc = cv2.VideoWriter_fourcc(*'H264')  # Using H.264 codec for better compression
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    # Create temp file for initial encoding
    temp_output = output_video_path + '.temp.mp4'
    out = cv2.VideoWriter(temp_output, fourcc, fps, (output_width, output_height))
    
    frame_count = 0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Update progress
        frame_count += 1
        if frame_count % 100 == 0:
            print(f"Processing frame {frame_count}/{total_frames} ({frame_count/total_frames*100:.1f}%)")
        
        # Crop the frame to square from the center
        h, w = frame.shape[:2]
        crop_size = min(w, h)
        start_x = (w - crop_size) // 2
        start_y = (h - crop_size) // 2
        square_frame = frame[start_y:start_y + crop_size, start_x:start_x + crop_size]
        
        # Resize if needed to match the calculated square_size
        if crop_size != square_size:
            square_frame = cv2.resize(square_frame, (square_size, square_size))
        
        # Create black canvas for 9:16
        output_frame = np.zeros((output_height, output_width, 3), dtype=np.uint8)
        
        # Place the square frame in the center
        output_frame[padding_y:padding_y + square_size, 0:square_size] = square_frame
        
        # Write the frame to output video
        out.write(output_frame)

    cap.release()
    out.release()
    
    # Use ffmpeg for additional compression if available
    try:
        import subprocess
        print("Applying additional compression with ffmpeg...")
        cmd = [
            'ffmpeg', '-i', temp_output, '-c:v', 'libx264', '-crf', '23', 
            '-preset', 'medium', output_video_path, '-y'
        ]
        subprocess.run(cmd, check=True)
        # Remove temp file
        import os
        os.remove(temp_output)
        print(f"Compressed video saved as: {output_video_path}")
    except (ImportError, subprocess.SubprocessError) as e:
        import os
        os.rename(temp_output, output_video_path)
        print(f"FFmpeg not available, using basic compression only. Video saved as: {output_video_path}")
        print(f"Error: {e}")

# Example usage
input_video = "/Users/pradhyun/temp/Cricket video edit/archive/media/IPL 2025 M02： SRH vs RR - Match Highlights [6370422303112].mp4"
output_video = 'cropped_video.mp4'  # Replace with your desired output path
crop_video_to_aspect_ratio(input_video, output_video)
