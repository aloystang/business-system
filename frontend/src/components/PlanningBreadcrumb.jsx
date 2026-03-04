import React from 'react'
import { Link } from 'react-router-dom'

export default function PlanningBreadcrumb({ sectionLabel, currentLabel }) {
  return (
    <div className="dash-planning-breadcrumb" aria-label="breadcrumb">
      <Link to="/planning">策划咨询</Link>
      <span className="dash-planning-sep">/</span>
      {sectionLabel ? (
        <>
          <span>{sectionLabel}</span>
          {currentLabel ? <span className="dash-planning-sep">/</span> : null}
        </>
      ) : null}
      {currentLabel ? <strong>{currentLabel}</strong> : null}
    </div>
  )
}
