import React, { useEffect, useMemo, useState } from 'react'
import DashboardLayout from '../components/DashboardLayout'
import ModuleTabs from '../components/ModuleTabs'
import PlanningBreadcrumb from '../components/PlanningBreadcrumb'
import MapPointPickerModal from '../components/MapPointPickerModal'
import { planningModules } from '../data/modules'
import { apiJson } from '../lib/api'
import { getSelectedPlanningProjectId, setSelectedPlanningProjectId } from '../lib/planningProject'

const EMPTY_FORM = {
  project_name: '',
  city: '',
  district: '',
  total_area: '',
  rentable_area: '',
  core_area: '',
  asset_distribution: '集中',
  ownership_structure: '甲方',
  vacancy_rate: '',
  rent_min: '',
  rent_max: '',
  main_business_type: '',
  competition_level: '中',
  city_population_10k: '',
  population_5km_10k: '',
  population_3km_10k: '',
  city_circle_level: '',
  competition_market_level: '',
  housing_price_5km: '',
  disposable_income_10k: '',
  regional_function_level: '',
  commercial_planning_level: '',
  rail_access_level: '',
  arterial_access_level: '',
  bus_access_level: '',
  operation_retrofit_potential_level: '',
  asset_rights_complexity_level: '',
  remark: '',
}

const EMPTY_MERCHANT_ROW = () => ({
  id: Date.now() + Math.floor(Math.random() * 10000),
  name: '',
  category: '',
  area_m2: '',
  rent_unit_price: '',
  daily_flow: '',
  address: '',
  city: '',
  district: '',
  longitude: '',
  latitude: '',
  note: '',
})

const EMPTY_COMPETITION_ROW = () => ({
  id: Date.now() + Math.floor(Math.random() * 10000),
  name: '',
  scale_m2: '',
  avg_rent_unit_price: '',
  vacancy_rate: '',
  business_type: '',
  distance_km: '',
  target_people: '',
  address: '',
  city: '',
  district: '',
  longitude: '',
  latitude: '',
})

function toInputNumber(value) {
  if (value === null || value === undefined) return ''
  return String(value)
}

function toNumberOrNull(value) {
  if (value === '' || value === null || value === undefined) return null
  const num = Number(value)
  if (Number.isNaN(num)) return null
  return num
}

function mapProjectToForm(project) {
  return {
    project_name: project.project_name || '',
    city: project.city || '',
    district: project.district || '',
    total_area: toInputNumber(project.total_area),
    rentable_area: toInputNumber(project.rentable_area),
    core_area: toInputNumber(project.core_area),
    asset_distribution: project.asset_distribution || '集中',
    ownership_structure: project.ownership_structure || '甲方',
    vacancy_rate: toInputNumber(project.vacancy_rate),
    rent_min: toInputNumber(project.rent_min),
    rent_max: toInputNumber(project.rent_max),
    main_business_type: project.main_business_type || '',
    competition_level: project.competition_level || '中',
    city_population_10k: toInputNumber(project.city_population_10k),
    population_5km_10k: toInputNumber(project.population_5km_10k),
    population_3km_10k: toInputNumber(project.population_3km_10k),
    city_circle_level: project.city_circle_level || '',
    competition_market_level: project.competition_market_level || '',
    housing_price_5km: toInputNumber(project.housing_price_5km),
    disposable_income_10k: toInputNumber(project.disposable_income_10k),
    regional_function_level: project.regional_function_level || '',
    commercial_planning_level: project.commercial_planning_level || '',
    rail_access_level: project.rail_access_level || '',
    arterial_access_level: project.arterial_access_level || '',
    bus_access_level: project.bus_access_level || '',
    operation_retrofit_potential_level: project.operation_retrofit_potential_level || '',
    asset_rights_complexity_level: project.asset_rights_complexity_level || '',
    remark: project.remark || '',
  }
}

function mapMerchantRows(rows) {
  if (!Array.isArray(rows) || rows.length === 0) return [EMPTY_MERCHANT_ROW()]
  return rows.slice(0, 99).map((row, index) => ({
    id: Date.now() + index,
    name: row.name || '',
    category: row.category || '',
    area_m2: toInputNumber(row.area_m2),
    rent_unit_price: toInputNumber(row.rent_unit_price),
    daily_flow: toInputNumber(row.daily_flow),
    address: row.address || '',
    city: row.city || '',
    district: row.district || '',
    longitude: toInputNumber(row.longitude),
    latitude: toInputNumber(row.latitude),
    note: row.note || '',
  }))
}

function mapCompetitionRows(rows, fallbackCompetitorList = '') {
  if (Array.isArray(rows) && rows.length > 0) {
    return rows.slice(0, 99).map((row, index) => ({
      id: Date.now() + index,
      name: row.name || '',
      scale_m2: toInputNumber(row.scale_m2),
      avg_rent_unit_price: toInputNumber(row.avg_rent_unit_price),
      vacancy_rate: toInputNumber(row.vacancy_rate),
      business_type: row.business_type || '',
      distance_km: toInputNumber(row.distance_km),
      target_people: row.target_people || '',
      address: row.address || '',
      city: row.city || '',
      district: row.district || '',
      longitude: toInputNumber(row.longitude),
      latitude: toInputNumber(row.latitude),
    }))
  }

  if (!fallbackCompetitorList) return [EMPTY_COMPETITION_ROW()]
  const names = fallbackCompetitorList
    .split(/[,，;\n]/)
    .map((item) => item.trim())
    .filter(Boolean)
  if (names.length === 0) return [EMPTY_COMPETITION_ROW()]
  return names.slice(0, 99).map((name, index) => ({
    ...EMPTY_COMPETITION_ROW(),
    id: Date.now() + index,
    name,
  }))
}

