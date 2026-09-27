import React from 'react'
import {
  AlertCircle,
  ArrowRight,
  Building2,
  CalendarDays,
  Check,
  ChevronRight,
  Clock3,
  Edit3,
  Layers3,
  LoaderCircle,
  MapPinned,
  RefreshCw,
  Route,
  Store,
  Trash2,
  X,
} from 'lucide-react'
import {
  deleteAdjustmentPlan,
  getAdjustmentPlan,
  getAdjustmentRoadmap,
  getUnitLayout,
  putAdjustmentPlan,
  resolveProjectIdByName,
} from './api'

const ACTIONS = ['保留', '升级', '置换', '改造', '合并', '拆分', '新招商']
const PLAN_STATUSES = ['草案', '审批中', '已定', '执行中', '完成']
const STATUS_COLORS = { 在租: '#4f9168', 自营: '#4f78d5', 装修: '#d88b4b', 空置: '#9da5aa' }
const FORMAT_COLORS = ['#4f78d5', '#4f9168', '#c47b54', '#8e71ad', '#4f91a6', '#b58a46', '#707f91', '#b46b83']

const number = (value) => Number(value || 0)
const money = (value) => `¥${number(value).toLocaleString('zh-CN', { maximumFractionDigits: 0 })}`
const percent = (value) => {
  const normalized = Math.abs(number(value)) <= 1 ? number(value) * 100 : number(value)
  return `${normalized.toFixed(1)}%`
}
const month = (value) => value ? String(value).slice(0, 7) : '未设置'
const safeId = (value) => String(value).replace(/[^a-zA-Z0-9]/g, '-')

function shade(hex, amount) {
  const value = Number.parseInt(hex.slice(1), 16)
  const channel = (shift) => Math.max(0, Math.min(255, ((value >> shift) & 255) + amount))
  return `rgb(${channel(16)}, ${channel(8)}, ${channel(0)})`
}

function iso(x, y, z) {
  return { x: 500 + (x - y) * 0.78, y: 188 + (x + y) * 0.36 - z }
}

function points(items) {
  return items.map((item) => `${item.x.toFixed(1)},${item.y.toFixed(1)}`).join(' ')
}

function makeFootprints(count) {
  const slots = []
  const cols = Math.max(6, Math.ceil(Math.sqrt(count * 1.55)))
  const rows = Math.ceil(count / cols) + 1
  const cellW = 410 / cols
  const cellH = 330 / rows
  for (let row = 0; row < rows; row += 1) {
    for (let col = 0; col < cols; col += 1) {
      const inAtrium = col >= Math.floor(cols / 2) - 1 && col <= Math.floor(cols / 2) && row >= 1 && row <= rows - 2
      if (inAtrium) continue
      const x = 70 + col * cellW
      const y = 48 + row * cellH
      const inset = (row + col) % 3 === 0 ? 4 : 7
      const skew = (row * 7 + col * 3) % 8
      slots.push([
        [x + inset, y + inset],
        [x + cellW - inset, y + inset + skew * 0.25],
        [x + cellW - inset - skew * 0.3, y + cellH - inset],
        [x + inset, y + cellH - inset - skew * 0.18],
      ])
    }
  }
  return slots.slice(0, count)
}

function quarterStart(quarter) {
  const match = String(quarter || '').match(/(\d{4})Q([1-4])/)
  if (!match) return ''
  return `${match[1]}-${String((Number(match[2]) - 1) * 3 + 1).padStart(2, '0')}-01`
}

function Metric({ label, value, meta, icon: Icon, tone = '' }) {
  return <div className={`layoutSandbox-metric ${tone}`}>
    <span className="layoutSandbox-metricIcon"><Icon size={17} /></span>
    <div><span>{label}</span><strong>{value}</strong></div>
    <small>{meta}</small>
  </div>
}

