import React, { useEffect, useMemo, useState } from 'react'
import DashboardLayout from '../components/DashboardLayout'
import ModuleTabs from '../components/ModuleTabs'
import PlanningBreadcrumb from '../components/PlanningBreadcrumb'
import { planningModules } from '../data/modules'
import { apiJson } from '../lib/api'
import { getSelectedPlanningProjectId, setSelectedPlanningProjectId } from '../lib/planningProject'

function formatDate(value) {
  if (!value) return ''
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return ''
  return date.toLocaleString('zh-CN')
}

export default function PlanningScreening() {
  const [config, setConfig] = useState(null)
  const [projects, setProjects] = useState([])
  const [selectedProjectId, setSelectedProjectIdState] = useState(getSelectedPlanningProjectId())
  const [latestResult, setLatestResult] = useState(null)
  const [riskNote, setRiskNote] = useState('')
  const [loadingConfig, setLoadingConfig] = useState(false)
  const [loadingProjects, setLoadingProjects] = useState(false)
  const [loadingResult, setLoadingResult] = useState(false)
  const [runningCalc, setRunningCalc] = useState(false)
  const [error, setError] = useState('')
  const [toast, setToast] = useState('')

  const selectedProject = useMemo(
    () => projects.find((item) => item.project_id === selectedProjectId) || null,
    [projects, selectedProjectId]
  )

  const levelHeaders = config?.levels || [5, 4, 3, 2, 1]
  const categories = config?.categories || []

  const indicatorResultMap = useMemo(() => {
    const map = new Map()
    ;(latestResult?.indicators || []).forEach((item) => {
      map.set(item.key, item)
    })
    return map
  }, [latestResult])

  const showToast = (message) => {
    setToast(message)
    setTimeout(() => setToast(''), 2200)
  }

  const loadConfig = async () => {
    setLoadingConfig(true)
    try {
      const result = await apiJson('/api/screening/config')
      setConfig(result)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoadingConfig(false)
    }
  }

  const loadProjects = async () => {
    setLoadingProjects(true)
    try {
      const data = await apiJson('/api/projects?confirmed=1')
      const list = Array.isArray(data) ? data : []
      setProjects(list)
      if (selectedProjectId && !list.some((item) => item.project_id === selectedProjectId)) {
        setSelectedProjectIdState('')
        setSelectedPlanningProjectId('')
        setLatestResult(null)
      }
    } catch (err) {
      setError(err.message)
      setProjects([])
    } finally {
      setLoadingProjects(false)
    }
  }

  const loadLatestResult = async (projectId) => {
    if (!projectId) {
      setLatestResult(null)
      return
    }
    setLoadingResult(true)
    try {
      const result = await apiJson(`/api/projects/${projectId}/screening/latest`)
      setLatestResult(result)
      setRiskNote(result.risk_note || '')
    } catch (err) {
      if (err.message.toLowerCase().includes('not found')) {
        setLatestResult(null)
      } else {
        setError(err.message)
      }
    } finally {
      setLoadingResult(false)
    }
  }

  useEffect(() => {
    loadConfig()
    loadProjects()
  }, [])

  useEffect(() => {
    if (!selectedProjectId) return
    loadLatestResult(selectedProjectId)
  }, [selectedProjectId])

  const setSelectedProject = (projectId) => {
    setSelectedProjectIdState(projectId)
    setSelectedPlanningProjectId(projectId)
    setError('')
    if (!projectId) {
      setLatestResult(null)
      setRiskNote('')
    }
  }

  const handleRunScreening = async () => {
    if (!selectedProjectId) {
      setError('请先选择项目')
      return
    }
    setRunningCalc(true)
    setError('')
    try {
      const result = await apiJson(`/api/projects/${selectedProjectId}/screening/calc`, {
        method: 'POST',
        body: JSON.stringify({
          risk_note: riskNote || null,
        }),
      })
      setLatestResult(result)
      showToast(`筛选结果已存档（v${result.calc_version}）`)
    } catch (err) {
      if (Array.isArray(err.missing_fields) && err.missing_fields.length > 0) {
        setError(`${err.message}：${err.missing_fields.join('、')}`)
      } else {
        setError(err.message)
      }
    } finally {
      setRunningCalc(false)
    }
  }

  const currentScore = latestResult?.total_score ?? null
  const currentConclusion = latestResult?.conclusion || '未计算'
  const currentSummary =
    latestResult?.overall_summary ||
    '整体总结将由模型生成，主要呈现项目综合评价依据、优势与风险提示，约 300 字以内。'
  const indicatorCount = categories.reduce((sum, group) => sum + (group.indicators || []).length, 0)

  return (
    <DashboardLayout title="策划咨询" overline="PLANNING">
      <section className="dash-form-page">
        {toast && <div className="toast">{toast}</div>}
        <PlanningBreadcrumb sectionLabel="新建项目" currentLabel="项目筛选" />
        <ModuleTabs modules={planningModules} basePath="/planning/new" />

        {error && <div className="notice">{error}</div>}

        <div className="dash-screening">
          <div className="dash-card dash-card-secondary dash-page-intro dash-page-intro--compact dash-screening-hero">
            <div className="dash-screening-header">
              <div>
                <h2>项目筛选模型</h2>
                <p className="dash-module-desc">选择项目并完成模型筛选。</p>
                <p className="dash-helper dash-screening-hero-note">
                  一级/二级指标来自统一配置，评分结果由采集字段自动映射生成。
                </p>
              </div>
              <div className="dash-collect-statuses">
                <span className={`dash-status ${selectedProjectId ? 'merchant' : 'deleted'}`}>
                  {selectedProjectId ? '已选择项目' : '未选择项目'}
                </span>
                <span
                  className={`dash-status ${
                    selectedProject?.is_confirmed === 1 ? 'merchant' : 'deleted'
                  }`}
                >
                  {selectedProject?.is_confirmed === 1 ? '已确认数据' : '待确认数据'}
                </span>
              </div>
            </div>
            <div className="dash-collect-kpis dash-screening-kpis">
              <article className="dash-collect-kpi">
                <span>配置版本</span>
                <strong>{config?.version || 'v1'}</strong>
                <small>统一口径维护</small>
              </article>
              <article className="dash-collect-kpi">
                <span>指标树</span>
                <strong>{indicatorCount || '—'} 项</strong>
                <small>{categories.length} 个一级分类</small>
              </article>
              <article className="dash-collect-kpi">
                <span>当前项目</span>
                <strong>{selectedProject?.project_name || '待选择'}</strong>
                <small>{selectedProject ? `${selectedProject.city} · ${selectedProject.district}` : '从已确认项目中选择'}</small>
              </article>
              <article className="dash-collect-kpi">
                <span>最新版本</span>
                <strong>{latestResult?.calc_version ? `v${latestResult.calc_version}` : '未计算'}</strong>
                <small>{latestResult?.created_at ? formatDate(latestResult.created_at) : '存档后生成'}</small>
              </article>
            </div>
          </div>

          <div className="dash-card dash-card-muted dash-screening-toolbar">
            <div className="dash-screening-actions-top dash-collect-toolbar-row">
              <label className="dash-screening-select">
                <span>选择项目</span>
                <select
                  className="dash-select"
                  value={selectedProjectId}
                  onChange={(event) => setSelectedProject(event.target.value)}
                  disabled={loadingProjects || loadingResult}
                >
                  <option value="">请选择项目</option>
                  {projects.map((project) => (
                    <option key={project.project_id} value={project.project_id}>
                      {project.project_name}
                    </option>
                  ))}
                </select>
              </label>
              <div className="dash-collect-toolbar-actions">
                <button
                  className="dash-btn primary"
                  type="button"
                  onClick={handleRunScreening}
                  disabled={!selectedProjectId || runningCalc || loadingResult || loadingConfig}
                >
                  {runningCalc ? '计算中...' : '存档'}
                </button>
              </div>
            </div>
            <div className="dash-collect-toolbar-meta">
              <span>评分档位由数据采集字段自动映射计算，不支持人工覆盖。</span>
            </div>
          </div>

          <div className="dash-screening-summary">
            <div className="dash-summary-item">
              <span>得分情况</span>
              <strong>{currentScore ?? '—'}</strong>
              <small>{selectedProject ? '按 100 分制线性归一' : '选择项目后可计算'}</small>
            </div>
            <div className="dash-summary-item">
              <span>结论</span>
              <strong>{currentConclusion}</strong>
              {latestResult?.calc_version && (
                <small>
                  v{latestResult.calc_version} · {formatDate(latestResult.created_at)}
                </small>
              )}
            </div>
            <div className="dash-summary-item long">
              <span>整体总结</span>
              <p>{currentSummary}</p>
            </div>
          </div>

          <div className="dash-card dash-screening-card">
            <div className="dash-card-header">
              <strong className="dash-section-title">
                <span className="material-symbols-outlined">rule</span>
                指标评分明细
              </strong>
              <span className="dash-section-note">5 / 4 / 3 / 2 / 1 五档评分，橙点为当前档位</span>
            </div>
            <div className="dash-table-scroll">
              <table className="dash-screening-table">
              <colgroup>
                <col style={{ width: '14%' }} />
                <col style={{ width: '16%' }} />
                {levelHeaders.map((score) => (
                  <col key={`col-score-${score}`} style={{ width: `${28 / levelHeaders.length}%` }} />
                ))}
                <col style={{ width: '42%' }} />
              </colgroup>
              <thead>
                <tr>
                  <th className="dash-screening-head-left">一级指标</th>
                  <th className="dash-screening-head-left">二级指标</th>
                  {levelHeaders.map((score) => (
                    <th key={score} className="dash-screening-head-score">
                      {score}
                    </th>
                  ))}
                  <th className="dash-screening-head-left">权重 & 备注</th>
                </tr>
              </thead>
              <tbody>
                {!loadingConfig &&
                  categories.map((group) =>
                    (group.indicators || []).map((row, index) => {
                      const rowResult = indicatorResultMap.get(row.key)
                      const effectiveLevel = rowResult?.level ?? null
                      const isManual = rowResult?.manual_override === true
                      return (
                        <tr key={row.key}>
                          {index === 0 && (
                            <td className="dash-screening-group-cell" rowSpan={group.indicators.length}>
                              {group.name}
                            </td>
                          )}
                          <td className="dash-screening-indicator-cell">{row.name}</td>
                          {levelHeaders.map((score) => (
                            <td className="dash-screening-score" key={`${row.key}-${score}`}>
                              <span
                                className={`dash-screening-dot-btn readonly ${isManual ? 'manual' : 'auto'}`}
                              >
                                <span
                                  className={`dash-screening-dot ${
                                    effectiveLevel === score ? 'active' : ''
                                  }`}
                                />
                              </span>
                            </td>
                          ))}
                          <td className="dash-screening-note">
                            <strong>{row.weight}%</strong>
                            <span>{row.note}</span>
                            <small>{isManual ? '人工覆盖（历史）' : rowResult ? '自动判档' : '待计算'}</small>
                          </td>
                        </tr>
                      )
                    })
                  )}
              </tbody>
              </table>
            </div>
            {!loadingConfig && categories.length === 0 && <p className="dash-helper">暂无筛选配置。</p>}
            {loadingConfig && <p className="dash-helper">正在加载筛选配置...</p>}
            {selectedProject && selectedProject.is_confirmed !== 1 && (
              <p className="dash-helper" style={{ color: '#b45309' }}>
                当前项目未确认，存档会被后端拒绝。
              </p>
            )}
          </div>

          <div className="dash-card dash-form-card" style={{ marginBottom: 16 }}>
            <div className="dash-card-header">
              <strong className="dash-section-title">
                <span className="material-symbols-outlined">warning</span>
                关键风险提示
              </strong>
            </div>
            <div className="dash-fields">
              <label className="dash-field span-4">
                <span>风险备注</span>
                <textarea
                  className="dash-textarea"
                  placeholder="可填写关键风险提示"
                  value={riskNote}
                  onChange={(event) => setRiskNote(event.target.value)}
                />
              </label>
            </div>
          </div>
        </div>
      </section>
    </DashboardLayout>
  )
}
