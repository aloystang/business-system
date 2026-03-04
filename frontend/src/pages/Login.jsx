import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { apiJson, setToken } from '../lib/api'

export default function Login() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const navigate = useNavigate()

  const handleSubmit = async (event) => {
    event.preventDefault()
    setError('')
    try {
      const data = await apiJson('/api/auth/login', {
        method: 'POST',
        body: JSON.stringify({ username, password }),
      })
      setToken(data.access_token)
      navigate('/planning')
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <main className="dash-auth-shell">
      <div className="dash-auth-card">
        <div className="dash-auth-brand">Business OS</div>
        <h2>登录系统</h2>
        <p className="dash-subtext">使用本地账号进入商业管理系统，继续进行前策、情报与地图工作台操作。</p>
        {error && <div className="notice">{error}</div>}
        <form onSubmit={handleSubmit} className="dash-auth-grid">
          <label className="dash-field">
            <span>用户名</span>
            <input
              className="dash-input"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
            />
          </label>
          <label className="dash-field">
            <span>密码</span>
            <input
              className="dash-input"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </label>
          <button className="dash-btn primary" type="submit">
            登录
          </button>
        </form>
      </div>
    </main>
  )
}
