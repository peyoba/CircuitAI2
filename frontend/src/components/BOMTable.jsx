import React from 'react'
import { t } from '../i18n'

export default function BOMTable({ bom }) {
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
