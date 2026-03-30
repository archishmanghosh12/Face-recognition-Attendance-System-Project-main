import { useEffect, useRef, useState } from 'react'
import { Routes, Route, useNavigate, useParams } from 'react-router-dom'
import './App.css'

function Home() {
  const videoRef = useRef(null)
  const canvasRef = useRef(null)
  const navigate = useNavigate()
  const [status, setStatus] = useState('Ready')
  const [name, setName] = useState('')
  const [rollNumber, setRollNumber] = useState('')
  const [studentClass, setStudentClass] = useState('')
  const [section, setSection] = useState('')
  const [branch, setBranch] = useState('')
  const [consent, setConsent] = useState(false)
  const [result, setResult] = useState('-')
  const [users, setUsers] = useState([])
  const [retentionDays, setRetentionDays] = useState(null)

  useEffect(() => {
    startCamera()
    loadUsers()
    loadRetention()
  }, [])

  async function startCamera() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true })
      if (videoRef.current) {
        videoRef.current.srcObject = stream
      }
    } catch {
      setStatus('Camera access denied')
    }
  }

  function captureImage() {
    const video = videoRef.current
    const canvas = canvasRef.current
    if (!video || !canvas) return null
    const ctx = canvas.getContext('2d')
    canvas.width = video.videoWidth || 640
    canvas.height = video.videoHeight || 480
    const cx = canvas.width / 2
    const cy = canvas.height / 2
    const rx = canvas.width * 0.26
    const ry = canvas.height * 0.36
    ctx.fillStyle = '#000000'
    ctx.fillRect(0, 0, canvas.width, canvas.height)
    ctx.save()
    ctx.beginPath()
    ctx.ellipse(cx, cy, rx, ry, 0, 0, Math.PI * 2)
    ctx.clip()
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height)
    ctx.restore()
    return canvas.toDataURL('image/jpeg')
  }

  async function register() {
    if (!name.trim()) {
      setResult('Enter a name first.')
      return
    }
    if (!rollNumber.trim() || !studentClass.trim() || !section.trim() || !branch.trim()) {
      setResult('Enter roll number, class, section, and branch.')
      return
    }
    if (!consent) {
      setResult('Consent is required to register.')
      return
    }
    setStatus('Registering...')
    const image = captureImage()
    if (!image) return

    const res = await fetch('/api/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: name.trim(),
        rollNumber: rollNumber.trim(),
        studentClass: studentClass.trim(),
        section: section.trim(),
        branch: branch.trim(),
        image,
        consent
      })
    })
    const data = await res.json()
    setStatus(data.ok ? 'Registered' : 'Error')
    setResult(data.ok ? data.message : data.error)
    if (data.ok) loadUsers()
  }

  async function recognize() {
    setStatus('Recognizing...')
    const image = captureImage()
    if (!image) return

    const res = await fetch('/api/recognize', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ image })
    })
    const data = await res.json()
    setStatus(data.ok ? 'Done' : 'Error')
    if (data.ok) {
      setResult(`Detected: ${data.name} (conf ${data.confidence})`)
      loadUsers()
    } else {
      setResult(data.error)
    }
  }

  async function loadUsers() {
    const res = await fetch('/api/users')
    const data = await res.json()
    setUsers(data.rows || [])
  }

  async function loadRetention() {
    const res = await fetch('/api/retention')
    const data = await res.json()
    setRetentionDays(data.days)
  }

  function onRowClick(row) {
    navigate(`/user/${encodeURIComponent(row.name)}`)
  }

  return (
    <main className="page">
      <header className="hero">
        <div>
          <p className="eyebrow">Offline - Local - Private</p>
          <h1>Face Attendance</h1>
          <p className="sub">Capture attendance using your webcam. No internet required.</p>
        </div>
        <div className="status">{status}</div>
      </header>

      <section className="panel capture-panel">
        <div className="card side-card register-card">
          <h2>Register New Person</h2>
          <p>Enter a name and capture one clear face image.</p>
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Full name"
          />
          <input
            value={rollNumber}
            onChange={(e) => setRollNumber(e.target.value)}
            placeholder="Roll number"
          />
            <input
              value={studentClass}
              onChange={(e) => setStudentClass(e.target.value)}
              placeholder="Year"
            />
          <input
            value={section}
            onChange={(e) => setSection(e.target.value)}
            placeholder="Section"
          />
          <input
            value={branch}
            onChange={(e) => setBranch(e.target.value)}
            placeholder="Branch"
          />
          <label className="consent">
            <input
              type="checkbox"
              checked={consent}
              onChange={(e) => setConsent(e.target.checked)}
            />
            I consent to storing my face data for attendance.
          </label>
          <button onClick={register}>Capture & Register</button>
          {retentionDays !== null && (
            <div className="muted small">
              Retention: {retentionDays > 0 ? `${retentionDays} days` : 'Forever'}
            </div>
          )}
        </div>

        <div className="camera">
          <div className="camera-frame">
            <video ref={videoRef} autoPlay playsInline />
            <div className="camera-overlay" aria-hidden="true">
              <div className="face-guide"></div>
            </div>
          </div>
          <p className="guide-note">Align your face inside the oval</p>
          <canvas ref={canvasRef} hidden />
        </div>

        <div className="card side-card mark-card">
          <h2>Mark Attendance</h2>
          <p>Capture and match against registered faces.</p>
          <button onClick={recognize}>Capture & Recognize</button>
          <div className="result">{result}</div>
        </div>
      </section>

      <section className="panel">
        <div className="card wide">
          <div className="card-head">
            <h2>Attendance Log</h2>
            <button className="refresh" onClick={loadUsers}>Refresh</button>
          </div>
          <div className="table">
            <div className="row header">
              <div>Name</div>
              <div>Roll Number</div>
              <div>Open</div>
            </div>
            {users.map((row, idx) => (
              <div
                className="row clickable"
                key={`${row.name}-${row.rollNumber}-${idx}`}
                onClick={() => onRowClick(row)}
              >
                <div>{row.name}</div>
                <div>{row.rollNumber}</div>
                <div>View</div>
              </div>
            ))}
          </div>
        </div>
      </section>
    </main>
  )
}

