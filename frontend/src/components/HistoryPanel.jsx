import React, { useState, useEffect } from 'react'
import { t } from '../i18n'

const API_BASE = import.meta.env.VITE_API_BASE || ''
const HISTORY_KEY = 'circuitai_history'
const MAX_HISTORY = 20

// localStorage helpers (fallback / offline cache)
export function loadHistory() {
  try {
    return JSON.parse(localStorage.getItem(HISTORY_KEY) || '[]')
  } catch { return [] }
}

export function saveToHistory(entry) {
  const history = loadHistory()
  history.unshift(entry)
  if (history.length > MAX_HISTORY) history.length = MAX_HISTORY
  localStorage.setItem(HISTORY_KEY, JSON.stringify(history))
}

function removeFromLocalHistory(id) {
  const history = loadHistory().filter(h => h.id !== id)
  localStorage.setItem(HISTORY_KEY, JSON.stringify(history))
  return history
}

// Fetch from backend API, merge with localStorage
async function fetchServerHistory(limit = 20) {
  try {
    const res = await fetch(`${API_BASE}/api/v1/history?limit=${limit}`)
    if (!res.ok) return null
    const data = await res.json()
    return (data.items || []).map(item => ({
      id: item.task_id,
      fileName: item.circuit_type || t('unnamed'),
      timestamp: item.created ? item.created * 1000 : Date.now(),
      componentCount: item.component_count || 0,
      errorCount: item.error_count || 0,
      source: 'server',
    }))
  } catch {
    return null
  }
}

function mergeHistory(serverItems, localItems) {
  const seen = new Set()
  const merged = []
  // Server items first (authoritative)
  for (const item of (serverItems || [])) {
    seen.add(item.id)
    merged.push(item)
  }
  // Local items that aren't on server
  for (const item of localItems) {
    if (!seen.has(item.id)) {
      merged.push({ ...item, source: 'local' })
    }
  }
  // Sort newest first
  merged.sort((a, b) => (b.timestamp || 0) - (a.timestamp || 0))
  return merged.slice(0, MAX_HISTORY)
}

export default function HistoryPanel({ onLoad, onClose }) {
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    async function load() {
      const local = loadHistory()
      const server = await fetchServerHistory()
      if (cancelled) return
      setItems(mergeHistory(server, local))
      setLoading(false)
    }
    load()
    return () => { cancelled = true }
  }, [])

  const handleDelete = (id) => {
    removeFromLocalHistory(id)
    setItems(prev => prev.filter(h => h.id !== id))
  }

  if (loading) return (
    <div className="history-panel">
      <div className="history-header">
        <h3>{t('historyTitle')}</h3>
        <button className="btn-close" onClick={onClose}>✕</button>
      </div>
      <p className="empty">⏳ {t('loading') || 'Loading...'}</p>
    </div>
  )

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
              {h.source === 'server' && <span className="history-badge">☁️</span>}
            </div>
            <button className="btn-delete" onClick={() => handleDelete(h.id)}>🗑</button>
          </li>
        ))}
      </ul>
    </div>
  )
}
