import React from 'react'
import DashboardLayout from '../components/DashboardLayout'

export default function Settings() {
  return (
    <DashboardLayout title="设置" overline="SETTINGS">
      <section className="dash-form-page">
        <div className="dash-card dash-card-secondary dash-page-intro dash-page-intro--compact">
          <div className="dash-module-header">
            <div>
              <h2>系统设置</h2>
              <p className="dash-module-desc">管理个人偏好、系统配置与后续集成能力，当前保留为设置页占位。</p>
            </div>
            <div className="dash-collect-statuses">
              <span className="dash-status merchant">系统页</span>
              <span className="dash-status competitor">待扩展</span>
            </div>
          </div>
          <div className="dash-page-intro-grid">
            <article className="dash-page-intro-metric">
              <span>当前状态</span>
              <strong>占位</strong>
              <small>后续可接入用户偏好、通知策略与系统集成配置。</small>
            </article>
            <article className="dash-page-intro-metric">
              <span>推荐方向</span>
              <strong>配置中心</strong>
              <small>统一管理地图、情报同步、导出与权限相关配置。</small>
            </article>
            <article className="dash-page-intro-metric">
              <span>交互形态</span>
              <strong>工作台</strong>
              <small>延续当前全站设计系统，不独立采用新框架。</small>
            </article>
          </div>
        </div>
        <div className="dash-card dash-empty-page-card">
          <strong className="dash-section-title">设置内容</strong>
          <p className="dash-subtext">这里预留系统级设置内容，包括地图 Key、情报同步、通知偏好与角色权限相关配置。</p>
        </div>
      </section>
    </DashboardLayout>
  )
}
