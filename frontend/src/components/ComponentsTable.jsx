import React from 'react'
import { t } from '../i18n'

export default function ComponentsTable({ components }) {
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