export default function PlanningCollect() {
  const [projects, setProjects] = useState([])
  const [selectedProjectId, setSelectedProjectIdState] = useState(getSelectedPlanningProjectId())
  const [form, setForm] = useState(EMPTY_FORM)
  const [merchantRows, setMerchantRows] = useState([EMPTY_MERCHANT_ROW()])
  const [competitionRows, setCompetitionRows] = useState([EMPTY_COMPETITION_ROW()])
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [confirming, setConfirming] = useState(false)
  const [error, setError] = useState('')
  const [toast, setToast] = useState('')
  const [pickerState, setPickerState] = useState({
    open: false,
    rowType: '',
    rowId: null,
  })

  const selectedProject = useMemo(
    () => projects.find((item) => item.project_id === selectedProjectId) || null,
    [projects, selectedProjectId]
  )

  const competitorSummary = useMemo(
    () =>
      competitionRows
        .map((row) => row.name.trim())
        .filter(Boolean)
        .join('，'),
    [competitionRows]
  )

  const showToast = (message) => {
    setToast(message)
    setTimeout(() => setToast(''), 2200)
  }

  const loadProjects = async () => {
    setLoading(true)
    setError('')
    try {
      const data = await apiJson('/api/projects')
      const list = Array.isArray(data) ? data : []
      setProjects(list)
      if (selectedProjectId && !list.some((item) => item.project_id === selectedProjectId)) {
        setSelectedProjectIdState('')
        setSelectedPlanningProjectId('')
        setForm(EMPTY_FORM)
        setMerchantRows([EMPTY_MERCHANT_ROW()])
        setCompetitionRows([EMPTY_COMPETITION_ROW()])
      }
    } catch (err) {
      setError(err.message)
      setProjects([])
    } finally {
      setLoading(false)
    }
  }

  const loadProjectDetail = async (projectId) => {
    if (!projectId) {
      setForm(EMPTY_FORM)
      return
    }
    setLoading(true)
    setError('')
    try {
      const detail = await apiJson(`/api/projects/${projectId}`)
      setForm(mapProjectToForm(detail))
      setMerchantRows(mapMerchantRows(detail.merchant_rows))
      setCompetitionRows(mapCompetitionRows(detail.competition_rows, detail.competitor_list))
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadProjects()
  }, [])

  useEffect(() => {
    if (!selectedProjectId) return
    loadProjectDetail(selectedProjectId)
  }, [selectedProjectId])

  const setSelectedProject = (projectId) => {
    setSelectedProjectIdState(projectId)
    setSelectedPlanningProjectId(projectId)
    if (!projectId) {
      setForm(EMPTY_FORM)
      setMerchantRows([EMPTY_MERCHANT_ROW()])
      setCompetitionRows([EMPTY_COMPETITION_ROW()])
    }
  }

  const updateForm = (key, value) => {
    setForm((prev) => ({ ...prev, [key]: value }))
  }

  const addMerchantRow = () => {
    if (merchantRows.length >= 99) return
    setMerchantRows((rows) => [...rows, EMPTY_MERCHANT_ROW()])
  }

  const removeMerchantRow = (id) => {
    if (merchantRows.length <= 1) return
    setMerchantRows((rows) => rows.filter((row) => row.id !== id))
  }

  const updateMerchantRow = (id, key, value) => {
    setMerchantRows((rows) =>
      rows.map((row) => (row.id === id ? { ...row, [key]: value } : row))
    )
  }

  const addCompetitionRow = () => {
    if (competitionRows.length >= 99) return
    setCompetitionRows((rows) => [...rows, EMPTY_COMPETITION_ROW()])
  }

  const removeCompetitionRow = (id) => {
    if (competitionRows.length <= 1) return
    setCompetitionRows((rows) => rows.filter((row) => row.id !== id))
  }

  const updateCompetitionRow = (id, key, value) => {
    setCompetitionRows((rows) =>
      rows.map((row) => (row.id === id ? { ...row, [key]: value } : row))
    )
  }

  const openMapPicker = (rowType, rowId) => {
    setPickerState({ open: true, rowType, rowId })
  }

  const closeMapPicker = () => {
    setPickerState({ open: false, rowType: '', rowId: null })
  }

  const applyPickedPoint = ({ longitude, latitude, address, city, district }) => {
    const lng = Number(longitude)
    const lat = Number(latitude)
    if (!Number.isFinite(lng) || !Number.isFinite(lat)) return
    if (pickerState.rowType === 'merchant') {
      updateMerchantRow(pickerState.rowId, 'longitude', String(lng))
      updateMerchantRow(pickerState.rowId, 'latitude', String(lat))
      if (address) updateMerchantRow(pickerState.rowId, 'address', address)
      if (city) updateMerchantRow(pickerState.rowId, 'city', city)
      if (district) updateMerchantRow(pickerState.rowId, 'district', district)
    }
    if (pickerState.rowType === 'competition') {
      updateCompetitionRow(pickerState.rowId, 'longitude', String(lng))
      updateCompetitionRow(pickerState.rowId, 'latitude', String(lat))
      if (address) updateCompetitionRow(pickerState.rowId, 'address', address)
      if (city) updateCompetitionRow(pickerState.rowId, 'city', city)
      if (district) updateCompetitionRow(pickerState.rowId, 'district', district)
    }
    closeMapPicker()
  }

  const validateRequired = () => {
    if (!form.project_name.trim()) return '项目名称为必填项'
    if (!form.city.trim()) return '城市为必填项'
    if (!form.district.trim()) return '行政区为必填项'
    if (form.total_area === '' || Number.isNaN(Number(form.total_area))) return '总建筑面积为必填项'
    if (!form.asset_distribution) return '分布形态为必填项'
    if (!form.ownership_structure) return '权属结构为必填项'
    if (!form.competition_level) return '竞争强度为必填项'
    return ''
  }

  const validateSurveyRows = () => {
    const merchantRequired = ['name', 'category', 'area_m2', 'rent_unit_price', 'daily_flow', 'address', 'city', 'district']
    for (let i = 0; i < merchantRows.length; i += 1) {
      const row = merchantRows[i]
      const hasAnyValue = merchantRequired.concat(['note', 'longitude', 'latitude']).some((key) => String(row[key] ?? '').trim() !== '')
      if (!hasAnyValue) continue
      const missing = merchantRequired.filter((key) => String(row[key] ?? '').trim() === '')
      if (missing.length > 0) {
        return `商家调研第${i + 1}行缺少必填项：${missing.join('、')}`
      }
      const hasLng = String(row.longitude ?? '').trim() !== ''
      const hasLat = String(row.latitude ?? '').trim() !== ''
      if (hasLng !== hasLat) return `商家调研第${i + 1}行经纬度需同时填写`
    }

    const competitionRequired = ['name', 'scale_m2', 'avg_rent_unit_price', 'vacancy_rate', 'business_type', 'distance_km', 'target_people', 'address', 'city', 'district']
    for (let i = 0; i < competitionRows.length; i += 1) {
      const row = competitionRows[i]
      const hasAnyValue = competitionRequired.concat(['longitude', 'latitude']).some((key) => String(row[key] ?? '').trim() !== '')
      if (!hasAnyValue) continue
      const missing = competitionRequired.filter((key) => String(row[key] ?? '').trim() === '')
      if (missing.length > 0) {
        return `竞争关系第${i + 1}行缺少必填项：${missing.join('、')}`
      }
      const hasLng = String(row.longitude ?? '').trim() !== ''
      const hasLat = String(row.latitude ?? '').trim() !== ''
      if (hasLng !== hasLat) return `竞争关系第${i + 1}行经纬度需同时填写`
    }
    return ''
  }

  const buildSurveyRows = () => {
    const merchant_rows = merchantRows
      .filter((row) =>
        ['name', 'category', 'area_m2', 'rent_unit_price', 'daily_flow', 'address', 'city', 'district', 'note', 'longitude', 'latitude'].some(
          (key) => String(row[key] ?? '').trim() !== ''
        )
      )
      .map((row) => ({
        name: row.name.trim(),
        category: row.category.trim(),
        area_m2: Number(row.area_m2),
        rent_unit_price: Number(row.rent_unit_price),
        daily_flow: Number(row.daily_flow),
        address: row.address.trim(),
        city: row.city.trim(),
        district: row.district.trim(),
        note: row.note.trim() || null,
        longitude: toNumberOrNull(row.longitude),
        latitude: toNumberOrNull(row.latitude),
      }))

    const competition_rows = competitionRows
      .filter((row) =>
        ['name', 'scale_m2', 'avg_rent_unit_price', 'vacancy_rate', 'business_type', 'distance_km', 'target_people', 'address', 'city', 'district', 'longitude', 'latitude'].some(
          (key) => String(row[key] ?? '').trim() !== ''
        )
      )
      .map((row) => ({
        name: row.name.trim(),
        scale_m2: Number(row.scale_m2),
        avg_rent_unit_price: Number(row.avg_rent_unit_price),
        vacancy_rate: Number(row.vacancy_rate),
        business_type: row.business_type.trim(),
        distance_km: Number(row.distance_km),
        target_people: row.target_people.trim(),
        address: row.address.trim(),
        city: row.city.trim(),
        district: row.district.trim(),
        longitude: toNumberOrNull(row.longitude),
        latitude: toNumberOrNull(row.latitude),
      }))

    return { merchant_rows, competition_rows }
  }

  const buildPayload = () => ({
    project_name: form.project_name.trim(),
    city: form.city.trim(),
    district: form.district.trim(),
    total_area: toNumberOrNull(form.total_area),
    rentable_area: toNumberOrNull(form.rentable_area),
    core_area: toNumberOrNull(form.core_area),
    asset_distribution: form.asset_distribution,
    ownership_structure: form.ownership_structure,
    vacancy_rate: toNumberOrNull(form.vacancy_rate),
    rent_min: toNumberOrNull(form.rent_min),
    rent_max: toNumberOrNull(form.rent_max),
    main_business_type: form.main_business_type.trim() || null,
    competitor_list: competitorSummary || null,
    competition_level: form.competition_level,
    city_population_10k: toNumberOrNull(form.city_population_10k),
    population_5km_10k: toNumberOrNull(form.population_5km_10k),
    population_3km_10k: toNumberOrNull(form.population_3km_10k),
    city_circle_level: form.city_circle_level || null,
    competition_market_level: form.competition_market_level || null,
    housing_price_5km: toNumberOrNull(form.housing_price_5km),
    disposable_income_10k: toNumberOrNull(form.disposable_income_10k),
    regional_function_level: form.regional_function_level || null,
    commercial_planning_level: form.commercial_planning_level || null,
    rail_access_level: form.rail_access_level || null,
    arterial_access_level: form.arterial_access_level || null,
    bus_access_level: form.bus_access_level || null,
    operation_retrofit_potential_level: form.operation_retrofit_potential_level || null,
    asset_rights_complexity_level: form.asset_rights_complexity_level || null,
    remark: form.remark.trim() || null,
    ...buildSurveyRows(),
  })

  const saveProject = async (showSavedToast = true) => {
    const invalid = validateRequired()
    if (invalid) {
      throw new Error(invalid)
    }
    const surveyInvalid = validateSurveyRows()
    if (surveyInvalid) {
      throw new Error(surveyInvalid)
    }

    const payload = buildPayload()
    const endpoint = selectedProjectId ? `/api/projects/${selectedProjectId}` : '/api/projects'
    const method = selectedProjectId ? 'PUT' : 'POST'

    const saved = await apiJson(endpoint, {
      method,
      body: JSON.stringify(payload),
    })

    setSelectedProjectIdState(saved.project_id)
    setSelectedPlanningProjectId(saved.project_id)
    setForm(mapProjectToForm(saved))
    setMerchantRows(mapMerchantRows(saved.merchant_rows))
    setCompetitionRows(mapCompetitionRows(saved.competition_rows, saved.competitor_list))
    await loadProjects()
    if (showSavedToast) {
      showToast('项目数据已保存')
    }
    return saved
  }

  const handleSave = async () => {
    setSaving(true)
    setError('')
    try {
      await saveProject(true)
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  const handleConfirm = async () => {
    setConfirming(true)
    setError('')
    try {
      const saved = await saveProject(false)
      const confirmed = await apiJson(`/api/projects/${saved.project_id}/confirm`, {
        method: 'POST',
      })
      setForm(mapProjectToForm(confirmed))
      await loadProjects()
      if (confirmed.calc_warning) {
        showToast(`已确认数据，自动测算提示：${confirmed.calc_warning}`)
      } else {
        showToast('已确认数据，系统已自动生成双口径测算结果')
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setConfirming(false)
    }
  }

  return (
    <DashboardLayout title="策划咨询" overline="PLANNING">
      <section className="dash-form-page">
        {toast && <div className="toast">{toast}</div>}
        <PlanningBreadcrumb sectionLabel="新建项目" currentLabel="数据采集" />
        <ModuleTabs modules={planningModules} basePath="/planning/new" />

        {error && <div className="notice">{error}</div>}

        <form className="dash-form-stack" autoComplete="off">
          <div className="dash-card dash-card-secondary dash-page-intro dash-page-intro--compact dash-collect-hero">
            <div className="dash-module-header">
              <div>
                <h2>项目数据采集与结构化</h2>
                <p className="dash-module-desc">
                  录入项目现场与商家调研信息，统一结构化字段，作为后续筛选与测算的基础。
                </p>
              </div>
              <div className="dash-collect-statuses">
                <span className={`dash-status ${selectedProjectId ? 'merchant' : 'deleted'}`}>
                  {selectedProjectId ? '历史项目' : '新建项目'}
                </span>
                <span className={`dash-status ${selectedProject?.is_confirmed === 1 ? 'merchant' : 'deleted'}`}>
                  {selectedProject?.is_confirmed === 1 ? '已确认' : '待确认'}
                </span>
              </div>
            </div>
            <div className="dash-collect-kpis">
              <article className="dash-collect-kpi">
                <span>项目模式</span>
                <strong>{selectedProjectId ? '编辑已有项目' : '新建项目'}</strong>
                <small>支持保存与再次确认</small>
              </article>
              <article className="dash-collect-kpi">
                <span>商家调研</span>
                <strong>{merchantRows.length} 条</strong>
                <small>沉淀租金、面积与客流</small>
              </article>
              <article className="dash-collect-kpi">
                <span>竞争关系</span>
                <strong>{competitionRows.length} 条</strong>
                <small>沉淀体量、空置率与客群</small>
              </article>
              <article className="dash-collect-kpi">
                <span>下一步</span>
                <strong>筛选 + 测算</strong>
                <small>确认后自动生成基础结果</small>
              </article>
            </div>
          </div>

          <div className="dash-card dash-card-muted dash-collect-toolbar">
            <div className="dash-screening-actions-top dash-collect-toolbar-row">
              <label className="dash-screening-select">
                <span>选择项目</span>
                <select
                  className="dash-select"
                  value={selectedProjectId}
                  onChange={(event) => setSelectedProject(event.target.value)}
                  disabled={loading}
                >
                  <option value="">新建项目</option>
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
                  onClick={handleSave}
                  disabled={loading || saving || confirming}
                >
                  {saving ? '保存中...' : '保存数据'}
                </button>
                <button
                  className="dash-btn primary"
                  type="button"
                  onClick={handleConfirm}
                  disabled={loading || saving || confirming}
                >
                  {confirming ? '确认中...' : selectedProject?.is_confirmed === 1 ? '重新确认' : '确认数据'}
                </button>
              </div>
            </div>
            <div className="dash-collect-toolbar-meta">
              <span>保存后可持续编辑；确认后会自动进入筛选与双口径测算链路。</span>
            </div>
          </div>

          <div className="dash-card dash-form-card">
            <div className="dash-card-header">
              <strong className="dash-section-title">
                <span className="material-symbols-outlined">info</span>
                基本信息
              </strong>
              <span className="dash-section-note">带 * 为必填</span>
            </div>
            <div className="dash-fields">
              <label className="dash-field">
                <span>项目名称 *</span>
                <input
                  className="dash-input"
                  placeholder="城市+区+项目"
                  autoComplete="off"
                  value={form.project_name}
                  onChange={(event) => updateForm('project_name', event.target.value)}
                />
              </label>
              <label className="dash-field">
                <span>城市 *</span>
                <input
                  className="dash-input"
                  placeholder="如：重庆"
                  autoComplete="off"
                  value={form.city}
                  onChange={(event) => updateForm('city', event.target.value)}
                />
              </label>
              <label className="dash-field">
                <span>行政区 *</span>
                <input
                  className="dash-input"
                  placeholder="如：渝中区"
                  autoComplete="off"
                  value={form.district}
                  onChange={(event) => updateForm('district', event.target.value)}
                />
              </label>
            </div>
          </div>

          <div className="dash-card dash-form-card">
            <div className="dash-card-header">
              <strong className="dash-section-title">
                <span className="material-symbols-outlined">tune</span>
                项目宏观数据
              </strong>
              <span className="dash-section-note">用于项目筛选自动判档</span>
            </div>
            <div className="dash-fields">
              <label className="dash-field">
                <span>城市人口（万人）</span>
                <input
                  className="dash-input"
                  placeholder="例如 120"
                  value={form.city_population_10k}
                  onChange={(event) => updateForm('city_population_10k', event.target.value)}
                />
              </label>
              <label className="dash-field">
                <span>项目周边 5km 人口（万人）</span>
                <input
                  className="dash-input"
                  placeholder="例如 45"
                  value={form.population_5km_10k}
                  onChange={(event) => updateForm('population_5km_10k', event.target.value)}
                />
              </label>
              <label className="dash-field">
                <span>项目周边 3km 人口（万人）</span>
                <input
                  className="dash-input"
                  placeholder="例如 26"
                  value={form.population_3km_10k}
                  onChange={(event) => updateForm('population_3km_10k', event.target.value)}
                />
              </label>
              <label className="dash-field">
                <span>城市房价（元/㎡）</span>
                <input
                  className="dash-input"
                  placeholder="例如 18000"
                  value={form.housing_price_5km}
                  onChange={(event) => updateForm('housing_price_5km', event.target.value)}
                />
              </label>
              <label className="dash-field">
                <span>人均可支配收入（万元）</span>
                <input
                  className="dash-input"
                  placeholder="例如 4.8"
                  value={form.disposable_income_10k}
                  onChange={(event) => updateForm('disposable_income_10k', event.target.value)}
                />
              </label>
              <label className="dash-field">
                <span>城市级别及商圈</span>
                <select
                  className="dash-select"
                  value={form.city_circle_level}
                  onChange={(event) => updateForm('city_circle_level', event.target.value)}
                >
                  <option value="">请选择</option>
                  <option value="一线城市核心商圈">一线城市核心商圈</option>
                  <option value="二线城市核心商圈/一线城市区域商圈">二线城市核心商圈/一线城市区域商圈</option>
                  <option value="二线城市区域商圈/三线城市核心商圈">二线城市区域商圈/三线城市核心商圈</option>
                  <option value="三线城市区域商圈">三线城市区域商圈</option>
                  <option value="未形成商圈">未形成商圈</option>
                </select>
              </label>
              <label className="dash-field">
                <span>市场竞争状况</span>
                <select
                  className="dash-select"
                  value={form.competition_market_level}
                  onChange={(event) => updateForm('competition_market_level', event.target.value)}
                >
                  <option value="">请选择</option>
                  <option value="3km内无5万㎡以上同业定位商业项目">3km内无5万㎡以上同业定位商业项目</option>
                  <option value="3km内无8万㎡以上同业定位商业项目">3km内无8万㎡以上同业定位商业项目</option>
                  <option value="3km内有1个8万㎡同业定位商业项目">3km内有1个8万㎡同业定位商业项目</option>
                  <option value="3km内有2个8万㎡同业定位商业项目">3km内有2个8万㎡同业定位商业项目</option>
                  <option value="3km内超过2个8万㎡同业定位商业项目">3km内超过2个8万㎡同业定位商业项目</option>
                </select>
              </label>
              <label className="dash-field">
                <span>区域功能定位</span>
                <select
                  className="dash-select"
                  value={form.regional_function_level}
                  onChange={(event) => updateForm('regional_function_level', event.target.value)}
                >
                  <option value="">请选择</option>
                  <option value="城市级大型住宅区">城市级大型住宅区</option>
                  <option value="城市级大型商务区">城市级大型商务区</option>
                  <option value="城市次级住宅区">城市次级住宅区</option>
                  <option value="城市次级商务区">城市次级商务区</option>
                  <option value="以上情况都不属于">以上情况都不属于</option>
                </select>
              </label>
              <label className="dash-field">
                <span>商业规划</span>
                <select
                  className="dash-select"
                  value={form.commercial_planning_level}
                  onChange={(event) => updateForm('commercial_planning_level', event.target.value)}
                >
                  <option value="">请选择</option>
                  <option value="城市商业区中心核心地点">城市商业区中心核心地点</option>
                  <option value="城市商业区中心非核心地点">城市商业区中心非核心地点</option>
                  <option value="城市副商业区中心核心地点">城市副商业区中心核心地点</option>
                  <option value="城市副商业区中心非核心地点">城市副商业区中心非核心地点</option>
                  <option value="受商圈影响较小">受商圈影响较小</option>
                </select>
              </label>
              <label className="dash-field">
                <span>轨道覆盖</span>
                <select
                  className="dash-select"
                  value={form.rail_access_level}
                  onChange={(event) => updateForm('rail_access_level', event.target.value)}
                >
                  <option value="">请选择</option>
                  <option value="直接连接轨道交通站点">直接连接轨道交通站点</option>
                  <option value="与轨道交通站点100m">与轨道交通站点100m</option>
                  <option value="与轨道交通站点200m">与轨道交通站点200m</option>
                  <option value="200m以外无轨道交通站点">200m以外无轨道交通站点</option>
                  <option value="500m以外无轨道交通站点">500m以外无轨道交通站点</option>
                </select>
              </label>
              <label className="dash-field">
                <span>主干道通达</span>
                <select
                  className="dash-select"
                  value={form.arterial_access_level}
                  onChange={(event) => updateForm('arterial_access_level', event.target.value)}
                >
                  <option value="">请选择</option>
                  <option value="有2条城市主干道">有2条城市主干道</option>
                  <option value="有1条城市主干道">有1条城市主干道</option>
                  <option value="与城市主干道50m">与城市主干道50m</option>
                  <option value="与城市主干道100m">与城市主干道100m</option>
                  <option value="与城市主干道>100m">与城市主干道&gt;100m</option>
                </select>
              </label>
              <label className="dash-field">
                <span>公交站点</span>
                <select
                  className="dash-select"
                  value={form.bus_access_level}
                  onChange={(event) => updateForm('bus_access_level', event.target.value)}
                >
                  <option value="">请选择</option>
                  <option value="5条以上公交站点在项目1公里范围内">5条以上公交站点在项目1公里范围内</option>
                  <option value="3条以上公交站点在项目1公里范围内">3条以上公交站点在项目1公里范围内</option>
                  <option value="2条以上公交站点在项目1公里范围内">2条以上公交站点在项目1公里范围内</option>
                  <option value="1条以上公交站点在项目1公里范围内">1条以上公交站点在项目1公里范围内</option>
                  <option value="公交站点在项目1公里以外">公交站点在项目1公里以外</option>
                </select>
              </label>
              <label className="dash-field">
                <span>经营与改造潜力</span>
                <select
                  className="dash-select"
                  value={form.operation_retrofit_potential_level}
                  onChange={(event) =>
                    updateForm('operation_retrofit_potential_level', event.target.value)
                  }
                >
                  <option value="">请选择</option>
                  <option value="低投入可快速提升">低投入可快速提升</option>
                  <option value="低投入可阶段提升">低投入可阶段提升</option>
                  <option value="中等投入可提升">中等投入可提升</option>
                  <option value="高投入方可改善">高投入方可改善</option>
                  <option value="短期改善空间有限">短期改善空间有限</option>
                </select>
              </label>
              <label className="dash-field">
                <span>资产与权属复杂度</span>
                <select
                  className="dash-select"
                  value={form.asset_rights_complexity_level}
                  onChange={(event) =>
                    updateForm('asset_rights_complexity_level', event.target.value)
                  }
                >
                  <option value="">请选择</option>
                  <option value="权属清晰决策链短">权属清晰决策链短</option>
                  <option value="权属较清晰协同可控">权属较清晰协同可控</option>
                  <option value="存在多方协同">存在多方协同</option>
                  <option value="权属较复杂审批链长">权属较复杂审批链长</option>
                  <option value="权属复杂落地难度高">权属复杂落地难度高</option>
                </select>
              </label>
            </div>
          </div>

          <div className="dash-card dash-form-card">
            <div className="dash-card-header">
              <strong className="dash-section-title">
                <span className="material-symbols-outlined">square_foot</span>
                项目规模
              </strong>
            </div>
            <div className="dash-fields">
              <label className="dash-field">
                <span>总建筑面积（㎡）*</span>
                <input
                  className="dash-input"
                  placeholder="例如 35000"
                  value={form.total_area}
                  onChange={(event) => updateForm('total_area', event.target.value)}
                />
              </label>
              <label className="dash-field">
                <span>可出租面积（㎡）</span>
                <input
                  className="dash-input"
                  placeholder="例如 22000"
                  value={form.rentable_area}
                  onChange={(event) => updateForm('rentable_area', event.target.value)}
                />
              </label>
              <label className="dash-field">
                <span>核心区块面积（㎡）</span>
                <input
                  className="dash-input"
                  placeholder="例如 8000"
                  value={form.core_area}
                  onChange={(event) => updateForm('core_area', event.target.value)}
                />
              </label>
            </div>
          </div>

          <div className="dash-card dash-form-card">
            <div className="dash-card-header">
              <strong className="dash-section-title">
                <span className="material-symbols-outlined">domain</span>
                资产属性
              </strong>
            </div>
            <div className="dash-fields">
              <label className="dash-field">
                <span>分布形态 *</span>
                <select
                  className="dash-select"
                  value={form.asset_distribution}
                  onChange={(event) => updateForm('asset_distribution', event.target.value)}
                >
                  <option value="集中">集中</option>
                  <option value="分散">分散</option>
                  <option value="混合">混合</option>
                </select>
              </label>
              <label className="dash-field">
                <span>权属结构 *</span>
                <select
                  className="dash-select"
                  value={form.ownership_structure}
                  onChange={(event) => updateForm('ownership_structure', event.target.value)}
                >
                  <option value="甲方">甲方</option>
                  <option value="第三方">第三方</option>
                  <option value="混合">混合</option>
                </select>
              </label>
            </div>
          </div>

          <div className="dash-card dash-form-card">
            <div className="dash-card-header">
              <strong className="dash-section-title">
                <span className="material-symbols-outlined">monitoring</span>
                经营现状
              </strong>
            </div>
            <div className="dash-fields">
              <label className="dash-field">
                <span>当前空置率（%）</span>
                <input
                  className="dash-input"
                  placeholder="例如 18"
                  value={form.vacancy_rate}
                  onChange={(event) => updateForm('vacancy_rate', event.target.value)}
                />
              </label>
              <label className="dash-field">
                <span>租金区间（最低）</span>
                <input
                  className="dash-input"
                  placeholder="元/㎡/月"
                  value={form.rent_min}
                  onChange={(event) => updateForm('rent_min', event.target.value)}
                />
              </label>
              <label className="dash-field">
                <span>租金区间（最高）</span>
                <input
                  className="dash-input"
                  placeholder="元/㎡/月"
                  value={form.rent_max}
                  onChange={(event) => updateForm('rent_max', event.target.value)}
                />
              </label>
              <label className="dash-field">
                <span>主要业态类型</span>
                <input
                  className="dash-input"
                  placeholder="如：餐饮/零售/亲子"
                  value={form.main_business_type}
                  onChange={(event) => updateForm('main_business_type', event.target.value)}
                />
              </label>
            </div>
          </div>

          <div className="dash-card dash-form-card">
            <div className="dash-card-header">
              <strong className="dash-section-title">
                <span className="material-symbols-outlined">storefront</span>
                商家调研
              </strong>
              <div className="dash-section-actions">
                <span className="dash-count-pill">{merchantRows.length} 条</span>
                <span className="dash-section-note">最多 99 行</span>
                <button
                  className="dash-btn secondary"
                  type="button"
                  onClick={addMerchantRow}
                  disabled={merchantRows.length >= 99}
                >
                  新增行
                </button>
              </div>
            </div>
            <div className="dash-table-scroll">
              <div className="dash-merchant-table">
                <div className="dash-merchant-row header">
                  <span>商家名称</span>
                  <span>品类</span>
                  <span>面积（㎡）</span>
                  <span>租金</span>
                  <span>日均客流</span>
                  <span>地址</span>
                  <span>城市</span>
                  <span>区域</span>
                  <span>位置</span>
                  <span>备注</span>
                  <span />
                </div>
                {merchantRows.map((row) => (
                  <div className="dash-merchant-row" key={row.id}>
                    <input
                      className="dash-input"
                      placeholder="如：XX餐饮"
                      autoComplete="off"
                      value={row.name}
                      onChange={(event) => updateMerchantRow(row.id, 'name', event.target.value)}
                    />
                    <input
                      className="dash-input"
                      placeholder="餐饮/零售"
                      autoComplete="off"
                      value={row.category}
                      onChange={(event) => updateMerchantRow(row.id, 'category', event.target.value)}
                    />
                    <input
                      className="dash-input"
                      placeholder="80"
                      autoComplete="off"
                      value={row.area_m2}
                      onChange={(event) => updateMerchantRow(row.id, 'area_m2', event.target.value)}
                    />
                    <input
                      className="dash-input"
                      placeholder="元/㎡/月"
                      autoComplete="off"
                      value={row.rent_unit_price}
                      onChange={(event) => updateMerchantRow(row.id, 'rent_unit_price', event.target.value)}
                    />
                    <input
                      className="dash-input"
                      placeholder="1200"
                      autoComplete="off"
                      value={row.daily_flow}
                      onChange={(event) => updateMerchantRow(row.id, 'daily_flow', event.target.value)}
                    />
                    <input
                      className="dash-input"
                      placeholder="详细地址"
                      autoComplete="off"
                      value={row.address}
                      onChange={(event) => updateMerchantRow(row.id, 'address', event.target.value)}
                    />
                    <input
                      className="dash-input"
                      placeholder="城市"
                      autoComplete="off"
                      value={row.city}
                      onChange={(event) => updateMerchantRow(row.id, 'city', event.target.value)}
                    />
                    <input
                      className="dash-input"
                      placeholder="区域"
                      autoComplete="off"
                      value={row.district}
                      onChange={(event) => updateMerchantRow(row.id, 'district', event.target.value)}
                    />
                    <button
                      className="dash-btn secondary dash-location-btn"
                      type="button"
                      onClick={() => openMapPicker('merchant', row.id)}
                    >
                      {row.longitude && row.latitude ? '已选点' : '地图选点'}
                    </button>
                    <input
                      className="dash-input"
                      placeholder="调研备注"
                      autoComplete="off"
                      value={row.note}
                      onChange={(event) => updateMerchantRow(row.id, 'note', event.target.value)}
                    />
                    <button
                      className="dash-icon-btn"
                      type="button"
                      onClick={() => removeMerchantRow(row.id)}
                      disabled={merchantRows.length <= 1}
                    >
                      <span className="material-symbols-outlined">close</span>
                    </button>
                  </div>
                ))}
              </div>
            </div>
            <p className="dash-helper">可继续添加商家行，支持删除。</p>
          </div>

          <div className="dash-card dash-form-card">
            <div className="dash-card-header">
              <strong className="dash-section-title">
                <span className="material-symbols-outlined">emoji_flags</span>
                竞争关系
              </strong>
              <div className="dash-section-actions">
                <span className="dash-count-pill">{competitionRows.length} 条</span>
                <span className="dash-section-note">最多 99 行</span>
                <button
                  className="dash-btn secondary"
                  type="button"
                  onClick={addCompetitionRow}
                  disabled={competitionRows.length >= 99}
                >
                  新增行
                </button>
              </div>
            </div>
            <div className="dash-table-scroll">
              <div className="dash-competition-table">
                <div className="dash-competition-row header">
                  <span>竞品名称</span>
                  <span>商业体量（㎡）</span>
                  <span>平均租金单价</span>
                  <span>空置率（%）</span>
                  <span>主要业态</span>
                  <span>距离（km）</span>
                  <span>目标人群</span>
                  <span>地址</span>
                  <span>城市</span>
                  <span>区域</span>
                  <span>位置</span>
                  <span />
                </div>
                {competitionRows.map((row) => (
                  <div className="dash-competition-row" key={row.id}>
                    <input
                      className="dash-input"
                      placeholder="竞品名称"
                      autoComplete="off"
                      value={row.name}
                      onChange={(event) => updateCompetitionRow(row.id, 'name', event.target.value)}
                    />
                    <input
                      className="dash-input"
                      placeholder="例如 50000"
                      autoComplete="off"
                      value={row.scale_m2}
                      onChange={(event) => updateCompetitionRow(row.id, 'scale_m2', event.target.value)}
                    />
                    <input
                      className="dash-input"
                      placeholder="元/㎡/月"
                      autoComplete="off"
                      value={row.avg_rent_unit_price}
                      onChange={(event) =>
                        updateCompetitionRow(row.id, 'avg_rent_unit_price', event.target.value)
                      }
                    />
                    <input
                      className="dash-input"
                      placeholder="18"
                      autoComplete="off"
                      value={row.vacancy_rate}
                      onChange={(event) =>
                        updateCompetitionRow(row.id, 'vacancy_rate', event.target.value)
                      }
                    />
                    <input
                      className="dash-input"
                      placeholder="餐饮/零售"
                      autoComplete="off"
                      value={row.business_type}
                      onChange={(event) =>
                        updateCompetitionRow(row.id, 'business_type', event.target.value)
                      }
                    />
                    <input
                      className="dash-input"
                      placeholder="3.5"
                      autoComplete="off"
                      value={row.distance_km}
                      onChange={(event) =>
                        updateCompetitionRow(row.id, 'distance_km', event.target.value)
                      }
                    />
                    <input
                      className="dash-input"
                      placeholder="年轻家庭/白领"
                      autoComplete="off"
                      value={row.target_people}
                      onChange={(event) =>
                        updateCompetitionRow(row.id, 'target_people', event.target.value)
                      }
                    />
                    <input
                      className="dash-input"
                      placeholder="详细地址"
                      autoComplete="off"
                      value={row.address}
                      onChange={(event) => updateCompetitionRow(row.id, 'address', event.target.value)}
                    />
                    <input
                      className="dash-input"
                      placeholder="城市"
                      autoComplete="off"
                      value={row.city}
                      onChange={(event) => updateCompetitionRow(row.id, 'city', event.target.value)}
                    />
                    <input
                      className="dash-input"
                      placeholder="区域"
                      autoComplete="off"
                      value={row.district}
                      onChange={(event) =>
                        updateCompetitionRow(row.id, 'district', event.target.value)
                      }
                    />
                    <button
                      className="dash-btn secondary dash-location-btn"
                      type="button"
                      onClick={() => openMapPicker('competition', row.id)}
                    >
                      {row.longitude && row.latitude ? '已选点' : '地图选点'}
                    </button>
                    <button
                      className="dash-icon-btn"
                      type="button"
                      onClick={() => removeCompetitionRow(row.id)}
                      disabled={competitionRows.length <= 1}
                    >
                      <span className="material-symbols-outlined">close</span>
                    </button>
                  </div>
                ))}
              </div>
            </div>
            <div className="dash-fields" style={{ marginTop: 12 }}>
              <label className="dash-field">
                <span>竞争强度 *</span>
                <select
                  className="dash-select"
                  value={form.competition_level}
                  onChange={(event) => updateForm('competition_level', event.target.value)}
                >
                  <option value="强">强</option>
                  <option value="中">中</option>
                  <option value="弱">弱</option>
                </select>
              </label>
              <label className="dash-field span-2">
                <span>竞品概要（自动汇总）</span>
                <input className="dash-input" value={competitorSummary} readOnly />
              </label>
            </div>
            <p className="dash-helper">竞品信息支持与商家调研同样的增删。</p>
          </div>

          <div className="dash-card dash-form-card">
            <div className="dash-card-header">
              <strong className="dash-section-title">
                <span className="material-symbols-outlined">sticky_note_2</span>
                备注
              </strong>
            </div>
            <div className="dash-fields">
              <label className="dash-field span-4">
                <span>补充说明</span>
                <textarea
                  className="dash-textarea"
                  placeholder="自由补充说明"
                  value={form.remark}
                  onChange={(event) => updateForm('remark', event.target.value)}
                />
              </label>
            </div>
          </div>
        </form>
      </section>
      <MapPointPickerModal
        open={pickerState.open}
        initialPoint={
          pickerState.rowType === 'merchant'
            ? merchantRows.find((row) => row.id === pickerState.rowId)
            : competitionRows.find((row) => row.id === pickerState.rowId)
        }
        onClose={closeMapPicker}
        onConfirm={applyPickedPoint}
      />
    </DashboardLayout>
  )
}
