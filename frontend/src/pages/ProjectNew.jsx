import React, { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { apiJson } from '../lib/api'

export default function ProjectNew() {
  const navigate = useNavigate()
  const [form, setForm] = useState({
    project_name: '',
    city: '',
    district: '',
    total_area: '',
    rentable_area: '',
    asset_distribution: '集中',
    ownership_structure: '甲方',
    competition_level: '中',
  })
  const [error, setError] = useState('')

  const handleChange = (key, value) => {
    setForm((prev) => ({ ...prev, [key]: value }))
  }

  const toNumberOrNull = (value) => {
    if (value === null || value === undefined || value === '') return null
    const num = Number(value)
    return Number.isNaN(num) ? null : num
  }

  const handleSave = async () => {
    setError('')
    if (!form.project_name || !form.city || !form.district || !form.total_area) {
      setError('请填写项目名称/城市/行政区/总面积')
      return
    }
    try {
      await apiJson('/api/projects', {
        method: 'POST',
        body: JSON.stringify({
          project_name: form.project_name,
          city: form.city,
          district: form.district,
          total_area: toNumberOrNull(form.total_area),
          rentable_area: toNumberOrNull(form.rentable_area),
          asset_distribution: form.asset_distribution,
          ownership_structure: form.ownership_structure,
          competition_level: form.competition_level,
        }),
      })
      navigate('/projects?created=1')
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">新建项目</h1>
          <div className="page-subtitle">录入基础信息后可确认并进入计算</div>
        </div>
        <div className="page-actions">
          <button className="button" onClick={handleSave}>
            保存
          </button>
        </div>
      </div>

      {error && <div className="notice">{error}</div>}

      <div className="card">
        <div className="grid two">
          <div>
            <label>项目名称</label>
            <input
              className="input"
              value={form.project_name}
              onChange={(e) => handleChange('project_name', e.target.value)}
            />
          </div>
          <div>
            <label>城市</label>
            <input
              className="input"
              value={form.city}
              onChange={(e) => handleChange('city', e.target.value)}
            />
          </div>
          <div>
            <label>行政区</label>
            <input
              className="input"
              value={form.district}
              onChange={(e) => handleChange('district', e.target.value)}
            />
          </div>
          <div>
            <label>总面积(㎡)</label>
            <input
              className="input"
              type="number"
              step="0.01"
              value={form.total_area}
              onChange={(e) => handleChange('total_area', e.target.value)}
            />
          </div>
          <div>
            <label>可出租面积(㎡)</label>
            <input
              className="input"
              type="number"
              step="0.01"
              value={form.rentable_area}
              onChange={(e) => handleChange('rentable_area', e.target.value)}
            />
          </div>
          <div>
            <label>资产分布形态</label>
            <select
              className="select"
              value={form.asset_distribution}
              onChange={(e) => handleChange('asset_distribution', e.target.value)}
            >
              <option value="集中">集中</option>
              <option value="分散">分散</option>
              <option value="混合">混合</option>
            </select>
          </div>
          <div>
            <label>权属结构</label>
            <select
              className="select"
              value={form.ownership_structure}
              onChange={(e) => handleChange('ownership_structure', e.target.value)}
            >
              <option value="甲方">甲方</option>
              <option value="第三方">第三方</option>
              <option value="混合">混合</option>
            </select>
          </div>
          <div>
            <label>竞争强度</label>
            <select
              className="select"
              value={form.competition_level}
              onChange={(e) => handleChange('competition_level', e.target.value)}
            >
              <option value="强">强</option>
              <option value="中">中</option>
              <option value="弱">弱</option>
            </select>
          </div>
        </div>

        <div className="page-actions" style={{ marginTop: 24 }}>
          <button className="button" onClick={handleSave}>
            保存
          </button>
          <Link className="button secondary" to="/projects">
            取消
          </Link>
        </div>
      </div>
    </div>
  )
}
