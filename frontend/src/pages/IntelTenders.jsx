import React, { useEffect, useMemo, useState } from 'react'
import DashboardLayout from '../components/DashboardLayout'
import IntelSubnav from '../components/intel/IntelSubnav'
import IntelDetailDrawer from '../components/intel/IntelDetailDrawer'
import IntelSourcePanel from '../components/intel/IntelSourcePanel'
import { apiJson } from '../lib/api'
import { INTEL_PAGE_SIZE, groupBySource, toQuery } from '../lib/intel'

export default function IntelTenders() {
  const [kpis, setKpis] = useState(null)
  const [items, setItems] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [detailLoading, setDetailLoading] = useState(false)
  const [detailError, setDetailError] = useState('')
  const [selectedDetail, setSelectedDetail] = useState(null)

  useEffect(() => {
    const load = async () => {
      setLoading(true)
      setError('')
      try {
        const [kpiResp, itemsResp] = await Promise.all([
          apiJson('/api/intel/kpis?item_type=tender'),
          apiJson(`/api/intel/items?${toQuery({ item_type: 'tender', page, page_size: INTEL_PAGE_SIZE })}`),
        ])
        setKpis(kpiResp)
        setItems(itemsResp.items || [])
        setTotal(Number(itemsResp.total || 0))
      } catch (err) {
        setError(err.message || '加载招投标采集失败')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [page])

  const openDetail = async (itemId) => {
    setDrawerOpen(true)
    setDetailLoading(true)
    setDetailError('')
    try {
      const detail = await apiJson(`/api/intel/items/${itemId}`)
      setSelectedDetail(detail)
    } catch (err) {
      setDetailError(err.message || '加载详情失败')
      setSelectedDetail(null)
    } finally {
      setDetailLoading(false)
    }
  }

  const groups = useMemo(() => groupBySource(items), [items])
  const stageGroups = useMemo(() => groups.slice(0, 3), [groups])
  const feedGroups = useMemo(() => groups.slice(3), [groups])
  const headlineItems = useMemo(() => items.slice(0, 2), [items])
  const totalPages = Math.max(1, Math.ceil(total / INTEL_PAGE_SIZE))

  return (
    <DashboardLayout title="招投标采集" overline="INTELLIGENCE">
      <section className="intel-editorial-shell">
        <section className="intel-immersive-hero intel-immersive-hero--tenders">
          <IntelSubnav />

          <div className="intel-immersive-badge intel-immersive-badge--tender">
            <span className="material-symbols-outlined">gavel</span>
            <div>
              <strong>TENDER</strong>
              <small>NOW</small>
            </div>
          </div>

          <div className="intel-immersive-copy">
            <span className="intel-immersive-kicker">PROCUREMENT & BIDDING</span>
            <h2>招投标采集</h2>
            <p>Track public resources, service procurement and tender updates in a single reading surface.</p>
          </div>

          {headlineItems.length ? (
            <div className="intel-headline-wall">
              {headlineItems.map((item, index) => (
                <article key={item.id} className={`intel-headline-card intel-headline-card--${index === 0 ? 'primary' : 'secondary'}`}>
                  <span className="intel-headline-label">{index === 0 ? 'KEY TENDER' : 'LATEST NOTICE'}</span>
                  <h3>{item.title}</h3>
                </article>
              ))}
            </div>
          ) : null}

          <div className="intel-immersive-stage intel-immersive-stage--tender">
            <div className="intel-stage-topline">
              <div className="intel-stage-brand">
                <span className="material-symbols-outlined">policy</span>
                <div>
                  <strong>Tender Scan</strong>
                  <small>按平台分组 · 每个来源展示多条公告</small>
                </div>
              </div>
              <div className="intel-stage-meta">
                <span>{(kpis?.today_count ?? 0).toLocaleString()} 今日新增</span>
                <span>{(kpis?.total_count ?? total).toLocaleString()} 全部条目</span>
              </div>
            </div>

            {loading ? <p className="intel-stage-loading">加载中...</p> : null}
            {error ? <div className="dash-card alert">{error}</div> : null}
            {!loading && !error && stageGroups.length === 0 ? (
              <div className="intel-empty-stage">
                <span className="material-symbols-outlined">gavel</span>
                <strong>暂无招投标内容</strong>
                <p>旁路采集完成后会直接在这里呈现。</p>
              </div>
            ) : null}

            <div className="intel-source-grid intel-source-grid--stage">
              {stageGroups.map((group) => (
                <IntelSourcePanel key={group.source} group={group} theme="tender" onOpenDetail={openDetail} />
              ))}
            </div>
          </div>
        </section>

        {feedGroups.length ? (
          <section className="intel-editorial-section intel-editorial-section--feed">
            <div className="intel-editorial-head intel-editorial-head--light">
              <div>
                <span className="intel-editorial-label">MORE</span>
                <h3>更多来源</h3>
              </div>
              <p>按平台归类阅读，优先保留预算、截止时间与发布主体。</p>
            </div>

            <div className="intel-source-grid intel-source-grid--feed">
              {feedGroups.map((group) => (
                <IntelSourcePanel key={group.source} group={group} theme="tender" onOpenDetail={openDetail} />
              ))}
            </div>

            <footer className="intel-editorial-pagination">
              <button type="button" className="intel-page-btn" disabled={page <= 1} onClick={() => setPage((current) => Math.max(1, current - 1))}>上一页</button>
              <button type="button" className="intel-page-btn" disabled={page >= totalPages} onClick={() => setPage((current) => Math.min(totalPages, current + 1))}>下一页</button>
            </footer>
          </section>
        ) : null}

        <IntelDetailDrawer open={drawerOpen} loading={detailLoading} error={detailError} detail={selectedDetail} onClose={() => setDrawerOpen(false)} theme="tender" />
      </section>
    </DashboardLayout>
  )
}
