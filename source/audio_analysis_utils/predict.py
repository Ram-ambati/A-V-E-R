import os
import torch
import numpy as np
import source.audio_analysis_utils.utils as utils
import source.config as config
import source.audio_analysis_utils.preprocess_data as data

# ------------------------- CONFIGURATIONS ------------------------- #
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # Suppress TensorFlow logs
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'  # Disable unnecessary optimizations

# ------------------------- HELPER FUNCTIONS ------------------------- #

def round_probabilities(prob_dict, decimals=4):
    """Rounds probabilities to a specified number of decimal places."""
    return {emotion: round(prob, decimals) for emotion, prob in prob_dict.items()}

# ------------------------- MAIN PREDICTION FUNCTION ------------------------- #

def predict(input_file_name, model_save_path=config.AUDIO_MODEL_SAVE_PATH):
    """
    Predicts the emotion from an audio file.
    Returns structured prediction data with emotion, probability, and softmax probabilities.
    """
    if not input_file_name or not os.path.exists(input_file_name):
        return {"error": "Audio file not found."}

    audio_file_only = os.path.basename(input_file_name)
    best_hyperparameters = utils.load_dict_from_json(config.AUDIO_BEST_HP_JSON_SAVE_PATH)

    # 🧹 Clean the audio file
    cleaned_audio_file = os.path.join(config.OUTPUT_FOLDER_PATH, audio_file_only.replace('.wav', '_clean.wav'))
    data.clean_single(input_file_name, save_path=cleaned_audio_file, print_flag=False)

    # 🎵 Extract MFCC features
    extracted_mfcc = utils.extract_mfcc(
        cleaned_audio_file,
        N_FFT=best_hyperparameters['N_FFT'],
        NUM_MFCC=best_hyperparameters['NUM_MFCC'],
        HOP_LENGTH=best_hyperparameters['HOP_LENGTH']
    )
    extracted_mfcc = np.repeat(extracted_mfcc[np.newaxis, np.newaxis, :, :], 3, axis=1)  # Shape: (1, 3, MFCC, Time)
    extracted_mfcc = torch.from_numpy(extracted_mfcc).float().to(config.device)

    # 🧠 Model inference
    model = torch.load(model_save_path, map_location=config.device)
    model.eval()

    with torch.no_grad():
        prediction = torch.nn.functional.softmax(model(extracted_mfcc), dim=1)
        prediction_numpy = prediction[0].cpu().numpy()

    max_prob = float(np.max(prediction_numpy))
    predicted_index = int(np.argmax(prediction_numpy))
    emotion = config.EMOTION_INDEX.get(predicted_index, "Unknown")

    probabilities = round_probabilities(
        dict(zip(config.EMOTION_INDEX.values(), prediction_numpy.tolist()))
    )

    # 📝 Return structured result
    return {
        "emotion": emotion,
        "probability": round(max_prob, 4),
        "probabilities": probabilities
    }
