import React from 'react'
import { t } from '../i18n'

const severityColors = {
  High: '#ef4444', high: '#ef4444',
  Medium: '#f59e0b', medium: '#f59e0b',
  Low: '#3b82f6', low: '#3b82f6'
}

export default function ErrorsList({ errors }) {
  if (!errors || !errors.length) return null

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
