import React from 'react'
import DashboardLayout from '../components/DashboardLayout'

export default function Profile() {
  return (
    <DashboardLayout title="用户" overline="PROFILE">
      <section className="dash-form-page">
        <div className="dash-card dash-card-secondary dash-page-intro dash-page-intro--compact">
          <div className="dash-module-header">
            <div>
              <h2>用户中心</h2>
              <p className="dash-module-desc">统一承接用户信息、登录状态与后续角色能力配置，当前保留为个人中心占位。</p>
            </div>
            <div className="dash-collect-statuses">
              <span className="dash-status merchant">个人页</span>
              <span className="dash-status competitor">待扩展</span>
            </div>
          </div>
          <div className="dash-page-intro-grid">
            <article className="dash-page-intro-metric">
              <span>账户状态</span>
              <strong>在线</strong>
              <small>当前使用本地账号进入系统，后续可扩展到组织成员体系。</small>
            </article>
            <article className="dash-page-intro-metric">
              <span>推荐方向</span>
              <strong>角色能力</strong>
              <small>沉淀个人负责项目、操作记录、收藏与通知订阅。</small>
            </article>
            <article className="dash-page-intro-metric">
              <span>展示形态</span>
              <strong>档案卡</strong>
              <small>与系统设置页保持统一的企业后台观感。</small>
            </article>
          </div>
        </div>
        <div className="dash-card dash-empty-page-card">
          <strong className="dash-section-title">用户档案</strong>
          <p className="dash-subtext">这里预留个人资料、角色权限、项目责任与操作轨迹等信息模块。</p>
        </div>
      </section>
    </DashboardLayout>
  )
}
