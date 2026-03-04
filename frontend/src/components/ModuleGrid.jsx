import React from 'react'
import { NavLink } from 'react-router-dom'

export default function ModuleGrid({ modules, basePath }) {
  const base = basePath.endsWith('/') ? basePath.slice(0, -1) : basePath

  return (
    <div className="dash-module-grid">
      {modules.map((module) => (
        <NavLink key={module.id} to={`${base}/${module.id}`} className="dash-module-card">
          <span className="dash-module-card-icon">
            <span className="material-symbols-outlined">{module.icon}</span>
          </span>
          <div className="dash-module-card-title">{module.title}</div>
          <div className="dash-module-card-en">{module.en}</div>
          <div className="dash-module-card-desc">{module.desc}</div>
          <div className="dash-module-card-meta">
            <span>能力 {module.canDo?.length || 0}</span>
            <span>交付 {module.outputs?.length || 0}</span>
          </div>
        </NavLink>
      ))}
    </div>
  )
}
