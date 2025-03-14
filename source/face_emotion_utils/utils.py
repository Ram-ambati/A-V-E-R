import cv2
import math
import numpy as np
import traceback
import pickle
import source.config as config
import os
import json
from sklearn.utils import shuffle
from sklearn.preprocessing import MultiLabelBinarizer

import source.face_emotion_utils.face_config as face_config
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # Suppress warnings and info logs
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'  # Disable TensorFlow optimizations

# save pickle object
def save_object(file_name, object):
    with open(file_name, 'wb') as f:
        pickle.dump(object, f)

# load pickle object
def load_object(file_name):
    with open(file_name, 'rb') as f:
        object = pickle.load(f)
    return object

def save_dict_as_json(file_name, dict, over_write=False):
    if os.path.exists(file_name) and over_write:
        with open(file_name) as f:
            existing_dict = json.load(f)

        existing_dict.update(dict)

        with open(file_name, 'w') as f:
            json.dump(existing_dict, f)
    else:
        with open(file_name, 'w') as f:
            json.dump(dict, f)

def load_dict_from_json(file_name):
    with open(file_name) as f:
        return json.load(f)

def create_folder(new_path):
    if not os.path.exists(new_path):
        print("Creating folder " + new_path)
        os.makedirs(new_path)

# Goal of this function is to return a number between 1 and 0. Default is division with max, but you can use minmax_scaler as well
def normalise_lists(lists, save_min_max=False, norm_range=(0, 1), use_minmax=False, print_flag=True):
    def normalise(list, X_min, X_max, use_minmax=use_minmax):
        X = np.array(list)
        if use_minmax:
            X_std = (X - X_min) / (X_max - X_min)
            X_norm = X_std * (max_norm_range - min_norm_range) + min_norm_range
        else:
            X_norm = X / X_max
        return X_norm

    min_norm_range, max_norm_range = norm_range

    if save_min_max:
        X_min = np.min(lists)
        X_max = np.max(lists)
        save_object(config.FACE_NORM_SCALAR_SAVE_PATH, (X_min, X_max))
    else:
        try:
            (X_min, X_max) = load_object(config.FACE_NORM_SCALAR_SAVE_PATH)
        except:
            traceback.print_exc()
            raise Exception("Make sure NORM_SCALAR was saved correctly during training")

    #if print_flag:
        #print(f'Min: {X_min}, Max: {X_max}, ("minmax=", {use_minmax})')

    normalised_lists = [normalise(l, X_min, X_max, use_minmax) for l in lists]
    return normalised_lists

def inverse_normalise(list, use_minmax=False):
    X = np.array(list).squeeze()
    (X_min, X_max) = load_object(config.NORM_SCALAR_SAVE_PATH)

    if use_minmax:
        return (X * (X_max - X_min)) + X_min
    else:
        return X * X_max

def euclidean_distance(coord_1, coord_2):
    x1, y1 = coord_1
    x2, y2 = coord_2
    return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)

def compute_distances(landmarks):
    dists = [euclidean_distance((landmark[0], landmark[1]), (landmark[0], landmark[1])) for landmark in landmarks]
    return dists

def get_as_softmax(label, count):
    full_soft = np.zeros(count)
    full_soft[label] = 1
    return full_soft

def pixel_to_image(pixels, name, len=48):
    pixels = list(str(pixels).split(" "))
    img_ar = []
    row = []
    for i in range(len(pixels)):
        row.append(int(pixels[i]))
        if ((i + 1) % len) == 0:
            img_ar.append(row)
            row = []
    img = np.array(img_ar)
    cv2.imwrite(name + ".png", img)
    return img_ar

def get_input_shape(which_input):
    if which_input == 'landmarks_depths':
        return (face_config.LANDMARK_COMBINATIONS_DEPTHS_CNT)
    elif which_input == 'image':
        return (3, face_config.FACE_SIZE, face_config.FACE_SIZE)

def shuffle_train_data(array, seed=0):
    return shuffle(array, random_state=seed)

def find_filename_match(known_filename, directory):
    files_list = os.listdir(directory)
    for file_name in files_list:
        if known_filename in file_name:
            return os.path.join(directory, file_name)
    print("NO MATCH FOUND FOR: ", known_filename, "IN", directory)
    return None
