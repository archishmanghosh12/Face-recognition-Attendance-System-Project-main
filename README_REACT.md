# Offline Face Attendance (React + Flask)

This setup uses a React frontend and a local Flask backend for offline face recognition.

## 1) Start the backend (Flask)

```
.\.venv\Scripts\python app.py
```

The API runs at `http://127.0.0.1:5000`.

## 2) Start the frontend (React)

```
cd web
npm run dev
```

Open the URL shown by Vite (usually `http://localhost:5173`).

## Notes
- The React dev server proxies `/api` to the Flask backend.
- Attendance is stored in `data/attendance.csv`.
- Registered faces are stored in `data/faces/`.