function PlanEditor({ unit, projectId, onClose, onChanged, initialDate }) {
  const plan = unit.plan || {}
  const [form, setForm] = React.useState({
    action: plan.action || (unit.status === '空置' ? '新招商' : '升级'),
    to_format: plan.to_format || unit.format || '',
    expected_rent: plan.expected_rent || unit.rent || '',
    plan_status: plan.plan_status || '草案',
    plan_date: initialDate || plan.plan_date || '',
    reason: plan.reason || '',
    owner: plan.owner || '',
  })
  const [saving, setSaving] = React.useState(false)
  const [error, setError] = React.useState('')
  const update = (key, value) => setForm((current) => ({ ...current, [key]: value }))
  const save = async (event) => {
    event.preventDefault()
    setSaving(true)
    setError('')
    try {
      await putAdjustmentPlan(projectId, unit.unit_id, {
        ...form,
        from_format: unit.format || undefined,
        expected_rent: form.expected_rent === '' ? undefined : Number(form.expected_rent),
      })
      await onChanged()
      onClose()
    } catch (requestError) {
      setError(requestError.status === 403 ? '无编辑权限，请联系系统管理员。' : requestError.message)
    } finally {
      setSaving(false)
    }
  }
  const remove = async () => {
    setSaving(true)
    setError('')
    try {
      await deleteAdjustmentPlan(projectId, unit.unit_id)
      await onChanged()
      onClose()
    } catch (requestError) {
      setError(requestError.status === 403 ? '无编辑权限，请联系系统管理员。' : requestError.message)
      setSaving(false)
    }
  }
  return <div className="layoutSandbox-editorBackdrop" role="presentation" onMouseDown={(event) => event.target === event.currentTarget && onClose()}>
    <form className="layoutSandbox-editor" onSubmit={save} aria-label={`${unit.unit_code}调改计划`}>
      <header><div><span>{unit.unit_code}</span><h3>{unit.tenant || '空置铺位'} · 调改计划</h3></div><button type="button" onClick={onClose} aria-label="关闭"><X size={18} /></button></header>
      <div className="layoutSandbox-formGrid">
        <label><span>调改动作</span><select value={form.action} onChange={(e) => update('action', e.target.value)}>{ACTIONS.map((item) => <option key={item}>{item}</option>)}</select></label>
        <label><span>计划状态</span><select value={form.plan_status} onChange={(e) => update('plan_status', e.target.value)}>{PLAN_STATUSES.map((item) => <option key={item}>{item}</option>)}</select></label>
        <label><span>目标业态</span><input value={form.to_format} onChange={(e) => update('to_format', e.target.value)} placeholder="例如：咖啡茶饮" /></label>
        <label><span>预期月租金（元）</span><input type="number" min="0" value={form.expected_rent} onChange={(e) => update('expected_rent', e.target.value)} /></label>
        <label><span>计划时间</span><input type="date" value={form.plan_date} onChange={(e) => update('plan_date', e.target.value)} /></label>
        <label><span>负责人</span><input value={form.owner} onChange={(e) => update('owner', e.target.value)} placeholder="负责人姓名" /></label>
        <label className="wide"><span>调改原因</span><textarea rows="3" value={form.reason} onChange={(e) => update('reason', e.target.value)} placeholder="填写调改依据和目标" /></label>
      </div>
      {error && <p className="layoutSandbox-formError" role="alert">{error}</p>}
      <footer>{unit.plan && <button type="button" className="danger" onClick={remove} disabled={saving}><Trash2 size={15} />删除计划</button>}<span /><button type="button" onClick={onClose}>取消</button><button type="submit" className="primary" disabled={saving}>{saving ? <LoaderCircle className="spin" size={16} /> : <Check size={16} />}保存计划</button></footer>
    </form>
  </div>
}

