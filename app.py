from flask import Flask, request, jsonify, send_file, render_template, send_from_directory
from emotion_analyzer import EmotionAnalyzer
import os
from werkzeug.utils import secure_filename
import logging
import time
from datetime import datetime

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure upload folders
UPLOAD_FOLDER = 'uploads'
REFERENCE_FOLDER = os.path.join(UPLOAD_FOLDER, 'reference')
PHOTOS_FOLDER = os.path.join(UPLOAD_FOLDER, 'photos')
OUTPUT_FOLDER = os.path.join(UPLOAD_FOLDER, 'output')
MARKED_PHOTOS_FOLDER = os.path.join(OUTPUT_FOLDER, 'marked_photos')
VIDEO_OUTPUT_FOLDER = os.path.join(OUTPUT_FOLDER, 'videos')

# Create necessary directories
for folder in [REFERENCE_FOLDER, PHOTOS_FOLDER, MARKED_PHOTOS_FOLDER, VIDEO_OUTPUT_FOLDER]:
    os.makedirs(folder, exist_ok=True)

analyzer = EmotionAnalyzer()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg'}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload_reference', methods=['POST'])
def upload_reference():
    try:
        # Check if this is the first file in a batch upload
        is_first_file = request.args.get('is_first', 'false').lower() == 'true'
        
        # Only clear the reference folder if this is the first file
        if is_first_file:
            logger.info("Clearing reference folder before new batch upload")
            clear_data(REFERENCE_FOLDER)
            
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
            
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(REFERENCE_FOLDER, filename)
            file.save(file_path)
            logger.info(f"Reference photo saved: {filename}")
            return jsonify({'message': 'Reference photo uploaded successfully'})
        else:
            return jsonify({'error': 'Invalid file type'}), 400
    except Exception as e:
        logger.error(f"Error uploading reference photo: {str(e)}")
        return jsonify({'error': f'Failed to upload reference photo: {str(e)}'}), 500

@app.route('/upload_photos', methods=['POST'])
def upload_photos():
    try:
        # Clear photos folder before new upload
        clear_data(PHOTOS_FOLDER)
        
        if 'files[]' not in request.files:
            return jsonify({'error': 'No files part'}), 400
            
        files = request.files.getlist('files[]')
        if not files or files[0].filename == '':
            return jsonify({'error': 'No selected files'}), 400
            
        uploaded_files = []
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(PHOTOS_FOLDER, filename)
                file.save(file_path)
                uploaded_files.append(filename)
                logger.info(f"Photo saved: {filename}")
            else:
                return jsonify({'error': f'Invalid file type: {file.filename}'}), 400
                
        return jsonify({
            'message': f'Successfully uploaded {len(uploaded_files)} photos',
            'files': uploaded_files
        })
    except Exception as e:
        logger.error(f"Error uploading photos: {str(e)}")
        return jsonify({'error': f'Failed to upload photos: {str(e)}'}), 500

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        clear_data(MARKED_PHOTOS_FOLDER)  # Clear only marked photos before new analysis
        # Check if reference photos exist
        if not os.listdir(REFERENCE_FOLDER):
            return jsonify({'error': 'No reference photos uploaded'}), 400
        
        # Check if photos to analyze exist
        if not os.listdir(PHOTOS_FOLDER):
            return jsonify({'error': 'No photos to analyze uploaded'}), 400
        
        logger.info("Starting face detection and analysis...")
        
        # Process photos with improved face recognition settings
        marked_files = analyzer.mark_reference_faces_in_photos(
            reference_dir=REFERENCE_FOLDER,
            photos_dir=PHOTOS_FOLDER,
            marked_dir=MARKED_PHOTOS_FOLDER,
            model_name='ArcFace',
            distance_metric='cosine',
            threshold=0.68,
            required_matches=2
        )
        
        logger.info(f"Processed {len(marked_files)} photos")
        
        if not marked_files:
            return jsonify({
                'message': 'No matching faces found in the uploaded photos',
                'marked_photos': []
            })

        return jsonify({
            'message': 'Analysis completed successfully',
            'marked_photos': [os.path.basename(f) for f in marked_files]
        })
            
    except Exception as e:
        logger.error(f"Error during analysis: {str(e)}")
        return jsonify({'error': f'Analysis failed: {str(e)}'}), 500

