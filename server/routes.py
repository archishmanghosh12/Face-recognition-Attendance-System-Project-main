from datetime import date, datetime
from typing import Dict

import os
import cv2
from flask import Blueprint, jsonify, render_template, request

from .config import ATTEND_PATH, FACE_DIR, RETENTION_DAYS
from .storage import (
    cleanup_old_data,
    get_class_start_date,
    load_consent,
    load_users,
    save_consent,
    save_users,
)
from .vision import (
    decode_image,
    detect_face,
    ensure_model_ready,
    get_latest_face_image_path,
    save_face_image,
    train_model,
)
import base64

routes = Blueprint("routes", __name__)


def _mark_attendance(name: str) -> None:
    today = date.today().isoformat()
    existing = set()
    if os.path.exists(ATTEND_PATH):
        with open(ATTEND_PATH, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split(",")
                if len(parts) >= 2:
                    existing.add((parts[0], parts[1]))
    if (name, today) in existing:
        return
    now = datetime.now().strftime("%H:%M:%S")
    with open(ATTEND_PATH, "a", encoding="utf-8") as f:
        f.write(f"{name},{today},{now}\n")


@routes.get("/")
def index():
    return render_template("index.html")


@routes.post("/api/register")
def register():
    cleanup_old_data()
    data = request.get_json(force=True)
    name = (data.get("name") or "").strip()
    roll_number = (data.get("rollNumber") or "").strip()
    student_class = (data.get("studentClass") or "").strip()
    section = (data.get("section") or "").strip()
    branch = (data.get("branch") or "").strip()
    image = data.get("image")
    consent = bool(data.get("consent"))
    if not name or not image:
        return jsonify({"ok": False, "error": "Name and image are required."}), 400
    if not roll_number or not student_class or not section or not branch:
        return jsonify(
            {"ok": False, "error": "Roll number, class, section and branch are required."}
        ), 400
    if not consent:
        return jsonify({"ok": False, "error": "Consent is required to register."}), 400

    frame = decode_image(image)
    if frame is None:
        return jsonify({"ok": False, "error": "Invalid image data."}), 400

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    face = detect_face(gray)
    if face is None:
        return jsonify({"ok": False, "error": "No face detected. Try again."}), 400

    save_face_image(name, gray, face)
    train_model()

    consent_map = load_consent()
    consent_map[name] = datetime.now().isoformat()
    save_consent(consent_map)

    users = load_users()
    users[name] = {
        "name": name,
        "rollNumber": roll_number,
        "studentClass": student_class,
        "section": section,
        "branch": branch,
        "updatedAt": datetime.now().isoformat(),
    }
    save_users(users)

    return jsonify({"ok": True, "message": f"Registered {name}."})


@routes.post("/api/recognize")
def recognize():
    cleanup_old_data()
    data = request.get_json(force=True)
    image = data.get("image")
    if not image:
        return jsonify({"ok": False, "error": "Image is required."}), 400

    recognizer, labels = ensure_model_ready()
    if recognizer is None:
        return jsonify({"ok": False, "error": "No trained model found. Register first."}), 400

    inverse_labels = {v: k for k, v in labels.items()}

    frame = decode_image(image)
    if frame is None:
        return jsonify({"ok": False, "error": "Invalid image data."}), 400

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    face = detect_face(gray)
    if face is None:
        return jsonify({"ok": False, "error": "No face detected. Try again."}), 400

    x, y, w, h = face
    roi = gray[y : y + h, x : x + w]

    label_id, confidence = recognizer.predict(roi)
    name = inverse_labels.get(label_id, "Unknown")

    if confidence > 70:
        name = "Unknown"

    if name != "Unknown":
        _mark_attendance(name)

    return jsonify({"ok": True, "name": name, "confidence": round(float(confidence), 2)})


@routes.get("/api/attendance")
def attendance():
    cleanup_old_data()
    rows = []
    if os.path.exists(ATTEND_PATH):
        with open(ATTEND_PATH, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split(",")
                if len(parts) >= 3:
                    rows.append({"name": parts[0], "date": parts[1], "time": parts[2]})
    return jsonify({"ok": True, "rows": rows})


@routes.get("/api/attendance/<name>")
def attendance_for_user(name: str):
    cleanup_old_data()
    rows = []
    if os.path.exists(ATTEND_PATH):
        with open(ATTEND_PATH, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split(",")
                if len(parts) >= 3 and parts[0].lower() == name.lower():
                    rows.append({"name": parts[0], "date": parts[1], "time": parts[2]})
    return jsonify({"ok": True, "rows": rows})


@routes.post("/api/delete/<name>")
def delete_user(name: str):
    name = name.strip()
    if not name:
        return jsonify({"ok": False, "error": "Name is required."}), 400

    if os.path.exists(ATTEND_PATH):
        kept = []
        with open(ATTEND_PATH, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split(",")
                if len(parts) >= 1 and parts[0].lower() == name.lower():
                    continue
                kept.append(line)
        with open(ATTEND_PATH, "w", encoding="utf-8") as f:
            f.writelines(kept)

    for person in os.listdir(FACE_DIR):
        if person.lower() == name.lower():
            person_dir = os.path.join(FACE_DIR, person)
            for fname in os.listdir(person_dir):
                os.remove(os.path.join(person_dir, fname))
            os.rmdir(person_dir)
            break

    consent_map = load_consent()
    consent_map.pop(name, None)
    save_consent(consent_map)

    users = load_users()
    matched_key = None
    for k in users.keys():
        if k.lower() == name.lower():
            matched_key = k
            break
    if matched_key:
        users.pop(matched_key, None)
    save_users(users)

    train_model()
    return jsonify({"ok": True})


@routes.get("/api/retention")
def retention():
    return jsonify({"ok": True, "days": RETENTION_DAYS})


@routes.get("/api/user/<name>")
def user_details(name: str):
    users = load_users()
    profile = None
    for k, v in users.items():
        if k.lower() == name.lower():
            profile = v
            break
    if profile is None:
        return jsonify({"ok": False, "error": "User profile not found."}), 404
    return jsonify({"ok": True, "profile": profile})


@routes.get("/api/user/<name>/photo")
def user_photo(name: str):
    users = load_users()
    matched_name = None
    for k in users.keys():
        if k.lower() == name.lower():
            matched_name = k
            break
    if matched_name is None:
        return jsonify({"ok": False, "error": "User not found."}), 404

    path = get_latest_face_image_path(matched_name)
    if path is None:
        return jsonify({"ok": False, "error": "No photo available."}), 404

    ext = os.path.splitext(path)[1].lower()
    mime = "image/png" if ext == ".png" else "image/jpeg"
    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode("ascii")
    return jsonify({"ok": True, "dataUrl": f"data:{mime};base64,{data}"})


@routes.get("/api/users")
def users():
    profiles = load_users()
    merged: Dict[str, Dict[str, str]] = {}

    for profile in profiles.values():
        name = (profile.get("name") or "").strip()
        if not name:
            continue
        merged[name.lower()] = {
            "name": name,
            "rollNumber": (profile.get("rollNumber") or "").strip(),
        }

    if os.path.exists(ATTEND_PATH):
        with open(ATTEND_PATH, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split(",")
                if len(parts) < 1:
                    continue
                name = parts[0].strip()
                if not name:
                    continue
                key = name.lower()
                if key not in merged:
                    merged[key] = {"name": name, "rollNumber": ""}

    rows = list(merged.values())
    rows.sort(key=lambda x: (x["name"].lower(), x["rollNumber"].lower()))
    return jsonify({"ok": True, "rows": rows})


@routes.get("/api/class-window")
def class_window():
    start = get_class_start_date()
    end = date.today()
    total_days = (end - start).days + 1
    return jsonify(
        {
            "ok": True,
            "startDate": start.isoformat(),
            "endDate": end.isoformat(),
            "totalDays": max(total_days, 1),
        }
    )
