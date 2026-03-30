import json
import os
from datetime import date, datetime, timedelta
from typing import Dict

from .config import (
    ATTEND_PATH,
    CLASS_START_DATE,
    CONSENT_PATH,
    FACE_DIR,
    RETENTION_DAYS,
    USERS_PATH,
)


def load_consent() -> Dict[str, str]:
    if not os.path.exists(CONSENT_PATH):
        return {}
    with open(CONSENT_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_consent(consent: Dict[str, str]) -> None:
    with open(CONSENT_PATH, "w", encoding="utf-8") as f:
        json.dump(consent, f, indent=2)


def load_users() -> Dict[str, Dict[str, str]]:
    if not os.path.exists(USERS_PATH):
        return {}
    with open(USERS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_users(users: Dict[str, Dict[str, str]]) -> None:
    with open(USERS_PATH, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2)


def parse_iso_date(value: str) -> date | None:
    try:
        return date.fromisoformat(value)
    except (ValueError, TypeError):
        return None


def get_class_start_date() -> date:
    configured = parse_iso_date(CLASS_START_DATE)
    if configured:
        return configured

    earliest: date | None = None
    if os.path.exists(ATTEND_PATH):
        with open(ATTEND_PATH, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split(",")
                if len(parts) < 2:
                    continue
                d = parse_iso_date(parts[1])
                if d is None:
                    continue
                if earliest is None or d < earliest:
                    earliest = d
    return earliest or date.today()


def cleanup_old_data() -> None:
    if RETENTION_DAYS <= 0:
        return
    cutoff = datetime.now() - timedelta(days=RETENTION_DAYS)

    # Clean attendance.csv
    if os.path.exists(ATTEND_PATH):
        kept = []
        with open(ATTEND_PATH, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split(",")
                if len(parts) >= 3:
                    try:
                        row_date = datetime.fromisoformat(parts[1])
                    except ValueError:
                        # Keep rows with unexpected format
                        kept.append(line)
                        continue
                    if row_date >= cutoff:
                        kept.append(line)
        with open(ATTEND_PATH, "w", encoding="utf-8") as f:
            f.writelines(kept)

    # Clean old face images
    removed_any = False
    if os.path.exists(FACE_DIR):
        for person in os.listdir(FACE_DIR):
            person_dir = os.path.join(FACE_DIR, person)
            if not os.path.isdir(person_dir):
                continue
            for fname in os.listdir(person_dir):
                if not fname.lower().endswith((".png", ".jpg", ".jpeg")):
                    continue
                fpath = os.path.join(person_dir, fname)
                stem = os.path.splitext(fname)[0]
                if stem.isdigit():
                    ts = datetime.fromtimestamp(int(stem))
                else:
                    ts = datetime.fromtimestamp(os.path.getmtime(fpath))
                if ts < cutoff:
                    os.remove(fpath)
                    removed_any = True
            if not os.listdir(person_dir):
                os.rmdir(person_dir)
                removed_any = True

    if removed_any:
        from .vision import train_model

        train_model()
