import './App.css'

function App() {
  return (
    <div className="app">
      <div className="hero-card">
        <span className="hero-icon">📊</span>
        <h1 className="hero-title">Sales Insight Automator</h1>
        <p className="hero-description">
          Upload a sales CSV or Excel file to generate an AI-powered sales
          summary.
        </p>

        {/* Upload form will be added here */}
        <div className="upload-area">
          <span className="upload-icon">☁️</span>
          Drop your file here or click to upload
        </div>
      </div>
    </div>
  )
}

export default App