function UserPage() {
  const { name } = useParams()
  const navigate = useNavigate()
  const [rows, setRows] = useState([])
  const [profile, setProfile] = useState(null)
  const [photoUrl, setPhotoUrl] = useState(null)
  const [summary, setSummary] = useState({ present: 0, absent: 0, total: 0 })
  const [classWindow, setClassWindow] = useState(null)
  const [series, setSeries] = useState([])

  useEffect(() => {
    loadUser()
  }, [name])

  async function loadUser() {
    const [attendanceRes, profileRes, classRes] = await Promise.all([
      fetch(`/api/attendance/${encodeURIComponent(name)}`),
      fetch(`/api/user/${encodeURIComponent(name)}`),
      fetch('/api/class-window')
    ])
    const attendanceData = await attendanceRes.json()
    const profileData = await profileRes.json()
    const classData = await classRes.json()
    const photoRes = await fetch(`/api/user/${encodeURIComponent(name)}/photo`)
    const photoData = await photoRes.json()
    const userRows = attendanceData.rows || []
    setRows(userRows)
    setProfile(profileData.ok ? profileData.profile : null)
    setPhotoUrl(photoData.ok ? photoData.dataUrl : null)
    setClassWindow(classData.ok ? classData : null)
    const { summary, series } = buildSeries(userRows, classData.ok ? classData.startDate : null)
    setSummary(summary)
    setSeries(series)
  }

  function buildSeries(rows, startDateOverride) {
    const presentDates = new Set(rows.map(r => r.date))
    const start = startDateOverride ? new Date(startDateOverride) : new Date()
    const end = new Date()
    const series = []
    let present = 0
    let absent = 0

    for (let d = new Date(start); d <= end; d.setDate(d.getDate() + 1)) {
      const iso = d.toISOString().slice(0, 10)
      const isPresent = presentDates.has(iso)
      if (isPresent) present += 1
      else absent += 1
      series.push({ date: iso, present: isPresent })
    }

    return { summary: { present, absent, total: present + absent }, series }
  }

  return (
    <main className="page">
      <header className="hero">
        <div>
          <p className="eyebrow">User Attendance</p>
          <h1>{decodeURIComponent(name || '')}</h1>
          <p className="sub">
            Daily requirement: present every day
            {classWindow ? ` (from ${classWindow.startDate})` : ''}
          </p>
        </div>
        <div className="status">{summary.present}/{summary.total} present</div>
      </header>

      <section className="panel">
        <div className="card wide">
          <div className="card-head">
            <h2>Summary</h2>
            <button className="refresh" onClick={() => navigate('/')}>Back</button>
          </div>
          {photoUrl && (
            <div className="profile-photo">
              <img src={photoUrl} alt="User face" />
            </div>
          )}
          {profile && (
            <div className="profile-grid">
              <div><strong>Roll No:</strong> {profile.rollNumber}</div>
              <div><strong>Year:</strong> {profile.studentClass}</div>
              <div><strong>Section:</strong> {profile.section}</div>
              <div><strong>Branch:</strong> {profile.branch}</div>
            </div>
          )}
          <div className="metrics">
            <div className="metric">
              <div className="label">Present</div>
              <div className="value good">{summary.present}</div>
            </div>
            <div className="metric">
              <div className="label">Absent</div>
              <div className="value bad">{summary.absent}</div>
            </div>
            <div className="metric">
              <div className="label">Total Days</div>
              <div className="value">{summary.total}</div>
            </div>
          </div>
        </div>
      </section>

      <section className="panel">
        <div className="card wide">
          <h2>Presence Split</h2>
          <div className="pie-wrap">
            <div
              className="pie"
              style={{
                background: `conic-gradient(#34d399 0 ${summary.total ? (summary.present / summary.total) * 360 : 0}deg, #fca5a5 0 360deg)`
              }}
            ></div>
            <div className="pie-legend">
              <div><span className="dot present"></span> Present: {summary.present}</div>
              <div><span className="dot absent"></span> Absent: {summary.absent}</div>
              <div><span className="dot total"></span> Total: {summary.total}</div>
            </div>
          </div>
        </div>
      </section>

      <section className="panel">
        <div className="card wide">
          <h2>Daily Record</h2>
          <div className="table">
            <div className="row header">
              <div>Date</div>
              <div>Status</div>
              <div>Time (if present)</div>
            </div>
            {series.map((d) => {
              const time = rows.find(r => r.date === d.date)?.time || '-'
              return (
                <div className="row" key={d.date}>
                  <div>{d.date}</div>
                  <div>{d.present ? 'Present' : 'Absent'}</div>
                  <div>{time}</div>
                </div>
              )
            })}
          </div>
        </div>
      </section>
    </main>
  )
}

function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/user/:name" element={<UserPage />} />
    </Routes>
  )
}

export default App
