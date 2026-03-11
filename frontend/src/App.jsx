import './App.css'
import UploadForm from './UploadForm'

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

        <UploadForm />
      </div>
    </div>
  )
}

export default App
