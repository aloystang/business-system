import React, { useEffect, useState } from 'react'
import { apiJson } from '../lib/api'

const FIELD_LABELS = {
  name: '项目名称',
  city: '城市',
  district: '行政区',
  location_desc: '项目位置描述',
  total_area_m2: '总建筑面积(㎡)',
  rentable_area_m2: '可出租面积(㎡)',
  core_area_m2: '核心区块面积(㎡)',
  distribution_form: '分布形态',
  ownership_structure: '权属结构',
  vacancy_rate: '当前空置率(%)',
  rent_range: '租金区间',
  primary_business_types: '主要业态类型',
  competitors: '周边竞品列表',
  competition_intensity: '竞品竞争强度',
  notes: '自由补充说明',
}

const emptyProfile = {
  name: '',
  city: '',
  district: '',
  location_desc: '',
  total_area_m2: '',
  rentable_area_m2: '',
  core_area_m2: '',
  distribution_form: '',
  ownership_structure: '',
  vacancy_rate: '',
  rent_range: '',
  primary_business_types: '',
  competitors: '',
  competition_intensity: '',
  notes: '',
}

export default function Intake() {
  const [rawText, setRawText] = useState('')
  const [intake, setIntake] = useState(null)
  const [profile, setProfile] = useState(emptyProfile)
  const [profiles, setProfiles] = useState([])
  const [error, setError] = useState('')

  const loadProfiles = async () => {
    try {
      const data = await apiJson('/api/profiles')
      setProfiles(data)
    } catch (err) {
      // ignore
    }
  }

  useEffect(() => {
    loadProfiles()
  }, [])

  const handleParse = async () => {
    setError('')
    try {
      const data = await apiJson('/api/intakes', {
        method: 'POST',
        body: JSON.stringify({ raw_text: rawText }),
      })
      setIntake(data)
      setProfile({
        ...emptyProfile,
        ...data.parsed_fields,
      })
    } catch (err) {
      setError(err.message)
    }
  }

  const handleProfileChange = (key, value) => {
    setProfile((prev) => ({ ...prev, [key]: value }))
  }

  const handleConfirm = async () => {
    if (!intake) return
    setError('')
    try {
      const payload = {
        ...profile,
        intake_id: intake.id,
        total_area_m2: profile.total_area_m2 ? Number(profile.total_area_m2) : null,
        rentable_area_m2: profile.rentable_area_m2 ? Number(profile.rentable_area_m2) : null,
        core_area_m2: profile.core_area_m2 ? Number(profile.core_area_m2) : null,
        vacancy_rate: profile.vacancy_rate ? Number(profile.vacancy_rate) : null,
      }
      await apiJson(`/api/intakes/${intake.id}/confirm`, {
        method: 'POST',
        body: JSON.stringify(payload),
      })
      setIntake(null)
      setRawText('')
      setProfile(emptyProfile)
      await loadProfiles()
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <div className="grid">
      <div className="card">
        <h2>项目数据采集与结构化</h2>
        <p>粘贴自由文本后解析，确认字段并保存。</p>
        {error && <div className="notice">{error}</div>}
        <textarea
          className="textarea"
          rows={8}
          placeholder="例：\n项目名称：重庆渝中广场\n城市：重庆\n行政区：渝中区\n总建筑面积：120000㎡\n可出租面积：80000㎡\n当前空置率：12%\n租金区间：80-120元/㎡/月\n主要业态类型：餐饮、零售\n竞品列表：解放碑广场、时代天街\n竞争强度：强"
          value={rawText}
          onChange={(e) => setRawText(e.target.value)}
        />
        <div style={{ marginTop: 12 }}>
          <button className="button" onClick={handleParse}>
            解析文本
          </button>
        </div>
      </div>

      {intake && (
        <div className="card">
          <h3>解析结果（可编辑确认）</h3>
          {intake.unknown_lines?.length > 0 && (
            <div className="notice">
              未识别行：{intake.unknown_lines.join(' / ')}
            </div>
          )}
          <div className="grid two">
            {Object.keys(emptyProfile).map((key) => (
              <div key={key}>
                <label>{FIELD_LABELS[key] || key}</label>
                <input
                  className="input"
                  value={profile[key] ?? ''}
                  onChange={(e) => handleProfileChange(key, e.target.value)}
                />
              </div>
            ))}
          </div>
          <div style={{ marginTop: 12 }}>
            <button className="button" onClick={handleConfirm}>
              确认并保存
            </button>
          </div>
        </div>
      )}

      <div className="card">
        <h3>已确认项目档案</h3>
        <table className="table">
          <thead>
            <tr>
              <th>ID</th>
              <th>项目名称</th>
              <th>城市</th>
              <th>行政区</th>
              <th>面积(㎡)</th>
            </tr>
          </thead>
          <tbody>
            {profiles.map((item) => (
              <tr key={item.id}>
                <td>{item.id}</td>
                <td>{item.name}</td>
                <td>{item.city || '-'}</td>
                <td>{item.district || '-'}</td>
                <td>{item.total_area_m2 || '-'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
