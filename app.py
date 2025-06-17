from flask import Flask, request, jsonify, send_file, render_template
from emotion_analyzer import EmotionAnalyzer
import os
from werkzeug.utils import secure_filename
import logging
import time

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
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'mp4', 'avi', 'mov'}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload_reference', methods=['POST'])
def upload_reference():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(REFERENCE_FOLDER, filename)
            file.save(filepath)
            logger.info(f"Reference photo saved: {filename}")
            return jsonify({'message': 'Reference photo uploaded successfully'})
        
        return jsonify({'error': 'Invalid file type'}), 400
    except Exception as e:
        logger.error(f"Error in upload_reference: {str(e)}")
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500

@app.route('/upload_photos', methods=['POST'])
def upload_photos():
    try:
        if 'files[]' not in request.files:
            return jsonify({'error': 'No files part'}), 400
        
        files = request.files.getlist('files[]')
        if not files or files[0].filename == '':
            return jsonify({'error': 'No selected files'}), 400
        
        saved_files = []
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(PHOTOS_FOLDER, filename)
                file.save(filepath)
                saved_files.append(filename)
                logger.info(f"Photo saved: {filename}")
        
        if not saved_files:
            return jsonify({'error': 'No valid files uploaded'}), 400
        
        return jsonify({
            'message': f'Successfully uploaded {len(saved_files)} photos',
            'files': saved_files
        })
    except Exception as e:
        logger.error(f"Error in upload_photos: {str(e)}")
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        # Check if reference photos exist
        if not os.listdir(REFERENCE_FOLDER):
            return jsonify({'error': 'No reference photos uploaded'}), 400
        
        # Check if photos to analyze exist
        if not os.listdir(PHOTOS_FOLDER):
            return jsonify({'error': 'No photos to analyze uploaded'}), 400
        
        logger.info("Starting face detection and emotion analysis...")
        
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
                'marked_photos': [],
                'video_path': None,
                'emotion_stats': {}
            })
        
        # Create video from marked photos
        video_path = analyzer.create_video_from_photos(
            marked_files,
            output_dir=VIDEO_OUTPUT_FOLDER
        )
        logger.info(f"Created video: {video_path}")
        
        # Generate emotion statistics
        emotion_stats = analyzer.generate_emotion_statistics(marked_files)
        logger.info("Generated emotion statistics")
        
        return jsonify({
            'message': 'Analysis completed successfully',
            'marked_photos': [os.path.basename(f) for f in marked_files],
            'video_path': os.path.basename(video_path) if video_path else None,
            'emotion_stats': emotion_stats
        })
            
    except Exception as e:
        logger.error(f"Error during analysis: {str(e)}")
        return jsonify({'error': f'Analysis failed: {str(e)}'}), 500

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
def clear_data():
    try:
        # Clear all directories
        for folder in [REFERENCE_FOLDER, PHOTOS_FOLDER, MARKED_PHOTOS_FOLDER, VIDEO_OUTPUT_FOLDER]:
            for file in os.listdir(folder):
                file_path = os.path.join(folder, file)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                except Exception as e:
                    logger.error(f"Error deleting {file_path}: {str(e)}")
        
        return jsonify({'message': 'All data cleared successfully'})
    except Exception as e:
        logger.error(f"Error clearing data: {str(e)}")
        return jsonify({'error': f'Failed to clear data: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True) 