import os
import numpy as np
from moviepy.editor import ImageSequenceClip, AudioFileClip, CompositeAudioClip
import json
from datetime import datetime
from PIL import Image

class MusicGenerator:
    def __init__(self, output_dir='output'):
        self.output_dir = output_dir
        self.emotion_to_music = {
            'happy': {
                'tempo': 'upbeat',
                'key': 'major',
                'style': 'celebratory'
            },
            'sad': {
                'tempo': 'slow',
                'key': 'minor',
                'style': 'melancholic'
            },
            'angry': {
                'tempo': 'fast',
                'key': 'minor',
                'style': 'intense'
            },
            'surprise': {
                'tempo': 'moderate',
                'key': 'major',
                'style': 'dramatic'
            },
            'fear': {
                'tempo': 'slow',
                'key': 'minor',
                'style': 'suspenseful'
            },
            'disgust': {
                'tempo': 'moderate',
                'key': 'minor',
                'style': 'dark'
            },
            'neutral': {
                'tempo': 'moderate',
                'key': 'major',
                'style': 'ambient'
            }
        }
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
    
    def generate_music_parameters(self, emotion_analysis):
        """Generate music parameters based on emotional analysis"""
        # Calculate average emotion scores
        emotion_scores = {}
        for emotion in self.emotion_to_music.keys():
            scores = [result['emotions'][emotion] for result in emotion_analysis]
            emotion_scores[emotion] = np.mean(scores)
        
        # Get dominant emotions
        dominant_emotions = [result['dominant_emotion'] for result in emotion_analysis]
        
        # Generate music parameters
        music_params = {
            'tempo': self._calculate_tempo(dominant_emotions),
            'key': self._calculate_key(emotion_scores),
            'style': self._calculate_style(emotion_scores),
            'duration': len(emotion_analysis) * 3  # 3 seconds per photo
        }
        
        return music_params
    
    def _calculate_tempo(self, dominant_emotions):
        """Calculate overall tempo based on dominant emotions"""
        tempo_scores = {
            'happy': 1.2,
            'sad': 0.8,
            'angry': 1.4,
            'surprise': 1.1,
            'fear': 0.9,
            'disgust': 1.0,
            'neutral': 1.0
        }
        
        avg_tempo = np.mean([tempo_scores[emotion] for emotion in dominant_emotions])
        
        if avg_tempo > 1.2:
            return 'fast'
        elif avg_tempo < 0.9:
            return 'slow'
        else:
            return 'moderate'
    
    def _calculate_key(self, emotion_scores):
        """Calculate overall key based on emotion scores"""
        # Higher scores for positive emotions suggest major key
        positive_emotions = ['happy', 'surprise']
        negative_emotions = ['sad', 'angry', 'fear', 'disgust']
        
        positive_score = sum(emotion_scores[emotion] for emotion in positive_emotions)
        negative_score = sum(emotion_scores[emotion] for emotion in negative_emotions)
        
        return 'major' if positive_score > negative_score else 'minor'
    
    def _calculate_style(self, emotion_scores):
        """Calculate overall style based on emotion scores"""
        # Find the emotion with the highest average score
        dominant_emotion = max(emotion_scores.items(), key=lambda x: x[1])[0]
        return self.emotion_to_music[dominant_emotion]['style']
    
    def resize_images_to_common_size(self, photo_files, target_size=(720, 480)):
        resized_files = []
        for i, file in enumerate(photo_files):
            img = Image.open(file)
            img = img.convert('RGB')
            img = img.resize(target_size, Image.LANCZOS)
            temp_path = os.path.join(self.output_dir, f"resized_{i}.jpg")
            img.save(temp_path)
            resized_files.append(temp_path)
        return resized_files
    
    def create_video(self, photos_dir, emotion_analysis, output_filename='emotional_journey.mp4'):
        """Create a video with photos and generated music"""
        # Get list of photos
        photo_files = [os.path.join(photos_dir, result['file_name']) 
                      for result in emotion_analysis]
        if not photo_files:
            raise ValueError("No photos found for video generation.")
        
        # Resize images to a common size
        target_size = (720, 480)
        resized_files = self.resize_images_to_common_size(photo_files, target_size)

        # Create video clip
        clip = ImageSequenceClip(resized_files, fps=1/3)  # 3 seconds per photo
        
        # Generate music parameters
        music_params = self.generate_music_parameters(emotion_analysis)
        
        # TODO: Implement actual music generation using a music generation model
        # For now, we'll use a placeholder audio file
        # In a real implementation, you would use a model like MusicLM or Mubert API
        
        # Save video
        output_path = os.path.join(self.output_dir, output_filename)
        clip.write_videofile(output_path, audio=False)  # We'll add audio later
        
        return output_path 