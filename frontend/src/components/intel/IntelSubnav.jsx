import React from 'react'
import { NavLink, useLocation } from 'react-router-dom'

const tabs = [
  { to: '/intel', alias: ['/intel/news'], label: '新闻采集' },
  { to: '/intel/tenders', alias: [], label: '招投标采集' },
]

export default function IntelSubnav() {
  const location = useLocation()

  return (
    <nav className="intel-subnav" aria-label="情报专题导航">
      {tabs.map((tab) => {
        const isAliasActive = tab.alias.some((path) => location.pathname === path)
        return (
          <NavLink
            key={tab.to}
            to={tab.to}
            end={tab.to === '/intel'}
            className={({ isActive }) =>
              `intel-subnav-link ${isActive || isAliasActive ? 'active' : ''}`
            }
          >
            {tab.label}
          </NavLink>
        )
      })}
    </nav>
  )
}
