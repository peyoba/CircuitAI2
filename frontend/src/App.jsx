import React, { useState, useCallback } from 'react'
import axios from 'axios'
import { t, getLang, setLang } from './i18n'
import './App.css'

const API_BASE = import.meta.env.VITE_API_BASE || ''

/* ========== 元件列表表格 ========== */
function ComponentsTable({ components }) {
  if (!components || !components.length) return <p className="empty">{t('noComponents')}</p>
  return (
    <table className="data-table">
      <thead>
        <tr>
          <th>{t('componentId')}</th>
          <th>{t('componentType')}</th>
          <th>{t('componentParam')}</th>
          <th>{t('componentQty')}</th>
          <th>{t('componentPins')}</th>
        </tr>
      </thead>
      <tbody>
        {components.map((c, i) => (
          <tr key={i}>
            <td className="ref">{c.ref || c.name || '-'}</td>
            <td><span className="type-badge">{c.type || '-'}</span></td>
            <td className="value">{c.value || c.model || '-'}</td>
            <td className="center">{c.quantity || 1}</td>
            <td className="desc">{c.pins || c.remarks || '-'}</td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}

/* ========== 拓扑结构卡片 ========== */
function TopologyCard({ topology }) {
  if (!topology) return null
  if (typeof topology === 'string') return <p className="text-content">{topology}</p>
  
  const labels = {
    power_path: t('topo_power_path'),
    signal_path: t('topo_signal_path'),
    grounding: t('topo_grounding'),
    ground_method: t('topo_ground_method'),
    modules: t('topo_modules'),
    module_division: t('topo_module_division')
  }
  
  return (
    <div className="info-cards">
      {Object.entries(topology).map(([k, v]) => (
        <div key={k} className="info-card">
          <div className="info-label">{labels[k] || k}</div>
          <div className="info-value">{typeof v === 'object' ? JSON.stringify(v) : String(v)}</div>
        </div>
      ))}
    </div>
  )
}

/* ========== 电路功能卡片 ========== */
function FunctionCard({ func }) {
  if (!func) return null
  if (typeof func === 'string') return <p className="text-content">{func}</p>
  
  return (
    <div className="function-card">
      {func.circuit_type && (
        <div className="func-type">
          <span className="func-icon">🎯</span>
          <span className="func-type-text">{func.circuit_type}</span>
        </div>
      )}
      {func.description && <p className="func-desc">{func.description}</p>}
      {func.applications && (
        <div className="func-app">
          <strong>{t('typicalApp')}</strong>{func.applications}
        </div>
      )}
    </div>
  )
}

/* ========== BOM 表格 ========== */
function BOMTable({ bom }) {
  if (!bom || !bom.length) return null
  return (
    <table className="data-table bom-table">
      <thead>
        <tr>
          <th>{t('bomIndex')}</th>
          <th>{t('bomName')}</th>
          <th>{t('bomModel')}</th>
          <th>{t('bomQty')}</th>
          <th>{t('bomRemarks')}</th>
        </tr>
      </thead>
      <tbody>
        {bom.map((item, i) => (
          <tr key={i}>
            <td className="center">{item.index || i + 1}</td>
            <td>{item.name || '-'}</td>
            <td className="value">{item.model || item.value || '-'}</td>
            <td className="center">{item.quantity || '-'}</td>
            <td className="desc">{item.remarks || '-'}</td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}

/* ========== 错误检测卡片 ========== */
function ErrorsList({ errors }) {
  if (!errors || !errors.length) return null
  
  const severityColors = {
    High: '#ef4444', high: '#ef4444',
    Medium: '#f59e0b', medium: '#f59e0b',
    Low: '#3b82f6', low: '#3b82f6'
  }
  
  return (
    <div className="errors-list">
      {errors.map((err, i) => {
        const severity = err.severity || 'Medium'
        const color = severityColors[severity] || '#f59e0b'
        return (
          <div key={i} className="error-card" style={{ borderLeftColor: color }}>
            <div className="error-header">
              <span className="error-severity" style={{ background: color }}>
                {severity}
              </span>
              <span className="error-type">{err.type || t('unknownIssue')}</span>
            </div>
            <p className="error-desc">{err.description || ''}</p>
            {err.suggestion && (
              <div className="error-suggestion">
                <strong>{t('suggestion')}</strong>{err.suggestion}
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}

/* ========== 关键节点 ========== */
function KeyNodes({ nodes }) {
  if (!nodes || !nodes.length) return null
  return (
    <div className="key-nodes">
      {nodes.map((node, i) => (
        <span key={i} className="node-tag">
          {typeof node === 'object' ? (node.name || JSON.stringify(node)) : String(node)}
        </span>
      ))}
    </div>
  )
}

/* ========== 历史记录管理 ========== */
const HISTORY_KEY = 'circuitai_history'
const MAX_HISTORY = 20

function loadHistory() {
  try {
    return JSON.parse(localStorage.getItem(HISTORY_KEY) || '[]')
  } catch { return [] }
}

function saveToHistory(entry) {
  const history = loadHistory()
  history.unshift(entry)
  if (history.length > MAX_HISTORY) history.length = MAX_HISTORY
  localStorage.setItem(HISTORY_KEY, JSON.stringify(history))
}

function removeFromHistory(id) {
  const history = loadHistory().filter(h => h.id !== id)
  localStorage.setItem(HISTORY_KEY, JSON.stringify(history))
  return history
}

function HistoryPanel({ onLoad, onClose }) {
  const [items, setItems] = useState(loadHistory())
  if (!items.length) return (
    <div className="history-panel">
      <div className="history-header">
        <h3>{t('historyTitle')}</h3>
        <button className="btn-close" onClick={onClose}>✕</button>
      </div>
      <p className="empty">{t('noHistory')}</p>
    </div>
  )
  return (
    <div className="history-panel">
      <div className="history-header">
        <h3>{t('historyTitle')} <span className="count-badge">{items.length}</span></h3>
        <button className="btn-close" onClick={onClose}>✕</button>
      </div>
      <ul className="history-list">
        {items.map(h => (
          <li key={h.id} className="history-item">
            <div className="history-info" onClick={() => onLoad(h)}>
              <span className="history-name">{h.fileName || t('unnamed')}</span>
              <span className="history-date">{new Date(h.timestamp).toLocaleString()}</span>
              <span className="history-stats">
                {h.componentCount || 0} {t('componentUnit')} · {h.errorCount || 0} {t('issueUnit')}
              </span>
            </div>
            <button className="btn-delete" onClick={() => setItems(removeFromHistory(h.id))}>🗑</button>
          </li>
        ))}
      </ul>
    </div>
  )
}

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
    // Force re-render by reloading — simple approach for module-level t()
    window.location.reload()
  }

  // 设置文件的通用方法
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
  )
}

export default App
