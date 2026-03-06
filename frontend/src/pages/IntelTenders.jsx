import React, { useEffect, useMemo, useState } from 'react'
import DashboardLayout from '../components/DashboardLayout'
import IntelSubnav from '../components/intel/IntelSubnav'
import IntelDetailDrawer from '../components/intel/IntelDetailDrawer'
import IntelSourcePanel from '../components/intel/IntelSourcePanel'
import { apiJson } from '../lib/api'
import { fetchAllIntelItems, groupBySource } from '../lib/intel'

export default function IntelTenders() {
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [detailLoading, setDetailLoading] = useState(false)
  const [detailError, setDetailError] = useState('')
  const [selectedDetail, setSelectedDetail] = useState(null)

  useEffect(() => {
    let cancelled = false

    const load = async () => {
      setLoading(true)
      setError('')
      try {
        const itemsResp = await fetchAllIntelItems(apiJson, { item_type: 'tender' })
        if (!cancelled) {
          setItems(itemsResp.items || [])
        }
      } catch (err) {
        if (!cancelled) {
          setError(err.message || '加载招投标采集失败')
        }
      } finally {
        if (!cancelled) {
          setLoading(false)
        }
      }
    }

    load()

    return () => {
      cancelled = true
    }
  }, [])

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

  return (
    <DashboardLayout title="招投标采集" overline="INTELLIGENCE">
      <section className="intel-stream-shell">
        <section className="intel-stream-header">
          <IntelSubnav />

          <div className="intel-summary-reserve intel-summary-reserve--tender">
            <span className="intel-summary-reserve-label">TODAY SUMMARY</span>
            <p className="intel-summary-reserve-line">今日招投标摘要（预留）：等待智能总结 API 接入。</p>
          </div>
        </section>

        <section className="intel-stream-panel intel-stream-panel--tender">
          {loading ? <p className="intel-stage-loading">加载中...</p> : null}
          {error ? <div className="dash-card alert">{error}</div> : null}
          {!loading && !error && groups.length === 0 ? (
            <div className="intel-empty-stage">
              <span className="material-symbols-outlined">gavel</span>
              <strong>暂无招投标内容</strong>
              <p>旁路采集完成后会直接在这里呈现。</p>
            </div>
          ) : null}

          <div className="intel-source-grid intel-source-grid--stream">
            {groups.map((group) => (
              <IntelSourcePanel key={group.source} group={group} theme="tender" onOpenDetail={openDetail} />
            ))}
          </div>
        </section>

        <IntelDetailDrawer
          open={drawerOpen}
          loading={detailLoading}
          error={detailError}
          detail={selectedDetail}
          onClose={() => setDrawerOpen(false)}
          theme="tender"
        />
      </section>
    </DashboardLayout>
  )
}
