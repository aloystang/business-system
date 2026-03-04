import React, { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { API_BASE } from '../lib/api'
import { stageLabel } from '../lib/stages'

export default function SharePage() {
  const { token } = useParams()
  const [project, setProject] = useState(null)
  const [deliverables, setDeliverables] = useState([])
  const [error, setError] = useState('')

  useEffect(() => {
    const load = async () => {
      try {
        const res = await fetch(`${API_BASE}/api/public/share/${token}`)
        if (!res.ok) throw new Error('invalid')
        const data = await res.json()
        setProject(data)

        const dres = await fetch(`${API_BASE}/api/public/share/${token}/deliverables`)
        if (dres.ok) {
          const items = await dres.json()
          setDeliverables(items)
        }
      } catch (err) {
        setError('链接已失效')
      }
    }

    load()
  }, [token])

  const downloadPdf = () => {
    window.open(`${API_BASE}/api/public/share/${token}/pdf`, '_blank')
  }

  const downloadDeliverable = (id) => {
    window.open(`${API_BASE}/api/public/share/${token}/deliverables/${id}/download`, '_blank')
  }

  if (error) {
    return (
      <main>
        <div className="container">
          <div className="card">{error}</div>
        </div>
      </main>
    )
  }

  if (!project) {
    return (
      <main>
        <div className="container">
          <div className="card">加载中...</div>
        </div>
      </main>
    )
  }

  return (
    <main>
      <div className="container grid">
        <div className="card">
          <h2>{project.name}</h2>
          <p>{project.external_summary || '暂无对外摘要'}</p>
          <div className="grid two">
            <div>
              <strong>项目编号</strong>
              <div>{project.code}</div>
            </div>
            <div>
              <strong>阶段</strong>
              <div>{stageLabel(project.current_stage)}</div>
            </div>
            <div>
              <strong>区域</strong>
              <div>{project.region}</div>
            </div>
            <div>
              <strong>业态</strong>
              <div>{project.asset_type}</div>
            </div>
            <div>
              <strong>客户</strong>
              <div>{project.client_name}</div>
            </div>
            <div>
              <strong>地址</strong>
              <div>{project.address || '-'}</div>
            </div>
            <div>
              <strong>面积</strong>
              <div>{project.area_m2 || '-'}</div>
            </div>
            <div>
              <strong>人口指数</strong>
              <div>{project.population_index || '-'}</div>
            </div>
          </div>
        </div>

        <div className="card">
          <h3>对外交付物</h3>
          <table className="table">
            <thead>
              <tr>
                <th>类型</th>
                <th>标题</th>
                <th>版本</th>
                <th>时间</th>
                <th>下载</th>
              </tr>
            </thead>
            <tbody>
              {deliverables.map((item) => (
                <tr key={item.id}>
                  <td>{item.type}</td>
                  <td>{item.title}</td>
                  <td>v{item.version}</td>
                  <td>{new Date(item.created_at).toLocaleString()}</td>
                  <td>
                    <button className="button secondary" onClick={() => downloadDeliverable(item.id)}>
                      下载
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {deliverables.length === 0 && <p>暂无对外交付物</p>}
        </div>

        <div className="card">
          <h3>对外 PDF</h3>
          <button className="button" onClick={downloadPdf}>
            下载对外 PDF
          </button>
        </div>
      </div>
    </main>
  )
}
