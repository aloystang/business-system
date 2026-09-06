// 全局数据上下文：挂载时拉真实后端数据，替换写死的演示数据。
// 加载中/失败时用 fallback（原演示数据）兜底，保证页面永远不空。
import React from 'react'
import { getBrands, getOperations, getProjects } from './api'

const AppDataContext = React.createContext(null)

export function AppDataProvider({ fallback, children }) {
  const [data, setData] = React.useState({ ...fallback, ops: null, live: false })

  React.useEffect(() => {
    let alive = true
    Promise.all([getProjects(), getBrands(), getOperations().catch(() => null)])
      .then(([projects, brands, ops]) => {
        if (!alive) return
        setData((prev) => ({
          projects: projects.length ? projects : prev.projects,
          brands: brands.length ? brands : prev.brands,
          ops,
          live: true,
        }))
      })
      .catch(() => { /* 后端未启动时静默保留演示数据 */ })
    return () => { alive = false }
  }, [])

  return <AppDataContext.Provider value={data}>{children}</AppDataContext.Provider>
}

export function useAppData() {
  return React.useContext(AppDataContext)
}
