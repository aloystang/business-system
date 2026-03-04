import React from 'react'
import { NavLink } from 'react-router-dom'

export default function ModuleTabs({ modules, basePath }) {
  const base = basePath.endsWith('/') ? basePath.slice(0, -1) : basePath

  return (
    <div className="dash-module-tabs">
      {modules.map((module) => (
        <NavLink
          key={module.id}
          to={`${base}/${module.id}`}
          className={({ isActive }) => `dash-module-tab ${isActive ? 'active' : ''}`}
        >
          <span className="dash-module-title">{module.title}</span>
          <span className="dash-module-en">{module.en}</span>
        </NavLink>
      ))}
    </div>
  )
}
