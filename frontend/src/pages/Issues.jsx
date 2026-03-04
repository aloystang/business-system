import React, { useEffect, useState } from 'react'
import { apiJson } from '../lib/api'

export default function IssuesCenter() {
  const [issues, setIssues] = useState([])
  const [status, setStatus] = useState('')

  const loadIssues = async () => {
    const query = status ? `?status=${status}` : ''
    const data = await apiJson(`/api/issues${query}`)
    setIssues(data)
  }

  useEffect(() => {
    loadIssues()
  }, [status])

  return (
    <div className="card">
      <h2>闭环中心</h2>
      <div style={{ maxWidth: 240, marginBottom: 12 }}>
        <label>状态筛选</label>
        <select className="select" value={status} onChange={(e) => setStatus(e.target.value)}>
          <option value="">全部</option>
          <option value="open">open</option>
          <option value="in_progress">in_progress</option>
          <option value="resolved">resolved</option>
          <option value="closed">closed</option>
        </select>
      </div>
      <table className="table">
        <thead>
          <tr>
            <th>项目ID</th>
            <th>标题</th>
            <th>状态</th>
            <th>优先级</th>
            <th>截止</th>
          </tr>
        </thead>
        <tbody>
          {issues.map((issue) => (
            <tr key={issue.id}>
              <td>{issue.project_id}</td>
              <td>{issue.title}</td>
              <td>{issue.status}</td>
              <td>{issue.priority}</td>
              <td>{issue.due_date || '-'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
