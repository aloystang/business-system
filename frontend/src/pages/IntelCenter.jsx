import React, { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import DashboardLayout from '../components/DashboardLayout'
import IntelSubnav from '../components/intel/IntelSubnav'
import { apiJson } from '../lib/api'
import { toQuery } from '../lib/intel'

export default function IntelCenter() {
  const navigate = useNavigate()
  const [kpis, setKpis] = useState(null)
  const [tenderTotal, setTenderTotal] = useState(0)
  const [newsTotal, setNewsTotal] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const loadData = async () => {
    setLoading(true)
    setError('')
    try {
      const [kpiResp, tenderResp, newsResp, jobsResp] = await Promise.all([
        apiJson('/api/intel/kpis?item_type=all'),
        apiJson(`/api/intel/items?${toQuery({ item_type: 'tender', page: 1, page_size: 1 })}`),
        apiJson(`/api/intel/items?${toQuery({ item_type: 'news', page: 1, page_size: 1 })}`),
        apiJson('/api/intel/sync/jobs?limit=1'),
      ])
      setKpis(kpiResp)
      setTenderTotal(Number(tenderResp.total || 0))
      setNewsTotal(Number(newsResp.total || 0))
      setKpis((prev) => ({
        ...(prev || {}),
        ...kpiResp,
        latest_sync_status: jobsResp?.[0]?.status || '待同步',
      }))
    } catch (err) {
      setError(err.message || '加载情报中心失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  const kpiCards = useMemo(
    () => [
      { label: '情报总量', value: kpis?.total_count ?? 0, tone: 'primary' },
      { label: '新闻采集', value: newsTotal, tone: 'secondary' },
      { label: '招投标采集', value: tenderTotal, tone: 'secondary' },
      { label: '最近同步', value: kpis?.latest_sync_status || '待同步', tone: 'muted' },
    ],
    [kpis, newsTotal, tenderTotal]
  )

  const entryCards = [
    {
      title: '新闻采集',
      english: 'News Feed',
      description: '进入品牌化新闻专题页，查看精选内容、资讯卡片流与详情抽屉。',
      stat: `${newsTotal} 条`,
      icon: 'newspaper',
      tone: 'primary',
      to: '/intel/news',
    },
    {
      title: '招投标采集',
      english: 'Tender Monitor',
      description: '进入招投标专题页，聚合预算、截止时间、发布方与原文链接。',
      stat: `${tenderTotal} 条`,
      icon: 'gavel',
      tone: 'secondary',
      to: '/intel/tenders',
    },
    {
      title: '规则管理',
      english: 'Rule Config',
      description: '维护关键词、类型、区域与预算阈值规则，支撑后续情报策略。',
      stat: '规则工作台',
      icon: 'tune',
      tone: 'muted',
      to: '/intel/rules',
    },
    {
      title: '同步作业',
      english: 'Sync Jobs',
      description: '查看同步历史、执行状态与手动同步入口，核查数据链路是否正常。',
      stat: kpis?.latest_sync_status || '待同步',
      icon: 'sync',
      tone: 'muted',
      to: '/intel/sync',
    },
  ]

  return (
    <DashboardLayout title="情报中心" overline="INTELLIGENCE">
      <section className="dash-form-page">
        <IntelSubnav />

        <div className="dash-card dash-card-primary dash-page-intro intel-hub-hero">
          <div className="dash-module-header">
            <div>
              <h2>情报中心</h2>
              <p className="dash-module-desc">统一进入新闻采集、招投标采集、规则管理与同步作业的总入口。</p>
            </div>
            <div className="dash-history-actions">
              <button type="button" className="dash-btn secondary" disabled={loading} onClick={loadData}>
                刷新
              </button>
            </div>
          </div>
          <div className="intel-hero-grid">
            <article className="intel-hero-metric">
              <span>信息结构</span>
              <strong>新闻 / 招投标</strong>
              <small>拆分为两个独立专题页，保持阅读效率与页面辨识度。</small>
            </article>
            <article className="intel-hero-metric">
              <span>专题模式</span>
              <strong>总入口 + 专题页</strong>
              <small>总入口负责分发，专题页负责浏览、详情与原文跳转。</small>
            </article>
            <article className="intel-hero-metric">
              <span>当前总量</span>
              <strong>{(kpis?.total_count ?? 0).toLocaleString()}</strong>
              <small>保留现有接口与数据结构，不改后端逻辑。</small>
            </article>
          </div>
        </div>

        {error ? <div className="dash-card alert">{error}</div> : null}

        <div className="dash-history-kpis intel-hub-kpis">
          {kpiCards.map((card) => (
            <div
              key={card.label}
              className={`dash-card dash-history-kpi-card ${
                card.tone === 'primary'
                  ? 'dash-card-primary'
                  : card.tone === 'secondary'
                    ? 'dash-card-secondary'
                    : 'dash-card-muted'
              }`}
            >
              <span>{card.label}</span>
              <strong>{card.value}</strong>
            </div>
          ))}
        </div>

        <div className="intel-hub-grid">
          {entryCards.map((card) => (
            <button
              key={card.title}
              type="button"
              className={`dash-card intel-hub-entry ${
                card.tone === 'primary'
                  ? 'dash-card-primary'
                  : card.tone === 'secondary'
                    ? 'dash-card-secondary'
                    : 'dash-card-muted'
              }`}
              onClick={() => navigate(card.to)}
            >
              <span className="intel-hub-entry-icon material-symbols-outlined">{card.icon}</span>
              <div className="intel-hub-entry-copy">
                <small>{card.english}</small>
                <strong>{card.title}</strong>
                <p>{card.description}</p>
              </div>
              <div className="intel-hub-entry-foot">
                <span className="dash-pill muted">{card.stat}</span>
                <span className="material-symbols-outlined">arrow_outward</span>
              </div>
            </button>
          ))}
        </div>
      </section>
    </DashboardLayout>
  )
}
