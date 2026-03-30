Offline Face Recognition Attendance System

1) Title Slide
- Project: Offline Face Recognition Attendance System
- Team/Author: <Your Name>
- Department/College: <Your Dept>
- Academic Year: 2025-2026
- Date: 24 Mar 2026

2) Agenda
- Problem statement
- Objectives
- System overview
- Architecture
- Data flow (registration + recognition)
- Core features
- Data storage
- API endpoints
- UI workflow
- Attendance logic
- Privacy and retention
- Results
- Limitations
- Future work
- Demo steps

3) Problem Statement
- Manual attendance wastes class time and introduces errors.
- Proxy attendance is easy in large classrooms and weakly supervised settings.
- Many solutions depend on stable internet, which is unreliable in some campuses.
- A simple, low-cost, offline system is needed to improve reliability and integrity.

4) Objectives
- Provide offline face-based attendance capture using a standard webcam.
- Keep setup minimal: one PC + camera + local storage.
- Store data locally for privacy and ownership.
- Offer clear per-user analytics for attendance review.
- Reduce proxy attendance by verifying identity at capture time.

5) System Overview
- Frontend: React web UI for registration, recognition, and review.
- Backend: Flask REST API for registration/recognition and data access.
- Face recognition: OpenCV LBPH (local, fast, no cloud).
- Storage: CSV + JSON files and face images on disk.
- Entire system runs offline on a single machine.

6) Architecture
- Browser captures webcam image and sends it to Flask API.
- Backend detects face, saves cropped image, and trains LBPH model.
- Recognition uses the saved LBPH model to identify the face.
- Attendance is written to a CSV; profile details go to JSON.
- No external dependencies or cloud calls.

7) Data Flow: Registration
- User enters: name, roll number, year, section, branch.
- Webcam frame is captured; only the oval region is kept.
- Face is detected and cropped.
- Face crop saved to data/faces/<name>/.
- LBPH model retrained and stored in data/model.yml.
- User profile saved in data/users.json.

8) Data Flow: Recognition
- User clicks “Capture & Recognize.”
- Frame is captured and masked to the oval region.
- Face detected and classified with LBPH.
- If match found, attendance is logged for the current date.
- Duplicate attendance for the same day is prevented.

9) Core Features
- Fully offline operation.
- Face guide overlay to align the subject.
- Register user with roll number, year, section, branch.
- Attendance log with quick user lookup.
- Per-user detail page with profile + photo.
- Consent tracking and configurable retention.

10) Data Storage
- data/attendance.csv: name, date, time
- data/users.json: name, rollNumber, year, section, branch, updatedAt
- data/consent.json: consent timestamp per user
- data/faces/<name>/: stored face crops
- data/model.yml + data/labels.json: trained model + labels

11) API Endpoints
- POST /api/register: register user and save face
- POST /api/recognize: recognize face and mark attendance
- GET /api/users: list registered users (name + roll)
- GET /api/user/<name>: user profile
- GET /api/user/<name>/photo: latest face photo
- GET /api/attendance/<name>: attendance per user
- GET /api/class-window: class start/end dates

12) UI Workflow
- Home screen has three columns: Register, Camera, Mark Attendance.
- Registration captures profile details + consent.
- Attendance log lists name and roll number only.
- Clicking a user opens profile, photo, pie chart, and daily record.

13) Attendance Logic
- Attendance is recorded once per user per day.
- Total class days are computed from a class start date to today.
- Class start date can be set via CLASS_START_DATE env var.
- Pie chart shows present vs absent proportion.

14) Privacy and Retention
- All data stored locally on the same machine.
- No cloud or external API calls.
- Consent is required before registration.
- Retention default is forever; can be configured with RETENTION_DAYS.
- User data can be deleted manually from profile view.

15) Results / Outcomes
- Faster attendance with less manual effort.
- Reduced proxy attendance risk.
- Works even without internet.
- Clear analytics for instructors.
- Simple storage and easy backup.

16) Limitations
- Accuracy depends on camera quality and lighting.
- Single face per capture; no batch recognition.
- No liveness detection yet (photo spoofing risk).
- Model retraining time grows with dataset size.

17) Future Enhancements
- Admin login and role-based access.
- Export to Excel/PDF.
- Liveness detection to prevent spoofing.
- Multi-camera and batch capture support.
- Scheduled automatic backup/restore.

18) Demo Steps
- Start backend: python app.py
- Start frontend: npm run dev
- Register a user with details
- Mark attendance
- Open user profile to view pie chart and record
