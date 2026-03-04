import React, { useEffect, useState } from 'react'
import DashboardLayout from '../components/DashboardLayout'
import PlanningBreadcrumb from '../components/PlanningBreadcrumb'
import { apiJson } from '../lib/api'
import MapPointPickerModal from '../components/MapPointPickerModal'
import { CHONGQING_DISTRICTS } from '../lib/options'

function createRow() {
  return {
    id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    name: '',
    category: '',
    area_m2: '',
    rent_unit_price: '',
    daily_flow: '',
    address: '',
    city: '',
    district: '',
    note: '',
    longitude: '',
    latitude: '',
  }
}

export default function PlanningMerchant() {
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

  const addRow = () => {
    setForm((prev) => ({ ...prev, rows: [...prev.rows, createRow()] }))
  }

  const removeRow = (index) => {
    setForm((prev) => ({ ...prev, rows: prev.rows.filter((_, idx) => idx !== index) }))
  }

  const handleSubmit = async () => {
    setSaving(true)
    setError('')
    setSuccess('')
    try {
      if (!form.district) {
        throw new Error('请选择区域')
      }
      if (!form.rows.some((row) => row.name && row.address && row.category)) {
        throw new Error('请至少填写一条完整商家记录')
      }
      const payload = {
        source_mode: form.source_mode,
        project_id: form.source_mode === 'project' ? form.project_id : null,
        city: form.city,
        district: form.district,
        merchant_rows: form.rows.map((row) => ({
          name: row.name,
          category: row.category,
          area_m2: Number(row.area_m2),
          rent_unit_price: Number(row.rent_unit_price),
          daily_flow: Number(row.daily_flow),
          address: row.address,
          note: row.note,
          city: row.city || form.city,
          district: row.district || form.district,
          longitude: row.longitude ? Number(row.longitude) : null,
          latitude: row.latitude ? Number(row.latitude) : null,
        })),
      }
      await apiJson('/api/market/merchant/submissions', {
        method: 'POST',
        body: JSON.stringify(payload),
      })
      setSuccess('商家信息已提交并进入城市数据池')
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
        <PlanningBreadcrumb sectionLabel="商家信息" />
        {error && <div className="notice">{error}</div>}
        {success && <div className="dash-helper">{success}</div>}

        <div className="dash-card dash-card-secondary dash-page-intro dash-page-intro--compact dash-market-hero">
          <div className="dash-module-header">
            <div>
              <h2>商家信息采集</h2>
              <p className="dash-module-desc">日常采集商家调研数据，默认独立入池，可选挂接项目。</p>
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
              <small>商家信息</small>
            </article>
            <article className="dash-inline-kpi">
              <span>采集模式</span>
              <strong>{form.source_mode === 'project' ? '挂接项目' : '独立入池'}</strong>
              <small>城市数据池</small>
            </article>
            <article className="dash-inline-kpi">
              <span>位置能力</span>
              <strong>地图选点</strong>
              <small>支持坐标回填</small>
            </article>
          </div>
        </div>

        <div className="dash-card dash-card-muted dash-market-toolbar">
          <div className="dash-collect-toolbar-row">
            <div className="dash-market-toolbar-title">
              <strong>提交与归属设置</strong>
              <span>先确定区域与归属方式，再批量录入商家样本。</span>
            </div>
            <div className="dash-collect-toolbar-actions">
              <button className="dash-btn primary" type="button" onClick={handleSubmit} disabled={saving}>
                {saving ? '提交中...' : '提交商家信息'}
              </button>
            </div>
          </div>
        </div>

        <div className="dash-card dash-page-toolbar-card">
          <div className="dash-card-header">
            <div className="dash-page-toolbar-copy">
              <strong>采集范围</strong>
              <span className="dash-subtext">先选择区域与归属方式，再逐行录入商家样本并使用地图选点。</span>
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
              <span className="material-symbols-outlined">table_rows</span>
              商家明细表
            </strong>
            <div className="dash-section-actions">
              <span className="dash-count-pill">{form.rows.length} 条</span>
              <span className="dash-section-note">地址支持地图选点并自动回填经纬度</span>
            </div>
          </div>
          <div className="dash-table-scroll">
            <table className="table">
              <thead>
                <tr>
                  <th>商家名称</th>
                  <th>品类</th>
                  <th>面积(㎡)</th>
                  <th>租金单价</th>
                  <th>日均客流</th>
                  <th>地址</th>
                  <th>备注</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                {form.rows.map((row, index) => (
                  <tr key={row.id}>
                    <td><input className="dash-input" value={row.name} onChange={(e) => updateRow(index, 'name', e.target.value)} /></td>
                    <td><input className="dash-input" value={row.category} onChange={(e) => updateRow(index, 'category', e.target.value)} /></td>
                    <td><input className="dash-input" value={row.area_m2} onChange={(e) => updateRow(index, 'area_m2', e.target.value)} /></td>
                    <td><input className="dash-input" value={row.rent_unit_price} onChange={(e) => updateRow(index, 'rent_unit_price', e.target.value)} /></td>
                    <td><input className="dash-input" value={row.daily_flow} onChange={(e) => updateRow(index, 'daily_flow', e.target.value)} /></td>
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
                    <td><input className="dash-input" value={row.note} onChange={(e) => updateRow(index, 'note', e.target.value)} /></td>
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
