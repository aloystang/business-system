import React, { useEffect, useState } from 'react'
import DashboardLayout from '../components/DashboardLayout'
import PlanningBreadcrumb from '../components/PlanningBreadcrumb'
import { apiJson } from '../lib/api'
import MapPointPickerModal from '../components/MapPointPickerModal'
import { CHONGQING_DISTRICTS, TARGET_PEOPLE_OPTIONS } from '../lib/options'

function createRow() {
  return {
    id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    name: '',
    scale_m2: '',
    avg_rent_unit_price: '',
    vacancy_rate: '',
    business_type: '',
    distance_km: '',
    target_people_values: [],
    address: '',
    city: '',
    district: '',
    longitude: '',
    latitude: '',
  }
}

export default function PlanningCompetitor() {
  const [projects, setProjects] = useState([])
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [form, setForm] = useState({
    city: '重庆市',
    district: '',
    source_mode: 'standalone',
    project_id: '',
    rows: [createRow()],
  })
  const [pickerState, setPickerState] = useState({ open: false, rowId: '' })

  useEffect(() => {
    apiJson('/api/projects')
      .then((items) => setProjects(Array.isArray(items) ? items : []))
      .catch(() => {})
  }, [])

  const updateRow = (index, key, value) => {
    setForm((prev) => {
      const rows = [...prev.rows]
      rows[index] = { ...rows[index], [key]: value }
      return { ...prev, rows }
    })
  }

  const toggleTargetPeople = (index, value) => {
    setForm((prev) => {
      const rows = [...prev.rows]
      const selected = new Set(rows[index].target_people_values || [])
      if (selected.has(value)) {
        selected.delete(value)
      } else {
        selected.add(value)
      }
      rows[index] = { ...rows[index], target_people_values: Array.from(selected) }
      return { ...prev, rows }
    })
  }

  const addRow = () => setForm((prev) => ({ ...prev, rows: [...prev.rows, createRow()] }))
  const removeRow = (index) => setForm((prev) => ({ ...prev, rows: prev.rows.filter((_, idx) => idx !== index) }))

  const openMapPicker = (rowId) => {
    setPickerState({ open: true, rowId })
  }

  const closeMapPicker = () => {
    setPickerState({ open: false, rowId: '' })
  }

  const getPickerInitialPoint = () => {
    const row = form.rows.find((item) => item.id === pickerState.rowId)
    if (!row) return null
    return {
      longitude: row.longitude,
      latitude: row.latitude,
      address: row.address,
      city: row.city || form.city,
      district: row.district || form.district,
    }
  }

  const applyPickedPoint = ({ longitude, latitude, address, city, district }) => {
    const lng = Number(longitude)
    const lat = Number(latitude)
    if (!Number.isFinite(lng) || !Number.isFinite(lat)) return
    setForm((prev) => {
      const rows = prev.rows.map((row) => {
        if (row.id !== pickerState.rowId) return row
        return {
          ...row,
          longitude: String(lng),
          latitude: String(lat),
          address: address || row.address,
          city: city || prev.city,
          district: district || prev.district,
        }
      })
      return {
        ...prev,
        district: prev.district || district || prev.district,
        rows,
      }
    })
    closeMapPicker()
  }

  const handleSubmit = async () => {
    setSaving(true)
    setError('')
    setSuccess('')
    try {
      if (!form.district) {
        throw new Error('请选择区域')
      }
      const incomplete = form.rows.find(
        (row) =>
          row.name &&
          row.address &&
          (!Array.isArray(row.target_people_values) || row.target_people_values.length === 0)
      )
      if (incomplete) {
        throw new Error('目标人群为必选（可多选）')
      }
      const payload = {
        source_mode: form.source_mode,
        project_id: form.source_mode === 'project' ? form.project_id : null,
        city: form.city,
        district: form.district,
        competitor_rows: form.rows.map((row) => ({
          name: row.name,
          scale_m2: Number(row.scale_m2),
          avg_rent_unit_price: Number(row.avg_rent_unit_price),
          vacancy_rate: Number(row.vacancy_rate),
          business_type: row.business_type,
          distance_km: Number(row.distance_km),
          target_people: (row.target_people_values || []).join('、'),
          address: row.address,
          city: row.city || form.city,
          district: row.district || form.district,
          longitude: row.longitude ? Number(row.longitude) : null,
          latitude: row.latitude ? Number(row.latitude) : null,
        })),
      }
      await apiJson('/api/market/competitor/submissions', {
        method: 'POST',
        body: JSON.stringify(payload),
      })
      setSuccess('竞争关系已提交并进入城市数据池')
      setForm((prev) => ({ ...prev, rows: [createRow()] }))
    } catch (err) {
      setError(err.message || '提交失败')
    } finally {
      setSaving(false)
    }
  }

  return (
    <DashboardLayout title="策划咨询" overline="PLANNING">
      <section className="dash-form-page">
        <PlanningBreadcrumb sectionLabel="竞争关系" />
        {error && <div className="notice">{error}</div>}
        {success && <div className="dash-helper">{success}</div>}

        <div className="dash-card dash-card-secondary dash-page-intro dash-page-intro--compact dash-market-hero">
          <div className="dash-module-header">
            <div>
              <h2>竞争关系采集</h2>
              <p className="dash-module-desc">独立采集竞品数据，支撑城市级竞争分析。</p>
            </div>
            <div className="dash-collect-statuses">
              <span className="dash-status merchant">城市：{form.city}</span>
              <span className={`dash-status ${form.source_mode === 'project' ? 'competitor' : 'merchant'}`}>
                {form.source_mode === 'project' ? '挂接项目' : '独立入池'}
              </span>
            </div>
          </div>

          <div className="dash-inline-kpis dash-market-kpis">
            <article className="dash-inline-kpi">
              <span>当前行数</span>
              <strong>{form.rows.length}</strong>
              <small>竞品信息</small>
            </article>
            <article className="dash-inline-kpi">
              <span>采集模式</span>
              <strong>{form.source_mode === 'project' ? '挂接项目' : '独立入池'}</strong>
              <small>竞争关系库</small>
            </article>
            <article className="dash-inline-kpi">
              <span>目标人群</span>
              <strong>多选标签</strong>
              <small>适配城市客群分析</small>
            </article>
          </div>
        </div>

        <div className="dash-card dash-card-muted dash-market-toolbar">
          <div className="dash-collect-toolbar-row">
            <div className="dash-market-toolbar-title">
              <strong>提交与归属设置</strong>
              <span>先确定区域与归属方式，再批量录入竞品样本。</span>
            </div>
            <div className="dash-collect-toolbar-actions">
              <button className="dash-btn primary" type="button" onClick={handleSubmit} disabled={saving}>
                {saving ? '提交中...' : '提交竞争关系'}
              </button>
            </div>
          </div>
        </div>

        <div className="dash-card dash-page-toolbar-card">
          <div className="dash-card-header">
            <div className="dash-page-toolbar-copy">
              <strong>采集范围</strong>
              <span className="dash-subtext">先选择区域与归属方式，再逐行录入竞品样本并完成地图选点。</span>
            </div>
          </div>
          <div className="dash-map-filter-grid">
            <label className="dash-field">
              <span>城市</span>
              <input className="dash-input" value={form.city} onChange={(e) => setForm((prev) => ({ ...prev, city: e.target.value }))} disabled />
            </label>
            <label className="dash-field">
              <span>区域</span>
              <select className="dash-select" value={form.district} onChange={(e) => setForm((prev) => ({ ...prev, district: e.target.value }))}>
                <option value="">请选择区域</option>
                {CHONGQING_DISTRICTS.map((item) => (
                  <option key={item} value={item}>
                    {item}
                  </option>
                ))}
              </select>
            </label>
            <label className="dash-field">
              <span>归属模式</span>
              <select
                className="dash-select"
                value={form.source_mode}
                onChange={(e) => setForm((prev) => ({ ...prev, source_mode: e.target.value }))}
              >
                <option value="standalone">独立采集</option>
                <option value="project">挂接项目</option>
              </select>
            </label>
            <label className="dash-field">
              <span>项目（可选）</span>
              <select
                className="dash-select"
                value={form.project_id}
                onChange={(e) => setForm((prev) => ({ ...prev, project_id: e.target.value }))}
                disabled={form.source_mode !== 'project'}
              >
                <option value="">请选择项目</option>
                {projects.map((item) => (
                  <option key={item.project_id} value={item.project_id}>
                    {item.project_name}
                  </option>
                ))}
              </select>
            </label>
          </div>
        </div>

        <div className="card dash-history-table-card">
          <div className="dash-card-header">
            <strong className="dash-section-title">
              <span className="material-symbols-outlined">conversion_path</span>
              竞争关系明细表
            </strong>
            <div className="dash-section-actions">
              <span className="dash-count-pill">{form.rows.length} 条</span>
              <span className="dash-section-note">支持目标人群多选与地图选点</span>
            </div>
          </div>
          <div className="dash-table-scroll">
            <table className="table">
              <thead>
                <tr>
                  <th>竞品名称</th>
                  <th>体量(㎡)</th>
                  <th>平均租金</th>
                  <th>空置率(%)</th>
                  <th>主要业态</th>
                  <th>距离(km)</th>
                  <th>目标人群</th>
                  <th>地址</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                {form.rows.map((row, index) => (
                  <tr key={row.id}>
                    <td><input className="dash-input" value={row.name} onChange={(e) => updateRow(index, 'name', e.target.value)} /></td>
                    <td><input className="dash-input" value={row.scale_m2} onChange={(e) => updateRow(index, 'scale_m2', e.target.value)} /></td>
                    <td><input className="dash-input" value={row.avg_rent_unit_price} onChange={(e) => updateRow(index, 'avg_rent_unit_price', e.target.value)} /></td>
                    <td><input className="dash-input" value={row.vacancy_rate} onChange={(e) => updateRow(index, 'vacancy_rate', e.target.value)} /></td>
                    <td><input className="dash-input" value={row.business_type} onChange={(e) => updateRow(index, 'business_type', e.target.value)} /></td>
                    <td><input className="dash-input" value={row.distance_km} onChange={(e) => updateRow(index, 'distance_km', e.target.value)} /></td>
                    <td>
                      <div className="dash-target-people">
                        {TARGET_PEOPLE_OPTIONS.map((option) => {
                          const checked = (row.target_people_values || []).includes(option)
                          return (
                            <label key={option} className="dash-target-chip">
                              <input
                                type="checkbox"
                                checked={checked}
                                onChange={() => toggleTargetPeople(index, option)}
                              />
                              <span>{option}</span>
                            </label>
                          )
                        })}
                      </div>
                    </td>
                    <td>
                      <div className="dash-address-cell">
                        <input className="dash-input" value={row.address} onChange={(e) => updateRow(index, 'address', e.target.value)} />
                        <button type="button" className="dash-btn secondary" onClick={() => openMapPicker(row.id)}>
                          选点
                        </button>
                      </div>
                      {(row.longitude && row.latitude) ? (
                        <div className="dash-helper">{`${Number(row.longitude).toFixed(6)}, ${Number(row.latitude).toFixed(6)}`}</div>
                      ) : null}
                    </td>
                    <td>
                      <button type="button" className="dash-btn secondary" onClick={() => removeRow(index)} disabled={form.rows.length <= 1}>
                        删除
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="dash-history-actions dash-section-footer-actions">
            <button type="button" className="dash-btn secondary" onClick={addRow}>新增一行</button>
          </div>
        </div>
        <MapPointPickerModal
          open={pickerState.open}
          initialPoint={getPickerInitialPoint()}
          onClose={closeMapPicker}
          onConfirm={applyPickedPoint}
        />
      </section>
    </DashboardLayout>
  )
}
