import React, { useEffect, useMemo, useState } from 'react'
import DashboardLayout from '../components/DashboardLayout'
import PlanningBreadcrumb from '../components/PlanningBreadcrumb'
import { apiJson } from '../lib/api'
import { CHONGQING_DISTRICTS } from '../lib/options'

const DEFAULT_CITY = import.meta.env.VITE_MAP_DEFAULT_CITY || '重庆市'

function formatTime(value) {
  if (!value) return '—'
  const ts = Date.parse(value)
  if (!Number.isFinite(ts)) return '—'
  return new Date(ts).toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function buildQuery(params) {
  const search = new URLSearchParams()
  Object.entries(params).forEach(([k, v]) => {
    if (v === undefined || v === null || v === '') return
    search.set(k, String(v))
  })
  const query = search.toString()
  return query ? `?${query}` : ''
}

const STATUS_TO_API = {
  normal: 'active',
  deleted: 'deleted',
  all: 'all',
}

export default function PlanningScreeningHistory() {
  const [queryType, setQueryType] = useState('merchant')
  const [filters, setFilters] = useState({
    city: DEFAULT_CITY,
    district: '',
    industry: '',
    keyword: '',
    status: 'all',
    page: 1,
    page_size: 20,
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [summary, setSummary] = useState(null)
  const [points, setPoints] = useState([])
  const [totalPoints, setTotalPoints] = useState(0)

  const refresh = async (nextFilters = filters, nextType = queryType) => {
    setLoading(true)
    setError('')
    try {
      const data = await apiJson(
        `/api/market/history${buildQuery({
          city: nextFilters.city,
          district: nextFilters.district,
          type: nextType,
          status: STATUS_TO_API[nextFilters.status] || 'all',
          industry: nextFilters.industry,
          keyword: nextFilters.keyword,
          page: nextFilters.page,
          page_size: nextFilters.page_size,
        })}`
      )
      setSummary(data.summary || null)
      setPoints(Array.isArray(data.points) ? data.points : [])
      setTotalPoints(Number(data.total_points || 0))
    } catch (err) {
      setError(err.message || '加载查询数据失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    refresh()
  }, [filters, queryType])

  const updateFilter = (key, value) => {
    setFilters((prev) => ({ ...prev, [key]: value, page: 1 }))
  }

  const resetFilters = () => {
    setFilters({
      city: DEFAULT_CITY,
      district: '',
      industry: '',
      keyword: '',
      status: 'all',
      page: 1,
      page_size: 20,
    })
  }

  const handlePointAction = async (pointId, action) => {
    try {
      if (action === 'delete') {
        const reason = window.prompt('删除原因（可选）', '') || ''
        await apiJson(`/api/market/items/${encodeURIComponent(pointId)}/delete`, {
          method: 'POST',
          body: JSON.stringify({ reason }),
        })
      } else {
        await apiJson(`/api/market/items/${encodeURIComponent(pointId)}/restore`, {
          method: 'POST',
          body: JSON.stringify({}),
        })
      }
      refresh()
    } catch (err) {
      setError(err.message || '操作失败')
    }
  }

  const handleBulkAction = async (action) => {
    const affectedPreview = points.length
    if (affectedPreview === 0) {
      window.alert('当前筛选条件下没有可处理点位。')
      return
    }

    const isDelete = action === 'delete'
    const actionLabel = isDelete ? '批量删除' : '批量恢复'
    if (!window.confirm(`当前条件命中 ${affectedPreview} 条，确认执行${actionLabel}？`)) return

    try {
      const reason = isDelete ? window.prompt('批量删除原因（可选）', '') || '' : ''
      const payload = {
        city: filters.city || '',
        district: filters.district || '',
        industry: filters.industry || '',
        type: queryType,
        keyword: filters.keyword || '',
        reason,
      }
      const endpoint = isDelete ? '/api/market/items/bulk-delete' : '/api/market/items/bulk-restore'
      const result = await apiJson(endpoint, {
        method: 'POST',
        body: JSON.stringify(payload),
      })
      window.alert(`${actionLabel}完成：共处理 ${result.affected_count || 0} 条点位`)
      refresh()
    } catch (err) {
      setError(err.message || `${actionLabel}失败`)
    }
  }

  const totalPages = Math.max(1, Math.ceil(totalPoints / filters.page_size))
  const modeTitle = queryType === 'merchant' ? '商家信息查询' : '竞争关系查询'

  const industryOptions = useMemo(() => {
    const set = new Set()
    points.forEach((item) => {
      if (item.industry) set.add(item.industry)
    })
    return Array.from(set)
  }, [points])

  return (
    <DashboardLayout title="策划咨询" overline="PLANNING">
      <section className="dash-form-page">
        <PlanningBreadcrumb sectionLabel="数据查询" />

        <div className="dash-card dash-card-secondary dash-page-intro dash-page-intro--compact dash-history-hero">
          <div className="dash-module-header">
            <div>
              <h2>数据查询</h2>
              <p className="dash-module-desc">按区域与业态查询商家/竞品数据，并执行删除与恢复。</p>
            </div>
            <div className="dash-collect-statuses">
              <span className="dash-status merchant">当前城市：{DEFAULT_CITY}</span>
              <span className={`dash-status ${points.length ? 'merchant' : 'deleted'}`}>
                {points.length ? `当前命中 ${points.length} 条` : '暂无命中数据'}
              </span>
            </div>
          </div>
          <div className="dash-history-hero-grid">
            <article className="dash-history-hero-metric">
              <span>当前模式</span>
              <strong>{queryType === 'merchant' ? '商家信息' : '竞争关系'}</strong>
              <small>支持按区域、业态与关键词快速检索</small>
            </article>
            <article className="dash-history-hero-metric">
              <span>查询状态</span>
              <strong>{filters.status === 'all' ? '全部' : filters.status === 'normal' ? '正常' : '已删除'}</strong>
              <small>保留删除与恢复双向治理能力</small>
            </article>
            <article className="dash-history-hero-metric">
              <span>分页</span>
              <strong>第 {filters.page} / {totalPages} 页</strong>
              <small>总计 {totalPoints} 条可检索记录</small>
            </article>
          </div>
        </div>

        {error && <div className="notice">{error}</div>}

        <div className="dash-card dash-card-muted dash-history-mode-card">
          <div className="dash-query-mode-switch">
            <button
              type="button"
              className={`dash-btn ${queryType === 'merchant' ? 'primary' : 'secondary'}`}
              onClick={() => setQueryType('merchant')}
            >
              商家信息查询
            </button>
            <button
              type="button"
              className={`dash-btn ${queryType === 'competitor' ? 'primary' : 'secondary'}`}
              onClick={() => setQueryType('competitor')}
            >
              竞争关系查询
            </button>
          </div>
          <p className="dash-helper">{modeTitle}</p>
        </div>

        <div className="dash-card dash-card-secondary dash-map-filter-card dash-history-filter-card">
          <div className="dash-map-filter-grid">
            <label className="dash-field">
              <span>区域</span>
              <select className="dash-select" value={filters.district} onChange={(event) => updateFilter('district', event.target.value)}>
                <option value="">全部区域</option>
                {CHONGQING_DISTRICTS.map((district) => (
                  <option key={district} value={district}>
                    {district}
                  </option>
                ))}
              </select>
            </label>
            <label className="dash-field">
              <span>业态</span>
              <select className="dash-select" value={filters.industry} onChange={(event) => updateFilter('industry', event.target.value)}>
                <option value="">全部业态</option>
                {industryOptions.map((item) => (
                  <option key={item} value={item}>
                    {item}
                  </option>
                ))}
              </select>
            </label>
            <label className="dash-field">
              <span>关键词</span>
              <input
                className="dash-input"
                value={filters.keyword}
                onChange={(event) => updateFilter('keyword', event.target.value)}
                placeholder="名称/地址/项目"
              />
            </label>
            <label className="dash-field">
              <span>状态</span>
              <select className="dash-select" value={filters.status} onChange={(event) => updateFilter('status', event.target.value)}>
                <option value="all">全部</option>
                <option value="normal">正常</option>
                <option value="deleted">已删除</option>
              </select>
            </label>
          </div>
          <div className="dash-history-actions">
            <button type="button" className="dash-btn secondary" onClick={resetFilters}>
              清空筛选
            </button>
          </div>
        </div>

        <div className="dash-card dash-card-muted dash-history-kpi-wrap">
          <div className="dash-history-kpis">
            <div className="dash-history-kpi-card">
              <span>命中点位</span>
              <strong>{totalPoints}</strong>
            </div>
            <div className="dash-history-kpi-card">
              <span>正常点位</span>
              <strong>{summary?.active_points ?? 0}</strong>
            </div>
            <div className="dash-history-kpi-card">
              <span>已删除点位</span>
              <strong>{summary?.deleted_points ?? 0}</strong>
            </div>
            <div className="dash-history-kpi-card">
              <span>当前查询类型</span>
              <strong>{queryType === 'merchant' ? '商家' : '竞品'}</strong>
            </div>
          </div>
        </div>

        <div className="dash-card dash-card-secondary dash-history-table-card">
          <div className="dash-card-header">
            <strong className="dash-section-title">
              <span className="material-symbols-outlined">cleaning_services</span>
              批量清理工具
            </strong>
            <span className="dash-section-note">按当前筛选条件执行批量操作</span>
          </div>
          <p className="dash-helper">当前条件命中 {points.length} 条；先预览再执行批量操作。</p>
          <div className="dash-history-actions">
            <button type="button" className="dash-btn secondary" onClick={() => handleBulkAction('restore')}>
              批量恢复
            </button>
            <button type="button" className="dash-btn secondary" onClick={() => handleBulkAction('delete')}>
              批量删除
            </button>
          </div>
        </div>

        <div className="card dash-history-table-card">
          <div className="dash-card-header">
            <strong className="dash-section-title">
              <span className="material-symbols-outlined">dataset</span>
              {modeTitle}
            </strong>
            <span className="dash-section-note">支持单条删除与恢复</span>
          </div>
          <div className="dash-table-scroll">
            <table className="table">
              <thead>
                <tr>
                  <th>名称</th>
                  <th>区域</th>
                  <th>业态</th>
                  <th>目标人群</th>
                  <th>地址</th>
                  <th>来源项目</th>
                  <th>时间</th>
                  <th>状态</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                {points.length === 0 && (
                  <tr>
                    <td colSpan={9} className="dash-helper">
                      暂无数据
                    </td>
                  </tr>
                )}
                {points.map((row) => (
                  <tr key={row.point_id}>
                    <td>{row.name}</td>
                    <td>{`${row.city} · ${row.district}`}</td>
                    <td>{row.industry || '—'}</td>
                    <td>{row.target_people || '—'}</td>
                    <td>{row.address}</td>
                    <td>{row.project_name || row.project_id || '—'}</td>
                    <td>{formatTime(row.created_at)}</td>
                    <td>
                      <span className={`dash-status ${row.deleted ? 'deleted' : 'merchant'}`}>{row.deleted ? '已删除' : '正常'}</span>
                    </td>
                    <td>
                      {row.deleted ? (
                        <button type="button" className="dash-btn secondary" onClick={() => handlePointAction(row.point_id, 'restore')}>
                          恢复
                        </button>
                      ) : (
                        <button type="button" className="dash-btn secondary" onClick={() => handlePointAction(row.point_id, 'delete')}>
                          删除
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="dash-history-pagination">
            <span>
              第 {filters.page} / {totalPages} 页，共 {totalPoints} 条
            </span>
            <div>
              <button
                type="button"
                className="dash-btn secondary"
                disabled={filters.page <= 1 || loading}
                onClick={() => setFilters((prev) => ({ ...prev, page: prev.page - 1 }))}
              >
                上一页
              </button>
              <button
                type="button"
                className="dash-btn secondary"
                disabled={filters.page >= totalPages || loading}
                onClick={() => setFilters((prev) => ({ ...prev, page: prev.page + 1 }))}
              >
                下一页
              </button>
            </div>
          </div>
        </div>
      </section>
    </DashboardLayout>
  )
}
