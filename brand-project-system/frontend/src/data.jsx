// 全局数据上下文：真实登录态 + 挂载后拉真实后端数据。
// 未登录 → 渲染登录页；登录后 → 拉 projects/brands/operations/risk-alerts，
// 并把「经营台账」的真实出租率/收入/成本/收缴率合并进 projects，供各页面直接展示。
import React from 'react'
import {
  fmtPct, fmtWan, getBrands, getMe, getOperations, getProjects, getRiskAlerts,
  hasToken, loginWithCredentials, logout as apiLogout,
} from './api'
import LoginPage from './LoginPage'

const AppDataContext = React.createContext(null)

// 用后端「经营台账」的真实口径覆盖项目的出租率/收入/成本/收缴率——
// 找不到台账数据的项目显示"—"，绝不编造数字。
function mergeOperationsIntoProjects(projects, ops) {
  if (!ops) return projects
  const byId = Object.fromEntries(ops.projects.map((r) => [r.project_id, r]))
  return projects.map((p) => {
    const row = byId[p.id]
    if (!row) return p
    return {
      ...p,
      occupancy: fmtPct(row.occupancy_rate),
      revenue: fmtWan(row.revenue_received),
      cost: fmtWan(row.cost),
      collection: fmtPct(row.collect_rate),
      noi: row.noi,
      arrears: row.arrears,
    }
  })
}

const EMPTY_DATA = { projects: [], brands: [], ops: null, risk: null }

export function AppDataProvider({ children }) {
  // checking：正在核对本地 token；anon：未登录；authed：已登录
  const [authStatus, setAuthStatus] = React.useState('checking')
  const [user, setUser] = React.useState(null)
  const [data, setData] = React.useState(EMPTY_DATA)

  const loadAppData = React.useCallback(async () => {
    const [projects, brands, ops, risk] = await Promise.all([
      getProjects(), getBrands(),
      getOperations().catch(() => null),
      getRiskAlerts().catch(() => null),
    ])
    setData({ projects: mergeOperationsIntoProjects(projects, ops), brands, ops, risk })
  }, [])

  React.useEffect(() => {
    let alive = true
    if (!hasToken()) { setAuthStatus('anon'); return }
    getMe().then((me) => {
      if (!alive) return
      setUser(me)
      setAuthStatus('authed')
      return loadAppData()
    }).catch(() => { if (alive) setAuthStatus('anon') })
    return () => { alive = false }
  }, [loadAppData])

  const login = React.useCallback(async (username, password) => {
    await loginWithCredentials(username, password)   // 失败会抛错，交给 LoginPage 展示
    const me = await getMe()
    setUser(me)
    setAuthStatus('authed')
    await loadAppData()
  }, [loadAppData])

  const logout = React.useCallback(() => {
    apiLogout()
    setUser(null)
    setData(EMPTY_DATA)
    setAuthStatus('anon')
  }, [])

  // 是否拥有某权限点；admin 主角色直通（与后端 user_has_permission 口径一致）。
  const can = React.useCallback((perm) => {
    if (!user) return false
    if (user.role === 'admin') return true
    return (user.permissions || []).includes(perm)
  }, [user])

  if (authStatus === 'checking') return null
  if (authStatus === 'anon') return <LoginPage onLogin={login} />

  const value = { ...data, user, can, logout, refresh: loadAppData }
  return <AppDataContext.Provider value={value}>{children}</AppDataContext.Provider>
}

export function useAppData() {
  return React.useContext(AppDataContext)
}
