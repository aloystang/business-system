import React from 'react'
import { Link, useLocation } from 'react-router-dom'

export default function Layout({ children }) {
  const location = useLocation()

  const navItems = [
    { label: '项目', to: '/projects' },
    { label: '模型规则', to: '/models' },
    { label: '导出与日志', to: '/exports' },
  ]

  const isActive = (path) => location.pathname === path || location.pathname.startsWith(`${path}/`)

  return (
    <div>
      <header className="header">
        <div className="container header-inner">
          <Link className="brand" to="/projects">
            商业项目管理系统
          </Link>
          <div className="header-search">
            <input className="input" placeholder="搜索项目/城市/区域" />
          </div>
          <div className="header-user">
            <div className="avatar">U</div>
            <button className="button secondary">Settings</button>
          </div>
        </div>
      </header>
      <main>
        <div className="container app-shell">
          <aside className="sidebar">
            <div className="sidebar-links">
              {navItems.map((item) => (
                <Link
                  key={item.label}
                  className={`sidebar-link ${isActive(item.to) ? 'active' : ''}`}
                  to={item.to}
                >
                  {item.label}
                </Link>
              ))}
            </div>
          </aside>
          <div className="content">{children}</div>
        </div>
      </main>
    </div>
  )
}
