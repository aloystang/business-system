import React from 'react'
import {
  AlertTriangle, ArrowRight, CheckCircle2, ChevronRight, Clock3,
  FileText, ListChecks, Plus, RefreshCw, ShieldAlert, WalletCards, X,
} from 'lucide-react'
import { useAppData } from './data'
import { createTask, fmtPct, fmtWan, getLeasesEnriched, getTasksEnriched, updateTaskStatus } from './api'

const tabs = [
  ['loop', '闭环管理', ListChecks],
  ['budget', '预算计划', WalletCards],
  ['contract', '合同租赁', FileText],
  ['risk', '风险预警', ShieldAlert],
]

function ManagerDialog({ title, subtitle, children, onClose, actions }) {
  return <div className="manager-dialogBackdrop" role="presentation" onMouseDown={(event) => event.target === event.currentTarget && onClose()}>
    <section className="manager-dialog" role="dialog" aria-modal="true" aria-label={title}>
      <header><div><span>{subtitle}</span><h2>{title}</h2></div><button type="button" aria-label="关闭" onClick={onClose}><X size={18} /></button></header>
      <div className="manager-dialogBody">{children}</div>
      {actions && <footer>{actions}</footer>}
    </section>
  </div>
}

function PageIntro({ eyebrow, title, description, action }) {
  return <div className="manager-intro"><div><span>{eyebrow}</span><h2>{title}</h2><p>{description}</p></div>{action}</div>
}

function Kpis({ items, onSelect }) {
  return <div className="manager-kpis">{items.map((item) => <button type="button" key={item.label} onClick={() => onSelect?.(item)}>
    <span>{item.label}</span><strong>{item.value}</strong><small className={item.tone || ''}>{item.meta}</small><i style={{ '--progress': item.progress || '0%' }} />
  </button>)}</div>
}

function DetailPairs({ rows }) {
  return <div className="manager-detailPairs">{rows.map(([key, value]) => <div key={key}><span>{key}</span><strong>{value}</strong></div>)}</div>
}

function EmptyPanel({ text }) {
  return <div className="manager-panel" style={{ padding: '32px 20px', textAlign: 'center', color: 'var(--muted)' }}>{text}</div>
}

// ---------- 闭环管理：真实跟进任务（GET/POST/PATCH /tasks） ----------

const TASK_STATUS_FLOW = { '待办': '进行中', '进行中': '已完成' }
const TASK_STATUS_TONE = { '待办': '', '进行中': 'orange', '已完成': 'green', '已取消': 'red' }

