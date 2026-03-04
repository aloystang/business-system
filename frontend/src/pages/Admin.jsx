import React, { useEffect, useState } from 'react'
import { apiJson } from '../lib/api'

export default function Admin() {
  const [rules, setRules] = useState(null)

  useEffect(() => {
    apiJson('/api/rules/stage').then(setRules).catch(() => {})
  }, [])

  return (
    <div className="card">
      <h2>管理视图</h2>
      <p>阶段门槛规则（只读）</p>
      <pre style={{ background: '#0f172a', color: 'white', padding: 12, borderRadius: 8 }}>
        {rules ? JSON.stringify(rules, null, 2) : '加载中...'}
      </pre>
    </div>
  )
}
