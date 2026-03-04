import React, { useEffect, useMemo, useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { apiJson } from '../lib/api'

const formatArea = (value) => {
  if (value === null || value === undefined || value === '') return '-'
  const num = Number(value)
  if (Number.isNaN(num)) return '-'
  return `${new Intl.NumberFormat('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(num)} ㎡`
}

const formatDate = (value) => {
  if (!value) return '-'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString('zh-CN')
}

export default function Projects() {
  const [projects, setProjects] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')
  const [confirmed, setConfirmed] = useState('all')
  const [level, setLevel] = useState('all')
  const [toast, setToast] = useState('')
  const location = useLocation()
  const navigate = useNavigate()

  const loadProjects = async () => {
    setLoading(true)
    setError('')
    try {
      const data = await apiJson('/api/projects')
      if (Array.isArray(data)) {
        setProjects(data)
      } else if (data && Array.isArray(data.items)) {
        setProjects(data.items)
      } else {
        setProjects([])
      }
    } catch (err) {
      setError(err.message)
      setProjects([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadProjects()
  }, [])

  useEffect(() => {
    if (location.search.includes('created=1')) {
      setToast('项目创建成功')
      const timer = setTimeout(() => setToast(''), 2000)
      navigate('/projects', { replace: true })
      return () => clearTimeout(timer)
    }
    return undefined
  }, [location.search, navigate])

  const hasLevel = useMemo(
    () => projects.some((project) => project.project_level),
    [projects]
  )

  useEffect(() => {
    if (!hasLevel && level !== 'all') {
      setLevel('all')
    }
  }, [hasLevel, level])

  const filtered = useMemo(() => {
    const keyword = search.trim().toLowerCase()
    return projects.filter((project) => {
      const matchesSearch =
        !keyword ||
        project.project_name?.toLowerCase().includes(keyword) ||
        project.city?.toLowerCase().includes(keyword) ||
        project.district?.toLowerCase().includes(keyword)

      const matchesConfirmed =
        confirmed === 'all'
          ? true
          : confirmed === 'confirmed'
          ? project.is_confirmed === 1
          : project.is_confirmed !== 1

      const projectLevel = project.project_level
      const matchesLevel =
        level === 'all' ? true : projectLevel ? projectLevel === level : false

      return matchesSearch && matchesConfirmed && matchesLevel
    })
  }, [projects, search, confirmed, level])

  const clearFilters = () => {
    setSearch('')
    setConfirmed('all')
    setLevel('all')
  }

  return (
    <div>
      {toast && <div className="toast">{toast}</div>}
      <div className="page-header">
        <div>
          <h1 className="page-title">项目</h1>
          <div className="page-subtitle">管理项目、查看等级、进入筛选与测算</div>
        </div>
        <div className="page-actions">
          <Link className="button" to="/projects/new">
            新建项目
          </Link>
        </div>
      </div>

      <div className="card toolbar">
        <div className="toolbar-left">
          <input
            className="input"
            placeholder="搜索项目名称/城市/区域"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          <select className="select" value={confirmed} onChange={(e) => setConfirmed(e.target.value)}>
            <option value="all">确认状态（全部）</option>
            <option value="confirmed">已确认</option>
            <option value="unconfirmed">未确认</option>
          </select>
          <select
            className="select"
            value={level}
            onChange={(e) => setLevel(e.target.value)}
            disabled={!hasLevel}
          >
            <option value="all">项目等级（全部）</option>
            <option value="核心型">核心型</option>
            <option value="成熟型">成熟型</option>
            <option value="基础型">基础型</option>
          </select>
        </div>
        <div className="toolbar-right">
          <button className="button secondary" onClick={clearFilters}>
            清空筛选
          </button>
        </div>
      </div>

      {error && <div className="notice">{error}</div>}

      <div className="card">
        <table className="table">
          <thead>
            <tr>
              <th>项目名称</th>
              <th>城市区</th>
              <th>面积</th>
              <th>确认状态</th>
              <th>等级</th>
              <th>更新时间</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            {loading && (
              <>
                {[1, 2, 3].map((row) => (
                  <tr key={`skeleton-${row}`}>
                    <td>
                      <div className="skeleton line" />
                    </td>
                    <td>
                      <div className="skeleton short" />
                    </td>
                    <td>
                      <div className="skeleton short" />
                    </td>
                    <td>
                      <div className="skeleton short" />
                    </td>
                    <td>
                      <div className="skeleton short" />
                    </td>
                    <td>
                      <div className="skeleton short" />
                    </td>
                    <td>
                      <div className="skeleton short" />
                    </td>
                  </tr>
                ))}
              </>
            )}

            {!loading && filtered.length === 0 && (
              <tr>
                <td colSpan="7">
                  <div className="empty-state">
                    <div className="empty-icon">＋</div>
                    <div>暂无项目</div>
                    <div style={{ marginTop: 12 }}>
                      <Link className="button" to="/projects/new">
                        新建项目
                      </Link>
                    </div>
                  </div>
                </td>
              </tr>
            )}

            {!loading &&
              filtered.map((project) => {
                const updated = project.updated_at || project.created_at
                const projectLevel = project.project_level || '未计算'
                return (
                  <tr
                    key={project.project_id}
                    className="table-row"
                    onClick={() => navigate(`/projects/${project.project_id}`)}
                  >
                    <td>
                      <Link to={`/projects/${project.project_id}`}>{project.project_name}</Link>
                    </td>
                    <td>
                      {project.city}
                      {project.district ? ` · ${project.district}` : ''}
                    </td>
                    <td>{formatArea(project.total_area)}</td>
                    <td>
                      <span
                        className={`tag ${
                          project.is_confirmed === 1 ? 'confirmed' : 'unconfirmed'
                        }`}
                      >
                        {project.is_confirmed === 1 ? '已确认' : '未确认'}
                      </span>
                    </td>
                    <td>
                      <span className={`tag ${projectLevel === '未计算' ? 'muted' : 'primary'}`}>
                        {projectLevel}
                      </span>
                    </td>
                    <td>{formatDate(updated)}</td>
                    <td>
                      <Link
                        className="button secondary"
                        to={`/projects/${project.project_id}`}
                        onClick={(e) => e.stopPropagation()}
                      >
                        进入
                      </Link>
                    </td>
                  </tr>
                )
              })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
