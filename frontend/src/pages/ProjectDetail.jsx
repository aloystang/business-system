import React, { useEffect, useMemo, useState } from 'react'
import { useParams } from 'react-router-dom'
import { apiJson } from '../lib/api'

const tabs = [
  { key: 'overview', label: 'Overview' },
  { key: 'data', label: 'Data' },
  { key: 'screening', label: 'Screening' },
  { key: 'calc', label: 'Calc' },
]

const groupConfigs = [
  {
    id: 'basic',
    title: '项目基本信息',
    fields: [
      { key: 'project_name', label: '项目名称', required: true, type: 'text' },
      { key: 'city', label: '城市', required: true, type: 'text' },
      { key: 'district', label: '行政区', required: true, type: 'text' },
      { key: 'location_desc', label: '位置描述', required: false, type: 'text' },
    ],
  },
  {
    id: 'scale',
    title: '商业规模',
    fields: [
      { key: 'total_area', label: '总面积', required: true, type: 'number' },
      { key: 'rentable_area', label: '可出租面积', required: false, type: 'number' },
      { key: 'core_area', label: '核心区面积', required: false, type: 'number' },
    ],
  },
  {
    id: 'asset',
    title: '资产属性',
    fields: [
      {
        key: 'asset_distribution',
        label: '资产分布',
        required: true,
        type: 'select',
        options: ['集中', '分散', '混合'],
      },
      {
        key: 'ownership_structure',
        label: '权属结构',
        required: true,
        type: 'select',
        options: ['甲方', '第三方', '混合'],
      },
    ],
  },
  {
    id: 'operation',
    title: '经营现状',
    fields: [
      { key: 'vacancy_rate', label: '空置率(%)', required: false, type: 'number' },
      { key: 'rent_min', label: '租金下限', required: false, type: 'number' },
      { key: 'rent_max', label: '租金上限', required: false, type: 'number' },
      { key: 'main_business_type', label: '主要业态类型', required: false, type: 'text' },
    ],
  },
  {
    id: 'competition',
    title: '竞争关系',
    fields: [
      { key: 'competitor_list', label: '竞品列表', required: false, type: 'text' },
      {
        key: 'competition_level',
        label: '竞争强度',
        required: true,
        type: 'select',
        options: ['强', '中', '弱'],
      },
    ],
  },
  {
    id: 'remark',
    title: '备注',
    fields: [{ key: 'remark', label: '备注', required: false, type: 'textarea' }],
  },
]

