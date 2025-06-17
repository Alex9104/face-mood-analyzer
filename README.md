# Emotion-Based Music Journey Generator

A creative application that analyzes emotions in photos and generates a musical journey based on the detected emotions. Perfect for creating emotional storytelling through music and visual content.

## Features
- Face detection and emotion analysis across multiple photos
- Emotion-based music generation using machine learning
- Interactive web interface for visualization
- Timeline-based emotional journey presentation
- Support for multiple input photos
- Real-time emotion analysis and music generation

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
4. The system will process your photos and generate a musical journey

## Requirements
- Python 3.8+
- CUDA-capable GPU (recommended for faster processing)
- Modern web browser

## Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

## License
This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments
- Built with Flask
- Uses deep learning for emotion detection
- Music generation powered by machine learning algorithms 