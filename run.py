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
import os

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


# ------------------------- AUDIO ANALYSIS ------------------------- #
def extract_audio(video_file):
    """Extract audio from a video file."""
    try:
        video = mp.VideoFileClip(video_file)

        # ✅ Check if video has an audio track
        if video.audio is None:
            print(" No audio stream found in the video.")
            return None

        audio_file = os.path.join(
            config.INPUT_FOLDER_PATH,
            os.path.splitext(os.path.basename(video_file))[0] + ".wav"
        )

        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            video.audio.write_audiofile(audio_file)

        video.reader.close()
        return audio_file

    except Exception as e:
        print(f"❌ Error extracting audio: {repr(e)}")
        return None



def handle_audio_analysis(audio_file):
    """Perform audio emotion analysis."""
    result = audio_predict.predict(audio_file)
    save_analysis_results(result, audio_file)
    print(f" AUDIO ANALYSIS RESULT:\n Emotion: {result['emotion']}\n Probability: {result['probability']}\n Probabilities: {json.dumps(result['probabilities'], indent=4)}")


# ------------------------- IMAGE ANALYSIS ------------------------- #

def handle_image_analysis(image_file):
    """Perform image emotion analysis."""
    if not os.path.isfile(image_file):
        print("❌ Error: Image file not found.")
        return

    image = cv2.imread(image_file)
    if image is None:
        print("❌ Error: Failed to read image.")
        return

    frame_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    prediction_result = face_predict.predict(frame_rgb, video_mode=False)

    result = {
        "emotion": prediction_result["emotion"],
        "probabilities": prediction_result["probabilities"]
    }

    save_analysis_results(result, image_file)
    print(f" IMAGE ANALYSIS RESULT:\n Emotion: {result['emotion']}\n Probabilities: {json.dumps(result['probabilities'], indent=4)}")


# ------------------------- VIDEO ANALYSIS ------------------------- #

def handle_face_analysis(video_file):
    """Perform frame-wise face emotion analysis on a video."""
    if not video_file.lower().endswith('.mp4'):
        print("❌ Error: Only .mp4 files are supported.")
        return

    video = cv2.VideoCapture(video_file)
    if not video.isOpened():
        print("❌ Error: Couldn't open video file.")
        return

    fps_in = video.get(cv2.CAP_PROP_FPS) or 30
    analysis_results = []
    frame_count = 0

    while True:
        for _ in range(10):  # Process every 10th frame
            ret, _ = video.read()
            if not ret:
                break

        ret, frame = video.read()
        if not ret:
            break

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        prediction_result = face_predict.predict(frame_rgb, video_mode=False)

        analysis_results.append({
            "frame": frame_count,
            "emotion": prediction_result["emotion"],
            "probabilities": prediction_result["probabilities"]
        })

        frame_count += 10

    video.release()
    save_analysis_results(analysis_results, video_file)


# ------------------------- COMBINED ANALYSIS ------------------------- #

# ------------------------- COMBINED ANALYSIS ------------------------- #

def handle_combined_analysis(video_file):
    """Perform combined audio and video emotion analysis."""
    results = {}

    # 🔊 AUDIO ANALYSIS
    audio_file = extract_audio(video_file)
    if audio_file and os.path.isfile(audio_file):
        print(f"Starting audio analysis on: {audio_file}")
        results["audio_analysis"] = audio_predict.predict(audio_file)
        print(f"Audio analysis completed: {results['audio_analysis']}")
    else:
        print("Audio extraction failed or audio file not found. Skipping audio analysis.")

    # 🎥 VIDEO ANALYSIS
    video_results = []
    video = cv2.VideoCapture(video_file)
    frame_count = 0

    while True:
        # Skip 10 frames to reduce processing load
        for _ in range(10):
            ret, _ = video.read()
            if not ret:
                break

        ret, frame = video.read()
        if not ret:
            break

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        prediction_result = face_predict.predict(frame_rgb, video_mode=False)
        video_results.append({
            "frame": frame_count,
            "emotion": prediction_result["emotion"],
            "probabilities": prediction_result["probabilities"]
        })

        frame_count += 10

    video.release()
    results["video_analysis"] = video_results

    # 📝 SAVE ANALYSIS RESULTS
    result_filename = f"{os.path.splitext(os.path.basename(video_file))[0]}_analysis.json"
    result_path = os.path.join(RESULTS_FOLDER, result_filename)

    with open(result_path, "w") as f:
        json.dump(results, f, indent=4)

    print(f" Analysis saved: {result_path}")
    print("COMBINED ANALYSIS COMPLETED")



# ------------------------- MAIN FUNCTION ------------------------- #

def print_usage():
    """Display usage instructions."""
    print("\n Usage:")
    print("  python run.py -VA <video.mp4>   # Video Analysis")
    print("  python run.py -AA <audio.mp3>   # Audio Analysis")
    print("  python run.py -IA <image.png>   # Image Analysis")
    print("  python run.py -CA <video.mp4>   # Combined Analysis")
    print("  python run.py <file_name>       # Auto-detect and process file\n")


def main(file_name):
    """Auto-detect file type and perform analysis."""
    full_file_path = resolve_file_path(file_name)
    if not full_file_path:
        print(f"❌ Error: File '{file_name}' not found.")
        return

    if file_name.lower().endswith((".png", ".jpg", ".jpeg")):
        handle_image_analysis(full_file_path)
    elif file_name.lower().endswith((".mp3", ".wav")):
        handle_audio_analysis(full_file_path)
    elif file_name.lower().endswith(".mp4"):
        handle_combined_analysis(full_file_path)
    else:
        print("❌ Unsupported file type.")
        print_usage()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)

    create_folders()

    if len(sys.argv) == 3:
        mode, file_name = sys.argv[1], sys.argv[2]
        full_file_path = resolve_file_path(file_name)

        if not full_file_path:
            print(f"❌ Error: File '{file_name}' not found.")
            sys.exit(1)

        if mode == "-VA":
            handle_face_analysis(full_file_path)
        elif mode == "-AA":
            handle_audio_analysis(full_file_path)
        elif mode == "-IA":
            handle_image_analysis(full_file_path)
        elif mode == "-CA":
            handle_combined_analysis(full_file_path)
        else:
            print("❌ Invalid command or file type.")
            print_usage()

    elif len(sys.argv) == 2:
        main(sys.argv[1])
    else:
        print("\n❌ Invalid command format.")
        print_usage()
