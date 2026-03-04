import React from 'react'
import { useNavigate } from 'react-router-dom'
import DashboardLayout from '../components/DashboardLayout'
import { setSelectedPlanningProjectId } from '../lib/planningProject'

const planningEntryCards = [
  {
    key: 'new',
    title: '新建项目',
    en: 'New Project',
    desc: '进入数据采集、项目筛选与项目测算流程。',
    icon: 'add_circle',
  },
  {
    key: 'history',
    title: '数据查询',
    en: 'Data Query',
    desc: '查看历史填报、点位管理与删除恢复。',
    icon: 'query_stats',
  },
  {
    key: 'merchant',
    title: '商家信息',
    en: 'Merchant Survey',
    desc: '独立采集商家数据，可后续挂接项目。',
    icon: 'storefront',
  },
  {
    key: 'competitor',
    title: '竞争关系',
    en: 'Competitor Survey',
    desc: '独立采集竞品数据，持续沉淀城市样本。',
    icon: 'conversion_path',
  },
]

export default function PlanningOverview() {
  const navigate = useNavigate()

  const handleEntryClick = (key) => {
    if (key === 'new') {
      setSelectedPlanningProjectId('')
      navigate('/planning/new/collect')
      return
    }
    if (key === 'history') {
      navigate('/planning/history')
      return
    }
    if (key === 'merchant') {
      navigate('/planning/merchant')
      return
    }
    navigate('/planning/competitor')
  }

  return (
    <DashboardLayout title="策划咨询" overline="PLANNING">
      <section className="dash-form-page">
        <div className="dash-card dash-card-primary dash-landing-hero dash-planning-hero">
          <div className="dash-module-header">
            <div>
              <h2>策划咨询工作台</h2>
              <p className="dash-module-desc">围绕项目孵化与城市数据池沉淀，组织前策采集、筛选、测算与日常样本积累。</p>
            </div>
            <div className="dash-collect-statuses">
              <span className="dash-status merchant">4 个核心入口</span>
              <span className="dash-status competitor">项目流 + 数据池</span>
            </div>
          </div>
          <div className="dash-planning-hero-grid">
            <article className="dash-planning-hero-metric">
              <span>新建项目</span>
              <strong>采集 → 筛选 → 测算</strong>
              <small>完整前策工作流</small>
            </article>
            <article className="dash-planning-hero-metric">
              <span>数据查询</span>
              <strong>查 / 删 / 恢复</strong>
              <small>历史点位治理工作台</small>
            </article>
            <article className="dash-planning-hero-metric">
              <span>日常沉淀</span>
              <strong>商家 + 竞品</strong>
              <small>独立采集并沉淀城市样本</small>
            </article>
          </div>
        </div>

        <div className="dash-screening-entry-grid">
          {planningEntryCards.map((card) => (
            <button
              key={card.key}
              type="button"
              className="dash-screening-entry-card"
              onClick={() => handleEntryClick(card.key)}
            >
              <span className="dash-screening-entry-icon material-symbols-outlined">{card.icon}</span>
              <div className="dash-screening-entry-title">{card.title}</div>
              <div className="dash-screening-entry-en">{card.en}</div>
              <p className="dash-screening-entry-desc">{card.desc}</p>
            </button>
          ))}
        </div>
      </section>
    </DashboardLayout>
  )
}
