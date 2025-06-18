from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="face-mood-analyzer",
    version="1.0.2",
    author="Akshay Chikhalkar",
    author_email="akshaychikhalkar15@gmail.com",
    description="AI-powered emotion analyzer that detects faces in photos and generates corresponding music",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/akshaychikhalkar/face-mood-analyzer",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.8",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Scientific/Engineering :: Image Recognition",
        "Topic :: Multimedia :: Sound/Audio :: Analysis",
    ],
    python_requires=">=3.8",
    install_requires=[
        "tensorflow==2.12.0",
        "numpy==1.23.5",
        "deepface==0.0.75",
        "opencv-python-headless==4.8.0.76",
        "pillow==10.0.0",
        "flask==2.3.3",
        "python-dotenv==1.0.0",
        "moviepy==1.0.3",
        "scikit-learn==1.3.0",
        "torch==2.0.1",
        "torchvision==0.15.2",
        "transformers==4.31.0",
    ],
    license="MIT",
) 