import React, { useState } from 'react'
import CircuitUploader from './components/CircuitUploader'
import AnalysisResult from './components/AnalysisResult'
import './App.css'

function App() {
  const [analysisResult, setAnalysisResult] = useState(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleAnalysisComplete = (result) => {
    setAnalysisResult(result)
    setIsLoading(false)
    setError(null)
  }

  const handleAnalysisError = (err) => {
    setError(err.message || '分析失败，请重试')
    setIsLoading(false)
  }

  const handleStartAnalysis = () => {
    setIsLoading(true)
    setError(null)
    setAnalysisResult(null)
  }

  const handleReset = () => {
    setAnalysisResult(null)
    setError(null)
    setIsLoading(false)
  }

  return (
    <div className="app">
      <header className="header">
        <h1>⚡ CircuitAI</h1>
        <p>AI驱动的电路图识别、解释与错误检测工具</p>
      </header>

      <main className="main-content">
        {!analysisResult ? (
          <CircuitUploader
            onAnalysisComplete={handleAnalysisComplete}
            onAnalysisError={handleAnalysisError}
            onStartAnalysis={handleStartAnalysis}
            isLoading={isLoading}
          />
        ) : (
          <AnalysisResult
            result={analysisResult}
            onReset={handleReset}
          />
        )}

        {error && (
          <div className="error">
            <p>❌ {error}</p>
          </div>
        )}
      </main>

      <footer className="footer">
        <p>CircuitAI © 2026 | 专注于电路图辅助分析</p>
      </footer>
    </div>
  )
}

export default App
