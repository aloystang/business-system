// 后端 API 客户端：真实登录（无自动免密），token 存 sessionStorage（关闭标签页即清除，
// 比 localStorage 更收敛；生产上更稳妥的做法是后端签发 httpOnly cookie，此处先用这个折中方案）。
// vite 已把 /api 代理到 http://127.0.0.1:8000，故默认用相对路径。
const BASE = import.meta.env.VITE_API_BASE || ''
const TOKEN_KEY = 'xs_bpr_token'

let token = null
try { token = sessionStorage.getItem(TOKEN_KEY) } catch { /* 隐私模式下可能不可用 */ }

export function hasToken() {
  return !!token
}

export function setToken(t) {
  token = t
  try { sessionStorage.setItem(TOKEN_KEY, t) } catch { /* 忽略存储失败，仍可用内存态 */ }
}

export function clearToken() {
  token = null
  try { sessionStorage.removeItem(TOKEN_KEY) } catch { /* 忽略 */ }
}

// 用户名+密码登录，失败抛错（凭据错误/登录过于频繁等），调用方负责展示错误信息。
export async function loginWithCredentials(username, password) {
  const body = new URLSearchParams({ username, password })
  const res = await fetch(`${BASE}/api/v1/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body,
  })
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}))
    throw new Error(detail.detail || (res.status === 429 ? '登录失败次数过多，请稍后再试' : '用户名或密码错误'))
  }
  const { access_token } = await res.json()
  setToken(access_token)
  return access_token
}

export function logout() {
  clearToken()
}

// 当前登录用户 + 角色中文名 + 实际权限点列表（供界面按权限显隐/禁用控件）。
export async function getMe() {
  return apiGet('/auth/me')
}

class AuthRequiredError extends Error {
  constructor() {
    super('未登录')
    this.name = 'AuthRequiredError'
  }
}

async function apiGet(path) {
  if (!token) throw new AuthRequiredError()
  const res = await fetch(`${BASE}/api/v1${path}`, { headers: { Authorization: `Bearer ${token}` } })
  if (res.status === 401) {
    clearToken()
    throw new AuthRequiredError()
  }
  if (!res.ok) throw new Error(`请求失败 ${res.status}: ${path}`)
  return res.json()
}

async function apiWrite(path, method, payload) {
  if (!token) throw new AuthRequiredError()
  const res = await fetch(`${BASE}/api/v1${path}`, {
    method,
    headers: {
      Authorization: `Bearer ${token}`,
      ...(payload ? { 'Content-Type': 'application/json' } : {}),
    },
    ...(payload ? { body: JSON.stringify(payload) } : {}),
  })
  if (res.status === 401) {
    clearToken()
    throw new AuthRequiredError()
  }
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}))
    const error = new Error(detail.detail || `请求失败 ${res.status}: ${path}`)
    error.status = res.status
    throw error
  }
  if (res.status === 204) return null
  return res.json()
}

// 经纬度 → 回退示意图的百分比坐标（真实高德地图用 lng/lat，此处仅供地图未加载时的示意视图）
const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v))
const lngToX = (lng) => clamp((lng - 106.45) / (106.85 - 106.45) * 80 + 10, 4, 96)
const latToY = (lat) => clamp((29.80 - lat) / (29.80 - 29.54) * 72 + 14, 6, 94)

function fmtArea(m2) {
  if (!m2) return '—'
  return m2 >= 10000 ? `${(m2 / 10000).toFixed(1)}万㎡` : `${Math.round(m2)}㎡`
}

export function fmtWan(yuan) {
  if (yuan == null) return '—'
  return `${(yuan / 10000).toFixed(1)}万元`
}

export function fmtPct(ratio) {
  if (ratio == null) return '—'
  return `${(ratio * 100).toFixed(1)}%`
}

export function fmtAreaWan(m2) {
  if (!m2) return '—'
  return m2 >= 10000 ? `${(m2 / 10000).toFixed(1)}万㎡` : `${Math.round(m2)}㎡`
}

export async function getProjects() {
  const rows = await apiGet('/projects')
  return rows.map((p) => ({
    id: p.id,
    name: p.project_name,
    type: p.project_type,
    status: p.project_status,
    grade: p.grade || '—',
    lng: p.location?.longitude,
    lat: p.location?.latitude,
    x: p.location?.longitude != null ? lngToX(p.location.longitude) : 50,
    y: p.location?.latitude != null ? latToY(p.location.latitude) : 50,
    area: fmtArea(p.business_area_m2),
    areaM2: p.business_area_m2 || 0,
    matches: 0,
    next: '待补充下一步任务',
    owner: p.operator || '新盛公司',
    // 经营指标先给合理占位（后端未返回经营数据时），真实值由 data.jsx 用
    // /dashboard/operations 逐项目联查后覆盖——不在此处编造。
    occupancy: '—', revenue: '—', cost: '—', collection: '—',
  }))
}

function engineeringText(powerKw, needsGas) {
  const parts = []
  if (powerKw) parts.push(`电量${powerKw}kW`)
  parts.push(needsGas ? '需燃气' : '无需燃气')
  return parts.join('·') || '—'
}

export async function getBrands() {
  const rows = await apiGet('/brands')
  return rows.map((b) => ({
    code: b.brand_code,
    name: b.brand_name,
    category: [b.l1_category, b.l2_category].filter(Boolean).join(' · ') || '—',
    level1: b.l1_category || '—',
    level2: b.l2_category || '—',
    level3: b.l3_category || '—',
    grade: b.grade || '—',
    intent: b.cooperation_intent || '—',
    stores: b.store_count || 0,
    cities: b.hq_city || '—',
    area: (b.area_min != null && b.area_max != null) ? `${b.area_min}-${b.area_max}㎡` : '—',
    engineering: engineeringText(b.power_req_kw, b.needs_gas),
    property: b.property_preference || '待补充',
    opening: b.opening_plan || '待补充',
    tags: (b.tags || '').split(';').filter(Boolean),
  }))
}

export async function getOperations(period) {
  const query = period ? `?period=${encodeURIComponent(period)}` : ''
  return apiGet(`/dashboard/operations${query}`)
}

// 跨项目运营风险：欠租 Top / 近期到期租约 / 空置 Top
export async function getRiskAlerts(expiringDays) {
  const query = expiringDays ? `?expiring_days=${expiringDays}` : ''
  return apiGet(`/dashboard/risk-alerts${query}`)
}

// 单项目经营台账（出租率/收入/成本/NOI/收缴/欠租/坪效/到期）
export async function getProjectOperations(id, period) {
  const query = period ? `?period=${encodeURIComponent(period)}` : ''
  return apiGet(`/projects/${id}/operations${query}`)
}

// 业态与调改：现有业态构成 + 逐铺位调改计划及测算
export async function getTenantMix(id) {
  return apiGet(`/projects/${id}/tenant-mix`)
}

export async function getAdjustmentPlan(id) {
  return apiGet(`/projects/${id}/adjustment-plan`)
}

export async function getUnitLayout(id) {
  return apiGet(`/projects/${id}/unit-layout`)
}

export async function getAdjustmentRoadmap(id) {
  return apiGet(`/projects/${id}/adjustment-roadmap`)
}

export async function getEarlySwapTradeoff(id, unitId, params = {}) {
  const qs = new URLSearchParams(params).toString()
  return apiGet(`/projects/${id}/adjustment-plan/${unitId}/early-swap-tradeoff${qs ? `?${qs}` : ''}`)
}

export function putAdjustmentPlan(id, unitId, body) {
  return apiWrite(`/projects/${id}/adjustment-plan/${unitId}`, 'PUT', body)
}

export function deleteAdjustmentPlan(id, unitId) {
  return apiWrite(`/projects/${id}/adjustment-plan/${unitId}`, 'DELETE')
}

// 合同租赁台账（用于「管理中心 · 合同租赁」）：联查项目/商户/铺位拼成可直接渲染的行。
export async function getLeasesEnriched() {
  const [leases, projects, merchants, units] = await Promise.all([
    apiGet('/leases'), apiGet('/projects'), apiGet('/merchants'), apiGet('/units'),
  ])
  const projectById = Object.fromEntries(projects.map((p) => [p.id, p.project_name]))
  const merchantById = Object.fromEntries(merchants.map((m) => [m.id, m.name]))
  const unitById = Object.fromEntries(units.map((u) => [u.id, u]))
  return leases.map((l) => {
    const unit = unitById[l.unit_id]
    return {
      id: l.id, no: l.contract_no || l.lease_code,
      project: projectById[l.project_id] || '—',
      tenant: merchantById[l.merchant_id] || '—',
      area: unit ? `${unit.rentable_area_m2 || 0}㎡` : '—',
      rent: l.base_rent ? `${Math.round(l.base_rent / (unit?.rentable_area_m2 || 1))}元/㎡/月` : '—',
      term: [l.start_date, l.end_date].filter(Boolean).join(' ~ ') || '—',
      status: l.lease_status,
      endDate: l.end_date,
    }
  })
}

// 闭环任务（用于「管理中心 · 闭环管理」）：联查项目名拼成可直接渲染的行。
export async function getTasksEnriched() {
  const [tasks, projects] = await Promise.all([apiGet('/tasks'), apiGet('/projects')])
  const projectById = Object.fromEntries(projects.map((p) => [p.id, p.project_name]))
  return tasks.map((t) => ({
    id: t.id, title: t.title, status: t.status, priority: t.priority || '中',
    projectId: t.project_id, project: projectById[t.project_id] || '—',
    due: t.plan_date || '—', detail: t.detail || '',
  }))
}

export function createTask(body) {
  return apiWrite('/tasks', 'POST', body)
}

export function updateTaskStatus(id, status) {
  return apiWrite(`/tasks/${id}`, 'PATCH', { status })
}

// 项目名 → 后端真实 id（仍有极少数页面用名称对接，找不到时调用方应自行兜底）
export async function resolveProjectIdByName(name) {
  const norm = (s) => (s || '').replace(/\s+/g, '')
  const rows = await getProjects()
  const hit = rows.find((p) => norm(p.name) === norm(name))
  return hit ? hit.id : null
}