@app.route('/generate_video', methods=['POST'])
def generate_video():
    try:
        clear_data(VIDEO_OUTPUT_FOLDER)  # Clear only video output before generating new one
        # Get list of marked photos
        marked_files = [os.path.join(MARKED_PHOTOS_FOLDER, f) for f in os.listdir(MARKED_PHOTOS_FOLDER) 
                       if f.endswith(('.png', '.jpg', '.jpeg'))]
        
        if not marked_files:
            return jsonify({'error': 'No marked photos found'}), 400
            
        # Sort files to maintain order
        marked_files.sort()
        
        # Create video from images using the analyzer
        logger.info(f"Starting video generation with {len(marked_files)} images...")
        success = analyzer.create_video_from_photos(
            marked_files,
            output_dir=VIDEO_OUTPUT_FOLDER,
            fps=2  # 2 seconds per image
        )
        
        if not success:
            logger.error("Video generation failed")
            return jsonify({'error': 'Failed to generate video'}), 500
            
        # Return the fixed output video name since we're not using timestamps anymore
        video_filename = 'output_video.mp4'
        video_path = os.path.join(VIDEO_OUTPUT_FOLDER, video_filename)
        logger.info(f"Video generated successfully at: {video_path}")
        return jsonify({'video_path': video_filename})
    except Exception as e:
        logger.error(f"Error generating video: {str(e)}")
        return jsonify({'error': f'Failed to generate video: {str(e)}'}), 500

@app.route('/download/<path:filename>')
def download_file(filename):
    try:
        # Determine the correct directory based on file type/location
        if filename.startswith('marked_'):
            directory = MARKED_PHOTOS_FOLDER
        elif filename.endswith(('.mp4', '.avi', '.mov')):
            directory = VIDEO_OUTPUT_FOLDER
        else:
            return jsonify({'error': 'Invalid file type'}), 400
        
        file_path = os.path.join(directory, filename)
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
            
        return send_file(
            file_path,
            as_attachment=True
        )
    except Exception as e:
        logger.error(f"Error downloading file: {str(e)}")
        return jsonify({'error': f'Download failed: {str(e)}'}), 500

@app.route('/clear', methods=['POST'])
def clear_data(folder_name=None):
    """Clear files from specified folder or all folders if none specified"""
    try:
        if folder_name:
            # Clear specific folder
            if os.path.exists(folder_name):
                logger.info(f"Clearing folder: {folder_name}")
                for file in os.listdir(folder_name):
                    file_path = os.path.join(folder_name, file)
                    try:
                        if os.path.isfile(file_path):
                            os.unlink(file_path)
                            logger.info(f"Deleted file: {file_path}")
                    except Exception as e:
                        logger.error(f"Error deleting {file_path}: {str(e)}")
        else:
            # Clear all folders
            for directory in [UPLOAD_FOLDER, REFERENCE_FOLDER, OUTPUT_FOLDER]:
                if os.path.exists(directory):
                    logger.info(f"Clearing folder: {directory}")
                    for file in os.listdir(directory):
                        file_path = os.path.join(directory, file)
                        try:
                            if os.path.isfile(file_path):
                                os.unlink(file_path)
                                logger.info(f"Deleted file: {file_path}")
                        except Exception as e:
                            logger.error(f"Error deleting {file_path}: {str(e)}")
        
        return jsonify({'message': 'Data cleared successfully'})
    except Exception as e:
        logger.error(f"Error clearing data: {str(e)}")
        return jsonify({'error': f'Failed to clear data: {str(e)}'}), 500

@app.route('/videos/<path:filename>')
def serve_video(filename):
    """Serve video files from the videos folder"""
    try:
        if not os.path.exists(os.path.join(VIDEO_OUTPUT_FOLDER, filename)):
            logger.error(f"Video file not found: {filename}")
            return jsonify({'error': 'Video file not found'}), 404
            
        # Add MIME type for mp4 videos
        return send_from_directory(VIDEO_OUTPUT_FOLDER, filename, mimetype='video/mp4')
    except Exception as e:
        logger.error(f"Error serving video: {str(e)}")
        return jsonify({'error': f'Failed to serve video: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True) 