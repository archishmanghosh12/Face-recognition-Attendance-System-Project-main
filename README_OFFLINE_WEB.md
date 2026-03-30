# Offline Face Attendance (Web)

This is a fully offline face attendance system with a local web UI.

## Run

```
.\.venv\Scripts\python app.py
```

Then open `http://127.0.0.1:5000` in your browser.

## How it works
- Uses your webcam in the browser.
- Registers faces locally (saved to `data/faces/`).
- Trains an LBPH model offline (`data/model.yml`).
- Marks attendance into `data/attendance.csv`.

## Notes
- Good lighting and a clear frontal face improves accuracy.
- If recognition is too strict/loose, adjust the confidence threshold in `app.py`.
