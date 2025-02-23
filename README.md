# A V E R (Audio Visual Emotion Recognition)

A V E R is a web application built with Flask that performs emotion recognition from audio, video, and images. It provides a user-friendly interface where users can upload files for analysis, and the system will process and return the analysis results. The system leverages deep learning models for emotion detection and visualizes the outcomes in an interactive and insightful way.

## Features

- **Audio Emotion Recognition**: Detects emotions from audio files.
- **Face Emotion Recognition**: Analyzes facial expressions to infer emotions.
- **Video Emotion Recognition**: Processes video files to detect emotions from both the audio and video frames.
- **Combined Analysis**: Analyzes both audio and video for a comprehensive emotion analysis.
- **Interactive Frontend**: Upload files via drag-and-drop or form submission for real-time analysis.
- **Analysis Results**: Displays results in tables and graphs, such as average emotions and emotion trends over time.

## Installation

### Prerequisites

- Python 3.10+
- Flask
- PyTorch
- OpenCV
- MoviePy
- TensorFlow (optional, depending on your model)
- Other dependencies listed in `requirements.txt`

### Steps to Set Up

1.Clone the repository:

    git clone https://github.com/Ram-ambati/A-V-E-R.git
    
2.Create the virtual environment
   
    python -m venv venv
    
3.Activate the virtual environment
  On Windows activate your env

    .\venv\Scripts\activate
    
4.Install the required dependencies:

    pip install -r requirements.txt

5.Run the `setup.py`  (once) to create folders and set paths to models 

    python setup.py
    
6.Run the Flask application:

    python app.py

The app will be accessible at `http://127.0.0.1:5000/`.


## Folder Structure

The directory structure of the project is as follows, so make sure you downloaded everything:
```
├── .git/
├── __pycache__/
├── AnalysisResults/
├── data/
├── input_files/
├── models/
├── output_files/
├── source/
├── static/
├── templates/
├── VideoBufferFolder/
├── .gitattributes
├── app.py
├── requirements.txt
├── run.py
└── setup.py
```



## How It Works

1. **File Upload**: Users upload an audio, video, or image file through the frontend interface.
2. **Analysis**: Based on the selected analysis type, the backend calls the appropriate functions from the `audio_analysis_utils`, `face_emotion_utils`, or a combined analysis script.
3. **Result Processing**: The results are structured, saved in JSON format, and displayed to the user.
4. **Visualization**: Results such as emotion trends are visualized using tables and charts.

## API Endpoints

- **POST /upload**: Uploads files (image, audio, video) for analysis.
- **GET /analysis/{file_name}**: Retrieves the analysis results in JSON format for the specified file.

