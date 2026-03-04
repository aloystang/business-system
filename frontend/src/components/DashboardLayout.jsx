import React from 'react'
import { NavLink, useLocation } from 'react-router-dom'

const navSections = [
  {
    title: '总览',
    items: [{ to: '/overview', label: '业务全览', icon: 'grid_view' }],
  },
  {
    title: '业务',
    items: [
      { to: '/planning', label: '策划咨询', icon: 'lightbulb' },
      { to: '/management', label: '管理咨询', icon: 'fact_check' },
      { to: '/leasing', label: '招商运营', icon: 'storefront' },
      { to: '/operations', label: '委托运营', icon: 'handshake' },
      { to: '/intel', label: '情报中心', icon: 'newspaper' },
    ],
  },
  {
    title: '系统',
    items: [
      { to: '/settings', label: '设置', icon: 'settings' },
      { to: '/profile', label: '用户', icon: 'account_circle' },
    ],
  },
]

function NavItem({ to, label, icon }) {
  return (
    <NavLink to={to} className={({ isActive }) => `dash-nav-item ${isActive ? 'active' : ''}`}>
      <span className="dash-icon">
        <span className="material-symbols-outlined">{icon}</span>
      </span>
      <span className="dash-nav-label">{label}</span>
    </NavLink>
  )
}

export default function DashboardLayout({ title, overline, children }) {
  const location = useLocation()
  const isIntel = location.pathname === '/intel' || location.pathname.startsWith('/intel/')

  const searchPlaceholder = (() => {
    if (location.pathname.startsWith('/overview')) return '搜索区域 / 商家 / 竞品'
    if (location.pathname.startsWith('/planning')) return '搜索项目 / 模块 / 数据'
    if (location.pathname.startsWith('/intel')) return '搜索情报 / 新闻 / 招标'
    return '搜索内容'
  })()

  return (
    <div className={`dash-root ${isIntel ? 'dash-root--intel' : ''}`}>
      <aside className="dash-sidebar">
        <NavLink to="/overview" className="dash-logo">
          <span className="dash-logo-kicker">COMMERCIAL OS</span>
          <span className="dash-logo-wordmark">
            <span className="dash-logo-mark">
              <span className="material-symbols-outlined">grid_view</span>
            </span>
            <span className="dash-logo-copy">
              <strong>业务系统</strong>
              <small>商业管理工作台</small>
            </span>
          </span>
        </NavLink>

        <nav className="dash-nav" aria-label="主导航">
          {navSections.map((section) => (
            <div key={section.title} className="dash-nav-section">
              <div className="dash-nav-section-title">{section.title}</div>
              <div className="dash-nav-section-items">
                {section.items.map((item) => (
                  <NavItem key={item.to} {...item} />
                ))}
              </div>
            </div>
          ))}
        </nav>

        <div className="dash-sidebar-foot">
          <div className="dash-sidebar-user">
            <span className="dash-sidebar-user-avatar">A</span>
            <div className="dash-sidebar-user-copy">
              <strong>Admin</strong>
              <small>本地账号</small>
            </div>
          </div>
        </div>
      </aside>

      <main className={`dash-main ${isIntel ? 'dash-main--intel' : ''}`}>
        <header className={`dash-header ${isIntel ? 'dash-header--compact' : ''}`}>
          <div className="dash-header-copy">
            {overline && <div className="dash-overline">{overline}</div>}
            <h1>{title}</h1>
          </div>

          <div className="dash-header-tools">
            <label className="dash-top-search" aria-label="全局搜索">
              <span className="material-symbols-outlined">search</span>
              <input type="search" placeholder={searchPlaceholder} />
              <span className="dash-top-search-kbd">/</span>
            </label>
            <button className="dash-tool-btn dash-bell" type="button" aria-label="通知">
              <span className="material-symbols-outlined">notifications</span>
              <span className="dash-dot" />
            </button>
            <button className="dash-user-chip" type="button" aria-label="用户入口">
              <span className="dash-user-avatar">A</span>
              <span className="dash-user-meta">
                <strong>Admin</strong>
                <small>本地账号</small>
              </span>
            </button>
          </div>
        </header>

        <div className="dash-page-shell">{children}</div>
      </main>
    </div>
  )
}