function LoopView({ notify }) {
  const { projects, can } = useAppData()
  const [items, setItems] = React.useState(null)
  const [selected, setSelected] = React.useState(null)
  const [filter, setFilter] = React.useState('全部')
  const [createOpen, setCreateOpen] = React.useState(false)
  const [form, setForm] = React.useState({ title: '', projectId: '', priority: '中', due: '' })

  const load = React.useCallback(() => { getTasksEnriched().then(setItems).catch(() => setItems([])) }, [])
  React.useEffect(() => { load() }, [load])

  if (items === null) return <EmptyPanel text="正在加载闭环任务…" />
  const visible = filter === '全部' ? items : items.filter((item) => item.status === filter)
  const overdue = items.filter((t) => t.due !== '—' && t.due < new Date().toISOString().slice(0, 10) && t.status !== '已完成').length
  const done = items.filter((t) => t.status === '已完成').length
  const closeRate = items.length ? Math.round((done / items.length) * 100) : 0

  const advance = async (item) => {
    const next = TASK_STATUS_FLOW[item.status]
    if (!next) return
    try {
      await updateTaskStatus(item.id, next)
      notify(`事项"${item.title}"已更新为${next}`)
      setSelected(null); load()
    } catch (err) { notify(err.message || '更新失败') }
  }
  const submitCreate = async (event) => {
    event.preventDefault()
    try {
      await createTask({
        title: form.title, project_id: form.projectId ? Number(form.projectId) : null,
        priority: form.priority, plan_date: form.due || null,
      })
      notify(`已创建闭环事项"${form.title}"`)
      setCreateOpen(false); setForm({ title: '', projectId: '', priority: '中', due: '' }); load()
    } catch (err) { notify(err.message || '创建失败') }
  }

  return <>
    <PageIntro eyebrow="MANAGEMENT LOOP" title="经营事项闭环" description="把预警、任务、措施与验收放进同一条责任链（数据来自真实跟进任务台账）。" action={can('match:write') ? <button className="primaryAction" onClick={() => setCreateOpen(true)}><Plus size={16} />新建闭环事项</button> : null} />
    <Kpis items={[
      { label: '进行中事项', value: String(items.filter((i) => i.status === '进行中').length), meta: `共 ${items.length} 项` },
      { label: '待办事项', value: String(items.filter((i) => i.status === '待办').length), meta: '尚未开始处理', tone: 'orange' },
      { label: '已逾期', value: String(overdue), meta: '计划日期已过', tone: overdue ? 'red' : '' },
      { label: '闭环率', value: `${closeRate}%`, meta: `${done}/${items.length} 已完成`, tone: 'green', progress: `${closeRate}%` },
    ]} onSelect={() => setFilter('全部')} />
    <section className="manager-panel"><div className="manager-sectionHead"><div><h3>重点事项推进</h3><span>点击事项查看详情</span></div><div className="manager-segments">{['全部', '待办', '进行中', '已完成'].map((value) => <button className={filter === value ? 'active' : ''} onClick={() => setFilter(value)} key={value}>{value}</button>)}</div></div>
      {visible.length ? <div className="manager-loopTable"><div className="manager-tableHead"><span>事项</span><span>责任项目</span><span>优先级</span><span>计划时间</span><span>状态</span></div>{visible.map((item) => <button type="button" key={item.id} onClick={() => setSelected(item)}><span><strong>{item.title}</strong><small>#{item.id}</small></span><span>{item.project}</span><span>{item.priority}</span><span>{item.due}</span><em className={`manager-status status-${item.status}`}>{item.status}</em></button>)}</div> : <p style={{ padding: '14px 20px', color: 'var(--muted)' }}>暂无{filter === '全部' ? '' : filter}闭环事项。</p>}
    </section>
    {selected && <ManagerDialog title={selected.title} subtitle={`#${selected.id} · ${selected.project}`} onClose={() => setSelected(null)} actions={<><button onClick={() => setSelected(null)}>关闭</button>{TASK_STATUS_FLOW[selected.status] && <button className="primaryAction" onClick={() => advance(selected)}>推进至{TASK_STATUS_FLOW[selected.status]} <ArrowRight size={15} /></button>}</>}><DetailPairs rows={[["责任项目", selected.project], ["优先级", selected.priority], ["计划时间", selected.due], ["当前状态", selected.status], ["备注", selected.detail || '—']]} /></ManagerDialog>}
    {createOpen && <ManagerDialog title="新建闭环事项" subtitle="写入真实跟进任务台账" onClose={() => setCreateOpen(false)} actions={<><button onClick={() => setCreateOpen(false)}>取消</button><button type="submit" form="loop-create-form" className="primaryAction">保存</button></>}>
      <form id="loop-create-form" className="manager-createForm" onSubmit={submitCreate}>
        <label>事项标题<input required autoFocus value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} /></label>
        <label>关联项目<select value={form.projectId} onChange={(e) => setForm({ ...form, projectId: e.target.value })}><option value="">不关联</option>{projects.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}</select></label>
        <label>优先级<select value={form.priority} onChange={(e) => setForm({ ...form, priority: e.target.value })}><option>高</option><option>中</option><option>低</option></select></label>
        <label>计划完成日期<input type="date" value={form.due} onChange={(e) => setForm({ ...form, due: e.target.value })} /></label>
      </form>
    </ManagerDialog>}
  </>
}

// ---------- 预算计划：如实标注"预算台账尚未采集"，只展示真实实际数 ----------

function BudgetView() {
  const { ops } = useAppData()
  const [selected, setSelected] = React.useState(null)
  if (!ops) return <EmptyPanel text="正在加载经营数据…" />
  const rows = [...ops.projects].sort((a, b) => b.revenue_received - a.revenue_received).slice(0, 12)
  return <>
    <PageIntro eyebrow="BUDGET & PLAN" title="预算与计划管理" description="统一查看各项目的实际经营表现。" />
    <div className="manager-insight" style={{ margin: '0 0 16px' }}><AlertTriangle size={18} /><p><strong>说明</strong>系统尚未采集各项目的年度/月度预算目标，暂无法计算"预算达成率"或生成偏差分析——以下仅展示经营台账的真实实际数据，供先行参考。</p></div>
    <Kpis items={[
      { label: '组合实收', value: fmtWan(ops.kpi.revenue_received), meta: `${ops.kpi.project_count} 个项目合计` },
      { label: '组合成本', value: fmtWan(ops.kpi.cost), meta: '经营成本合计' },
      { label: '组合 NOI', value: fmtWan(ops.kpi.noi), meta: '实收 − 成本', tone: ops.kpi.noi >= 0 ? 'green' : 'red' },
      { label: '收缴率', value: fmtPct(ops.kpi.collect_rate), meta: `欠租 ${fmtWan(ops.kpi.arrears)}` },
    ]} />
    <section className="manager-panel"><div className="manager-sectionHead"><div><h3>项目实际经营（Top 12 · 按实收排序）</h3><span>点击项目查看明细</span></div></div><div className="manager-budgetTable"><div className="manager-tableHead"><span>项目</span><span>实收</span><span>成本</span><span>NOI</span><span>出租率</span><span>收缴率</span></div>{rows.map((row) => <button key={row.project_id} onClick={() => setSelected(row)}><strong>{row.project_name}</strong><span>{fmtWan(row.revenue_received)}</span><span>{fmtWan(row.cost)}</span><em className={row.noi >= 0 ? 'positive' : 'negative'}>{fmtWan(row.noi)}</em><span>{fmtPct(row.occupancy_rate)}</span><span>{fmtPct(row.collect_rate)}</span></button>)}</div></section>
    {selected && <ManagerDialog title={selected.project_name} subtitle="实际经营明细" onClose={() => setSelected(null)} actions={<button className="primaryAction" onClick={() => setSelected(null)}>关闭</button>}><DetailPairs rows={[["实收", fmtWan(selected.revenue_received)], ["成本", fmtWan(selected.cost)], ["NOI", fmtWan(selected.noi)], ["出租率", fmtPct(selected.occupancy_rate)], ["收缴率", fmtPct(selected.collect_rate)], ["欠租", fmtWan(selected.arrears)], ["租金坪效", `${selected.rent_psm_month || 0} 元/㎡/月`]]} /></ManagerDialog>}
  </>
}

// ---------- 合同租赁：真实租约台账（GET /leases + /merchants + /units 联查） ----------

function ContractView() {
  const { risk } = useAppData()
  const [leases, setLeases] = React.useState(null)
  const [selected, setSelected] = React.useState(null)
  React.useEffect(() => { getLeasesEnriched().then(setLeases).catch(() => setLeases([])) }, [])
  if (leases === null) return <EmptyPanel text="正在加载合同租赁台账…" />
  const active = leases.filter((l) => l.status === '生效')
  return <>
    <PageIntro eyebrow="LEASE LIFECYCLE" title="合同与租赁台账" description="全部在管项目的真实租约台账（来自出租经营台账）。" />
    <Kpis items={[
      { label: '有效合同', value: `${active.length}份`, meta: `台账合计 ${leases.length} 份` },
      { label: '90天内到期', value: `${risk?.summary.expiring_lease_count ?? '—'}份`, meta: `涉及月租 ${fmtWan(risk?.summary.expiring_rent_at_risk)}`, tone: 'orange' },
      { label: '已到期/终止', value: `${leases.filter((l) => l.status !== '生效').length}份`, meta: '状态非生效' },
    ]} />
    <section className="manager-panel"><div className="manager-sectionHead"><div><h3>租约清单</h3><span>点击查看合同详情</span></div></div><div className="manager-contractTable"><div className="manager-tableHead"><span>合同 / 商户</span><span>项目</span><span>计租面积</span><span>租金坪效</span><span>合同期限</span><span>状态</span></div>{leases.slice(0, 60).map((row) => <button key={row.id} onClick={() => setSelected(row)}><span><strong>{row.tenant}</strong><small>{row.no}</small></span><span>{row.project}</span><span>{row.area}</span><span>{row.rent}</span><span>{row.term}</span><em className={`manager-status status-${row.status === '生效' ? '进行中' : '已完成'}`}>{row.status}</em></button>)}</div>{leases.length > 60 && <p style={{ padding: '10px 20px', color: 'var(--muted)', fontSize: 12 }}>仅展示前 60 条，共 {leases.length} 条。</p>}</section>
    {selected && <ManagerDialog title={`${selected.tenant}租赁合同`} subtitle={`${selected.no} · ${selected.project}`} onClose={() => setSelected(null)} actions={<button onClick={() => setSelected(null)}>关闭</button>}><DetailPairs rows={[["商户", selected.tenant], ["所属项目", selected.project], ["计租面积", selected.area], ["租金坪效", selected.rent], ["合同期限", selected.term], ["合同状态", selected.status]]} /></ManagerDialog>}
  </>
}

// ---------- 风险预警：真实跨项目风险聚合（GET /dashboard/risk-alerts） ----------

function severityOf(daysLeft) {
  if (daysLeft <= 30) return { level: '红色', tone: 'red' }
  if (daysLeft <= 60) return { level: '橙色', tone: 'orange' }
  return { level: '黄色', tone: 'yellow' }
}

function RiskView({ notify, onNavigate }) {
  const { risk } = useAppData()
  const [selected, setSelected] = React.useState(null)
  if (!risk) return <EmptyPanel text="正在加载风险数据…" />

  const rows = [
    ...risk.arrears_top.map((r) => ({ id: `arrears-${r.project_id}`, title: `${r.project_name} 存在欠租`, category: '租金收缴', project: r.project_name, value: fmtWan(r.arrears), level: r.arrears > 50000 ? '红色' : '橙色', suggestion: '按欠款账期分级催收，建议优先联系欠租金额最高的商户。' })),
    ...risk.expiring_leases.map((e) => ({ id: `lease-${e.lease_code}`, title: `${e.project_name} · ${e.tenant} 租约将到期`, category: '合同到期', project: e.project_name, value: `${e.days_left} 天后到期`, level: severityOf(e.days_left).level, suggestion: `到期日 ${e.lease_end}，月租 ${fmtWan(e.monthly_rent)}；建议提前启动续租洽谈或按业态调改计划安排承接。` })),
    ...risk.vacant_top.map((v) => ({ id: `vacant-${v.project_id}`, title: `${v.project_name} 空置面积偏高`, category: '空置招商', project: v.project_name, value: `${v.vacant_units} 个铺位 · ${Math.round(v.vacant_area)}㎡`, level: '蓝色', suggestion: '建议纳入招商优先清单，结合项目业态与调改页面制定招商计划。' })),
  ]
  const [level, setLevel] = React.useState('全部')
  const visible = level === '全部' ? rows : rows.filter((r) => r.level === level)
  const counts = { 红色: rows.filter((r) => r.level === '红色').length, 橙色: rows.filter((r) => r.level === '橙色').length, 黄色: rows.filter((r) => r.level === '黄色').length, 蓝色: rows.filter((r) => r.level === '蓝色').length }

  return <>
    <PageIntro eyebrow="RISK EARLY WARNING" title="风险预警中心" description="跨项目自动汇总欠租、临期租约与空置招商风险（每次打开实时计算）。" action={<button onClick={() => notify('风险数据已是实时计算结果，无需手动刷新')}><RefreshCw size={15} />说明</button>} />
    <div className="manager-riskKpis">{Object.entries(counts).map(([name, count]) => <button className={level === name ? 'active' : ''} onClick={() => setLevel(level === name ? '全部' : name)} key={name}><i className={`riskDot ${name}`} /><span><strong>{count}</strong><small>{name}预警</small></span></button>)}</div>
    <section className="manager-panel"><div className="manager-sectionHead"><div><h3>{level === '全部' ? '全部风险事项' : `${level}预警`}</h3><span>共 {visible.length} 项</span></div><button onClick={() => setLevel('全部')}>重置筛选</button></div>
      {visible.length ? <div className="manager-riskTable"><div className="manager-tableHead"><span>等级</span><span>风险事项</span><span>分类</span><span>影响值</span></div>{visible.map((item) => <button key={item.id} onClick={() => setSelected(item)}><i className={`riskDot ${item.level}`} /><span><strong>{item.title}</strong><small>{item.project}</small></span><span>{item.category}</span><em>{item.value}</em></button>)}</div> : <p style={{ padding: '14px 20px', color: 'var(--muted)' }}>暂无该等级风险事项。</p>}
    </section>
    {selected && <ManagerDialog title={selected.title} subtitle={`${selected.category} · ${selected.level}预警`} onClose={() => setSelected(null)} actions={<button className="primaryAction" onClick={() => { setSelected(null); onNavigate?.('projects') }}>前往项目资源库 <ArrowRight size={15} /></button>}><DetailPairs rows={[["所属项目", selected.project], ["风险分类", selected.category], ["影响值", selected.value]]} /><div className="manager-insight danger"><AlertTriangle size={18} /><p><strong>建议处置</strong>{selected.suggestion}</p></div></ManagerDialog>}
  </>
}

export default function ManagementCenter({ notify, onNavigate, initialTab = 'loop' }) {
  const [tab, setTab] = React.useState(initialTab)
  return <div className="pageContent manager-root">
    <div className="manager-nav" role="tablist" aria-label="管理中心模块">{tabs.map(([id, label, Icon]) => <button type="button" role="tab" aria-selected={tab === id} className={tab === id ? 'active' : ''} key={id} onClick={() => setTab(id)}><Icon size={17} />{label}</button>)}</div>
    {tab === 'loop' && <LoopView notify={notify} />}
    {tab === 'budget' && <BudgetView />}
    {tab === 'contract' && <ContractView />}
    {tab === 'risk' && <RiskView notify={notify} onNavigate={onNavigate} />}
  </div>
}
