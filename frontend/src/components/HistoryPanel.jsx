import React, { useState } from 'react'
import { t } from '../i18n'

const HISTORY_KEY = 'circuitai_history'
const MAX_HISTORY = 20

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

function removeFromHistory(id) {
  const history = loadHistory().filter(h => h.id !== id)
  localStorage.setItem(HISTORY_KEY, JSON.stringify(history))
  return history
}

export default function HistoryPanel({ onLoad, onClose }) {
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
