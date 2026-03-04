import React from 'react'
import DashboardLayout from '../components/DashboardLayout'
import ModuleGrid from '../components/ModuleGrid'
import { operationsModules } from '../data/modules'

export default function Operations() {
  return (
    <DashboardLayout title="委托运营" overline="OPERATIONS">
      <section className="dash-form-page">
        <div className="dash-card dash-card-primary dash-landing-hero">
          <div className="dash-module-header">
            <div>
              <h2>委托运营工作台</h2>
              <p className="dash-module-desc">围绕筹开、日常运营、经营管理、内容运营与增值提升，承接长期运营闭环。</p>
            </div>
            <div className="dash-collect-statuses">
              <span className="dash-status merchant">5 个核心模块</span>
              <span className="dash-status competitor">长期经营与增值</span>
            </div>
          </div>
          <div className="dash-landing-hero-grid">
            <article className="dash-landing-hero-metric">
              <span>模块总数</span>
              <strong>{operationsModules.length}</strong>
              <small>筹开、运营、经营、内容、增值提升</small>
            </article>
            <article className="dash-landing-hero-metric">
              <span>线上能力</span>
              <strong>{operationsModules.reduce((sum, item) => sum + (item.canDo?.length || 0), 0)}</strong>
              <small>客流、租金、服务、内容与风险预警</small>
            </article>
            <article className="dash-landing-hero-metric">
              <span>交付成果</span>
              <strong>{operationsModules.reduce((sum, item) => sum + (item.outputs?.length || 0), 0)}</strong>
              <small>筹开计划、经营分析、长期价值提升报告</small>
            </article>
          </div>
        </div>
        <ModuleGrid modules={operationsModules} basePath="/operations" />
      </section>
    </DashboardLayout>
  )
}
