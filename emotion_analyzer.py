import os
import cv2
import numpy as np
from deepface import DeepFace
from PIL import Image
import json
from datetime import datetime
from retinaface import RetinaFace
import logging
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
import time

logger = logging.getLogger(__name__)

class EmotionAnalyzer:
    def __init__(self, photos_dir='photos', output_dir='output'):
        self.photos_dir = photos_dir
        self.output_dir = output_dir
        self.emotions = ['angry', 'disgust', 'fear', 'happy', 'sad', 'surprise', 'neutral']
        self.results = []
        self.cache_dir = 'cache'
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Initialize RetinaFace detector once
        self.detector = RetinaFace.build_model()
        
        # Initialize thread pool for parallel processing
        self.executor = ThreadPoolExecutor(max_workers=4)
        
    def analyze_photo(self, image_path):
        """Analyze emotions in a single photo"""
        try:
            # Read image
            img = cv2.imread(image_path)
            if img is None:
                raise Exception(f"Could not read image: {image_path}")
            
            # Analyze emotions using DeepFace
            result = DeepFace.analyze(
                img_path=image_path,
                actions=['emotion'],
                enforce_detection=False
            )
            
            # Extract the first face's emotions
            if isinstance(result, list):
                result = result[0]
            
            emotions = result['emotion']
            dominant_emotion = result['dominant_emotion']
            
            # Get image metadata
            img = Image.open(image_path)
            date_taken = None
            if hasattr(img, '_getexif') and img._getexif():
                exif = img._getexif()
                if exif:
                    date_taken = exif.get(36867)  # DateTimeOriginal tag
            
            return {
                'file_name': os.path.basename(image_path),
                'emotions': emotions,
                'dominant_emotion': dominant_emotion,
                'date_taken': date_taken,
                'confidence': emotions[dominant_emotion]
            }
            
        except Exception as e:
            print(f"Error analyzing {image_path}: {str(e)}")
            return None

    def analyze_all_photos(self):
        """Analyze all photos in the photos directory"""
        self.results = []
        
        # Get all image files
        image_extensions = ('.jpg', '.jpeg', '.png', '.bmp')
        image_files = [f for f in os.listdir(self.photos_dir) 
                      if f.lower().endswith(image_extensions)]
        
        # Sort files by name (assuming they might have timestamps)
        image_files.sort()
        
        for image_file in image_files:
            image_path = os.path.join(self.photos_dir, image_file)
            result = self.analyze_photo(image_path)
            if result:
                self.results.append(result)
        
        # Save results to JSON
        output_file = os.path.join(self.output_dir, 'emotion_analysis.json')
        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        return self.results

    def get_emotion_timeline(self):
        """Get a timeline of emotions across all photos"""
        if not self.results:
            self.analyze_all_photos()
        
        timeline = []
        for result in self.results:
            timeline.append({
                'file_name': result['file_name'],
                'dominant_emotion': result['dominant_emotion'],
                'confidence': result['confidence'],
                'date_taken': result['date_taken']
            })
        
        return timeline

    def get_emotion_statistics(self):
        """Get statistics about emotions across all photos"""
        if not self.results:
            self.analyze_all_photos()
        
        emotion_counts = {emotion: 0 for emotion in self.emotions}
        total_photos = len(self.results)
        
        for result in self.results:
            emotion_counts[result['dominant_emotion']] += 1
        
        return {
            'total_photos': total_photos,
            'emotion_distribution': emotion_counts,
            'most_common_emotion': max(emotion_counts.items(), key=lambda x: x[1])[0]
        }

    @lru_cache(maxsize=32)
    def _detect_faces(self, image_path):
        """Cached face detection to avoid reprocessing the same image"""
        try:
            img = cv2.imread(image_path)
            if img is None:
                return {}
            return RetinaFace.detect_faces(img, model=self.detector)
        except Exception as e:
            logger.error(f"Error detecting faces in {image_path}: {str(e)}")
            return {}

    def _process_single_photo(self, photo_path, reference_images, model_name, distance_metric, threshold, required_matches):
        """Process a single photo with face detection and recognition"""
        try:
            img = cv2.imread(photo_path)
            if img is None:
                return None

            faces = self._detect_faces(photo_path)
            if not isinstance(faces, dict):
                return None

            marked_img = img.copy()
            found_faces = False

            for face_idx, face_data in faces.items():
                facial_area = face_data['facial_area']
                x = int(facial_area[0])
                y = int(facial_area[1])
                w = int(facial_area[2] - x)
                h = int(facial_area[3] - y)
                
                # Ensure coordinates are within image bounds
                x = max(0, x)
                y = max(0, y)
                w = min(w, img.shape[1] - x)
                h = min(h, img.shape[0] - y)
                
                if w <= 0 or h <= 0:
                    continue
                
                detected_face_img = img[y:y+h, x:x+w]
                
                # Count successful matches with reference photos
                match_count = 0
                best_distance = float('inf')
                
                for ref_img in reference_images:
                    try:
                        result = DeepFace.verify(
                            img1_path=ref_img,
                            img2_path=detected_face_img,
                            model_name=model_name,
                            distance_metric=distance_metric,
                            enforce_detection=False
                        )
                        
                        if result['verified'] and result['distance'] <= threshold:
                            match_count += 1
                            best_distance = min(best_distance, result['distance'])
                            
                            if match_count >= required_matches:
                                break
                                
                    except Exception as e:
                        continue

                if match_count >= min(required_matches, len(reference_images)):
                    try:
                        emotion_result = DeepFace.analyze(
                            img_path=detected_face_img,
                            actions=['emotion'],
                            enforce_detection=False
                        )
                        dominant_emotion = emotion_result['dominant_emotion']
                        
                        # Add confidence score to the display
                        confidence_score = round((1 - best_distance) * 100, 1)
                        display_text = f"{dominant_emotion} ({confidence_score}%)"
                        
                        # Draw rectangle and text
                        rect_color = (0, 255, 0)
                        font = cv2.FONT_HERSHEY_SIMPLEX
                        font_scale = 0.9
                        thickness = 2
                        
                        # Draw rectangle
                        cv2.rectangle(marked_img, (x, y), (x + w, y + h), rect_color, 2)
                        
                        # Calculate text size
                        (text_width, text_height), baseline = cv2.getTextSize(
                            display_text, font, font_scale, thickness
                        )
                        
                        # Position text
                        text_x = x + w + 10
                        text_y = y + h // 2 + text_height // 2
                        
                        # Draw white background for text
                        cv2.rectangle(
                            marked_img,
                            (text_x - 2, text_y - text_height - 2),
                            (text_x + text_width + 2, text_y + baseline + 2),
                            (255, 255, 255),
                            -1
                        )
                        
                        # Draw text
                        cv2.putText(
                            marked_img, display_text, (text_x, text_y),
                            font, font_scale, rect_color,
                            thickness, cv2.LINE_AA
                        )
                        
                        found_faces = True
                        
                    except Exception as e:
                        logger.error(f"Error analyzing emotion in {photo_path}: {str(e)}")
                        continue

            if found_faces:
                return marked_img
            return None

        except Exception as e:
            logger.error(f"Error processing {photo_path}: {str(e)}")
            return None

    def mark_reference_faces_in_photos(self, reference_dir='reference', photos_dir='photos', marked_dir='output/marked_photos', 
                                     model_name='ArcFace', distance_metric='cosine',
                                     threshold=0.68, required_matches=2):
        """
        Mark faces in photos that match the reference photos.
        Uses RetinaFace for detection and ArcFace for recognition.
        Requires multiple matches for higher accuracy.
        """
        os.makedirs(marked_dir, exist_ok=True)
        
        # Get reference images
        reference_images = [os.path.join(reference_dir, f) for f in os.listdir(reference_dir) 
                          if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp'))]
        
        if len(reference_images) == 0:
            raise ValueError("No reference images found!")

        # Get main photos
        photo_files = [f for f in os.listdir(photos_dir) 
                      if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp'))]
        marked_files = []

        # Process photos in smaller batches to avoid timeouts
        batch_size = 5
        for i in range(0, len(photo_files), batch_size):
            batch = photo_files[i:i + batch_size]
            futures = []
            
            for photo_file in batch:
                photo_path = os.path.join(photos_dir, photo_file)
                future = self.executor.submit(
                    self._process_single_photo,
                    photo_path,
                    reference_images,
                    model_name,
                    distance_metric,
                    threshold,
                    required_matches
                )
                futures.append((photo_file, future))
                logger.info(f"Started processing {photo_file}")

            # Collect results for this batch
            for photo_file, future in futures:
                try:
                    marked_img = future.result(timeout=300)  # 5-minute timeout per photo
                    if marked_img is not None:
                        marked_path = os.path.join(marked_dir, f"marked_{photo_file}")
                        cv2.imwrite(marked_path, marked_img)
                        marked_files.append(marked_path)
                        logger.info(f"Successfully processed {photo_file}")
                    else:
                        logger.info(f"No matching faces found in {photo_file}")
                except Exception as e:
                    logger.error(f"Error processing {photo_file}: {str(e)}")
                    continue

            # Small delay between batches to prevent overload
            time.sleep(1)

        return marked_files

    def create_video_from_photos(self, photo_paths, output_dir='output/videos', fps=1):
        """Create a video from the processed photos"""
        if not photo_paths:
            return None

        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, 'output_video.mp4')

        # Get the first image to determine dimensions
        first_img = cv2.imread(photo_paths[0])
        height, width = first_img.shape[:2]

        # Create video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

        # Add each photo to the video
        for photo_path in photo_paths:
            img = cv2.imread(photo_path)
            if img is not None:
                out.write(img)

        out.release()
        return output_path

    def generate_emotion_statistics(self, photo_paths):
        """Generate emotion statistics from the processed photos"""
        emotion_counts = {}
        total_photos = 0

        for photo_path in photo_paths:
            try:
                img = cv2.imread(photo_path)
                if img is None:
                    continue

                # Extract emotion from the text overlay
                # Assuming format: "EMOTION (XX%)"
                text = photo_path.split('_')[-1].split('.')[0]  # Get filename without extension
                if '(' in text:
                    emotion = text.split('(')[0].strip().lower()
                    emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
                    total_photos += 1
            except Exception as e:
                logger.error(f"Error processing {photo_path}: {str(e)}")
                continue

        return emotion_counts 