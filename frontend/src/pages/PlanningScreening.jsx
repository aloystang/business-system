import React from 'react'
import { useNavigate } from 'react-router-dom'
import DashboardLayout from '../components/DashboardLayout'
import ModuleTabs from '../components/ModuleTabs'
import { planningModules } from '../data/modules'
import { setSelectedPlanningProjectId } from '../lib/planningProject'

const entryCards = [
  {
    key: 'new',
    title: '新建项目',
    en: 'New Project',
    desc: '进入数据采集与填报页面，创建并确认新项目。',
    icon: 'add_circle',
  },
  {
    key: 'history',
    title: '历史项目查询',
    en: 'History',
    desc: '查看往期填报与筛选结果，支持筛选与进入工作台。',
    icon: 'history',
  },
]

export default function PlanningScreeningEntry() {
  const navigate = useNavigate()

  const handleCardClick = (key) => {
    if (key === 'new') {
      setSelectedPlanningProjectId('')
      navigate('/planning/collect')
      return
    }
    navigate('/planning/screening/history')
  }

  return (
    <DashboardLayout title="策划咨询" overline="PLANNING">
      <section className="dash-form-page">
        <ModuleTabs modules={planningModules} basePath="/planning" />

        <div className="dash-module-header">
          <div>
            <h2>项目筛选</h2>
            <p className="dash-module-desc">请选择入口：新建项目或历史项目查询。</p>
          </div>
        </div>

        <div className="dash-screening-entry-grid">
          {entryCards.map((card) => (
            <button
              key={card.key}
              type="button"
              className="dash-screening-entry-card"
              onClick={() => handleCardClick(card.key)}
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