function UnitBrick({ unit, footprint, z, color, dimmed, selected, onSelect }) {
  const height = unit.status === '空置' ? 8 : unit.status === '装修' ? 16 : 23
  const base = footprint.map(([x, y]) => iso(x, y, z))
  const top = footprint.map(([x, y]) => iso(x, y, z + height))
  const center = footprint.reduce((result, point) => ({ x: result.x + point[0] / footprint.length, y: result.y + point[1] / footprint.length }), { x: 0, y: 0 })
  const label = iso(center.x, center.y, z + height)
  const edge = footprint.map((point, index) => ({ index, distance: ((point[0] + footprint[(index + 1) % footprint.length][0]) / 2 - 275) ** 2 + ((point[1] + footprint[(index + 1) % footprint.length][1]) / 2 - 230) ** 2 })).sort((a, b) => a.distance - b.distance)[0].index
  const a = footprint[edge]
  const b = footprint[(edge + 1) % footprint.length]
  const glass = [iso(a[0], a[1], z + height - 3), iso(b[0], b[1], z + height - 3), iso(b[0], b[1], z + 3), iso(a[0], a[1], z + 3)]
  const gradientId = `layoutSandbox-gradient-${safeId(color)}`
  return <g className={`layoutSandbox-unit ${selected ? 'selected' : ''}`} role="button" tabIndex="0" aria-label={`${unit.unit_code}，${unit.tenant || '空置'}，${unit.status}`} opacity={dimmed ? 0.12 : 1} onClick={() => !dimmed && onSelect(unit)} onKeyDown={(event) => (event.key === 'Enter' || event.key === ' ') && !dimmed && onSelect(unit)}>
    {footprint.map((point, index) => <polygon key={index} points={points([top[index], top[(index + 1) % top.length], base[(index + 1) % base.length], base[index]])} fill={shade(color, index % 2 ? -34 : -18)} opacity=".94" />)}
    {selected && <polygon points={points(top)} fill="none" stroke="var(--accent)" strokeWidth="8" opacity=".26" filter="url(#layoutSandbox-glow)" />}
    <polygon className="layoutSandbox-unitTop" points={points(top)} fill={`url(#${gradientId})`} stroke={selected ? 'var(--accent)' : shade(color, 35)} strokeWidth={selected ? 2.5 : 0.8} filter="url(#layoutSandbox-shadow)" />
    {unit.status !== '空置' && <polygon className="layoutSandbox-storefront" points={points(glass)} fill="url(#layoutSandbox-glass)" stroke="rgba(245,252,253,.72)" strokeWidth=".75" />}
    <text x={label.x} y={label.y + 3} textAnchor="middle" fill="#fff" stroke="#5d6468" strokeOpacity=".68" strokeWidth="2.7" paintOrder="stroke" fontSize="10.5" fontWeight="500">{unit.unit_code}</text>
    {unit.plan && <circle cx={label.x + 20} cy={label.y - 12} r="5.5" fill="var(--accent)" stroke="#fff" strokeWidth="2" />}
  </g>
}

function Architecture({ z, muted = false }) {
  const boundary = [[48, 24], [500, 32], [520, 82], [510, 405], [466, 445], [92, 448], [42, 392], [35, 110]]
  const plate = boundary.map(([x, y]) => iso(x, y, z))
  const bottom = boundary.map(([x, y]) => iso(x, y, z - 8))
  const atrium = [[226, 145], [325, 145], [345, 330], [252, 356], [224, 320]]
  const columns = [[214, 120], [336, 128], [209, 215], [350, 220], [219, 338], [350, 340]]
  return <g className="layoutSandbox-architecture" opacity={muted ? 0.28 : 1}>
    {boundary.map((point, index) => <polygon key={`slab-${index}`} points={points([plate[index], plate[(index + 1) % plate.length], bottom[(index + 1) % bottom.length], bottom[index]])} fill="url(#layoutSandbox-slab)" />)}
    <polygon points={points(plate)} fill="url(#layoutSandbox-floor)" stroke="rgba(111,137,140,.38)" strokeWidth="1.2" filter="url(#layoutSandbox-floorShadow)" />
    <polygon points={points(atrium.map(([x, y]) => iso(x, y, z + 1)))} fill="url(#layoutSandbox-atrium)" stroke="rgba(82,125,148,.35)" />
    {atrium.map((point, index) => {
      const next = atrium[(index + 1) % atrium.length]
      return <g key={`rail-${index}`}><polygon points={points([iso(point[0], point[1], z + 14), iso(next[0], next[1], z + 14), iso(next[0], next[1], z + 2), iso(point[0], point[1], z + 2)])} fill="url(#layoutSandbox-glassLight)" /><line x1={iso(point[0], point[1], z + 14).x} y1={iso(point[0], point[1], z + 14).y} x2={iso(next[0], next[1], z + 14).x} y2={iso(next[0], next[1], z + 14).y} stroke="rgba(94,115,121,.66)" strokeWidth="1.5" /></g>
    })}
    {columns.map(([x, y], index) => { const low = iso(x, y, z); const high = iso(x, y, z + 32); return <g key={`column-${index}`}><line x1={low.x} y1={low.y} x2={high.x} y2={high.y} stroke="url(#layoutSandbox-column)" strokeWidth="7" /><ellipse cx={high.x} cy={high.y} rx="4.5" ry="2.4" fill="#f8fbfa" /></g> })}
    <polygon points={points([[280, 250], [318, 254], [318, 314], [280, 318]].map(([x, y]) => iso(x, y, z + 35)))} fill="#f4f7f5" stroke="rgba(110,130,134,.35)" />
    <polygon points={points([iso(258, 190, z + 4), iso(308, 230, z + 25), iso(319, 221, z + 25), iso(269, 181, z + 4)])} fill="url(#layoutSandbox-escalator)" stroke="rgba(95,116,121,.5)" />
    <text x={iso(300, 286, z + 39).x} y={iso(300, 286, z + 39).y} textAnchor="middle" fill="#66747a" fontSize="8">电梯</text>
  </g>
}

