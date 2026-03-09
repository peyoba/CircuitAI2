import React, { useState } from 'react'
import axios from 'axios'
import './App.css'

const API_BASE = ''

/* ========== 元件列表表格 ========== */
function ComponentsTable({ components }) {
  if (!components || !components.length) return <p className="empty">未识别到元件</p>
  return (
    <table className="data-table">
      <thead>
        <tr>
          <th>编号</th>
          <th>类型</th>
          <th>参数/型号</th>
          <th>数量</th>
          <th>引脚/说明</th>
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
    power_path: '⚡ 电源路径',
    signal_path: '📡 信号路径',
    grounding: '🔌 接地方式',
    ground_method: '🔌 接地方式',
    modules: '📦 模块划分',
    module_division: '📦 模块划分'
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
          <strong>💡 典型应用：</strong>{func.applications}
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
          <th>#</th>
          <th>元件名称</th>
          <th>型号/参数</th>
          <th>数量</th>
          <th>备注</th>
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
              <span className="error-type">{err.type || '未知问题'}</span>
            </div>
            <p className="error-desc">{err.description || ''}</p>
            {err.suggestion && (
              <div className="error-suggestion">
                <strong>💡 建议：</strong>{err.suggestion}
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

/* ========== 主应用 ========== */
function App() {
  const [file, setFile] = useState(null)
  const [preview, setPreview] = useState(null)
  const [result, setResult] = useState(null)
  const [taskId, setTaskId] = useState(null)
  const [loading, setLoading] = useState(false)
  const [loadingTime, setLoadingTime] = useState(0)
  const [error, setError] = useState(null)

  // 设置文件的通用方法
  const setImageFile = (f) => {
    setFile(f)
    setPreview(URL.createObjectURL(f))
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
    if (droppedFile && droppedFile.type.startsWith('image/')) setImageFile(droppedFile)
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
    if (!file) { setError('请先选择图片'); return }
    setLoading(true)
    setError(null)
    setLoadingTime(0)
    const timer = setInterval(() => setLoadingTime(t => t + 1), 1000)

    const formData = new FormData()
    formData.append('file', file)

    try {
      // 异步模式：先提交，再轮询结果
      const submitRes = await axios.post(`${API_BASE}/api/v1/analyze-async`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 30000
      })
      const taskId = submitRes.data.task_id
      setTaskId(taskId)
      
      // 轮询结果
      while (true) {
        await new Promise(r => setTimeout(r, 3000)) // 每3秒查一次
        const pollRes = await axios.get(`${API_BASE}/api/v1/task/${taskId}`, { timeout: 10000 })
        const task = pollRes.data
        
        if (task.status === 'done') {
          setResult(task.result)
          break
        } else if (task.status === 'error') {
          setError(task.error || '分析失败')
          break
        }
        // 还在处理中，继续等
      }
    } catch (err) {
      const detail = err.response?.data?.detail || err.message || '分析失败，请重试'
      setError(typeof detail === 'object' ? JSON.stringify(detail) : detail)
    } finally {
      clearInterval(timer)
      setLoading(false)
    }
  }

  const errorCount = result?.errors?.length || 0
  const componentCount = result?.components?.length || 0
  const bomCount = result?.bom?.length || 0

  return (
    <div className="app">
      <header className="header">
        <h1>⚡ CircuitAI</h1>
        <p className="subtitle">AI 智能电路图分析工具</p>
      </header>

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
              <p>拖拽电路图到这里 / Ctrl+V 粘贴截图 / 点击选择文件</p>
              <input type="file" accept="image/*" onChange={handleFileChange} id="fileInput" />
              <label htmlFor="fileInput" className="upload-btn">选择文件</label>
            </div>
          ) : (
            <div className="upload-preview">
              <img src={preview} alt="电路图预览" className="preview-img" />
              <div className="upload-actions">
                <button className="btn-primary" onClick={handleUpload} disabled={loading}>
                  {loading ? (
                    <><span className="spinner"></span> AI 分析中 {loadingTime}s（请耐心等待1-2分钟）</>
                  ) : '🔍 开始分析'}
                </button>
                <button className="btn-secondary" onClick={() => { setFile(null); setPreview(null); setResult(null) }}>
                  重新选择
                </button>
              </div>
            </div>
          )}
        </section>

        {error && <div className="error-banner">❌ {error}</div>}

        {/* 分析结果 */}
        {result && (
          <div className="results">
            {/* 概览统计 */}
            <div className="stats-bar">
              <div className="stat-item">
                <span className="stat-num">{componentCount}</span>
                <span className="stat-label">元件识别</span>
              </div>
              <div className="stat-item">
                <span className="stat-num">{bomCount}</span>
                <span className="stat-label">BOM 物料</span>
              </div>
              <div className={`stat-item ${errorCount > 0 ? 'stat-warn' : 'stat-ok'}`}>
                <span className="stat-num">{errorCount}</span>
                <span className="stat-label">{errorCount > 0 ? '潜在问题' : '无问题'}</span>
              </div>
            </div>

            {/* 电路功能 */}
            <section className="result-card">
              <h3>⚡ 电路功能</h3>
              <FunctionCard func={result.function} />
            </section>

            {/* 元件列表 */}
            <section className="result-card">
              <h3>📋 元件列表 <span className="count-badge">{componentCount}</span></h3>
              <ComponentsTable components={result.components} />
            </section>

            {/* 拓扑结构 */}
            <section className="result-card">
              <h3>🔌 拓扑结构</h3>
              <TopologyCard topology={result.topology} />
            </section>

            {/* 关键节点 */}
            {result.key_nodes && result.key_nodes.length > 0 && (
              <section className="result-card">
                <h3>📍 关键节点</h3>
                <KeyNodes nodes={result.key_nodes} />
              </section>
            )}

            {/* BOM 表 */}
            {bomCount > 0 && (
              <section className="result-card">
                <h3>
                  📦 BOM 物料清单 <span className="count-badge">{bomCount}</span>
                  {taskId && (
                    <a
                      className="btn-export"
                      href={`${API_BASE}/api/v1/task/${taskId}/export-bom`}
                      download="bom.csv"
                    >📥 导出 CSV</a>
                  )}
                </h3>
                <BOMTable bom={result.bom} />
              </section>
            )}

            {/* 错误检测 */}
            {errorCount > 0 && (
              <section className="result-card">
                <h3>⚠️ 潜在问题 <span className="count-badge warn">{errorCount}</span></h3>
                <ErrorsList errors={result.errors} />
              </section>
            )}
          </div>
        )}
      </main>

      <footer className="footer">
        <p>CircuitAI © 2026 · Powered by AI</p>
      </footer>
    </div>
  )
}

export default App
