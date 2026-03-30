import base64
import os
import time
from typing import Dict, List, Tuple

import cv2
import numpy as np

from .config import FACE_DIR, LABELS_PATH, MODEL_PATH

face_cascade = cv2.CascadeClassifier(
    os.path.join(cv2.data.haarcascades, "haarcascade_frontalface_default.xml")
)


def decode_image(data_url: str) -> np.ndarray:
    if "," in data_url:
        data_url = data_url.split(",", 1)[1]
    img_bytes = base64.b64decode(data_url)
    img = np.frombuffer(img_bytes, dtype=np.uint8)
    return cv2.imdecode(img, cv2.IMREAD_COLOR)


def detect_face(gray: np.ndarray) -> Tuple[int, int, int, int] | None:
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
    if len(faces) == 0:
        return None
    faces = sorted(faces, key=lambda f: f[2] * f[3], reverse=True)
    return tuple(map(int, faces[0]))


def save_face_image(name: str, gray: np.ndarray, face_box) -> str:
    x, y, w, h = face_box
    roi = gray[y : y + h, x : x + w]
    person_dir = os.path.join(FACE_DIR, name)
    os.makedirs(person_dir, exist_ok=True)
    filename = f"{int(time.time())}.png"
    cv2.imwrite(os.path.join(person_dir, filename), roi)
    return filename


def get_latest_face_image_path(name: str) -> str | None:
    person_dir = os.path.join(FACE_DIR, name)
    if not os.path.isdir(person_dir):
        return None
    files = [
        os.path.join(person_dir, f)
        for f in os.listdir(person_dir)
        if f.lower().endswith((".png", ".jpg", ".jpeg"))
    ]
    if not files:
        return None
    return max(files, key=os.path.getmtime)


def train_model() -> None:
    labels = {}
    label_counter = 0
    images: List[np.ndarray] = []
    targets: List[int] = []

    for person in sorted(os.listdir(FACE_DIR)):
        person_dir = os.path.join(FACE_DIR, person)
        if not os.path.isdir(person_dir):
            continue
        labels[person] = label_counter
        for fname in os.listdir(person_dir):
            if not fname.lower().endswith((".png", ".jpg", ".jpeg")):
                continue
            img_path = os.path.join(person_dir, fname)
            img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
            if img is None:
                continue
            images.append(img)
            targets.append(label_counter)
        label_counter += 1

    if not images:
        if os.path.exists(MODEL_PATH):
            os.remove(MODEL_PATH)
        if os.path.exists(LABELS_PATH):
            os.remove(LABELS_PATH)
        return

    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.train(images, np.array(targets))
    recognizer.save(MODEL_PATH)
    save_labels(labels)


def load_model():
    if not os.path.exists(MODEL_PATH) or not os.path.exists(LABELS_PATH):
        return None, {}
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read(MODEL_PATH)
    return recognizer, load_labels()


def ensure_model_ready():
    if not os.path.exists(FACE_DIR):
        return None, {}
    recognizer, labels = load_model()
    if recognizer is not None and labels:
        return recognizer, labels
    train_model()
    return load_model()


def load_labels() -> Dict[str, int]:
    if not os.path.exists(LABELS_PATH):
        return {}
    import json

    with open(LABELS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_labels(labels: Dict[str, int]) -> None:
    import json

    with open(LABELS_PATH, "w", encoding="utf-8") as f:
        json.dump(labels, f, indent=2)