function SandboxView({ data, selectedUnit, setSelectedUnit, colorMode, expanded, planOnly, highlightedCodes }) {
  const floors = data.floors || []
  const preferredFloor = floors.includes('L1') ? 'L1' : floors[0] || ''
  const [activeFloor, setActiveFloor] = React.useState(preferredFloor)
  React.useEffect(() => {
    if (!floors.includes(activeFloor)) setActiveFloor(preferredFloor)
  }, [activeFloor, floors, preferredFloor])
  React.useEffect(() => {
    if (selectedUnit?.floor) setActiveFloor(selectedUnit.floor)
  }, [selectedUnit])
  const formats = [...new Set(data.units.map((unit) => unit.format || '空置'))]
  const formatMap = Object.fromEntries(formats.map((item, index) => [item, item === '空置' ? STATUS_COLORS.空置 : FORMAT_COLORS[index % FORMAT_COLORS.length]]))
  const colorFor = (unit) => {
    if (colorMode === 'status') return STATUS_COLORS[unit.status] || STATUS_COLORS.空置
    if (colorMode === 'timing') {
      if (!unit.lease_end || unit.status === '空置') return '#d7834b'
      const year = Number(String(unit.lease_end).slice(0, 4))
      const currentYear = new Date().getFullYear()
      return year <= currentYear ? '#d7834b' : year === currentYear + 1 ? '#4f78d5' : '#87939a'
    }
    return formatMap[unit.format || '空置']
  }
  const legend = colorMode === 'status' ? STATUS_COLORS : colorMode === 'timing' ? { '今年可调/空置': '#d7834b', '明年可调': '#4f78d5', '长期锁定': '#87939a' } : formatMap
  const visibleFloors = expanded ? floors : [activeFloor]
  return <div className="layoutSandbox-stage">
    <div className="layoutSandbox-floorRail" aria-label="楼层选择">{[...floors].reverse().map((floor) => <button type="button" key={floor} aria-pressed={activeFloor === floor} onClick={() => setActiveFloor(floor)}>{floor}</button>)}</div>
    <svg viewBox="0 0 1000 660" role="img" aria-label="项目逐层铺位2.5D沙盘">
      <defs>
        {[...new Set([...Object.values(STATUS_COLORS), ...FORMAT_COLORS, '#d7834b', '#87939a'])].map((color) => <linearGradient key={color} id={`layoutSandbox-gradient-${safeId(color)}`} x1="0" y1="0" x2="1" y2="1"><stop offset="0" stopColor={shade(color, 54)} /><stop offset=".45" stopColor={shade(color, 18)} /><stop offset="1" stopColor={shade(color, -17)} /></linearGradient>)}
        <linearGradient id="layoutSandbox-floor" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stopColor="#fff" stopOpacity=".94" /><stop offset="1" stopColor="#dce5e1" stopOpacity=".86" /></linearGradient>
        <linearGradient id="layoutSandbox-slab" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#d3dcda" /><stop offset="1" stopColor="#a9b8b7" /></linearGradient>
        <linearGradient id="layoutSandbox-glass" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stopColor="#f3fdff" stopOpacity=".76" /><stop offset=".5" stopColor="#9fcbd4" stopOpacity=".28" /><stop offset="1" stopColor="#edfdfd" stopOpacity=".65" /></linearGradient>
        <linearGradient id="layoutSandbox-glassLight" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stopColor="#fff" stopOpacity=".72" /><stop offset="1" stopColor="#9fc7cf" stopOpacity=".26" /></linearGradient>
        <linearGradient id="layoutSandbox-column" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stopColor="#aebcbc" /><stop offset=".5" stopColor="#fbfdfc" /><stop offset="1" stopColor="#9eadae" /></linearGradient>
        <linearGradient id="layoutSandbox-escalator"><stop offset="0" stopColor="#65777b" /><stop offset=".5" stopColor="#dfe7e5" /><stop offset="1" stopColor="#829296" /></linearGradient>
        <linearGradient id="layoutSandbox-atrium"><stop offset="0" stopColor="#b9d8e1" stopOpacity=".4" /><stop offset="1" stopColor="#739caf" stopOpacity=".17" /></linearGradient>
        <filter id="layoutSandbox-shadow" x="-30%" y="-45%" width="170%" height="210%"><feDropShadow dx="2" dy="7" stdDeviation="5" floodColor="#5f6d70" floodOpacity=".27" /></filter>
        <filter id="layoutSandbox-floorShadow" x="-25%" y="-35%" width="160%" height="190%"><feDropShadow dx="3" dy="14" stdDeviation="13" floodColor="#657377" floodOpacity=".2" /></filter>
        <filter id="layoutSandbox-glow" x="-50%" y="-60%" width="200%" height="220%"><feGaussianBlur stdDeviation="5" /></filter>
      </defs>
      <ellipse cx="505" cy="505" rx="335" ry="42" fill="rgba(77,91,95,.13)" filter="url(#layoutSandbox-floorShadow)" />
      {visibleFloors.map((floor) => {
        const floorIndex = floors.indexOf(floor)
        const z = expanded ? floorIndex * 100 : 92
        const units = data.units.filter((unit) => unit.floor === floor)
        const footprints = makeFootprints(units.length)
        const muted = expanded && floor !== activeFloor
        return <g key={floor} opacity={muted ? 0.34 : 1}>
          <Architecture z={z} muted={muted} />
          {units.map((unit, index) => <UnitBrick key={unit.unit_id} unit={unit} footprint={footprints[index]} z={z} color={colorFor(unit)} selected={unit.unit_id === selectedUnit?.unit_id} dimmed={planOnly && !unit.plan || highlightedCodes.length > 0 && !highlightedCodes.includes(unit.unit_code)} onSelect={setSelectedUnit} />)}
          <text x={iso(25, 250, z + 4).x} y={iso(25, 250, z + 4).y} fill="#536168" fontSize="12" fontWeight="600">{floor}</text>
        </g>
      })}
    </svg>
    <div className="layoutSandbox-legend">{Object.entries(legend).map(([label, color]) => <span key={label}><i style={{ background: `linear-gradient(135deg, ${shade(color, 35)}, ${shade(color, -15)})` }} />{label}</span>)}<span><i className="plan" />有调改计划</span></div>
  </div>
}

