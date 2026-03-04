import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import DashboardLayout from '../components/DashboardLayout'
import IntelSubnav from '../components/intel/IntelSubnav'
import { apiJson } from '../lib/api'

const defaultForm = {
  name: '',
  item_type: 'all',
  keywords: '',
  city: '重庆市',
  district: '',
  budget_min: '',
  budget_max: '',
  is_enabled: 1,
}

export default function IntelRules() {
  const navigate = useNavigate()
  const [rules, setRules] = useState([])
  const [form, setForm] = useState(defaultForm)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const load = async () => {
    setLoading(true)
    setError('')
    try {
      const data = await apiJson('/api/intel/rules')
      setRules(data || [])
    } catch (err) {
      setError(err.message || '加载规则失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  const createRule = async (event) => {
    event.preventDefault()
    if (!form.name.trim()) {
      setError('规则名称不能为空')
      return
    }
    try {
      await apiJson('/api/intel/rules', {
        method: 'POST',
        body: JSON.stringify({
          ...form,
          budget_min: form.budget_min === '' ? null : Number(form.budget_min),
          budget_max: form.budget_max === '' ? null : Number(form.budget_max),
          is_enabled: Number(form.is_enabled || 1),
        }),
      })
      setForm(defaultForm)
      await load()
    } catch (err) {
      setError(err.message || '创建规则失败')
    }
  }

  const toggleRule = async (rule) => {
    try {
      await apiJson(`/api/intel/rules/${rule.id}`, {
        method: 'PUT',
        body: JSON.stringify({ is_enabled: rule.is_enabled === 1 ? 0 : 1 }),
      })
      await load()
    } catch (err) {
      setError(err.message || '更新规则失败')
    }
  }

  const deleteRule = async (ruleId) => {
    try {
      await apiJson(`/api/intel/rules/${ruleId}`, { method: 'DELETE' })
      await load()
    } catch (err) {
      setError(err.message || '删除规则失败')
    }
  }

  return (
    <DashboardLayout title="规则管理" overline="INTELLIGENCE">
      <section className="dash-form-page">
        <IntelSubnav />
        <div className="dash-card dash-card-secondary dash-page-intro dash-page-intro--compact">
          <div className="dash-module-header">
            <div>
              <h2>规则管理</h2>
              <p className="dash-module-desc">管理关键词、城市区域与预算阈值规则，用于后续情报命中与订阅扩展。</p>
            </div>
            <div className="dash-collect-statuses">
              <span className="dash-status merchant">规则总数 {rules.length}</span>
              <span className="dash-status competitor">当前城市 {form.city}</span>
            </div>
          </div>
          <div className="dash-page-intro-grid">
            <article className="dash-page-intro-metric">
              <span>规则状态</span>
              <strong>{loading ? '加载中' : '可维护'}</strong>
              <small>支持新增、启用、停用与删除。</small>
            </article>
            <article className="dash-page-intro-metric">
              <span>关键词输入</span>
              <strong>逗号分隔</strong>
              <small>按城市、类型、预算等组合形成订阅规则。</small>
            </article>
            <article className="dash-page-intro-metric">
              <span>入口定位</span>
              <strong>情报中心</strong>
              <small>当前页作为规则配置与维护工作台。</small>
            </article>
          </div>
        </div>
        <div className="dash-card dash-page-toolbar-card">
          <div className="dash-card-header">
            <div className="dash-page-toolbar-copy">
              <strong>页面导航</strong>
              <span className="dash-subtext">返回情报中心，继续浏览新闻与招投标信息。</span>
            </div>
            <div className="dash-history-actions">
              <button type="button" className="dash-btn secondary" onClick={() => navigate('/intel')}>
                返回情报中心
              </button>
            </div>
          </div>
        </div>
        {error ? <div className="dash-card alert">{error}</div> : null}

        <div className="dash-card">
          <div className="dash-card-header">
            <strong className="dash-section-title">新增订阅规则</strong>
          </div>
          <form className="dash-fields" onSubmit={createRule}>
            <label className="dash-field">
              <span>规则名称</span>
              <input className="dash-input" value={form.name} onChange={(event) => setForm((prev) => ({ ...prev, name: event.target.value }))} />
            </label>
            <label className="dash-field">
              <span>类型</span>
              <select
                className="dash-select"
                value={form.item_type}
                onChange={(event) => setForm((prev) => ({ ...prev, item_type: event.target.value }))}
              >
                <option value="all">全部</option>
                <option value="news">新闻</option>
                <option value="tender">招投标</option>
              </select>
            </label>
            <label className="dash-field">
              <span>城市</span>
              <input className="dash-input" value={form.city} onChange={(event) => setForm((prev) => ({ ...prev, city: event.target.value }))} />
            </label>
            <label className="dash-field">
              <span>区域</span>
              <input className="dash-input" value={form.district} onChange={(event) => setForm((prev) => ({ ...prev, district: event.target.value }))} />
            </label>
            <label className="dash-field span-2">
              <span>关键词（逗号分隔）</span>
              <input
                className="dash-input"
                value={form.keywords}
                onChange={(event) => setForm((prev) => ({ ...prev, keywords: event.target.value }))}
              />
            </label>
            <label className="dash-field">
              <span>预算下限</span>
              <input
                className="dash-input"
                type="number"
                value={form.budget_min}
                onChange={(event) => setForm((prev) => ({ ...prev, budget_min: event.target.value }))}
              />
            </label>
            <label className="dash-field">
              <span>预算上限</span>
              <input
                className="dash-input"
                type="number"
                value={form.budget_max}
                onChange={(event) => setForm((prev) => ({ ...prev, budget_max: event.target.value }))}
              />
            </label>
            <div className="dash-history-actions">
              <button type="submit" className="dash-btn primary">
                保存规则
              </button>
            </div>
          </form>
        </div>

        <div className="dash-card">
          <div className="dash-card-header">
            <strong className="dash-section-title">现有规则</strong>
          </div>
          {loading ? (
            <p className="dash-subtext">加载中...</p>
          ) : (
            <div className="dash-table-scroll">
              <table className="table">
                <thead>
                  <tr>
                    <th>名称</th>
                    <th>类型</th>
                    <th>城市</th>
                    <th>区域</th>
                    <th>关键词</th>
                    <th>预算范围</th>
                    <th>状态</th>
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody>
                  {rules.length === 0 ? (
                    <tr>
                      <td colSpan={8}>暂无规则</td>
                    </tr>
                  ) : (
                    rules.map((rule) => (
                      <tr key={rule.id}>
                        <td>{rule.name}</td>
                        <td>{rule.item_type}</td>
                        <td>{rule.city || '-'}</td>
                        <td>{rule.district || '-'}</td>
                        <td>{rule.keywords || '-'}</td>
                        <td>
                          {(rule.budget_min ?? '-')}/{rule.budget_max ?? '-'}
                        </td>
                        <td>{rule.is_enabled === 1 ? '启用' : '停用'}</td>
                        <td>
                          <div className="dash-history-actions">
                            <button type="button" className="dash-btn secondary" onClick={() => toggleRule(rule)}>
                              {rule.is_enabled === 1 ? '停用' : '启用'}
                            </button>
                            <button type="button" className="dash-btn secondary" onClick={() => deleteRule(rule.id)}>
                              删除
                            </button>
                          </div>
                        </td>
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
