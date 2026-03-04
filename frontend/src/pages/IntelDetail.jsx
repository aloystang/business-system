import React, { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import DashboardLayout from '../components/DashboardLayout'
import { apiJson } from '../lib/api'

export default function IntelDetail() {
  const { itemId } = useParams()
  const navigate = useNavigate()
  const [detail, setDetail] = useState(null)
  const [projects, setProjects] = useState([])
  const [selectedProjectId, setSelectedProjectId] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const load = async () => {
    setLoading(true)
    setError('')
    try {
      const [detailResp, projectResp] = await Promise.all([
        apiJson(`/api/intel/items/${itemId}`),
        apiJson('/api/projects'),
      ])
      setDetail(detailResp)
      setProjects(projectResp || [])
    } catch (err) {
      setError(err.message || '加载详情失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [itemId])

  const linkProject = async () => {
    if (!selectedProjectId) {
      setError('请选择项目')
      return
    }
    try {
      await apiJson(`/api/intel/items/${itemId}/link-project`, {
        method: 'POST',
        body: JSON.stringify({ project_id: selectedProjectId, link_type: 'manual' }),
      })
      await load()
      setSelectedProjectId('')
    } catch (err) {
      setError(err.message || '关联项目失败')
    }
  }

  const setFollowUp = async (status) => {
    try {
      await apiJson(`/api/intel/items/${itemId}/follow-up`, {
        method: 'POST',
        body: JSON.stringify({ status }),
      })
      await load()
    } catch (err) {
      setError(err.message || '更新待办失败')
    }
  }

  return (
    <DashboardLayout title="情报详情" overline="INTELLIGENCE">
      <section className="dash-form-page">
        <div className="dash-card">
          <div className="dash-history-actions">
            <button type="button" className="dash-btn secondary" onClick={() => navigate('/intel')}>
              返回情报中心
            </button>
          </div>
        </div>
        {error ? <div className="dash-card alert">{error}</div> : null}
        {loading ? <div className="dash-card">加载中...</div> : null}

        {!loading && detail ? (
          <>
            <div className="dash-card">
              <div className="dash-card-header">
                <strong className="dash-section-title">
                  <span className="material-symbols-outlined">article</span>
                  {detail.title}
                </strong>
                <span className="dash-pill warning">
                  {detail.item_type === 'tender' ? '招投标' : '新闻'}
                </span>
              </div>
              <div className="dash-fields">
                <div className="dash-field">
                  <span>来源</span>
                  <strong>{detail.source_name || '-'}</strong>
                </div>
                <div className="dash-field">
                  <span>发布时间</span>
                  <strong>{detail.published_at || '-'}</strong>
                </div>
                <div className="dash-field">
                  <span>区域</span>
                  <strong>{[detail.city, detail.district].filter(Boolean).join(' · ') || '-'}</strong>
                </div>
                <div className="dash-field">
                  <span>发布方</span>
                  <strong>{detail.issuer || '-'}</strong>
                </div>
                <div className="dash-field">
                  <span>预算金额</span>
                  <strong>{detail.budget_amount ?? '-'}</strong>
                </div>
                <div className="dash-field">
                  <span>截止时间</span>
                  <strong>{detail.deadline_at || '-'}</strong>
                </div>
                <div className="dash-field span-4">
                  <span>摘要</span>
                  <p className="dash-subtext">{detail.summary || '-'}</p>
                </div>
              </div>
              <div className="dash-history-actions">
                {detail.raw_url ? (
                  <a className="dash-btn secondary" href={detail.raw_url} target="_blank" rel="noreferrer">
                    打开原文
                  </a>
                ) : null}
                <button type="button" className="dash-btn secondary" onClick={() => setFollowUp('pending')}>
                  标记待跟进
                </button>
                <button type="button" className="dash-btn secondary" onClick={() => setFollowUp('done')}>
                  标记已完成
                </button>
                <button type="button" className="dash-btn secondary" onClick={() => setFollowUp('ignored')}>
                  忽略
                </button>
              </div>
            </div>

            <div className="dash-card">
              <div className="dash-card-header">
                <strong className="dash-section-title">项目关联</strong>
              </div>
              <div className="dash-history-actions">
                <select value={selectedProjectId} onChange={(event) => setSelectedProjectId(event.target.value)}>
                  <option value="">选择项目</option>
                  {projects.map((project) => (
                    <option key={project.project_id} value={project.project_id}>
                      {project.project_name}
                    </option>
                  ))}
                </select>
                <button type="button" className="dash-btn primary" onClick={linkProject}>
                  关联项目
                </button>
              </div>
              <table className="table">
                <thead>
                  <tr>
                    <th>项目ID</th>
                    <th>项目名称</th>
                    <th>关联方式</th>
                    <th>关联时间</th>
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody>
                  {(detail.linked_projects || []).length === 0 ? (
                    <tr>
                      <td colSpan={5}>暂无关联项目</td>
                    </tr>
                  ) : (
                    detail.linked_projects.map((link) => (
                      <tr key={`${link.project_id}-${link.link_type}`}>
                        <td>{link.project_id}</td>
                        <td>{link.project_name || '-'}</td>
                        <td>{link.link_type}</td>
                        <td>{link.linked_at || '-'}</td>
                        <td>
                          <Link className="dash-btn secondary" to={`/projects/${link.project_id}`}>
                            打开项目
                          </Link>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </>
        ) : null}
      </section>
    </DashboardLayout>
  )
}