function UnitDetail({ unit, onEdit }) {
  if (!unit) return <aside className="layoutSandbox-detail"><div className="layoutSandbox-emptyCompact">点击沙盘铺位查看详情</div></aside>
  const psm = unit.area ? number(unit.rent) / number(unit.area) : 0
  return <aside className="layoutSandbox-detail" aria-live="polite">
    <header><div><span>{unit.unit_code} · {unit.floor}</span><h3>{unit.tenant || '空置铺位'}</h3></div><em className={`status-${unit.status}`}>{unit.status}</em></header>
    <div className="layoutSandbox-detailGrid"><div><span>计租面积</span><strong>{number(unit.area).toLocaleString()}㎡</strong></div><div><span>当前业态</span><strong>{unit.format || '待招商'}</strong></div><div><span>月租金</span><strong>{unit.rent ? money(unit.rent) : '—'}</strong></div><div><span>租金坪效</span><strong>{psm ? `${psm.toFixed(0)}元/㎡` : '—'}</strong></div><div className="wide"><span>租约状态</span><strong>{unit.lease_end ? `锁定至 ${month(unit.lease_end)}` : unit.status === '空置' ? '可立即招商' : '未登记到期日'}</strong></div></div>
    {unit.plan && <div className="layoutSandbox-planSummary"><span>调改计划</span><strong>{unit.plan.action} → {unit.plan.to_format || '目标业态待定'}</strong><p>{unit.plan.plan_status || '草案'} · {unit.plan.plan_date || '时间待定'} · 预期 {money(unit.plan.expected_rent)}</p></div>}
    <button type="button" className="layoutSandbox-editButton" onClick={onEdit}><Edit3 size={15} />{unit.plan ? '编辑调改计划' : '建立调改计划'}</button>
  </aside>
}

