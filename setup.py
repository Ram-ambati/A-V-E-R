import os
import config

#  DEFINE RESULTS FOLDER
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
