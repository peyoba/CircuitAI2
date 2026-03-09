import React from 'react'

export default function KeyNodes({ nodes }) {
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