function Measurement({ plan }) {
  const summary = plan?.summary
  if (!summary) return null
  const occupancyDelta = Math.abs(number(summary.delta?.occupancy_pts)) <= 1 ? number(summary.delta?.occupancy_pts) * 100 : number(summary.delta?.occupancy_pts)
  const rows = [
    ['出租率', percent(summary.current?.occupancy_rate), percent(summary.planned?.occupancy_rate), `${occupancyDelta >= 0 ? '+' : ''}${occupancyDelta.toFixed(1)}pts`],
    ['月租金', money(summary.current?.rent_total), money(summary.planned?.rent_total), `${number(summary.delta?.rent_total) >= 0 ? '+' : ''}${money(summary.delta?.rent_total)}`],
    ['租金坪效', `${number(summary.current?.rent_psm).toFixed(0)}元/㎡`, `${number(summary.planned?.rent_psm).toFixed(0)}元/㎡`, '联动测算'],
    ['NOI', money(summary.current?.noi), money(summary.planned?.noi), `${number(summary.delta?.noi) >= 0 ? '+' : ''}${money(summary.delta?.noi)}`],
  ]
  return <section className="layoutSandbox-measurement"><header><div><span>调改后测算</span><h3>经营结果联动</h3></div><small>月度成本 {money(summary.monthly_cost)}</small></header><div className="layoutSandbox-measureGrid">{rows.map(([label, current, planned, delta], index) => <div key={label}><span>{label}</span><strong>{current}</strong><ArrowRight size={14} /><strong>{planned}</strong><em className={String(delta).startsWith('-') ? 'negative' : index === 2 ? '' : 'positive'}>{delta}</em></div>)}</div></section>
}

function RoadmapView({ roadmap, onBatch, onOpportunity }) {
  if (!roadmap?.batches?.length && !roadmap?.expiry_windows?.length) return <div className="layoutSandbox-state"><Route size={28} /><strong>暂未生成调改路线图</strong><span>为铺位建立调改计划后，将按租约到期季度自动形成批次。</span></div>
  const batches = roadmap.batches || []
  const maxRent = Math.max(...batches.map((batch) => Math.abs(number(batch.cum_rent_delta))), 1)
  const chartPoints = batches.map((batch, index) => ({ x: 75 + index * (800 / Math.max(batches.length - 1, 1)), y: 165 - number(batch.cum_rent_delta) / maxRent * 105 }))
  return <div className="layoutSandbox-roadmap">
    <div className="layoutSandbox-roadmapIntro"><div><span>调改策略</span><strong>{roadmap.policy || '等到期自然调整'}</strong></div><p>按租约到期窗口分批实施，避免主动解约造成经营损失。</p></div>
    <div className="layoutSandbox-batches">{batches.map((batch) => <button type="button" key={batch.quarter} onClick={() => onBatch(batch)}><span>{batch.quarter}</span><strong>{batch.unit_count} 个铺位</strong><small>腾出 {number(batch.area_freed).toLocaleString()}㎡</small><em className={number(batch.rent_delta) < 0 ? 'negative' : ''}>{number(batch.rent_delta) >= 0 ? '+' : ''}{money(batch.rent_delta)}/月</em><ChevronRight size={15} /></button>)}</div>
    {batches.length > 0 && <div className="layoutSandbox-curve"><div className="layoutSandbox-curveTitle"><strong>累计增租曲线</strong><span>随季度调改批次逐步释放</span></div><svg viewBox="0 0 950 200" role="img" aria-label="累计增租季度趋势"><line x1="55" y1="170" x2="915" y2="170" stroke="rgba(90,105,112,.18)" /><path d={chartPoints.map((item, index) => `${index ? 'L' : 'M'} ${item.x} ${item.y}`).join(' ')} fill="none" stroke="var(--accent)" strokeWidth="3" />{chartPoints.map((item, index) => <g key={batches[index].quarter}><circle cx={item.x} cy={item.y} r="5" fill="var(--accent)" stroke="#fff" strokeWidth="2" /><text x={item.x} y="190" textAnchor="middle" fill="#6d777e" fontSize="11">{batches[index].quarter}</text><text x={item.x} y={item.y - 12} textAnchor="middle" fill="#475158" fontSize="10">{money(batches[index].cum_rent_delta)}</text></g>)}</svg></div>}
    <section className="layoutSandbox-expiry"><header><div><span>租约到期窗口</span><h3>未来可调机会</h3></div><small>点击未规划窗口可直接建立计划</small></header><div>{(roadmap.expiry_windows || []).map((window) => <button type="button" key={window.quarter} onClick={() => onOpportunity(window)}><CalendarDays size={17} /><span><strong>{window.quarter}</strong><small>{window.expiring_units} 个铺位 · {number(window.expiring_area).toLocaleString()}㎡</small></span><em>{window.planned ? '已规划' : '未来可调机会'}</em></button>)}</div></section>
  </div>
}

