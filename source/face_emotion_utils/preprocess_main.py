import source.config as config
import source.face_emotion_utils.face_mesh as face_mesh
import source.face_emotion_utils.utils as utils
import source.face_emotion_utils.face_config as face_config
import cv2
import os
import numpy as np
import librosa

# Function to extract MFCC (Mel-frequency cepstral coefficients) from audio files
def extract_mfccs(audio_path):
    # Load the audio file using librosa
    y, sr = librosa.load(audio_path, sr=16000)
    
    # Extract MFCC features from the audio
    mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13, hop_length=512, n_fft=2048)
    
    # Transpose the MFCC array to match expected shape (126, 13)
    mfccs = mfccs.T
    assert mfccs.shape == (126, 13), f"Unexpected shape for MFCCs: {mfccs.shape}"
    
    return np.array(mfccs)

# Function to load preprocessed data from disk
def load_preprocessed_data(
        normalise,
        input_path=config.PREPROCESSED_IMAGES_FOLDER_PATH,
        save_name_suffix="_default",
):
    # Load preprocessed data from files
    print(f"\nLoading preprocessed files from: {input_path}")
    save_folder = input_path

    # Load numpy arrays for landmarks, images, and labels
    X_landmark_depth = np.load(save_folder + f"X{save_name_suffix}.npy")
    X_images = np.load(save_folder + f"X_images{save_name_suffix}.npy")
    Y = np.load(save_folder + f"Y{save_name_suffix}.npy")
    print("Load complete")

    # Normalize landmark distances if requested
    if normalise:
        print("\nNormalising distances and images")
        X_landmark_depth = np.array(utils.normalise_lists(X_landmark_depth, save_min_max=True, use_minmax=False, print_flag=False))
        print("Normalisation complete")

    # Normalize images by scaling to [0, 1]
    X_images = X_images / 255.0

    return X_landmark_depth, X_images, Y

# Function to save preprocessed data to disk
def save_preprocessed_data(
        X_landmark_depth,
        X_images,
        Y,
        save_name_suffix='_default',
        output_path=config.PREPROCESSED_IMAGES_FOLDER_PATH,
):
    print("\nConverting to numpy arrays")
    # Convert lists to numpy arrays
    X_landmark_depth = np.array(X_landmark_depth)
    X_images = np.array(X_images)
    Y = np.array(Y)
    print("Conversion complete")

    # Print sample data for verification
    print(X_landmark_depth[:5])
    print(X_images[:5])
    print(Y[:5])
    print("\nShapes of arrays:")
    print(X_landmark_depth.shape)
    print(X_images.shape)
    print(Y.shape)

    # Save data to disk
    print(f"\nSaving preprocessed files to: {output_path}")
    save_folder = output_path
    utils.create_folder(new_path=save_folder)

    # Save arrays as .npy files
    np.save(save_folder + f"X{save_name_suffix}.npy", X_landmark_depth)
    np.save(save_folder + f"X_images{save_name_suffix}.npy", X_images)
    np.save(save_folder + f"Y{save_name_suffix}.npy", Y)
    print("Save complete")

# Function to preprocess images, extract face landmarks and labels
def preprocess_images(
        original_images_folders=config.ALL_EXTRACTED_FACES_FOLDERS,
        output_path=config.PREPROCESSED_IMAGES_FOLDER_PATH,
        print_flag=True,
):
    # Initialize lists to store data
    all_face_land_dists_depths_X = []  # Landmarks and depth distances
    all_face_images_X = []  # Grayscale face images
    all_face_emotions_Y = []  # Emotion labels as softmax vectors

    # Count the total number of images to process
    all_cnt = 0
    for folder in original_images_folders:
        for file in os.listdir(folder):
            all_cnt += 1

    detected_cnt = 1  # Counter for detected faces
    so_far_cnt = 0  # Counter for processed files
    for folder in original_images_folders:
        for file in os.listdir(folder):
            if print_flag:
                so_far_cnt += 1
                print(f"\nPreprocessing file {so_far_cnt}/{all_cnt}: {folder.split(config.ls)[-2]}/{file}")

            image = cv2.imread(folder + config.ls + file)

            # Get face mesh and cropped face
            results = face_mesh.get_mesh(image.copy(), showImg=False, upscale_landmarks=False)
            if results is None:
                if print_flag:
                    print("No mesh detected, skipping file", file)
                continue

            land_dists, image = results

            # Convert cropped image to grayscale
            if len(image.shape) > 2:
                grey_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                grey_image = image
            grey_image = cv2.resize(grey_image, (face_config.FACE_SIZE, face_config.FACE_SIZE))

            # Get face emotion label
            emotion_label = config.FULL_EMOTION_INDEX_REVERSE[file.split("_")[2].split(".")[0]]
            emotion_label_softmax = utils.get_as_softmax(emotion_label, config.NON_SIMPLIFIED_SOFTMAX_LEN)

            if print_flag:
                print(f"Image shape: {grey_image.shape}")
                print(f"Emotion label softmax: {emotion_label}, {emotion_label_softmax}")

            # Add to list
            all_face_land_dists_depths_X.append(land_dists)
            all_face_images_X.append(grey_image)
            all_face_emotions_Y.append(emotion_label_softmax)
            detected_cnt += 1

    print("Saving final data to file")
    # Save remaining data
    save_preprocessed_data(
        all_face_land_dists_depths_X,
        all_face_images_X,
        all_face_emotions_Y,
        output_path=output_path,
        save_name_suffix="_default",
    )
    print("Preprocessing complete")

    return all_face_land_dists_depths_X, all_face_images_X, all_face_emotions_Y
