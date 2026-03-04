import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import DashboardLayout from '../components/DashboardLayout'
import IntelSubnav from '../components/intel/IntelSubnav'
import { apiJson } from '../lib/api'

export default function IntelSync() {
  const navigate = useNavigate()
  const [jobs, setJobs] = useState([])
  const [loading, setLoading] = useState(false)
  const [running, setRunning] = useState(false)
  const [error, setError] = useState('')
  const [itemType, setItemType] = useState('all')

  const load = async () => {
    setLoading(true)
    setError('')
    try {
      const data = await apiJson('/api/intel/sync/jobs?limit=50')
      setJobs(data || [])
    } catch (err) {
      setError(err.message || '加载同步作业失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  const runSync = async () => {
    setRunning(true)
    setError('')
    try {
      await apiJson('/api/intel/sync/run', {
        method: 'POST',
        body: JSON.stringify({ item_type: itemType }),
      })
      await load()
    } catch (err) {
      setError(err.message || '执行同步失败')
    } finally {
      setRunning(false)
    }
  }

  return (
    <DashboardLayout title="同步作业" overline="INTELLIGENCE">
      <section className="dash-form-page">
        <IntelSubnav />
        <div className="dash-card dash-card-secondary dash-page-intro dash-page-intro--compact">
          <div className="dash-module-header">
            <div>
              <h2>同步作业台</h2>
              <p className="dash-module-desc">查看情报同步执行历史，并支持按新闻或招投标手动触发同步。</p>
            </div>
            <div className="dash-collect-statuses">
              <span className="dash-status merchant">最近作业 {jobs.length}</span>
              <span className="dash-status competitor">{running ? '同步中' : '待触发'}</span>
            </div>
          </div>
          <div className="dash-page-intro-grid">
            <article className="dash-page-intro-metric">
              <span>同步模式</span>
              <strong>{itemType === 'all' ? '全部' : itemType === 'news' ? '新闻' : '招投标'}</strong>
              <small>支持按类型执行手动刷新。</small>
            </article>
            <article className="dash-page-intro-metric">
              <span>当前状态</span>
              <strong>{running ? '运行中' : '待命'}</strong>
              <small>同步失败不会影响历史数据浏览。</small>
            </article>
            <article className="dash-page-intro-metric">
              <span>历史记录</span>
              <strong>{jobs.length}</strong>
              <small>最近 50 条作业执行历史。</small>
            </article>
          </div>
        </div>
        <div className="dash-card dash-page-toolbar-card">
          <div className="dash-card-header">
            <div className="dash-page-toolbar-copy">
              <strong>同步控制</strong>
              <span className="dash-subtext">返回情报中心或按类型手动发起同步。</span>
            </div>
            <div className="dash-history-actions">
              <button type="button" className="dash-btn secondary" onClick={() => navigate('/intel')}>
                返回情报中心
              </button>
              <select className="dash-select" value={itemType} onChange={(event) => setItemType(event.target.value)}>
                <option value="all">同步全部</option>
                <option value="news">仅新闻</option>
                <option value="tender">仅招投标</option>
              </select>
              <button type="button" className="dash-btn primary" disabled={running} onClick={runSync}>
                {running ? '同步中...' : '手动同步'}
              </button>
            </div>
          </div>
        </div>
        {error ? <div className="dash-card alert">{error}</div> : null}
        <div className="dash-card">
          <div className="dash-card-header">
            <strong className="dash-section-title">同步历史</strong>
          </div>
          {loading ? (
            <p className="dash-subtext">加载中...</p>
          ) : (
            <div className="dash-table-scroll">
              <table className="table">
                <thead>
                  <tr>
                    <th>任务ID</th>
                    <th>触发方式</th>
                    <th>状态</th>
                    <th>开始时间</th>
                    <th>结束时间</th>
                    <th>拉取</th>
                    <th>新增</th>
                    <th>去重</th>
                    <th>失败</th>
                  </tr>
                </thead>
                <tbody>
                  {jobs.length === 0 ? (
                    <tr>
                      <td colSpan={9}>暂无作业记录</td>
                    </tr>
                  ) : (
                    jobs.map((job) => (
                      <tr key={job.id}>
                        <td>{job.id}</td>
                        <td>{job.trigger_type}</td>
                        <td>{job.status}</td>
                        <td>{job.started_at || '-'}</td>
                        <td>{job.ended_at || '-'}</td>
                        <td>{job.pulled_count}</td>
                        <td>{job.upserted_count}</td>
                        <td>{job.deduped_count}</td>
                        <td>{job.failed_count}</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </section>
    </DashboardLayout>
  )
}
