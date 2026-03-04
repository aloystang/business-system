import React, { useEffect, useMemo, useState } from 'react'
import DashboardLayout from '../components/DashboardLayout'
import ModuleTabs from '../components/ModuleTabs'
import PlanningBreadcrumb from '../components/PlanningBreadcrumb'
import { planningModules } from '../data/modules'
import { apiJson } from '../lib/api'
import { getSelectedPlanningProjectId, setSelectedPlanningProjectId } from '../lib/planningProject'

function formatMoney(value) {
  if (value === null || value === undefined || value === '') return '—'
  const num = Number(value)
  if (Number.isNaN(num)) return '—'
  return `${num.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} 万元`
}

function formatNumber(value) {
  if (value === null || value === undefined || value === '') return '—'
  const num = Number(value)
  if (Number.isNaN(num)) return '—'
  return num.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function formatPercent(value) {
  if (value === null || value === undefined || value === '') return '—'
  const num = Number(value)
  if (Number.isNaN(num)) return '—'
  return `${(num * 100).toLocaleString('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}%`
}

function formatDate(value) {
  if (!value) return ''
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return ''
  return date.toLocaleString('zh-CN')
}

function normalizeRate(value) {
  const num = Number(value)
  if (Number.isNaN(num)) return null
  if (num > 1) return num / 100
  return num
}

function parseCurveInput(raw, years) {
  const items = String(raw || '')
    .split(/[,\n，]/)
    .map((item) => item.trim())
    .filter(Boolean)
  if (items.length !== years) {
    throw new Error(`曲线长度需为 ${years} 项`)
  }
  const result = items.map((item) => {
    const value = normalizeRate(item)
    if (value === null) throw new Error('曲线存在非法数字')
    return value
  })
  return result
}

function ResultCard({ title, basis, result }) {
  const summary = result?.summary || null
  const yearly = Array.isArray(result?.yearly) ? result.yearly : []

  return (
    <div className="dash-card dash-form-card dash-calc-result-card">
      <div className="dash-card-header">
        <strong className="dash-section-title">
          <span className="material-symbols-outlined">monitoring</span>
          {title}
        </strong>
        {result?.calc_version && (
          <span className="dash-section-note">
            {basis} · v{result.calc_version} · {formatDate(result.created_at)}
          </span>
        )}
      </div>

      {summary ? (
        <div className="dash-calc-kpi-grid">
          <div className="dash-calc-kpi-item">
            <span>总收入</span>
            <strong>{formatMoney(summary.total_revenue)}</strong>
          </div>
          <div className="dash-calc-kpi-item">
            <span>总成本</span>
            <strong>{formatMoney(summary.total_cost)}</strong>
          </div>
          <div className="dash-calc-kpi-item">
            <span>毛利</span>
            <strong>{formatMoney(summary.gross_profit)}</strong>
          </div>
          <div className="dash-calc-kpi-item">
            <span>毛利率</span>
            <strong>{formatPercent(summary.gross_margin)}</strong>
          </div>
          <div className="dash-calc-kpi-item">
            <span>税后毛利</span>
            <strong>{formatMoney(summary.tax_after_profit)}</strong>
          </div>
        </div>
      ) : (
        <div className="empty-state dash-calc-empty">暂无测算结果</div>
      )}

      <details className="dash-calc-details" open>
        <summary>10年明细</summary>
        {yearly.length ? (
          <div className="dash-table-scroll">
            <table className="dash-calc-table">
              <thead>
                <tr>
                  <th>年份</th>
                  <th>收入(万元)</th>
                  <th>成本(万元)</th>
                  <th>毛利(万元)</th>
                  <th>毛利率</th>
                  <th>税额(万元)</th>
                </tr>
              </thead>
              <tbody>
                {yearly.map((item) => (
                  <tr key={`${title}-${item.year_index}`}>
                    <td>{item.year_label || `第${item.year_index}年`}</td>
                    <td>{formatNumber(item.revenue)}</td>
                    <td>{formatNumber(item.cost)}</td>
                    <td>{formatNumber(item.gross_profit)}</td>
                    <td>{formatPercent(item.gross_margin)}</td>
                    <td>{item.tax === null || item.tax === undefined ? '—' : formatNumber(item.tax)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="empty-state">暂无逐年数据</div>
        )}
      </details>
    </div>
  )
}

export default function PlanningCalc() {
  const [projects, setProjects] = useState([])
  const [selectedProjectId, setSelectedProjectIdState] = useState(getSelectedPlanningProjectId())
  const [loadingProjects, setLoadingProjects] = useState(false)
  const [running, setRunning] = useState(false)
  const [loadingLatest, setLoadingLatest] = useState(false)
  const [loadingConfig, setLoadingConfig] = useState(false)
  const [error, setError] = useState('')
  const [toast, setToast] = useState('')

  const [assetResult, setAssetResult] = useState(null)
  const [internalResult, setInternalResult] = useState(null)
  const [config, setConfig] = useState(null)
  const [advancedOpen, setAdvancedOpen] = useState(false)
  const [overrideForm, setOverrideForm] = useState({
    rent_base: '',
    occupancy_curve: '',
    rent_growth_curve: '',
    leasing_commission_months: '',
    operation_commission_rate: '',
  })

  const selectedProject = useMemo(
    () => projects.find((item) => item.project_id === selectedProjectId) || null,
    [projects, selectedProjectId]
  )
  const years = Number(config?.planning_years || 10)
  const latestVersion = Math.max(assetResult?.calc_version || 0, internalResult?.calc_version || 0)
  const latestTime = assetResult?.created_at || internalResult?.created_at || ''

  const showToast = (message) => {
    setToast(message)
    setTimeout(() => setToast(''), 2200)
  }

  const setSelectedProject = (projectId) => {
    setSelectedProjectIdState(projectId)
    setSelectedPlanningProjectId(projectId)
    if (!projectId) {
      setAssetResult(null)
      setInternalResult(null)
    }
  }

  const loadProjects = async () => {
    setLoadingProjects(true)
    setError('')
    try {
      const data = await apiJson('/api/projects')
      const list = Array.isArray(data) ? data : []
      setProjects(list)
      if (selectedProjectId && !list.some((item) => item.project_id === selectedProjectId)) {
        setSelectedProject('')
      }
    } catch (err) {
      setProjects([])
      setError(err.message)
    } finally {
      setLoadingProjects(false)
    }
  }

  const loadConfig = async () => {
    setLoadingConfig(true)
    try {
      const data = await apiJson('/api/calc/config')
      setConfig(data)
      const defaults = data?.defaults || {}
      setOverrideForm({
        rent_base: defaults.rent_base_default === undefined ? '' : String(defaults.rent_base_default),
        occupancy_curve: Array.isArray(defaults.occupancy_curve)
          ? defaults.occupancy_curve.map((v) => Number(v) * 100).join(', ')
          : '',
        rent_growth_curve: Array.isArray(defaults.rent_growth_curve)
          ? defaults.rent_growth_curve.map((v) => Number(v) * 100).join(', ')
          : '',
        leasing_commission_months:
          defaults.leasing_commission_months === undefined
            ? ''
            : String(defaults.leasing_commission_months),
        operation_commission_rate:
          defaults.operation_commission_rate === undefined
            ? ''
            : String(Number(defaults.operation_commission_rate) * 100),
      })
    } catch (err) {
      setError(err.message)
      setConfig(null)
    } finally {
      setLoadingConfig(false)
    }
  }

  const loadLatest = async (projectId) => {
    if (!projectId) return
    setLoadingLatest(true)
    setError('')
    try {
      const safeGet = async (path) => {
        try {
          return await apiJson(path)
        } catch (err) {
          if (String(err.message || '').toLowerCase().includes('not found')) return null
          throw err
        }
      }
      const [asset, internal] = await Promise.all([
        safeGet(`/api/projects/${projectId}/calc/asset_owner/latest`),
        safeGet(`/api/projects/${projectId}/calc/internal/latest`),
      ])
      setAssetResult(asset)
      setInternalResult(internal)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoadingLatest(false)
    }
  }

  useEffect(() => {
    loadProjects()
    loadConfig()
  }, [])

  useEffect(() => {
    if (!selectedProjectId) return
    loadLatest(selectedProjectId)
  }, [selectedProjectId])

  const buildOverrides = () => {
    if (!advancedOpen) return null
    const overrides = {}

    if (overrideForm.rent_base !== '') {
      const rentBase = Number(overrideForm.rent_base)
      if (Number.isNaN(rentBase) || rentBase < 0) throw new Error('租金基准需为非负数字')
      overrides.rent_base = rentBase
    }
    if (overrideForm.occupancy_curve.trim()) {
      overrides.occupancy_curve = parseCurveInput(overrideForm.occupancy_curve, years)
    }
    if (overrideForm.rent_growth_curve.trim()) {
      overrides.rent_growth_curve = parseCurveInput(overrideForm.rent_growth_curve, years)
    }
    if (overrideForm.leasing_commission_months !== '') {
      const value = Number(overrideForm.leasing_commission_months)
      if (Number.isNaN(value) || value < 0) throw new Error('招商佣金(月)需为非负数字')
      overrides.leasing_commission_months = value
    }
    if (overrideForm.operation_commission_rate !== '') {
      const value = normalizeRate(overrideForm.operation_commission_rate)
      if (value === null || value < 0) throw new Error('运营提成率格式不正确')
      overrides.operation_commission_rate = value
    }

    return Object.keys(overrides).length ? overrides : null
  }

  const runAutoCalc = async () => {
    if (!selectedProjectId) {
      setError('请先选择项目')
      return
    }
    if (selectedProject?.is_confirmed !== 1) {
      setError('请先在数据采集页确认数据，再进行自动测算')
      return
    }

    setRunning(true)
    setError('')
    try {
      const overrides = buildOverrides()
      const body = overrides ? { overrides } : {}
      const result = await apiJson(`/api/projects/${selectedProjectId}/calc/auto`, {
        method: 'POST',
        body: JSON.stringify(body),
      })
      setAssetResult({
        ...(assetResult || {}),
        ...result.external,
        calc_version: result.calc_version,
        created_at: new Date().toISOString(),
      })
      setInternalResult({
        ...(internalResult || {}),
        ...result.internal,
        calc_version: result.calc_version,
        created_at: new Date().toISOString(),
      })
      showToast(`双口径测算已存档（v${result.calc_version}）`)
    } catch (err) {
      setError(err.message)
    } finally {
      setRunning(false)
    }
  }

  return (
    <DashboardLayout title="策划咨询" overline="PLANNING">
      <section className="dash-form-page">
        {toast && <div className="toast">{toast}</div>}
        <PlanningBreadcrumb sectionLabel="新建项目" currentLabel="项目测算" />
        <ModuleTabs modules={planningModules} basePath="/planning/new" />

        {error && <div className="notice">{error}</div>}

        <div className="dash-card dash-card-secondary dash-page-intro dash-page-intro--compact dash-calc-hero">
          <div className="dash-module-header">
            <div>
              <h2>双口径自动测算</h2>
              <p className="dash-module-desc">确认采集数据后自动生成甲方口径与华润口径的 10 年测算结果。</p>
            </div>
            <div className="dash-collect-statuses">
              <span className={`dash-status ${selectedProjectId ? 'merchant' : 'deleted'}`}>
                {selectedProjectId ? '已选择项目' : '未选择项目'}
              </span>
              <span className={`dash-status ${selectedProject?.is_confirmed === 1 ? 'merchant' : 'deleted'}`}>
                {selectedProject?.is_confirmed === 1 ? '已确认数据' : '待确认数据'}
              </span>
            </div>
          </div>

          <div className="dash-collect-kpis dash-calc-kpis">
            <article className="dash-collect-kpi">
              <span>测算周期</span>
              <strong>{years} 年</strong>
              <small>默认按配置周期生成</small>
            </article>
            <article className="dash-collect-kpi">
              <span>当前项目</span>
              <strong>{selectedProject?.project_name || '待选择'}</strong>
              <small>{selectedProject ? `${selectedProject.city} · ${selectedProject.district}` : '从已确认项目中选择'}</small>
            </article>
            <article className="dash-collect-kpi">
              <span>最近版本</span>
              <strong>{latestVersion ? `v${latestVersion}` : '未测算'}</strong>
              <small>{latestTime ? formatDate(latestTime) : '存档后生成版本'}</small>
            </article>
            <article className="dash-collect-kpi">
              <span>参数策略</span>
              <strong>{advancedOpen ? '自定义参数' : '默认参数'}</strong>
              <small>支持 5 个高级参数覆盖</small>
            </article>
          </div>
        </div>

        <div className="dash-card dash-card-muted dash-calc-toolbar">
          <div className="dash-screening-actions-top dash-collect-toolbar-row">
            <label className="dash-screening-select">
              <span>选择项目</span>
              <select
                className="dash-select"
                value={selectedProjectId}
                onChange={(event) => setSelectedProject(event.target.value)}
                disabled={loadingProjects || loadingLatest || running}
              >
                <option value="">请选择项目</option>
                {projects.map((project) => (
                  <option key={project.project_id} value={project.project_id}>
                    {project.project_name}（{project.is_confirmed === 1 ? '已确认' : '未确认'}）
                  </option>
                ))}
              </select>
            </label>
            <div className="dash-collect-toolbar-actions">
              <button
                className="dash-btn secondary"
                type="button"
                onClick={() => setAdvancedOpen((prev) => !prev)}
                disabled={loadingConfig || running}
              >
                {advancedOpen ? '收起高级参数' : '高级参数'}
              </button>
              <button
                className="dash-btn primary"
                type="button"
                onClick={runAutoCalc}
                disabled={!selectedProjectId || running || loadingConfig}
              >
                {running ? '计算中...' : '重新计算并存档'}
              </button>
            </div>
          </div>
          <div className="dash-collect-toolbar-meta">
            <span>确认数据后可直接重算；不填写高级参数时系统使用默认配置。</span>
          </div>
        </div>

        {advancedOpen && (
          <div className="dash-card dash-form-card">
            <div className="dash-card-header">
              <strong className="dash-section-title">
                <span className="material-symbols-outlined">tune</span>
                高级参数（可选）
              </strong>
              <span className="dash-section-note">仅开放 5 个关键参数，可留空使用默认配置</span>
            </div>
            <div className="dash-fields">
              <label className="dash-field">
                <span>租金基准（元/㎡/月）</span>
                <input
                  className="dash-input"
                  value={overrideForm.rent_base}
                  onChange={(event) =>
                    setOverrideForm((prev) => ({ ...prev, rent_base: event.target.value }))
                  }
                />
              </label>
              <label className="dash-field span-2">
                <span>出租率曲线（10项，逗号分隔，支持输入百分数）</span>
                <input
                  className="dash-input"
                  value={overrideForm.occupancy_curve}
                  onChange={(event) =>
                    setOverrideForm((prev) => ({ ...prev, occupancy_curve: event.target.value }))
                  }
                />
              </label>
              <label className="dash-field span-2">
                <span>租金递增曲线（10项，逗号分隔，支持输入百分数）</span>
                <input
                  className="dash-input"
                  value={overrideForm.rent_growth_curve}
                  onChange={(event) =>
                    setOverrideForm((prev) => ({ ...prev, rent_growth_curve: event.target.value }))
                  }
                />
              </label>
              <label className="dash-field">
                <span>招商佣金（月）</span>
                <input
                  className="dash-input"
                  value={overrideForm.leasing_commission_months}
                  onChange={(event) =>
                    setOverrideForm((prev) => ({
                      ...prev,
                      leasing_commission_months: event.target.value,
                    }))
                  }
                />
              </label>
              <label className="dash-field">
                <span>运营提成率（%）</span>
                <input
                  className="dash-input"
                  value={overrideForm.operation_commission_rate}
                  onChange={(event) =>
                    setOverrideForm((prev) => ({
                      ...prev,
                      operation_commission_rate: event.target.value,
                    }))
                  }
                />
              </label>
            </div>
          </div>
        )}

        <ResultCard title="外部测算（甲方口径）" basis="owner_v1" result={assetResult} />
        <ResultCard title="内部测算（华润口径）" basis="huarun_v1" result={internalResult} />
      </section>
    </DashboardLayout>
  )
}
