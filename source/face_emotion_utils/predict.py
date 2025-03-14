import os
import cv2
import numpy as np
import torch
import torch.nn.functional as F
from source.face_emotion_utils.face_mesh import get_mesh
from source.config import FACE_MODEL_SAVE_PATH, OUTPUT_FOLDER_PATH, device, SIMPLIFIED_EMOTIONS_INDEX

# ------------------------- CONFIGURATIONS ------------------------- #
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # Suppress TensorFlow logs
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'  # Disable unnecessary optimizations

FACE_SQUARE_SIZE = 64

# ------------------------- HELPER FUNCTIONS ------------------------- #

def round_probabilities(prob_dict, decimals=4):
    """Rounds probabilities to a specified number of decimal places for cleaner output."""
    return {emotion: round(prob, decimals) for emotion, prob in prob_dict.items()}

def _get_prediction(img, model, grad_cam=True):
    """
    Processes an image and returns the predicted emotion, max probability, and rounded softmax probabilities.
    """
    try:
        result = get_mesh(
            image=cv2.cvtColor(img, cv2.COLOR_RGB2BGR),
            upscale_landmarks=True,
            showImg=False,
            print_flag=False,  # Removed unnecessary prints
            return_mesh=True
        )
    except Exception as e:
        raise Exception(f"Face mesh failed: {e}")

    if result is None:
        return None, 0.0, {}

    landmarks_depths, face_input_org, _, _ = result

    # Prepare face input
    face_input = cv2.cvtColor(face_input_org, cv2.COLOR_BGR2GRAY)
    face_input = cv2.resize(face_input, (FACE_SQUARE_SIZE, FACE_SQUARE_SIZE))
    face_input = np.repeat(face_input[np.newaxis, :, :], 3, axis=0)  # Shape: (3, 64, 64)
    x = face_input / 255.0
    x = x.reshape((1,) + x.shape)  # Shape: (1, 3, 64, 64)
    landmarks_depths = np.array(landmarks_depths)[np.newaxis, :]

    # Model prediction
    pred = model(
        torch.from_numpy(x).float().to(device),
        torch.from_numpy(landmarks_depths).float().to(device)
    )
    pred = F.softmax(pred, dim=1)

    pred_numpy = pred[0].detach().cpu().numpy()
    prediction_index = int(pred_numpy.argmax())
    predicted_emotion = SIMPLIFIED_EMOTIONS_INDEX.get(prediction_index, 'Unknown')
    max_prob = float(pred_numpy.max())

    probabilities = round_probabilities({
        SIMPLIFIED_EMOTIONS_INDEX.get(i, f"Class_{i}"): float(prob)
        for i, prob in enumerate(pred_numpy)
    })

    return predicted_emotion, max_prob, probabilities

# ------------------------- MAIN PREDICTION FUNCTION ------------------------- #

def predict(image, video_mode=False, grad_cam=True):
    """
    Loads the model, processes the input image, and returns structured prediction data.
    """
    if isinstance(image, str):
        image = cv2.imread(image)
        if image is None:
            raise ValueError(f"Image not found at: {image}")
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    model = torch.load(FACE_MODEL_SAVE_PATH, map_location=device)
    model.to(device).eval()

    predicted_emotion, max_prob, probabilities = _get_prediction(image, model, grad_cam=grad_cam)

    return {
        "emotion": predicted_emotion,
        "simplified_emotion": predicted_emotion,  # Already simplified via SIMPLIFIED_EMOTIONS_INDEX
        "probability": round(max_prob, 4),
        "probabilities": probabilities
    }
