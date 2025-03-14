import os
import sys
import cv2
import json
import torch
import moviepy.editor as mp
import contextlib
import io
import source.audio_analysis_utils.predict as audio_predict
import source.face_emotion_utils.predict as face_predict
import source.config as config

# 📁 DEFINE RESULTS FOLDER
RESULTS_FOLDER = os.path.abspath("./AnalysisResults")
os.makedirs(RESULTS_FOLDER, exist_ok=True)  # Create folder if it doesn't exist

# ------------------------- CONFIGURATIONS ------------------------- #
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

# ------------------------- UTILITY FUNCTIONS ------------------------- #

def create_folders():
    """Create required directories if they don't exist."""
    paths = [
        config.INPUT_FOLDER_PATH,
        config.OUTPUT_FOLDER_PATH,
        config.MODEL_FOLDER_PATH,
        config.DATA_FOLDER_PATH,
        config.PREPROCESSED_IMAGES_FOLDER_PATH,
        config.PREPROCESSED_AUDIO_FOLDER_PATH,
        config.CLEANED_LABELLED_AUDIO_FOLDER_PATH,
        config.AUDIO_MODEL_FOLDER_PATH,
        config.FACE_MODEL_FOLDER_PATH,
        os.path.join(config.MAIN_PATH, "VideoBufferFolder"),
        os.path.join(config.MAIN_PATH, "AnalysisResults"),
    ]
    for path in paths:
        os.makedirs(path, exist_ok=True)


def resolve_file_path(file_name):
    """Resolve file path from given name or default input folder."""
    if os.path.isfile(file_name):
        return os.path.abspath(file_name)
    candidate_path = os.path.abspath(os.path.join(config.INPUT_FOLDER_PATH, file_name))
    return candidate_path if os.path.isfile(candidate_path) else None


def save_analysis_results(result_data, file_name):
    """Save analysis results as a JSON file."""
    result_file = os.path.join(
        config.MAIN_PATH, "AnalysisResults",
        f"{os.path.splitext(os.path.basename(file_name))[0]}_analysis.json"
    )
    with open(result_file, "w") as f:
        json.dump(result_data, f, indent=4)
    print(f" Analysis saved: {result_file}")

# Call create_folders to ensure required directories are created
create_folders()
