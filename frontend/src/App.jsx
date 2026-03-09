import React, { useState, useCallback } from 'react'
import axios from 'axios'
import { t, getLang, setLang } from './i18n'
import {
  ErrorBoundary,
  ComponentsTable,
  TopologyCard,
  FunctionCard,
  BOMTable,
  ErrorsList,
  KeyNodes,
  HistoryPanel,
  saveToHistory
} from './components'
import './App.css'

const API_BASE = import.meta.env.VITE_API_BASE || ''

/* ========== 主应用 ========== */
function App() {
  const [file, setFile] = useState(null)
  const [preview, setPreview] = useState(null)
  const [result, setResult] = useState(null)
  const [taskId, setTaskId] = useState(null)
  const [loading, setLoading] = useState(false)
  const [loadingTime, setLoadingTime] = useState(0)
  const [error, setError] = useState(null)
  const [showHistory, setShowHistory] = useState(false)
  const [loadingStage, setLoadingStage] = useState('')
  const [lang, setLangState] = useState(getLang())

  const LOADING_STAGES = [
    [0, t('stage_upload')],
    [5, t('stage_recognize')],
    [20, t('stage_topology')],
    [45, t('stage_bom')],
    [70, t('stage_detect')],
    [90, t('stage_report')],
  ]

  const toggleLang = () => {
    const next = lang === 'zh' ? 'en' : 'zh'
    setLang(next)
    setLangState(next)
    window.location.reload()
  }

  const setImageFile = (f) => {
    setFile(f)
    setPreview(f.type === 'application/pdf' ? 'pdf' : URL.createObjectURL(f))
    setResult(null)
    setError(null)
  }

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0]
    if (selectedFile) setImageFile(selectedFile)
  }

  const handleDrop = (e) => {
    e.preventDefault()
    const droppedFile = e.dataTransfer.files[0]
    if (droppedFile && (droppedFile.type.startsWith('image/') || droppedFile.type === 'application/pdf')) setImageFile(droppedFile)
  }

  // 全局粘贴监听：Ctrl+V 直接粘贴截图
  React.useEffect(() => {
    const handlePaste = (e) => {
      const items = e.clipboardData?.items
      if (!items) return
      for (const item of items) {
        if (item.type.startsWith('image/')) {
          e.preventDefault()
          const blob = item.getAsFile()
          if (blob) {
            const f = new File([blob], `screenshot_${Date.now()}.png`, { type: blob.type })
            setImageFile(f)
          }
          break
        }
      }
    }
    window.addEventListener('paste', handlePaste)
    return () => window.removeEventListener('paste', handlePaste)
  }, [])

  const handleUpload = async () => {
    if (!file) { setError(t('selectFirst')); return }
    setLoading(true)
    setError(null)
    setLoadingTime(0)
    setLoadingStage(LOADING_STAGES[0][1])
    const timer = setInterval(() => setLoadingTime(prev => {
      const next = prev + 1
      for (let i = LOADING_STAGES.length - 1; i >= 0; i--) {
        if (next >= LOADING_STAGES[i][0]) {
          setLoadingStage(LOADING_STAGES[i][1])
          break
        }
      }
      return next
    }), 1000)

    const formData = new FormData()
    formData.append('file', file)

    try {
      const submitRes = await axios.post(`${API_BASE}/api/v1/analyze-async`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 30000
      })
      const newTaskId = submitRes.data.task_id
      setTaskId(newTaskId)

      while (true) {
        await new Promise(r => setTimeout(r, 3000))
        const pollRes = await axios.get(`${API_BASE}/api/v1/task/${newTaskId}`, { timeout: 10000 })
        const task = pollRes.data

        if (task.status === 'done') {
          setResult(task.result)
          saveToHistory({
            id: newTaskId,
            fileName: file?.name || t('unnamed'),
            timestamp: Date.now(),
            componentCount: task.result?.components?.length || 0,
            errorCount: task.result?.errors?.length || 0,
            result: task.result
          })
          break
        } else if (task.status === 'error') {
          setError(task.error || t('errors'))
          break
        }
      }
    } catch (err) {
      const detail = err.response?.data?.detail || err.message || t('errors')
      setError(typeof detail === 'object' ? JSON.stringify(detail) : detail)
    } finally {
      clearInterval(timer)
      setLoading(false)
    }
  }

  const errorCount = result?.errors?.length || 0
  const componentCount = result?.components?.length || 0
  const bomCount = result?.bom?.length || 0

  const handleLoadHistory = (entry) => {
    setResult(entry.result)
    setTaskId(entry.id)
    setPreview(null)
    setFile(null)
    setError(null)
    setShowHistory(false)
  }

  return (
    <ErrorBoundary>
      <div className="app">
        <header className="header">
          <h1>{t('title')}</h1>
          <p className="subtitle">{t('subtitle')}</p>
          <div className="header-actions">
            <button className="btn-lang" onClick={toggleLang}>
              {lang === 'zh' ? 'EN' : '中文'}
            </button>
            <button className="btn-history" onClick={() => setShowHistory(!showHistory)}>
              {t('history')}
            </button>
          </div>
        </header>

        {showHistory && <HistoryPanel onLoad={handleLoadHistory} onClose={() => setShowHistory(false)} />}

        <main className="main">
          {/* 上传区域 */}
          <section
            className={`upload-zone ${preview ? 'has-file' : ''}`}
            onDragOver={(e) => e.preventDefault()}
            onDrop={handleDrop}
          >
            {!preview ? (
              <div className="upload-placeholder">
                <div className="upload-icon">📁</div>
                <p>{t('dropHint')}</p>
                <input type="file" accept="image/*,.pdf" onChange={handleFileChange} id="fileInput" />
                <label htmlFor="fileInput" className="upload-btn">{t('selectFile')}</label>
              </div>
            ) : (
              <div className="upload-preview">
                {preview === 'pdf' ? (
                  <div className="pdf-preview">
                    <span className="pdf-icon">📄</span>
                    <span className="pdf-name">{file?.name || t('pdfFile')}</span>
                  </div>
                ) : (
                  <img src={preview} alt="Circuit preview" className="preview-img" />
                )}
                <div className="upload-actions">
                  <button className="btn-primary" onClick={handleUpload} disabled={loading}>
                    {loading ? (
                      <><span className="spinner"></span> {loadingStage} ({loadingTime}s)</>
                    ) : t('startAnalysis')}
                  </button>
                  <button className="btn-secondary" onClick={() => { setFile(null); setPreview(null); setResult(null) }}>
                    {t('reselect')}
                  </button>
                </div>
              </div>
            )}
          </section>

          {error && (
            <div className="error-banner">
              ❌ {error}
              {file && !loading && (
                <button className="btn-retry" onClick={handleUpload}>{t('retry')}</button>
              )}
            </div>
          )}

          {/* 分析结果 */}
          {result && (
            <div className="results">
              {taskId && (
                <div className="export-bar">
                  <a className="btn-export-main" href={`${API_BASE}/api/v1/task/${taskId}/export-markdown`} download="circuit_analysis.md">
                    {t('exportMarkdown')}
                  </a>
                  <a className="btn-export-main secondary" href={`${API_BASE}/api/v1/task/${taskId}/export-bom`} download="bom.csv">
                    {t('exportBOM')}
                  </a>
                </div>
              )}

              <div className="stats-bar">
                <div className="stat-item">
                  <span className="stat-num">{componentCount}</span>
                  <span className="stat-label">{t('statComponents')}</span>
                </div>
                <div className="stat-item">
                  <span className="stat-num">{bomCount}</span>
                  <span className="stat-label">{t('statBOM')}</span>
                </div>
                <div className={`stat-item ${errorCount > 0 ? 'stat-warn' : 'stat-ok'}`}>
                  <span className="stat-num">{errorCount}</span>
                  <span className="stat-label">{errorCount > 0 ? t('statErrors') : t('statOk')}</span>
                </div>
              </div>

              <section className="result-card">
                <h3>{t('function')}</h3>
                <FunctionCard func={result.function} />
              </section>

              <section className="result-card">
                <h3>{t('components')} <span className="count-badge">{componentCount}</span></h3>
                <ComponentsTable components={result.components} />
              </section>

              <section className="result-card">
                <h3>{t('topology')}</h3>
                <TopologyCard topology={result.topology} />
              </section>

              {result.key_nodes && result.key_nodes.length > 0 && (
                <section className="result-card">
                  <h3>{t('keyNodes')}</h3>
                  <KeyNodes nodes={result.key_nodes} />
                </section>
              )}

              {bomCount > 0 && (
                <section className="result-card">
                  <h3>
                    {t('bom')} <span className="count-badge">{bomCount}</span>
                    {taskId && (
                      <a className="btn-export" href={`${API_BASE}/api/v1/task/${taskId}/export-bom`} download="bom.csv">
                        {t('exportCSV')}
                      </a>
                    )}
                    {taskId && (
                      <a className="btn-export" href={`${API_BASE}/api/v1/task/${taskId}/export-markdown`} download="circuit_analysis.md">
                        {t('exportMd')}
                      </a>
                    )}
                  </h3>
                  <BOMTable bom={result.bom} />
                </section>
              )}

              {errorCount > 0 && (
                <section className="result-card">
                  <h3>{t('errors')} <span className="count-badge warn">{errorCount}</span></h3>
                  <ErrorsList errors={result.errors} />
                </section>
              )}
            </div>
          )}
        </main>

        <footer className="footer">
          <p>{t('footer')}</p>
        </footer>
      </div>
    </ErrorBoundary>
  )
}

export default App
