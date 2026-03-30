import os

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(APP_ROOT, "data")
FACE_DIR = os.path.join(DATA_DIR, "faces")
MODEL_PATH = os.path.join(DATA_DIR, "model.yml")
LABELS_PATH = os.path.join(DATA_DIR, "labels.json")
ATTEND_PATH = os.path.join(DATA_DIR, "attendance.csv")
CONSENT_PATH = os.path.join(DATA_DIR, "consent.json")
USERS_PATH = os.path.join(DATA_DIR, "users.json")

CLASS_START_DATE = os.getenv("CLASS_START_DATE", "").strip()

# Keep face/attendance data forever by default.
# Set RETENTION_DAYS env var to a positive integer if you want auto-cleanup.
RETENTION_DAYS = int(os.getenv("RETENTION_DAYS", "0"))
