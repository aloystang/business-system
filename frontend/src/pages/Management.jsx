import React from 'react'
import DashboardLayout from '../components/DashboardLayout'
import ModuleGrid from '../components/ModuleGrid'
import { managementModules } from '../data/modules'

export default function Management() {
  return (
    <DashboardLayout title="管理咨询" overline="MANAGEMENT">
      <section className="dash-form-page">
        <div className="dash-card dash-card-primary dash-landing-hero">
          <div className="dash-module-header">
            <div>
              <h2>管理咨询工作台</h2>
              <p className="dash-module-desc">围绕工程、成本、采购、施工与交付，建立可执行的建设管理线上工作区。</p>
            </div>
            <div className="dash-collect-statuses">
              <span className="dash-status merchant">5 个核心模块</span>
              <span className="dash-status competitor">工程建设闭环</span>
            </div>
          </div>
          <div className="dash-landing-hero-grid">
            <article className="dash-landing-hero-metric">
              <span>模块总数</span>
              <strong>{managementModules.length}</strong>
              <small>覆盖设计、成本、采购、施工、交付</small>
            </article>
            <article className="dash-landing-hero-metric">
              <span>线上能力</span>
              <strong>{managementModules.reduce((sum, item) => sum + (item.canDo?.length || 0), 0)}</strong>
              <small>审批、计划、追踪、验收与留痕</small>
            </article>
            <article className="dash-landing-hero-metric">
              <span>交付成果</span>
              <strong>{managementModules.reduce((sum, item) => sum + (item.outputs?.length || 0), 0)}</strong>
              <small>台账、报告、看板与项目交付文档</small>
            </article>
          </div>
        </div>
        <ModuleGrid modules={managementModules} basePath="/management" />
      </section>
    </DashboardLayout>
  )
}
