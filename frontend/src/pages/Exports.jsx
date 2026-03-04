import React, { useState } from 'react'

export default function Exports() {
  const [tab, setTab] = useState('export')

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">导出与日志</h1>
          <div className="page-subtitle">查看导出结果与计算记录</div>
        </div>
        <div className="page-actions">
          <button className="button">导出 JSON</button>
        </div>
      </div>

      <div className="tabs">
        <div className={`tab ${tab === 'export' ? 'active' : ''}`} onClick={() => setTab('export')}>
          导出
        </div>
        <div className={`tab ${tab === 'logs' ? 'active' : ''}`} onClick={() => setTab('logs')}>
          日志
        </div>
      </div>

      {tab === 'export' && (
        <div className="card">
          <h3>导出</h3>
          <div className="placeholder-line" />
          <div className="placeholder-line" />
        </div>
      )}

      {tab === 'logs' && (
        <div className="card">
          <h3>日志</h3>
          <div className="placeholder-line" />
          <div className="placeholder-line" />
          <div className="placeholder-line" />
        </div>
      )}
    </div>
  )
}