export default function ProjectDetail() {
  const { projectId } = useParams()
  const [activeTab, setActiveTab] = useState('overview')
  const [project, setProject] = useState(null)
  const [screening, setScreening] = useState(null)
  const [screeningConfig, setScreeningConfig] = useState(null)
  const [screeningManualScores, setScreeningManualScores] = useState({})
  const [screeningPersistedManualScores, setScreeningPersistedManualScores] = useState({})
  const [screeningRiskNote, setScreeningRiskNote] = useState('')
  const [assetCalc, setAssetCalc] = useState(null)
  const [internalCalc, setInternalCalc] = useState(null)
  const [merchantCalc, setMerchantCalc] = useState(null)
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState(false)
  const [error, setError] = useState('')
  const [toast, setToast] = useState('')
  const [editingGroup, setEditingGroup] = useState(null)
  const [groupDraft, setGroupDraft] = useState({})
  const [groupErrors, setGroupErrors] = useState({})
  const [groupSaving, setGroupSaving] = useState(false)
  const [openGroups, setOpenGroups] = useState(() =>
    groupConfigs.reduce((acc, group) => ({ ...acc, [group.id]: true }), {})
  )

  const formatDate = (value) => {
    if (!value) return ''
    const date = new Date(value)
    if (Number.isNaN(date.getTime())) return value
    return date.toLocaleString('zh-CN')
  }

  const formatNumber = (value) => {
    if (value === null || value === undefined || value === '') return '—'
    const num = Number(value)
    if (Number.isNaN(num)) return value
    return num.toFixed(2)
  }

  const showToast = (message) => {
    setToast(message)
    setTimeout(() => setToast(''), 2000)
  }

  const syncScreeningState = (result) => {
    setScreening(result)
    setScreeningRiskNote(result?.risk_note || '')
    const manualMap = {}
    ;(result?.indicators || []).forEach((item) => {
      if (item.manual_override) {
        manualMap[item.key] = item.level
      }
    })
    setScreeningPersistedManualScores(manualMap)
    setScreeningManualScores(manualMap)
  }

  const loadProject = async () => {
    const data = await apiJson(`/api/projects/${projectId}`)
    setProject(data)
    return data
  }

  const safeGet = async (path) => {
    try {
      return await apiJson(path)
    } catch (err) {
      return null
    }
  }

  const loadOverview = async () => {
    setLoading(true)
    setError('')
    try {
      await loadProject()
      const [screeningData, screeningConfigData, assetData, internalData, merchantData] =
        await Promise.all([
          safeGet(`/api/projects/${projectId}/screening/latest`),
          safeGet('/api/screening/config'),
          safeGet(`/api/projects/${projectId}/calc/asset_owner/latest`),
          safeGet(`/api/projects/${projectId}/calc/internal/latest`),
          safeGet(`/api/projects/${projectId}/calc/merchant/latest`),
        ])
      syncScreeningState(screeningData)
      setScreeningConfig(screeningConfigData)
      setAssetCalc(assetData)
      setInternalCalc(internalData)
      setMerchantCalc(merchantData)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (projectId) {
      loadOverview()
    }
  }, [projectId])

  const runScreeningCalc = async () => {
    const result = await apiJson(`/api/projects/${projectId}/screening/calc`, {
      method: 'POST',
      body: JSON.stringify({
        risk_note: screeningRiskNote || null,
        manual_scores: screeningManualScores,
      }),
    })
    syncScreeningState(result)
    showToast('已生成新的筛选结果')
  }

  const handlePrimaryAction = async () => {
    if (!project) return
    setError('')
    if (project.is_confirmed !== 1) {
      setActionLoading(true)
      try {
        const updated = await apiJson(`/api/projects/${projectId}/confirm`, { method: 'POST' })
        setProject(updated)
        showToast('已确认数据')
      } catch (err) {
        setError(err.message)
      } finally {
        setActionLoading(false)
      }
      return
    }

    setActionLoading(true)
    try {
      await runScreeningCalc()
    } catch (err) {
      if (Array.isArray(err.missing_fields) && err.missing_fields.length > 0) {
        setError(`${err.message}：${err.missing_fields.join('、')}`)
      } else {
        setError(err.message)
      }
    } finally {
      setActionLoading(false)
    }
  }

  const handleConfirm = async () => {
    if (!project || project.is_confirmed === 1) return
    setActionLoading(true)
    setError('')
    try {
      const updated = await apiJson(`/api/projects/${projectId}/confirm`, { method: 'POST' })
      setProject(updated)
      showToast('已确认数据')
    } catch (err) {
      setError(err.message)
    } finally {
      setActionLoading(false)
    }
  }

  const startEditGroup = (group) => {
    if (!project) return
    const draft = {}
    group.fields.forEach((field) => {
      const value = project[field.key]
      draft[field.key] = value === null || value === undefined ? '' : String(value)
    })
    setEditingGroup(group.id)
    setGroupDraft(draft)
    setGroupErrors({})
  }

  const cancelEditGroup = () => {
    setEditingGroup(null)
    setGroupDraft({})
    setGroupErrors({})
  }

  const validateGroup = (group, draft) => {
    const errors = {}
    group.fields.forEach((field) => {
      const value = draft[field.key]
      if (field.required && (!value || value.toString().trim() === '')) {
        errors[field.key] = '必填'
        return
      }
      if (field.type === 'number' && value !== '' && value !== null && value !== undefined) {
        if (Number.isNaN(Number(value))) {
          errors[field.key] = '请输入数字'
          return
        }
        if (field.key === 'vacancy_rate') {
          const num = Number(value)
          if (num < 0 || num > 100) {
            errors[field.key] = '范围 0-100'
          }
        }
      }
      if (field.type === 'select' && value && field.options && !field.options.includes(value)) {
        errors[field.key] = '请选择'
      }
    })
    return errors
  }

  const updateDraft = (group, key, value) => {
    setGroupDraft((prev) => {
      const next = { ...prev, [key]: value }
      setGroupErrors(validateGroup(group, next))
      return next
    })
  }

  const saveGroup = async (group) => {
    const errors = validateGroup(group, groupDraft)
    setGroupErrors(errors)
    if (Object.keys(errors).length > 0) {
      return
    }
    const payload = {}
    group.fields.forEach((field) => {
      const value = groupDraft[field.key]
      if (field.type === 'number') {
        payload[field.key] = value === '' || value === null || value === undefined ? null : Number(value)
      } else {
        payload[field.key] = value === '' ? null : value
      }
    })
    setGroupSaving(true)
    setError('')
    try {
      const updated = await apiJson(`/api/projects/${projectId}`, {
        method: 'PUT',
        body: JSON.stringify(payload),
      })
      setProject(updated)
      showToast('保存成功')
      cancelEditGroup()
    } catch (err) {
      setError(err.message)
      showToast(err.message)
    } finally {
      setGroupSaving(false)
    }
  }

  const toggleGroup = (groupId) => {
    setOpenGroups((prev) => ({ ...prev, [groupId]: !prev[groupId] }))
  }

  const renderValue = (field) => {
    if (!project) return '—'
    const value = project[field.key]
    if (field.type === 'number') {
      return formatNumber(value)
    }
    if (value === null || value === undefined || value === '') return '—'
    return value
  }

  const projectSubtitle = useMemo(() => {
    if (!project) return ''
    const updated = project.updated_at || project.created_at
    return `${project.city || ''}·${project.district || ''} · ${formatDate(updated)}`
  }, [project])

  const statusTags = useMemo(() => {
    if (!project) return []
    const tags = [
      project.is_confirmed === 1 ? { label: '已确认', type: 'confirmed' } : { label: '未确认', type: 'unconfirmed' },
    ]
    if (screening) {
      tags.push({ label: '已计算', type: 'primary' })
    }
    return tags
  }, [project, screening])

  const records = useMemo(() => {
    if (!project) return []
    return [
      {
        label: '数据确认',
        value: project.is_confirmed === 1 ? '已确认' : '未确认',
        time: project.is_confirmed === 1 ? formatDate(project.updated_at || project.created_at) : '',
      },
      {
        label: '筛选',
        value: screening ? `v${screening.calc_version || '-'}` : '未计算',
        time: screening ? formatDate(screening.created_at) : '',
      },
      {
        label: '资产方测算',
        value: assetCalc ? `v${assetCalc.calc_version || '-'}` : '未测算',
        time: assetCalc ? formatDate(assetCalc.created_at) : '',
      },
      {
        label: '内部测算',
        value: internalCalc ? `v${internalCalc.calc_version || '-'}` : '未测算',
        time: internalCalc ? formatDate(internalCalc.created_at) : '',
      },
      {
        label: '商户测算',
        value: merchantCalc ? `v${merchantCalc.calc_version || '-'}` : '未测算',
        time: merchantCalc ? formatDate(merchantCalc.created_at) : '',
      },
    ]
  }, [project, screening, assetCalc, internalCalc, merchantCalc])

  const screeningLevels = useMemo(() => screeningConfig?.levels || [5, 4, 3, 2, 1], [screeningConfig])
  const screeningCategories = useMemo(() => screeningConfig?.categories || [], [screeningConfig])
  const screeningIndicatorMap = useMemo(() => {
    const map = new Map()
    ;(screening?.indicators || []).forEach((item) => {
      map.set(item.key, item)
    })
    return map
  }, [screening])
  const manualOverrideCount = useMemo(
    () => Object.keys(screeningManualScores).length,
    [screeningManualScores]
  )
  const hasUnsavedManualChanges = useMemo(() => {
    const draftKeys = Object.keys(screeningManualScores)
    const persistedKeys = Object.keys(screeningPersistedManualScores)
    if (draftKeys.length !== persistedKeys.length) return true
    return draftKeys.some((key) => screeningManualScores[key] !== screeningPersistedManualScores[key])
  }, [screeningManualScores, screeningPersistedManualScores])

  const toggleManualScore = (indicatorKey, level) => {
    setScreeningManualScores((prev) => {
      const next = { ...prev }
      if (next[indicatorKey] === level) {
        delete next[indicatorKey]
      } else {
        next[indicatorKey] = level
      }
      return next
    })
  }

  const clearManualScores = () => {
    setScreeningManualScores({})
  }

  return (
    <div>
      {toast && <div className="toast">{toast}</div>}
      <div className="page-header">
        <div>
          {loading ? (
            <>
              <div className="skeleton line" style={{ height: 28, width: 220 }} />
              <div className="skeleton short" style={{ height: 12, marginTop: 10 }} />
            </>
          ) : (
            <>
              <h1 className="page-title">{project?.project_name || '项目'}</h1>
              <div className="page-subtitle">{projectSubtitle}</div>
            </>
          )}
        </div>
        <div className="status-tags">
          {loading
            ? [1, 2].map((item) => (
                <div key={item} className="skeleton short" style={{ height: 24, width: 80 }} />
              ))
            : statusTags.map((tag) => (
                <span key={tag.label} className={`tag ${tag.type}`}>
                  {tag.label}
                </span>
              ))}
        </div>
        <div className="page-actions column">
          <button className="button" onClick={handlePrimaryAction} disabled={loading || actionLoading}>
            {project?.is_confirmed === 1 ? '重新计算筛选' : '确认数据并进入计算'}
          </button>
          <small style={{ color: 'var(--color-text-secondary)' }}>
            {project?.is_confirmed === 1 ? '点击可生成新版本结果' : '确认后才能计算'}
          </small>
        </div>
      </div>

      {error && <div className="notice">{error}</div>}

      <div className="tabs">
        {tabs.map((tab) => (
          <div
            key={tab.key}
            className={`tab ${activeTab === tab.key ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.key)}
          >
            {tab.label}
          </div>
        ))}
      </div>

      {activeTab === 'overview' && (
        <div className="grid">
          <div className="card">
            <h3>核心结论</h3>
            {loading ? (
              <div className="kpi-grid" style={{ marginTop: 16 }}>
                {[1, 2, 3].map((item) => (
                  <div key={item}>
                    <div className="skeleton short" />
                    <div className="skeleton line" style={{ marginTop: 10 }} />
                    <div className="skeleton short" />
                  </div>
                ))}
              </div>
            ) : (
              <div className="kpi-grid" style={{ marginTop: 16 }}>
                <div>
                  <div className="tag muted">筛选结论</div>
                  <div className="kpi-value" style={{ color: 'var(--color-primary)' }}>
                    {screening?.total_score ?? '—'}
                  </div>
                  <div style={{ marginTop: 4 }}>
                    <span className={`tag ${screening ? 'primary' : 'muted'}`}>
                      {screening?.conclusion || '未计算'}
                    </span>
                  </div>
                  {screening && (
                    <small>
                      v{screening.calc_version} · {formatDate(screening.created_at)}
                    </small>
                  )}
                  <div style={{ marginTop: 12 }}>
                    <button className="button secondary" onClick={() => setActiveTab('screening')}>
                      查看筛选详情
                    </button>
                  </div>
                </div>
                <div>
                  <div className="tag muted">资产方测算</div>
                  {assetCalc ? (
                    <>
                      <div className="kpi-value" style={{ color: 'var(--color-primary)' }}>
                        ROI {formatNumber(assetCalc.roi)}
                      </div>
                      <div style={{ marginTop: 4 }}>回收期 {formatNumber(assetCalc.payback_year)}</div>
                      <small>
                        v{assetCalc.calc_version} · {formatDate(assetCalc.created_at)}
                      </small>
                    </>
                  ) : (
                    <>
                      <div className="kpi-value">未测算</div>
                      <div style={{ marginTop: 12 }}>
                        <button className="button secondary" onClick={() => setActiveTab('calc')}>
                          去测算
                        </button>
                      </div>
                    </>
                  )}
                </div>
                <div>
                  <div className="tag muted">内部测算</div>
                  {internalCalc ? (
                    <>
                      <div className="kpi-value" style={{ color: 'var(--color-primary)' }}>
                        毛利率 {formatNumber(internalCalc.profit_margin)}
                      </div>
                      <div style={{ marginTop: 4 }}>
                        {internalCalc.total_profit !== null && internalCalc.total_profit !== undefined
                          ? `毛利额 ${formatNumber(internalCalc.total_profit)}`
                          : ''}
                      </div>
                      <small>
                        v{internalCalc.calc_version} · {formatDate(internalCalc.created_at)}
                      </small>
                    </>
                  ) : (
                    <>
                      <div className="kpi-value">未测算</div>
                      <div style={{ marginTop: 12 }}>
                        <button className="button secondary" onClick={() => setActiveTab('calc')}>
                          去测算
                        </button>
                      </div>
                    </>
                  )}
                </div>
              </div>
            )}
          </div>
          <div className="card">
            <h3>计算记录</h3>
            {loading ? (
              <>
                <div className="placeholder-line" />
                <div className="placeholder-line" />
                <div className="placeholder-line" />
              </>
            ) : records.length === 0 ? (
              <div className="empty-state">暂无记录</div>
            ) : (
              <div style={{ display: 'grid', gap: 12 }}>
                {records.map((record) => (
                  <div
                    key={record.label}
                    style={{ display: 'flex', justifyContent: 'space-between', gap: 16 }}
                  >
                    <strong>{record.label}</strong>
                    <div style={{ textAlign: 'right' }}>
                      <div>{record.value}</div>
                      {record.time && <small>{record.time}</small>}
                    </div>
                  </div>
                ))}
              </div>
            )}
            <div style={{ marginTop: 16, display: 'flex', gap: 12, flexWrap: 'wrap' }}>
              <button className="button secondary" onClick={() => setActiveTab('data')}>
                编辑数据
              </button>
              <button className="button secondary" onClick={() => setActiveTab('screening')}>
                查看筛选
              </button>
              <button className="button secondary" onClick={() => setActiveTab('calc')}>
                进入测算
              </button>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'data' && (
        <div className="grid">
          <div className="info-banner">
            {project?.is_confirmed === 1
              ? '已确认。如需修改数据，请编辑后重新确认。'
              : '未确认。确认后才能进行筛选与测算。'}
          </div>

          {loading ? (
            <div className="card">
              <div className="placeholder-line" />
              <div className="placeholder-line" />
              <div className="placeholder-line" />
            </div>
          ) : (
            <div className="accordion">
              {groupConfigs.map((group) => {
                const isEditing = editingGroup === group.id
                return (
                  <div className="accordion-group" key={group.id}>
                    <div className="accordion-header">
                      <button
                        className="accordion-toggle"
                        type="button"
                        onClick={() => toggleGroup(group.id)}
                      >
                        <span>{openGroups[group.id] ? '▾' : '▸'}</span>
                        {group.title}
                      </button>
                      <div className="accordion-actions">
                        {isEditing ? (
                          <>
                            <button
                              className="button"
                              onClick={() => saveGroup(group)}
                              disabled={groupSaving || Object.keys(groupErrors).length > 0}
                            >
                              保存
                            </button>
                            <button className="button secondary" onClick={cancelEditGroup}>
                              取消
                            </button>
                          </>
                        ) : (
                          <button className="button secondary" onClick={() => startEditGroup(group)}>
                            编辑
                          </button>
                        )}
                      </div>
                    </div>
                    {openGroups[group.id] && (
                      <div className="accordion-body">
                        {isEditing ? (
                          <div className="grid two">
                            {group.fields.map((field) => (
                              <div key={field.key}>
                                <label>{field.label}{field.required ? ' *' : ''}</label>
                                {field.type === 'textarea' ? (
                                  <textarea
                                    className="textarea"
                                    value={groupDraft[field.key] || ''}
                                    onChange={(e) => updateDraft(group, field.key, e.target.value)}
                                  />
                                ) : field.type === 'select' ? (
                                  <select
                                    className="select"
                                    value={groupDraft[field.key] || ''}
                                    onChange={(e) => updateDraft(group, field.key, e.target.value)}
                                  >
                                    <option value="">请选择</option>
                                    {field.options?.map((option) => (
                                      <option key={option} value={option}>
                                        {option}
                                      </option>
                                    ))}
                                  </select>
                                ) : (
                                  <input
                                    className="input"
                                    type={field.type === 'number' ? 'number' : 'text'}
                                    step={field.type === 'number' ? '0.01' : undefined}
                                    value={groupDraft[field.key] || ''}
                                    onChange={(e) => updateDraft(group, field.key, e.target.value)}
                                  />
                                )}
                                {groupErrors[field.key] && (
                                  <div className="field-error">{groupErrors[field.key]}</div>
                                )}
                              </div>
                            ))}
                          </div>
                        ) : (
                          <div className="field-list">
                            {group.fields.map((field) => (
                              <div className="field-row" key={field.key}>
                                <div className="field-label">{field.label}</div>
                                <div className="field-value">{renderValue(field)}</div>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          )}

          <div className="sticky-footer">
            <div className="footer-note">
              {project?.is_confirmed === 1
                ? '已确认（如修改请重新确认）'
                : '确认后可计算'}
            </div>
            <div className="page-actions">
              <button
                className="button"
                onClick={handleConfirm}
                disabled={project?.is_confirmed === 1 || actionLoading}
              >
                {project?.is_confirmed === 1 ? '已确认' : '确认数据并进入计算'}
              </button>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'screening' && (
        <div className="grid">
          <div className="card">
            <h3>筛选结果</h3>
            {screening ? (
              <div className="kpi-grid" style={{ marginTop: 16 }}>
                <div>
                  <div className="tag muted">总分</div>
                  <div className="kpi-value" style={{ color: 'var(--color-primary)' }}>
                    {screening.total_score}
                  </div>
                </div>
                <div>
                  <div className="tag muted">结论</div>
                  <div style={{ marginTop: 8 }}>
                    <span className="tag primary">{screening.conclusion || '未计算'}</span>
                  </div>
                </div>
                <div>
                  <div className="tag muted">版本</div>
                  <div style={{ marginTop: 8 }}>
                    v{screening.calc_version || '-'} · {formatDate(screening.created_at)}
                  </div>
                </div>
              </div>
            ) : (
              <div className="empty-state" style={{ marginTop: 12 }}>暂无筛选结果</div>
            )}
            {screening?.risk_note && (
              <div style={{ marginTop: 14 }}>
                <strong style={{ fontSize: 13 }}>关键风险提示：</strong>
                <div style={{ marginTop: 6, color: 'var(--color-text-secondary)' }}>{screening.risk_note}</div>
              </div>
            )}
            {screening?.overall_summary && (
              <div style={{ marginTop: 14 }}>
                <strong style={{ fontSize: 13 }}>整体总结：</strong>
                <div style={{ marginTop: 6, color: 'var(--color-text-secondary)' }}>
                  {screening.overall_summary}
                </div>
              </div>
            )}
            <div style={{ marginTop: 16 }}>
              <label style={{ display: 'block', marginBottom: 8 }}>关键风险提示（编辑后参与存档）</label>
              <textarea
                className="textarea"
                value={screeningRiskNote}
                onChange={(e) => setScreeningRiskNote(e.target.value)}
                placeholder="可填写关键风险提示"
              />
            </div>
            <div
              style={{
                marginTop: 12,
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                gap: 12,
              }}
            >
              <small style={{ color: 'var(--color-text-secondary)' }}>
                当前人工覆盖：{manualOverrideCount} 项
                {hasUnsavedManualChanges ? '（有未存档变更）' : ''}
              </small>
              <button
                className="button secondary"
                onClick={clearManualScores}
                disabled={manualOverrideCount === 0 || actionLoading}
              >
                清除人工覆盖
              </button>
            </div>
          </div>

          <div className="card dash-screening-card">
            <table className="dash-screening-table">
              <colgroup>
                {Array.from({ length: screeningLevels.length + 3 }).map((_, idx) => (
                  <col
                    key={`detail-col-${idx}`}
                    style={{ width: `${100 / (screeningLevels.length + 3)}%` }}
                  />
                ))}
              </colgroup>
              <thead>
                <tr>
                  <th className="dash-screening-head-left">一级指标</th>
                  <th className="dash-screening-head-left">二级指标</th>
                  {screeningLevels.map((level) => (
                    <th key={`detail-level-${level}`} className="dash-screening-head-score">
                      {level}
                    </th>
                  ))}
                  <th className="dash-screening-head-left">权重 & 备注</th>
                </tr>
              </thead>
              <tbody>
                {screeningCategories.map((group) =>
                  (group.indicators || []).map((item, index) => {
                    const result = screeningIndicatorMap.get(item.key)
                    const persistedLevel = screeningPersistedManualScores[item.key]
                    const effectiveLevel =
                      screeningManualScores[item.key] !== undefined
                        ? screeningManualScores[item.key]
                        : result?.level ?? null
                    const isManual = screeningManualScores[item.key] !== undefined
                    const hasManualChanged = screeningManualScores[item.key] !== persistedLevel
                    let overrideLabel = '未评分'
                    if (hasManualChanged) {
                      overrideLabel = isManual ? '人工覆盖（未存档）' : '自动判档（未存档）'
                    } else if (isManual || persistedLevel !== undefined) {
                      overrideLabel = '人工覆盖'
                    } else if (result) {
                      overrideLabel = '自动判档'
                    }
                    return (
                      <tr key={`detail-row-${item.key}`}>
                        {index === 0 && (
                          <td className="dash-screening-group-cell" rowSpan={group.indicators.length}>
                            {group.name}
                          </td>
                        )}
                        <td className="dash-screening-indicator-cell">{item.name}</td>
                        {screeningLevels.map((level) => (
                          <td className="dash-screening-score" key={`detail-dot-${item.key}-${level}`}>
                            <button
                              type="button"
                              className={`dash-screening-dot-btn ${isManual ? 'manual' : 'auto'}`}
                              onClick={() => toggleManualScore(item.key, level)}
                            >
                              <span
                                className={`dash-screening-dot ${
                                  effectiveLevel === level ? 'active' : ''
                                }`}
                              />
                            </button>
                          </td>
                        ))}
                        <td className="dash-screening-note">
                          <strong>{item.weight}%</strong>
                          <span>{item.note}</span>
                          <small>{overrideLabel}</small>
                        </td>
                      </tr>
                    )
                  })
                )}
              </tbody>
            </table>
            {!screeningCategories.length && <div className="empty-state">筛选配置未加载</div>}
            <div style={{ marginTop: 16, display: 'flex', justifyContent: 'flex-end' }}>
              <button
                className="button secondary"
                onClick={handlePrimaryAction}
                disabled={loading || actionLoading}
              >
                {project?.is_confirmed === 1 ? '重新计算筛选' : '先确认数据'}
              </button>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'calc' && (
        <div className="grid">
          {['资产方测算', '内部测算', '商户测算'].map((title) => (
            <div className="card" key={title}>
              <h3>{title}</h3>
              <div className="grid two">
                <div>
                  <div className="placeholder-line" />
                  <div className="placeholder-line" />
                  <div className="placeholder-line" />
                </div>
                <div>
                  <div className="placeholder-line" />
                  <div className="placeholder-line" />
                  <div className="placeholder-line" />
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {projectId && (
        <div style={{ marginTop: 16, fontSize: 12, color: '#888' }}>
          当前项目ID：{projectId}
        </div>
      )}
    </div>
  )
}
