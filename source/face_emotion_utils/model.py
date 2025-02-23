import cv2
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torchvision.models import *
import numpy as np
import os

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # Suppress warnings and info logs
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'  # Disable TensorFlow optimizations

import source.config as config
import source.face_emotion_utils.utils as utils
import source.face_emotion_utils.face_config as face_config

device = config.device
SOFTMAX_LEN = face_config.softmax_len
MODEL_SAVE_PATH = config.FACE_MODEL_SAVE_PATH

class CustomModelBase(nn.Module):
    """
    Base class for the model with a custom training/validation step.
    """
    def __init__(self, class_weights):
        super(CustomModelBase, self).__init__()
        self.class_weights = class_weights

    def training_step(self, batch):
        images, lands, labels = batch
        out = self(images, lands)  # Generate predictions
        loss = F.cross_entropy(out, labels, weight=self.class_weights)  # Calculate loss with class weights
        acc = utils.accuracy(out, labels)  # Calculate accuracy
        return loss, acc

    def validation_step(self, batch):
        images, lands, labels = batch
        out = self(images, lands)  # Generate predictions
        loss = F.cross_entropy(out, labels, weight=self.class_weights)  # Calculate loss with class weights
        acc = utils.accuracy(out, labels)  # Calculate accuracy
        return {'val_loss': loss.detach(), 'val_acc': acc}


class CustomModel(CustomModelBase):
    """
    A custom model that includes convolutional base and fully connected layers.
    """
    def __init__(
            self,
            input_shapes,
            dropout_rate,
            dense_units,
            num_layers,
            use_landmarks,
            class_weights=None,
            device=device,
    ):
        if class_weights is None:
            class_weights = torch.ones(SOFTMAX_LEN)
        else:
            class_weights = torch.tensor(class_weights)

        class_weights = class_weights.to(device)

        super(CustomModel, self).__init__(class_weights=class_weights)

        self.use_landmarks = use_landmarks
        input_shape, input_shape_2 = input_shapes

        # Base conv model setup
        self.base_model_conv = self.get_conv_model("resnet50", pretrained=True)
        self.base_model = nn.Sequential(*list(self.base_model_conv.children())[:-1])  # Remove final layer
        self.flatten = nn.Flatten()

        # Output size from base model
        with torch.no_grad():
            sample_input = torch.randn(1, input_shape[0], input_shape[1], input_shape[2])
            self.base_output_size = self.base_model(sample_input).numel()

        # Fully connected layers setup
        dense_input_size = self.base_output_size + input_shape_2
        dense_layers = []
        for _ in range(num_layers - 1):
            dense_layer = [
                nn.Linear(dense_units, dense_units),
                nn.ReLU(),
                nn.Dropout(dropout_rate)
            ]
            dense_layers.extend(dense_layer)

        self.fc = nn.Sequential(
            nn.Linear(dense_input_size, dense_units),
            nn.BatchNorm1d(dense_units),
            *dense_layers,
        )

        self.out_lands = nn.Linear(dense_units, SOFTMAX_LEN)
        self.out_no_lands = nn.Linear(self.base_output_size, SOFTMAX_LEN)

    def get_conv_model(self, conv_model_name, pretrained=True):
        if conv_model_name == "resnet50":
            return resnet50(pretrained=pretrained)
        else:
            raise ValueError("Unsupported model name")

    def forward(self, x1, x2):
        x1 = self.base_model(x1)
        x1 = self.flatten(x1)

        if self.use_landmarks:
            x = torch.cat((x1, x2), dim=1)
            x = self.fc(x)
            x = self.out_lands(x)
        else:
            x = self.out_no_lands(x1)

        return x


# Removed the training and hyperparameter optimization code

