import React from 'react'
import { t } from '../i18n'

export default function FunctionCard({ func }) {
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
