import React from 'react'
import { ShieldCheck, TriangleAlert } from 'lucide-react'

// 演示环境的角色示例账号（密码统一 demo1234，仅用于快速切身份体验 RBAC 差异；
// 生产上线前应移除，改为真实姓名 + 强密码）。
const DEMO_ACCOUNTS = [
  { username: 'admin', password: 'admin123', label: '系统管理员', desc: '全部权限' },
  { username: 'chenyu', password: 'demo1234', label: '陈昱 · 项目招商经理', desc: '项目/匹配读写' },
  { username: 'liran', password: 'demo1234', label: '李然 · 招商拓展经理', desc: '品牌/匹配读写' },
  { username: 'zhaoqing', password: 'demo1234', label: '赵青 · 管理层', desc: '全项目只读+敏感项目' },
  { username: 'wangke', password: 'demo1234', label: '王珂 · 受限查看者', desc: '仅可查看' },
]

export default function LoginPage({ onLogin }) {
  const [username, setUsername] = React.useState('')
  const [password, setPassword] = React.useState('')
  const [error, setError] = React.useState('')
  const [busy, setBusy] = React.useState(false)

  const submit = async (event) => {
    event.preventDefault()
    if (!username || !password) return
    setBusy(true)
    setError('')
    try {
      await onLogin(username, password)
    } catch (err) {
      setError(err.message || '登录失败')
    } finally {
      setBusy(false)
    }
  }

  const fillDemo = (acc) => {
    setUsername(acc.username)
    setPassword(acc.password)
    setError('')
  }

  return <div className="loginScreen">
    <div className="loginCard">
      <div className="loginBrand"><span className="loginMark">XS</span><div><strong>新盛资源管理</strong><small>品牌与项目资源管理系统</small></div></div>
      <form className="loginForm" onSubmit={submit}>
        <label>用户名<input autoFocus value={username} onChange={(e) => setUsername(e.target.value)} placeholder="请输入用户名" autoComplete="username" /></label>
        <label>密码<input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="请输入密码" autoComplete="current-password" /></label>
        {error && <div className="loginError"><TriangleAlert size={14} />{error}</div>}
        <button type="submit" className="loginSubmit" disabled={busy || !username || !password}>{busy ? '登录中…' : '登 录'}</button>
      </form>
      <div className="loginDemo">
        <div className="loginDemoHead"><ShieldCheck size={13} />演示环境 · 按角色体验权限差异</div>
        <div className="loginDemoList">
          {DEMO_ACCOUNTS.map((acc) => (
            <button type="button" key={acc.username} onClick={() => fillDemo(acc)}>
              <strong>{acc.label}</strong><small>{acc.desc}</small>
            </button>
          ))}
        </div>
        <p className="loginDemoHint">点击账号自动填入，仍需手动点击"登录"确认。</p>
      </div>
    </div>
  </div>
}
