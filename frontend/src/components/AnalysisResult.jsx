import React, { useState } from 'react'
import ReactMarkdown from 'react-markdown'

function AnalysisResult({ result, onReset }) {
  const [activeTab, setActiveTab] = useState('topology')

  const tabs = [
    { id: 'topology', label: '🔍 拓扑结构', icon: '🔍' },
    { id: 'bom', label: '📊 BOM表', icon: '📊' },
    { id: 'errors', label: '⚠️ 错误检测', icon: '⚠️' }
  ]

  const renderTopology = () => (
    <div className="result-content">
      <h3>电路拓扑分析</h3>
      {result.topology?.analysis ? (
        <div className="markdown-content">
          <ReactMarkdown>{result.topology.analysis}</ReactMarkdown>
        </div>
      ) : (
        <p className="no-data">暂无拓扑分析结果</p>
      )}
    </div>
  )

  const renderBOM = () => (
    <div className="result-content">
      <h3>BOM 物料清单</h3>
      {result.bom?.components && result.bom.components.length > 0 ? (
        <table className="bom-table">
          <thead>
            <tr>
              <th>序号</th>
              <th>元件编号</th>
              <th>类型</th>
              <th>参数</th>
              <th>数量</th>
            </tr>
          </thead>
          <tbody>
            {result.bom.components.map((comp, idx) => (
              <tr key={idx}>
                <td>{idx + 1}</td>
                <td>{comp.designator || '-'}</td>
                <td>{comp.type || '-'}</td>
                <td>{comp.value || comp.params || '-'}</td>
                <td>{comp.quantity || 1}</td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <p className="no-data">暂无 BOM 数据</p>
      )}
      {result.bom?.raw_analysis && (
        <details className="raw-details">
          <summary>查看原始分析</summary>
          <div className="markdown-content">
            <ReactMarkdown>{result.bom.raw_analysis}</ReactMarkdown>
          </div>
        </details>
      )}
    </div>
  )

  const renderErrors = () => (
    <div className="result-content">
      <h3>电路错误检测</h3>
      {result.errors?.errors && result.errors.errors.length > 0 ? (
        <div className="error-list">
          {result.errors.errors.map((err, idx) => (
            <div key={idx} className={`error-item error-level-${err.severity || 'warning'}`}>
              <div className="error-header">
                <span className="error-type">{err.type || '未知错误'}</span>
                <span className={`error-severity ${err.severity || 'warning'}`}>
                  {err.severity === 'critical' ? '🔴 严重' : 
                   err.severity === 'warning' ? '🟡 警告' : '🔵 提示'}
                </span>
              </div>
              <p className="error-message">{err.message}</p>
              {err.suggestion && (
                <p className="error-suggestion">💡 建议: {err.suggestion}</p>
              )}
            </div>
          ))}
        </div>
      ) : (
        <div className="no-errors">
          <span className="success-icon">✅</span>
          <p>未检测到明显错误</p>
        </div>
      )}
      {result.errors?.raw_analysis && (
        <details className="raw-details">
          <summary>查看原始分析</summary>
          <div className="markdown-content">
            <ReactMarkdown>{result.errors.raw_analysis}</ReactMarkdown>
          </div>
        </details>
      )}
    </div>
  )

  return (
    <div className="analysis-result">
      <div className="result-header">
        <h2>📝 分析结果</h2>
        <button className="btn btn-secondary" onClick={onReset}>
          重新上传
        </button>
      </div>

      <div className="tabs">
        {tabs.map(tab => (
          <button
            key={tab.id}
            className={`tab ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <div className="tab-content">
        {activeTab === 'topology' && renderTopology()}
        {activeTab === 'bom' && renderBOM()}
        {activeTab === 'errors' && renderErrors()}
      </div>
    </div>
  )
}

export default AnalysisResult
