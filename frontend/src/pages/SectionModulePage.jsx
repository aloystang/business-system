import React from 'react'
import { Navigate, useParams } from 'react-router-dom'
import DashboardLayout from '../components/DashboardLayout'
import ModuleTabs from '../components/ModuleTabs'

export default function SectionModulePage({ sectionTitle, overline, modules, basePath }) {
  const { moduleId } = useParams()
  const module = modules.find((item) => item.id === moduleId)

  if (!module) {
    return <Navigate to={basePath} replace />
  }

  return (
    <DashboardLayout title={sectionTitle} overline={overline}>
      <section className="dash-form-page">
        <div className="dash-card dash-card-secondary dash-page-intro dash-page-intro--compact">
          <div className="dash-module-header">
            <div>
              <h2>{module.title}</h2>
              <p className="dash-module-desc">{module.desc}</p>
            </div>
            <div className="dash-collect-statuses">
              <span className="dash-status merchant">{sectionTitle}</span>
              <span className="dash-status competitor">{module.en}</span>
            </div>
          </div>
          <div className="dash-page-intro-grid">
            <article className="dash-page-intro-metric">
              <span>模块目标</span>
              <strong>{module.goal ? '已配置' : '待配置'}</strong>
              <small>{module.goal || '待补充该模块的目标说明。'}</small>
            </article>
            <article className="dash-page-intro-metric">
              <span>线上能力</span>
              <strong>{module.canDo?.length || 0}</strong>
              <small>覆盖流程动作、节点控制与协同执行</small>
            </article>
            <article className="dash-page-intro-metric">
              <span>交付成果</span>
              <strong>{module.outputs?.length || 0}</strong>
              <small>支撑方案、台账、报告与过程留痕</small>
            </article>
          </div>
        </div>
        <ModuleTabs modules={modules} basePath={basePath} />
        <div className="dash-card dash-form-card">
          <div className="dash-card-header">
            <strong className="dash-section-title">
              <span className="material-symbols-outlined">{module.icon}</span>
              {module.title}
            </strong>
          </div>
          <p className="dash-subtext">{module.desc}</p>
        </div>

        <div className="dash-module-detail-grid">
          <div className="dash-card dash-form-card">
            <div className="dash-card-header">
              <strong className="dash-section-title">模块目标</strong>
            </div>
            <p className="dash-subtext">{module.goal || '待配置模块目标。'}</p>
          </div>

          <div className="dash-card dash-form-card">
            <div className="dash-card-header">
              <strong className="dash-section-title">线上可执行能力</strong>
            </div>
            <div className="dash-capability-chips">
              {(module.canDo || []).map((item) => (
                <span key={item} className="dash-capability-chip">
                  {item}
                </span>
              ))}
            </div>
          </div>

          <div className="dash-card dash-form-card">
            <div className="dash-card-header">
              <strong className="dash-section-title">可交付成果</strong>
            </div>
            <ul className="dash-deliverable-list">
              {(module.outputs || []).map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </div>
        </div>
      </section>
    </DashboardLayout>
  )
}
