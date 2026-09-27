// 后端 API 客户端：自动登录取 token，映射成前端组件所需的数据形状。
// vite 已把 /api 代理到 http://127.0.0.1:8000，故默认用相对路径。
const BASE = import.meta.env.VITE_API_BASE || ''
let token = null

async function login() {
  const body = new URLSearchParams({ username: 'admin', password: 'admin123' })
  const res = await fetch(`${BASE}/api/v1/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body,
  })
  if (!res.ok) throw new Error(`登录失败 ${res.status}`)
  token = (await res.json()).access_token
  return token
}

async function apiGet(path) {
  if (!token) await login()
  const call = () => fetch(`${BASE}/api/v1${path}`, { headers: { Authorization: `Bearer ${token}` } })
  let res = await call()
  if (res.status === 401) {
    await login()
    res = await call()
  }
  if (!res.ok) throw new Error(`请求失败 ${res.status}: ${path}`)
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
    matches: 0,
    next: '待补充下一步任务',
    owner: p.operator || '新盛公司',
  }))
}

export async function getBrands() {
  const rows = await apiGet('/brands')
  return rows.map((b) => ({
    code: b.brand_code,
    name: b.brand_name,
    category: b.l1_category || '—',
    grade: b.grade || '—',
    intent: b.cooperation_intent || '—',
    stores: b.store_count || 0,
    cities: b.hq_city || '—',
    area: '—',
    tags: (b.tags || '').split(';').filter(Boolean),
  }))
}

export async function getOperations(period) {
  const query = period ? `?period=${encodeURIComponent(period)}` : ''
  return apiGet(`/dashboard/operations${query}`)
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

async function apiWrite(path, method, payload) {
  if (!token) await login()
  const call = () => fetch(`${BASE}/api/v1${path}`, {
    method,
    headers: {
      Authorization: `Bearer ${token}`,
      ...(payload ? { 'Content-Type': 'application/json' } : {}),
    },
    ...(payload ? { body: JSON.stringify(payload) } : {}),
  })
  let res = await call()
  if (res.status === 401) {
    await login()
    res = await call()
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

export function putAdjustmentPlan(id, unitId, body) {
  return apiWrite(`/projects/${id}/adjustment-plan/${unitId}`, 'PUT', body)
}

export function deleteAdjustmentPlan(id, unitId) {
  return apiWrite(`/projects/${id}/adjustment-plan/${unitId}`, 'DELETE')
}

// 项目名 → 后端真实 id（前端项目卡列表仍是演示数据时用于对接台账）
export async function resolveProjectIdByName(name) {
  const norm = (s) => (s || '').replace(/\s+/g, '')
  const rows = await getProjects()
  const hit = rows.find((p) => norm(p.name) === norm(name))
  return hit ? hit.id : null
}
