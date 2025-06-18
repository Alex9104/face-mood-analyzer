# Face Mood Analyzer

A stable, production-ready AI application that analyzes emotions in photos and generates corresponding musical journeys. Built with well-tested, stable versions of industry-standard libraries.

## Features
- Advanced face detection and recognition using RetinaFace
- Emotion analysis across multiple photos (7 basic emotions)
- Face quality assessment and filtering
- Emotion-based music generation
- Interactive web interface
- Video generation with emotional music
- Support for multiple input photos
- Real-time processing and analysis

## Technical Stack
- TensorFlow 2.12.0
- PyTorch 2.0.1
- OpenCV 4.8.0
- DeepFace 0.0.75
- Flask 2.3.3

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Place your photos in the `uploads` directory

4. Run the application:
```bash
python app.py
```

## Project Structure
- `app.py`: Main Flask application and web interface
- `emotion_analyzer.py`: Face detection and emotion analysis module
- `music_generator.py`: Music generation based on emotional patterns
- `static/`: Web assets (CSS, JavaScript, images)
- `templates/`: HTML templates for the web interface
- `uploads/`: Directory for input photos
- `output/`: Directory for generated content

## Usage
1. Place your photos in the `uploads` directory
2. Run the application
3. Access the web interface at `http://localhost:5000`
4. Upload reference photos of the person to track
5. Upload photos to analyze
6. The system will process your photos and generate a musical journey

## Requirements
- Python 3.8+
- CUDA-capable GPU (recommended for faster processing)
- Modern web browser
- 4GB+ RAM
- 10GB+ disk space

## Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

## License
This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments
- Built with Flask
- Uses deep learning for emotion detection
- Music generation powered by machine learning algorithms 