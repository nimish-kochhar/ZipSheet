import { useState, useRef } from 'react'
import axios from 'axios'

const API_URL = 'http://localhost:8000'

function UploadForm() {
  const [file, setFile] = useState(null)
  const [email, setEmail] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [warnings, setWarnings] = useState([])
  const [aiPowered, setAiPowered] = useState(false)
  const fileInputRef = useRef(null)

  const handleFileChange = (e) => {
    const selected = e.target.files[0]
    if (!selected) return

    const allowed = [
      'text/csv',
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    ]
    if (!allowed.includes(selected.type)) {
      setError('Please upload a .csv or .xlsx file.')
      setFile(null)
      return
    }

    setError('')
    setSuccess('')
    setFile(selected)
  }

  const handleDrop = (e) => {
    e.preventDefault()
    e.stopPropagation()
    const dropped = e.dataTransfer.files[0]
    if (dropped) {
      const fakeEvent = { target: { files: [dropped] } }
      handleFileChange(fakeEvent)
    }
  }

  const handleDragOver = (e) => {
    e.preventDefault()
    e.stopPropagation()
  }

  const handleSubmit = async (e) => {
    e.preventDefault()

    if (!file) {
      setError('Please select a file first.')
      return
    }
    if (!email.trim()) {
      setError('Please enter your email address.')
      return
    }

    setError('')
    setSuccess('')
    setWarnings([])
    setAiPowered(false)
    setLoading(true)

    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('email', email)

      const response = await axios.post(`${API_URL}/analyze`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })

      setSuccess(response.data.summary || 'File analyzed successfully!')
      setWarnings(response.data.warnings || [])
      setAiPowered(response.data.ai_powered || false)
    } catch (err) {
      const msg =
        err.response?.data?.detail ||
        err.response?.data?.message ||
        err.message ||
        'Something went wrong. Please try again.'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <form className="upload-form" onSubmit={handleSubmit}>
      {/* ── Drop zone / file picker ── */}
      <div
        className={`drop-zone ${file ? 'drop-zone--has-file' : ''}`}
        onClick={() => fileInputRef.current?.click()}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv,.xlsx"
          onChange={handleFileChange}
          hidden
        />
        {file ? (
          <div className="drop-zone__file-info">
            <span className="drop-zone__file-icon">📄</span>
            <span className="drop-zone__file-name">{file.name}</span>
            <span className="drop-zone__file-size">
              {(file.size / 1024).toFixed(1)} KB
            </span>
          </div>
        ) : (
          <>
            <span className="drop-zone__icon">☁️</span>
            <span className="drop-zone__text">
              Drop your file here or click to browse
            </span>
            <span className="drop-zone__hint">.csv or .xlsx</span>
          </>
        )}
      </div>

      {/* ── Email ── */}
      <div className="form-field">
        <label htmlFor="email" className="form-label">Email address</label>
        <input
          id="email"
          type="email"
          className="form-input"
          placeholder="you@company.com"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
      </div>

      {/* ── Submit ── */}
      <button
        type="submit"
        className="submit-btn"
        disabled={loading}
      >
        {loading ? (
          <span className="spinner" />
        ) : (
          'Generate Summary'
        )}
      </button>

      {/* ── Feedback messages ── */}
      {error && <p className="msg msg--error">{error}</p>}
      {success && (
        <div className="msg msg--success">
          {aiPowered && <span className="ai-badge">✨ AI-Powered</span>}
          <pre className="summary-text">{success}</pre>
        </div>
      )}
      {warnings.length > 0 && (
        <div className="msg msg--warning">
          <strong>Notes:</strong>
          <ul className="warning-list">
            {warnings.map((w, i) => <li key={i}>{w}</li>)}
          </ul>
        </div>
      )}
    </form>
  )
}

export default UploadForm
