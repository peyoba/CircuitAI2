import React from 'react'
import { t } from '../i18n'

export default function TopologyCard({ topology }) {
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
