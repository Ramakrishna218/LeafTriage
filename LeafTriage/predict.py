import json
from pathlib import Path

import numpy as np
import tensorflow as tf
from PIL import Image

BASE = Path(__file__).parent
MODEL_PATH = BASE / "models" / "tomato_model_clean.keras"
LABEL_PATH = BASE / "models" / "class_names.json"

def load_model_and_labels():
    model = tf.keras.models.load_model(MODEL_PATH)

    with open(LABEL_PATH, encoding="utf-8") as f:
        labels = json.load(f)

    if model.output_shape[-1] != len(labels):
        raise ValueError("Model output and class labels do not match.")

    return model, labels

def predict_image(image, model, labels):
    image = image.convert("RGB").resize((224, 224))
    array = np.asarray(image, dtype=np.float32)

    array = tf.keras.applications.mobilenet_v2.preprocess_input(array)
    scores = model.predict(np.expand_dims(array, axis=0), verbose=0)[0]

    order = np.argsort(scores)[::-1]

    return [
        {"class": labels[int(i)], "score": float(scores[i])}
        for i in order
    ]
