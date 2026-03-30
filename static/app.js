const video = document.getElementById('video');
const canvas = document.getElementById('canvas');
const nameInput = document.getElementById('nameInput');
const rollInput = document.getElementById('rollInput');
const classInput = document.getElementById('classInput');
const sectionInput = document.getElementById('sectionInput');
const branchInput = document.getElementById('branchInput');
const registerBtn = document.getElementById('registerBtn');
const recognizeBtn = document.getElementById('recognizeBtn');
const refreshBtn = document.getElementById('refreshBtn');
const resultEl = document.getElementById('result');
const statusEl = document.getElementById('status');
const rowsEl = document.getElementById('rows');

async function startCamera() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ video: true });
    video.srcObject = stream;
  } catch (err) {
    statusEl.textContent = 'Camera access denied';
  }
}

function captureImage() {
  const ctx = canvas.getContext('2d');
  canvas.width = video.videoWidth || 640;
  canvas.height = video.videoHeight || 480;
  const cx = canvas.width / 2;
  const cy = canvas.height / 2;
  const rx = canvas.width * 0.26;
  const ry = canvas.height * 0.36;
  ctx.fillStyle = '#000000';
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  ctx.save();
  ctx.beginPath();
  ctx.ellipse(cx, cy, rx, ry, 0, 0, Math.PI * 2);
  ctx.clip();
  ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
  ctx.restore();
  return canvas.toDataURL('image/jpeg');
}

async function register() {
  const name = nameInput.value.trim();
  const rollNumber = rollInput.value.trim();
  const studentClass = classInput.value.trim();
  const section = sectionInput.value.trim();
  const branch = branchInput.value.trim();
  if (!name || !rollNumber || !studentClass || !section || !branch) {
    resultEl.textContent = 'Enter name, roll number, class, section and branch.';
    return;
  }
  statusEl.textContent = 'Registering...';
  const image = captureImage();
  const res = await fetch('/api/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, rollNumber, studentClass, section, branch, image, consent: true })
  });
  const data = await res.json();
  statusEl.textContent = data.ok ? 'Registered' : 'Error';
  resultEl.textContent = data.ok ? data.message : data.error;
  if (data.ok) {
    await loadAttendance();
  }
}

async function recognize() {
  statusEl.textContent = 'Recognizing...';
  const image = captureImage();
  const res = await fetch('/api/recognize', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ image })
  });
  const data = await res.json();
  statusEl.textContent = data.ok ? 'Done' : 'Error';
  if (data.ok) {
    resultEl.textContent = `Detected: ${data.name} (conf ${data.confidence})`;
    await loadAttendance();
  } else {
    resultEl.textContent = data.error;
  }
}

async function loadAttendance() {
  const res = await fetch('/api/users');
  const data = await res.json();
  rowsEl.innerHTML = '';
  data.rows.forEach(row => {
    const el = document.createElement('div');
    el.className = 'row clickable';
    el.innerHTML = `<div>${row.name}</div><div>${row.rollNumber || '-'}</div><div>View</div>`;
    rowsEl.appendChild(el);
  });
}

registerBtn.addEventListener('click', register);
recognizeBtn.addEventListener('click', recognize);
refreshBtn.addEventListener('click', loadAttendance);

startCamera();
loadAttendance();
