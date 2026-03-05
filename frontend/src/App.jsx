import React, { useState } from 'react'
import axios from 'axios'
import './App.css'

const API_BASE = ''

function App() {
  const [file, setFile] = useState(null)
  const [preview, setPreview] = useState(null)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0]
    if (selectedFile) {
      setFile(selectedFile)
      setPreview(URL.createObjectURL(selectedFile))
      setResult(null)
      setError(null)
    }
  }

  const handleUpload = async () => {
    if (!file) {
      setError('请先选择图片')
      return
    }

    setLoading(true)
    setError(null)

    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await axios.post(`${API_BASE}/api/v1/full-analysis`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 180000
      })
      setResult(response.data)
    } catch (err) {
      setError(err.response?.data?.detail || '分析失败，请重试')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app">
      <header className="header">
        <h1>⚡ CircuitAI</h1>
        <p>AI 电路图辅助工具</p>
      </header>

      <main className="main">
        <section className="upload-section">
          <h2>上传电路图</h2>
          <input type="file" accept="image/*" onChange={handleFileChange} />
          {preview && <img src={preview} alt="预览" className="preview" />}
          <button onClick={handleUpload} disabled={loading || !file}>
            {loading ? '分析中...' : '开始分析'}
          </button>
        </section>

        {error && <div className="error">{error}</div>}

        {result && (
          <section className="result-section">
            <h2>分析结果</h2>
            
            <div className="result-block">
              <h3>📋 元件列表 ({result.components?.length || 0})</h3>
              <pre>{JSON.stringify(result.components, null, 2)}</pre>
            </div>

            <div className="result-block">
              <h3>🔌 拓扑结构</h3>
              <p>{result.topology}</p>
            </div>

            <div className="result-block">
              <h3>⚡ 电路功能</h3>
              <p>{result.function}</p>
            </div>

            {result.bom && result.bom.length > 0 && (
              <div className="result-block">
                <h3>📦 BOM 表 ({result.bom.length})</h3>
                <pre>{JSON.stringify(result.bom, null, 2)}</pre>
              </div>
            )}

            {result.errors && result.errors.length > 0 && (
              <div className="result-block errors">
                <h3>⚠️ 检测到问题 ({result.errors.length})</h3>
                <pre>{JSON.stringify(result.errors, null, 2)}</pre>
              </div>
            )}
          </section>
        )}
      </main>
    </div>
  )
}

export default App
