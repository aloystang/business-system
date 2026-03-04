import React from 'react'
import DashboardLayout from '../components/DashboardLayout'
import ModuleGrid from '../components/ModuleGrid'
import { leasingModules } from '../data/modules'

export default function Leasing() {
  return (
    <DashboardLayout title="招商运营" overline="LEASING">
      <section className="dash-form-page">
        <div className="dash-card dash-card-primary dash-landing-hero">
          <div className="dash-module-header">
            <div>
              <h2>招商运营工作台</h2>
              <p className="dash-module-desc">从招商策略到内容落地与复盘，形成品牌资源、执行过程与结果指标的统一平台。</p>
            </div>
            <div className="dash-collect-statuses">
              <span className="dash-status merchant">5 个核心模块</span>
              <span className="dash-status competitor">品牌与渠道协同</span>
            </div>
          </div>
          <div className="dash-landing-hero-grid">
            <article className="dash-landing-hero-metric">
              <span>模块总数</span>
              <strong>{leasingModules.length}</strong>
              <small>招商策略、资源整合、执行、落地、复盘</small>
            </article>
            <article className="dash-landing-hero-metric">
              <span>线上能力</span>
              <strong>{leasingModules.reduce((sum, item) => sum + (item.canDo?.length || 0), 0)}</strong>
              <small>覆盖品牌资源、进度、条款与风险控制</small>
            </article>
            <article className="dash-landing-hero-metric">
              <span>交付成果</span>
              <strong>{leasingModules.reduce((sum, item) => sum + (item.outputs?.length || 0), 0)}</strong>
              <small>策略总表、资源池画像、复盘报告</small>
            </article>
          </div>
        </div>
        <ModuleGrid modules={leasingModules} basePath="/leasing" />
      </section>
    </DashboardLayout>
  )
}