export default function ProjectLayoutSandbox({ projectName }) {
  const [projectId, setProjectId] = React.useState(null)
  const [layout, setLayout] = React.useState(null)
  const [plan, setPlan] = React.useState(null)
  const [roadmap, setRoadmap] = React.useState(null)
  const [loading, setLoading] = React.useState(true)
  const [error, setError] = React.useState('')
  const [view, setView] = React.useState('sandbox')
  const [colorMode, setColorMode] = React.useState('format')
  const [expanded, setExpanded] = React.useState(false)
  const [planOnly, setPlanOnly] = React.useState(false)
  const [selectedUnit, setSelectedUnit] = React.useState(null)
  const [editing, setEditing] = React.useState(false)
  const [initialDate, setInitialDate] = React.useState('')
  const [highlightedCodes, setHighlightedCodes] = React.useState([])

  const loadData = React.useCallback(async (knownId = projectId) => {
    if (!knownId) return
    const [layoutData, planData, roadmapData] = await Promise.all([
      getUnitLayout(knownId),
      getAdjustmentPlan(knownId),
      getAdjustmentRoadmap(knownId).catch(() => null),
    ])
    setLayout(layoutData)
    setPlan(planData)
    setRoadmap(roadmapData)
    setSelectedUnit((current) => layoutData.units.find((unit) => unit.unit_id === current?.unit_id) || layoutData.units.find((unit) => unit.floor === 'L1') || layoutData.units[0] || null)
  }, [projectId])

  React.useEffect(() => {
    let alive = true
    setLoading(true)
    setError('')
    resolveProjectIdByName(projectName).then(async (id) => {
      if (!alive) return
      if (!id) throw new Error('暂未在后端找到与该演示项目对应的真实档案。')
      setProjectId(id)
      await loadData(id)
    }).catch((requestError) => alive && setError(requestError.message || '暂时无法加载铺位数据')).finally(() => alive && setLoading(false))
    return () => { alive = false }
  }, [projectName])

  const onBatch = (batch) => {
    const codes = (batch.units || []).map((unit) => unit.unit_code)
    setHighlightedCodes(codes)
    const first = layout?.units.find((unit) => codes.includes(unit.unit_code))
    if (first) setSelectedUnit(first)
    setColorMode('timing')
    setView('sandbox')
  }

  const onOpportunity = (window) => {
    const candidates = layout?.units.filter((unit) => unit.lease_end && `${new Date(unit.lease_end).getFullYear()}Q${Math.floor(new Date(unit.lease_end).getMonth() / 3) + 1}` === window.quarter && !unit.plan) || []
    if (!candidates.length) return
    setSelectedUnit(candidates[0])
    setInitialDate(quarterStart(window.quarter))
    setEditing(true)
    setView('sandbox')
  }

  if (loading) return <div className="layoutSandbox-state"><LoaderCircle className="spin" size={30} /><strong>正在载入项目铺位沙盘</strong><span>同步铺位、调改测算与租约路线图…</span></div>
  if (error) return <div className="layoutSandbox-state error"><AlertCircle size={30} /><strong>铺位数据暂未连接</strong><span>{error}</span><button type="button" onClick={() => window.location.reload()}><RefreshCw size={15} />重新加载</button></div>
  if (!layout?.units?.length) return <div className="layoutSandbox-state"><Store size={30} /><strong>该项目暂无铺位数据</strong><span>铺位导入后会在这里自动生成逐层沙盘。</span></div>

  const occupied = layout.units.filter((unit) => ['在租', '自营'].includes(unit.status)).length
  const rent = layout.units.reduce((sum, unit) => sum + number(unit.rent), 0)
  const planCount = layout.units.filter((unit) => unit.plan).length
  return <section className="layoutSandbox-root">
    <div className="layoutSandbox-metrics">
      <Metric label="综合出租率" value={percent(occupied / layout.units.length * 100)} meta={`${occupied}/${layout.units.length} 个铺位已招商`} icon={Store} tone="green" />
      <Metric label="当前月租金" value={money(rent)} meta="按有效铺位租金汇总" icon={Building2} tone="blue" />
      <Metric label="调改计划" value={`${planCount}项`} meta={roadmap?.summary?.first_quarter ? `${roadmap.summary.first_quarter} 起实施` : '等待批次规划'} icon={Route} tone="orange" />
    </div>
    <div className="layoutSandbox-topbar">
      <div className="layoutSandbox-viewTabs" role="tablist" aria-label="沙盘子视图"><button type="button" role="tab" aria-selected={view === 'sandbox'} onClick={() => setView('sandbox')}><MapPinned size={16} />铺位沙盘</button><button type="button" role="tab" aria-selected={view === 'roadmap'} onClick={() => setView('roadmap')}><Route size={16} />调改路线图</button></div>
      {view === 'sandbox' && <div className="layoutSandbox-controls"><label><span>着色</span><select value={colorMode} onChange={(event) => { setColorMode(event.target.value); setHighlightedCodes([]) }}><option value="format">按业态</option><option value="status">按状态</option><option value="timing">按可调时点</option></select></label><button type="button" aria-pressed={expanded} onClick={() => setExpanded(!expanded)}><Layers3 size={15} />{expanded ? '收拢楼层' : '展开楼层'}</button><button type="button" aria-pressed={planOnly} onClick={() => setPlanOnly(!planOnly)}>只看调改计划</button>{highlightedCodes.length > 0 && <button type="button" onClick={() => setHighlightedCodes([])}><X size={14} />清除批次高亮</button>}</div>}
    </div>
    {view === 'sandbox' ? <>
      <div className="layoutSandbox-canvasRow"><SandboxView data={layout} selectedUnit={selectedUnit} setSelectedUnit={setSelectedUnit} colorMode={colorMode} expanded={expanded} planOnly={planOnly} highlightedCodes={highlightedCodes} /><UnitDetail unit={selectedUnit} onEdit={() => { setInitialDate(''); setEditing(true) }} /></div>
      <div className="layoutSandbox-unitList"><header><div><span>铺位清单</span><h3>按楼层快速定位</h3></div><small>{layout.units.length} 个真实铺位</small></header><div>{layout.floors.map((floor) => <section key={floor}><strong>{floor}</strong><div>{layout.units.filter((unit) => unit.floor === floor).map((unit) => <button type="button" key={unit.unit_id} aria-pressed={selectedUnit?.unit_id === unit.unit_id} onClick={() => setSelectedUnit(unit)}><i style={{ background: STATUS_COLORS[unit.status] || STATUS_COLORS.空置 }} /><span>{unit.unit_code}</span><small>{unit.tenant || '空置'}</small>{unit.plan && <em />}</button>)}</div></section>)}</div></div>
      <Measurement plan={plan} />
    </> : <RoadmapView roadmap={roadmap} onBatch={onBatch} onOpportunity={onOpportunity} />}
    {editing && selectedUnit && <PlanEditor unit={selectedUnit} projectId={projectId} initialDate={initialDate} onClose={() => setEditing(false)} onChanged={() => loadData(projectId)} />}
  </section>
}
