import { useState, useRef } from 'react'
import axios from 'axios'

const API_URL = 'http://localhost:8000'

function UploadForm() {
  const [file, setFile] = useState(null)
  const [email, setEmail] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [summary, setSummary] = useState('')
  const [warnings, setWarnings] = useState([])
  const [profileSnippet, setProfileSnippet] = useState(null)
  const [emailStatus, setEmailStatus] = useState(null)
  const [profileOpen, setProfileOpen] = useState(false)
  const [copied, setCopied] = useState(false)
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
    setSummary('')
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

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(summary)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      /* clipboard may be blocked — ignore */
    }
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
    setSummary('')
    setWarnings([])
    setProfileSnippet(null)
    setEmailStatus(null)
    setProfileOpen(false)
    setCopied(false)
    setLoading(true)

    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('email', email)

      const response = await axios.post(`${API_URL}/analyze`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })

      const data = response.data
      setSummary(data.summary || 'File analyzed successfully!')
      setWarnings(data.warnings || [])
      setProfileSnippet(data.profile_snippet || null)
      setEmailStatus(data.email_status || null)
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

      {/* ── Error ── */}
      {error && <p className="msg msg--error">{error}</p>}

      {/* ── Warnings ── */}
      {warnings.length > 0 && (
        <div className="msg msg--warning">
          <strong>⚠ Notes:</strong>
          <ul className="warning-list">
            {warnings.map((w, i) => <li key={i}>{w}</li>)}
          </ul>
        </div>
      )}

      {/* ── Summary ── */}
      {summary && (
        <div className="msg msg--success">
          <div className="summary-header">
            <span className="ai-badge">📋 Summary</span>
            <button
              type="button"
              className="copy-btn"
              onClick={handleCopy}
              title="Copy summary to clipboard"
            >
              {copied ? '✓ Copied' : '📄 Copy'}
            </button>
          </div>
          <pre className="summary-text">{summary}</pre>
        </div>
      )}

      {/* ── Email status ── */}
      {emailStatus && (
        <div className={`msg ${emailStatus.sent ? 'msg--success' : 'msg--info'}`}>
          {emailStatus.sent
            ? '✅ Summary emailed successfully.'
            : '📧 Email logged to console (mail service not configured).'}
        </div>
      )}

      {/* ── Collapsible profile snippet ── */}
      {profileSnippet && (
        <div className="profile-section">
          <button
            type="button"
            className="profile-toggle"
            onClick={() => setProfileOpen((v) => !v)}
          >
            <span className={`profile-arrow ${profileOpen ? 'profile-arrow--open' : ''}`}>
              ▶
            </span>
            Show dataset profile
          </button>

          {profileOpen && (
            <div className="profile-body">
              <div className="profile-meta">
                <span className="profile-chip">{profileSnippet.n_rows?.toLocaleString()} rows</span>
                <span className="profile-chip">{profileSnippet.n_columns} columns</span>
                <span className="profile-chip">{profileSnippet.total_missing?.toLocaleString()} missing</span>
              </div>

              {profileSnippet.column_names && (
                <p className="profile-columns">
                  <strong>Columns:</strong>{' '}
                  {profileSnippet.column_names.join(', ')}
                </p>
              )}

              {profileSnippet.numeric_columns?.length > 0 && (
                <p className="profile-columns">
                  <strong>Numeric:</strong>{' '}
                  {profileSnippet.numeric_columns.join(', ')}
                </p>
              )}

              {profileSnippet.categorical_columns?.length > 0 && (
                <p className="profile-columns">
                  <strong>Categorical:</strong>{' '}
                  {profileSnippet.categorical_columns.join(', ')}
                </p>
              )}

              {profileSnippet.datetime_columns?.length > 0 && (
                <p className="profile-columns">
                  <strong>Datetime:</strong>{' '}
                  {profileSnippet.datetime_columns.join(', ')}
                </p>
              )}

              {profileSnippet.sample_rows && profileSnippet.sample_rows.length > 0 && (
                <div className="profile-table-wrap">
                  <table className="profile-table">
                    <thead>
                      <tr>
                        {Object.keys(profileSnippet.sample_rows[0]).map((col) => (
                          <th key={col}>{col}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {profileSnippet.sample_rows.slice(0, 5).map((row, ri) => (
                        <tr key={ri}>
                          {Object.values(row).map((val, ci) => (
                            <td key={ci}>{val}</td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </form>
  )
}

export default UploadForm
