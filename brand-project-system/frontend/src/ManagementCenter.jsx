import React from 'react'
import {
  AlertTriangle, ArrowRight, BadgeCheck, BarChart3, Building2, CalendarDays,
  Check, CheckCircle2, ChevronRight, CircleDollarSign, ClipboardCheck,
  Clock3, FileCheck2, FileText, Flag, Gauge, ListChecks, Plus, RefreshCw,
  ShieldAlert, Target, UserRoundCheck, WalletCards, X, XCircle,
} from 'lucide-react'

const tabs = [
  ['loop', '闭环管理', ListChecks],
  ['budget', '预算计划', WalletCards],
  ['contract', '合同租赁', FileText],
  ['approval', '审批决策', ClipboardCheck],
  ['risk', '风险预警', ShieldAlert],
]

const loopSeed = [
  { id: 'CL-026', title: '足球场空置铺位专项招商', source: '出租率预警', project: '重庆龙兴足球场', owner: '陈昱', due: '09-18', progress: 68, status: '执行中', level: '高', measure: '完成三家运动体验品牌商务条件确认', result: '已接洽 5 家，2 家进入条件谈判' },
  { id: 'CL-025', title: '悦荟城租金收缴提升', source: '欠租预警', project: '两江悦荟城', owner: '李然', due: '09-12', progress: 82, status: '待验收', level: '高', measure: '完成重点欠租商户分级催收', result: '收缴率由 94.1% 提升至 97.8%' },
  { id: 'CL-024', title: '云中街非主力时段客流改善', source: '经营分析', project: '两江云中街', owner: '赵青', due: '09-25', progress: 46, status: '执行中', level: '中', measure: '上线夜间活动并联动餐饮商户', result: '首周夜间客流同比增长 8.6%' },
  { id: 'CL-021', title: '网球馆能耗异常复核', source: '成本预警', project: '江北嘴网球馆', owner: '王珂', due: '09-08', progress: 100, status: '已闭环', level: '中', measure: '复核分项电表与设备运行时段', result: '确认冷机策略问题，月度节约约 1.8 万元' },
]

const budgets = [
  { project: '重庆龙兴足球场', budget: 1420, actual: 1280, forecast: 1396, costBudget: 790, costActual: 736, occupancy: '82.6%', owner: '陈昱' },
  { project: '两江悦荟城', budget: 410, actual: 386, forecast: 402, costBudget: 226, costActual: 218, occupancy: '91.2%', owner: '李然' },
  { project: '两江云中街', budget: 468, actual: 452, forecast: 474, costBudget: 284, costActual: 271, occupancy: '88.5%', owner: '赵青' },
  { project: '三洞桥 PARK', budget: 535, actual: 512, forecast: 528, costBudget: 315, costActual: 306, occupancy: '84.7%', owner: '陈昱' },
  { project: '江北嘴网球馆', budget: 132, actual: 116, forecast: 124, costBudget: 81, costActual: 78, occupancy: '79.6%', owner: '赵青' },
]

const contracts = [
  { id: 'HT-2026-0188', tenant: '超级猩猩', project: '重庆龙兴足球场', stage: '合同审批', node: '法务复核', date: '09-13', rent: '18.6万元/月', owner: '陈昱', risk: '正常', term: '2026-10-01 至 2031-09-30', deposit: '111.6万元' },
  { id: 'HT-2025-0096', tenant: '瑞幸咖啡', project: '两江悦荟城', stage: '履约经营', node: '月度收缴', date: '09-10', rent: '5.8万元/月', owner: '李然', risk: '催办', term: '2025-03-01 至 2028-02-29', deposit: '34.8万元' },
  { id: 'HT-2024-0063', tenant: '名创优品', project: '两江云中街', stage: '续租评估', node: '经营评审', date: '09-20', rent: '12.4万元/月', owner: '赵青', risk: '关注', term: '2024-01-01 至 2026-12-31', deposit: '74.4万元' },
  { id: 'HT-2026-0201', tenant: '百果园', project: '鱼复星光', stage: '装修进场', node: '图纸确认', date: '09-15', rent: '4.2万元/月', owner: '王珂', risk: '正常', term: '2026-09-01 至 2029-08-31', deposit: '25.2万元' },
  { id: 'HT-2023-0041', tenant: '社区药房', project: '江北嘴网球馆', stage: '退租交接', node: '费用清算', date: '09-09', rent: '3.1万元/月', owner: '李然', risk: '逾期', term: '2023-09-01 至 2026-08-31', deposit: '18.6万元' },
]

const approvalSeed = [
  { id: 'SP-202609-012', title: '超级猩猩商务条件审批', type: '租赁条件', project: '重庆龙兴足球场', applicant: '陈昱', submitted: '今天 09:42', amount: '年租金 223.2 万元', level: '重要', status: '待审批', summary: '首年租金单价 103 元/㎡/月，装修免租期 60 天，合同期 5 年。' },
  { id: 'SP-202609-011', title: '悦荟城中庭调改预算追加', type: '预算调整', project: '两江悦荟城', applicant: '李然', submitted: '昨天 16:18', amount: '追加 38.0 万元', level: '重要', status: '待审批', summary: '追加消防改造及公共区域导视费用，年度预算预计超支 2.1%。' },
  { id: 'SP-202609-009', title: '名创优品续租策略确认', type: '续租决策', project: '两江云中街', applicant: '赵青', submitted: '09-08 14:30', amount: '租金增幅 6%', level: '一般', status: '会签中', summary: '建议续租三年，第二年起租金年递增 3%，保持现有铺位面积。' },
  { id: 'SP-202609-006', title: '网球馆存量铺位业态置换', type: '调改方案', project: '江北嘴网球馆', applicant: '王珂', submitted: '09-07 11:20', amount: '预计增租 2.6 万/月', level: '一般', status: '已通过', summary: '将原生活服务铺位置换为运动康复，计划于原合同到期后实施。' },
]

const riskSeed = [
  { id: 'R-106', title: '社区药房退租交接逾期', category: '合同履约', project: '江北嘴网球馆', level: '红色', value: '逾期 9 天', owner: '李然', status: '处置中', due: '09-11', suggestion: '今日完成费用清算确认并锁定退铺验收时间。' },
  { id: 'R-103', title: '足球场出租率低于目标', category: '空置招商', project: '重庆龙兴足球场', level: '橙色', value: '偏差 -5.4pt', owner: '陈昱', status: '已派单', due: '09-18', suggestion: '优先推进运动体验、赛事服务类品牌，按到期窗口形成调改批次。' },
  { id: 'R-101', title: '悦荟城两户租金未按期到账', category: '租金收缴', project: '两江悦荟城', level: '橙色', value: '未收 18.6 万', owner: '李然', status: '处置中', due: '09-12', suggestion: '按欠款天数分级催收，超过 15 日触发法务预审。' },
  { id: 'R-098', title: '云中街月度能耗超预算', category: '预算成本', project: '两江云中街', level: '黄色', value: '超支 6.8%', owner: '赵青', status: '待派单', due: '09-16', suggestion: '复核夜间能耗与活动增量成本，更新本月滚动预测。' },
  { id: 'R-095', title: '三洞桥项目品牌资料完整度不足', category: '数据质量', project: '三洞桥 PARK', level: '蓝色', value: '完整度 72%', owner: '王珂', status: '观察中', due: '09-22', suggestion: '补齐工程条件、联系人及本年度开店计划。' },
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
    <span>{item.label}</span><strong>{item.value}</strong><small className={item.tone || ''}>{item.meta}</small><i style={{ '--progress': item.progress || '68%' }} />
  </button>)}</div>
}

function DetailPairs({ rows }) {
  return <div className="manager-detailPairs">{rows.map(([key, value]) => <div key={key}><span>{key}</span><strong>{value}</strong></div>)}</div>
}

function LoopView({ notify }) {
  const [items, setItems] = React.useState(loopSeed)
  const [selected, setSelected] = React.useState(null)
  const [filter, setFilter] = React.useState('全部')
  const visible = filter === '全部' ? items : items.filter((item) => item.status === filter)
  const advance = (item) => {
    const next = item.status === '执行中' ? '待验收' : item.status === '待验收' ? '已闭环' : item.status
    setItems((rows) => rows.map((row) => row.id === item.id ? { ...row, status: next, progress: next === '已闭环' ? 100 : Math.max(row.progress, 90) } : row))
    setSelected(null); notify(`事项“${item.title}”已更新为${next}`)
  }
  return <>
    <PageIntro eyebrow="MANAGEMENT LOOP" title="经营事项闭环" description="把预警、任务、措施、验收与复盘放进同一条责任链。" action={<button className="primaryAction" onClick={() => notify('已创建一条空白闭环事项，可在接入接口后正式保存')}><Plus size={16} />新建闭环事项</button>} />
    <Kpis items={[{ label: '进行中事项', value: '12', meta: '3 项本周到期' }, { label: '待验收', value: '4', meta: '需要管理人确认', tone: 'orange' }, { label: '逾期事项', value: '2', meta: '较上周减少 1 项', tone: 'red' }, { label: '本月闭环率', value: '86.7%', meta: '目标 90%', tone: 'green', progress: '86.7%' }]} onSelect={() => setFilter('全部')} />
    <section className="manager-panel"><div className="manager-sectionHead"><div><h3>重点事项推进</h3><span>点击事项查看完整责任链</span></div><div className="manager-segments">{['全部', '执行中', '待验收', '已闭环'].map((value) => <button className={filter === value ? 'active' : ''} onClick={() => setFilter(value)} key={value}>{value}</button>)}</div></div>
      <div className="manager-loopTable"><div className="manager-tableHead"><span>事项 / 来源</span><span>责任项目</span><span>责任人</span><span>截止时间</span><span>推进状态</span><span>完成度</span></div>{visible.map((item) => <button type="button" key={item.id} onClick={() => setSelected(item)}><span><strong>{item.title}</strong><small>{item.id} · {item.source}</small></span><span>{item.project}</span><span>{item.owner}</span><span>{item.due}</span><em className={`manager-status status-${item.status}`}>{item.status}</em><span className="manager-progress"><i style={{ width: `${item.progress}%` }} /><b>{item.progress}%</b></span></button>)}</div>
    </section>
    {selected && <ManagerDialog title={selected.title} subtitle={`${selected.id} · ${selected.source}`} onClose={() => setSelected(null)} actions={<><button onClick={() => setSelected(null)}>关闭</button>{selected.status !== '已闭环' && <button className="primaryAction" onClick={() => advance(selected)}>{selected.status === '执行中' ? '提交验收' : '确认闭环'} <ArrowRight size={15} /></button>}</>}><div className="manager-flow">{['发现问题', '生成任务', '执行措施', '验收结果', '复盘归档'].map((step, index) => <div className={index <= (selected.status === '已闭环' ? 4 : selected.status === '待验收' ? 3 : 2) ? 'done' : ''} key={step}><i>{index < 3 ? <Check size={13} /> : index + 1}</i><span>{step}</span></div>)}</div><DetailPairs rows={[["责任项目", selected.project], ["责任人", selected.owner], ["截止时间", selected.due], ["当前状态", selected.status], ["执行措施", selected.measure], ["阶段结果", selected.result]]} /></ManagerDialog>}
  </>
}

function BudgetView({ notify }) {
  const [selected, setSelected] = React.useState(null)
  const [period, setPeriod] = React.useState('2026年9月')
  const totalBudget = budgets.reduce((sum, row) => sum + row.budget, 0)
  const totalActual = budgets.reduce((sum, row) => sum + row.actual, 0)
  return <>
    <PageIntro eyebrow="BUDGET & PLAN" title="预算与计划管理" description="统一查看年度目标、月度执行、预算偏差与滚动预测。" action={<div className="manager-selects"><select value={period} onChange={(e) => setPeriod(e.target.value)}><option>2026年9月</option><option>2026年8月</option><option>2026年三季度</option><option>2026年全年</option></select><button onClick={() => notify(`${period}滚动预测已刷新`)}><RefreshCw size={15} />更新预测</button></div>} />
    <Kpis items={[{ label: '收入预算完成', value: `${(totalActual / totalBudget * 100).toFixed(1)}%`, meta: `${totalActual.toLocaleString()} / ${totalBudget.toLocaleString()} 万`, tone: 'green', progress: `${totalActual / totalBudget * 100}%` }, { label: '成本预算执行', value: '94.8%', meta: '节约 84 万元', tone: 'green', progress: '94.8%' }, { label: '预计年度达成', value: '98.6%', meta: '滚动预测口径', tone: 'orange', progress: '98.6%' }, { label: '偏差待纠正', value: '3项', meta: '1 项超过 10%', tone: 'red' }]} onSelect={(item) => notify(`正在查看${item.label}明细`)} />
    <div className="manager-twoColumns manager-budgetGrid">
      <section className="manager-panel"><div className="manager-sectionHead"><div><h3>月度预算执行趋势</h3><span>收入预算、实际与滚动预测 · 万元</span></div><span className="manager-legend"><i />预算 <i />实际</span></div><div className="manager-barChart">{[['4月',78,74],['5月',82,79],['6月',86,88],['7月',89,85],['8月',92,91],['9月',100,94]].map(([m,b,a]) => <div key={m}><span><i style={{height:`${b}%`}} /><i style={{height:`${a}%`}} /></span><small>{m}</small></div>)}</div></section>
      <section className="manager-panel manager-planCard"><div className="manager-sectionHead"><div><h3>年度重点计划</h3><span>董事会重点目标推进情况</span></div></div>{[['经营收入目标','3.26亿元','76%'],['综合出租率目标','90%','86.4%'],['重点品牌签约','36家','24家'],['存量铺位调改','42间','27间']].map(([name,target,actual]) => <button key={name} onClick={() => notify(`${name}计划明细已展开`)}><span><strong>{name}</strong><small>年度目标 {target}</small></span><b>{actual}</b><ChevronRight size={15} /></button>)}</section>
    </div>
    <section className="manager-panel"><div className="manager-sectionHead"><div><h3>项目预算执行</h3><span>{period} · 点击项目查看偏差构成</span></div></div><div className="manager-budgetTable"><div className="manager-tableHead"><span>项目</span><span>收入预算</span><span>收入实际</span><span>预测</span><span>成本执行</span><span>收入偏差</span><span>责任人</span></div>{budgets.map((row) => <button key={row.project} onClick={() => setSelected(row)}><strong>{row.project}</strong><span>{row.budget}万</span><span>{row.actual}万</span><span>{row.forecast}万</span><span>{row.costActual}/{row.costBudget}万</span><em className={row.actual >= row.budget ? 'positive' : 'negative'}>{((row.actual / row.budget - 1) * 100).toFixed(1)}%</em><span>{row.owner}</span></button>)}</div></section>
    {selected && <ManagerDialog title={selected.project} subtitle={`${period}预算执行分析`} onClose={() => setSelected(null)} actions={<><button onClick={() => setSelected(null)}>关闭</button><button className="primaryAction" onClick={() => { setSelected(null); notify('纠偏计划已加入闭环管理') }}>生成纠偏任务</button></>}><DetailPairs rows={[["收入预算", `${selected.budget} 万元`], ["收入实际", `${selected.actual} 万元`], ["收入偏差", `${((selected.actual / selected.budget - 1) * 100).toFixed(1)}%`], ["滚动预测", `${selected.forecast} 万元`], ["成本预算", `${selected.costBudget} 万元`], ["成本实际", `${selected.costActual} 万元`], ["综合出租率", selected.occupancy], ["责任人", selected.owner]]} /><div className="manager-insight"><AlertTriangle size={18} /><p><strong>管理建议</strong>收入略低于月度预算，建议将空置铺位招商和重点品牌签约纳入本月纠偏事项。</p></div></ManagerDialog>}
  </>
}

function ContractView({ notify }) {
  const [selected, setSelected] = React.useState(null)
  const stages = [['意向洽谈',12],['合同审批',4],['装修进场',7],['履约经营',186],['续租评估',9],['退租交接',3]]
  return <>
    <PageIntro eyebrow="LEASE LIFECYCLE" title="合同与租赁全生命周期" description="从意向洽谈到退租交接，统一管理合同节点、履约情况和到期策略。" action={<button className="primaryAction" onClick={() => notify('已打开合同起草入口（演示）')}><Plus size={16} />发起新合同</button>} />
    <div className="manager-lifecycle">{stages.map(([name,count],index) => <button key={name} onClick={() => notify(`已筛选${name}阶段，共 ${count} 项`)}><i>{index + 1}</i><span>{name}<strong>{count}</strong></span>{index < stages.length - 1 && <ArrowRight size={15} />}</button>)}</div>
    <Kpis items={[{ label: '有效合同', value: '186份', meta: '合同金额 8,642 万' }, { label: '90天内到期', value: '14份', meta: '9 份建议续租', tone: 'orange' }, { label: '履约异常', value: '3份', meta: '其中 1 份逾期', tone: 'red' }, { label: '电子归档率', value: '96.8%', meta: '目标 100%', tone: 'green', progress: '96.8%' }]} onSelect={(item) => notify(`已筛选${item.label}`)} />
    <section className="manager-panel"><div className="manager-sectionHead"><div><h3>近期关键节点</h3><span>点击合同查看租赁条件、履约和时间轴</span></div><button onClick={() => notify('合同节点日历已打开')}><CalendarDays size={15} />节点日历</button></div><div className="manager-contractTable"><div className="manager-tableHead"><span>合同 / 商户</span><span>项目</span><span>生命周期</span><span>当前节点</span><span>节点日期</span><span>月租金</span><span>风险</span></div>{contracts.map((row) => <button key={row.id} onClick={() => setSelected(row)}><span><strong>{row.tenant}</strong><small>{row.id}</small></span><span>{row.project}</span><em className="manager-stage">{row.stage}</em><span>{row.node}</span><span>{row.date}</span><span>{row.rent}</span><em className={`manager-risk risk-${row.risk}`}>{row.risk}</em></button>)}</div></section>
    {selected && <ManagerDialog title={`${selected.tenant}租赁合同`} subtitle={`${selected.id} · ${selected.project}`} onClose={() => setSelected(null)} actions={<><button onClick={() => setSelected(null)}>关闭</button><button onClick={() => notify('合同原件预览已打开')}><FileCheck2 size={15} />查看合同原件</button><button className="primaryAction" onClick={() => { setSelected(null); notify('已创建合同节点跟进任务') }}>创建跟进</button></>}><div className="manager-contractTimeline">{stages.map(([stage], index) => <div className={index <= stages.findIndex(([s]) => s === selected.stage) ? 'done' : ''} key={stage}><i>{index + 1}</i><span>{stage}</span></div>)}</div><DetailPairs rows={[["商户品牌", selected.tenant], ["合同期限", selected.term], ["合同租金", selected.rent], ["履约保证金", selected.deposit], ["当前节点", `${selected.stage} · ${selected.node}`], ["节点日期", selected.date], ["责任人", selected.owner], ["风险状态", selected.risk]]} /></ManagerDialog>}
  </>
}

function ApprovalView({ notify }) {
  const [items, setItems] = React.useState(approvalSeed)
  const [selected, setSelected] = React.useState(null)
  const [comment, setComment] = React.useState('同意，按审批条件推进。')
  const decide = (status) => {
    setItems((rows) => rows.map((row) => row.id === selected.id ? { ...row, status } : row))
    notify(`${selected.id} 已${status}`); setSelected(null)
  }
  return <>
    <PageIntro eyebrow="APPROVAL & DECISION" title="审批与决策中心" description="集中处理租赁条件、预算调整、品牌准入、调改与合同变更事项。" action={<button onClick={() => notify('已切换到我的已办事项')}><CheckCircle2 size={15} />查看已办</button>} />
    <Kpis items={[{ label: '待我审批', value: `${items.filter(i => i.status === '待审批').length}项`, meta: '1 项已等待超过 24h', tone: 'red' }, { label: '会签中', value: '3项', meta: '法务与财务处理中', tone: 'orange' }, { label: '本月已办', value: '28项', meta: '平均用时 6.2 小时', tone: 'green' }, { label: '决策金额', value: '486万', meta: '本月累计审批口径' }]} onSelect={(item) => notify(`已筛选${item.label}`)} />
    <div className="manager-approvalLayout"><section className="manager-panel manager-approvalList"><div className="manager-sectionHead"><div><h3>待决策事项</h3><span>按重要程度和等待时长排序</span></div></div>{items.map((item) => <button className={selected?.id === item.id ? 'active' : ''} key={item.id} onClick={() => setSelected(item)}><i className={`level-${item.level}`}>{item.level === '重要' ? <Flag size={16} /> : <FileCheck2 size={16} />}</i><span><strong>{item.title}</strong><small>{item.project} · {item.type} · {item.submitted}</small></span><em className={`manager-status status-${item.status}`}>{item.status}</em><ChevronRight size={16} /></button>)}</section><section className="manager-panel manager-decisionGuide"><div className="manager-sectionHead"><div><h3>决策辅助</h3><span>管理口径与智能提示</span></div></div><div className="manager-decisionScore"><Gauge size={28} /><span><small>今日审批效率</small><strong>92</strong></span></div>{[['超出租金授权线','0项'],['涉及预算追加','1项'],['法务意见待回','2项'],['需要集体决策','0项']].map(([label,value]) => <button key={label} onClick={() => notify(`已查看${label}`)}><span>{label}</span><strong>{value}</strong><ChevronRight size={14} /></button>)}</section></div>
    {selected && <ManagerDialog title={selected.title} subtitle={`${selected.id} · ${selected.type}`} onClose={() => setSelected(null)} actions={<><button onClick={() => decide('已驳回')}><XCircle size={15} />驳回</button><button onClick={() => decide('退回补充')}>退回补充</button><button className="primaryAction" onClick={() => decide('已通过')}><BadgeCheck size={15} />审批通过</button></>}><DetailPairs rows={[["所属项目", selected.project], ["申请人", selected.applicant], ["提交时间", selected.submitted], ["决策金额", selected.amount], ["当前状态", selected.status], ["事项说明", selected.summary]]} /><label className="manager-comment"><span>审批意见</span><textarea rows="3" value={comment} onChange={(event) => setComment(event.target.value)} /></label><div className="manager-insight"><Gauge size={18} /><p><strong>决策提示</strong>该事项未超过当前授权边界，相关预算和法务意见已齐备，可由当前审批人决策。</p></div></ManagerDialog>}
  </>
}

function RiskView({ notify }) {
  const [items, setItems] = React.useState(riskSeed)
  const [selected, setSelected] = React.useState(null)
  const [level, setLevel] = React.useState('全部')
  const visible = level === '全部' ? items : items.filter((item) => item.level === level)
  const update = (status) => { setItems((rows) => rows.map((row) => row.id === selected.id ? { ...row, status } : row)); notify(`风险 ${selected.id} 已更新为${status}`); setSelected(null) }
  return <>
    <PageIntro eyebrow="RISK EARLY WARNING" title="风险预警中心" description="统一识别经营、欠租、空置、合同、预算和数据质量风险。" action={<button onClick={() => notify('预警规则试算完成，本次发现 5 项管理风险')}><RefreshCw size={15} />重新扫描</button>} />
    <div className="manager-riskKpis">{[['红色','1','需立即处置'],['橙色','2','本周重点'],['黄色','1','限期整改'],['蓝色','1','持续观察']].map(([name,count,meta]) => <button className={level === name ? 'active' : ''} onClick={() => setLevel(level === name ? '全部' : name)} key={name}><i className={`riskDot ${name}`} /><span><strong>{count}</strong><small>{name}预警</small></span><em>{meta}</em></button>)}</div>
    <section className="manager-panel"><div className="manager-sectionHead"><div><h3>{level === '全部' ? '全部风险事项' : `${level}预警`}</h3><span>点击风险查看处置建议并派发责任人</span></div><button onClick={() => setLevel('全部')}>重置筛选</button></div><div className="manager-riskTable"><div className="manager-tableHead"><span>等级</span><span>风险事项</span><span>分类</span><span>影响值</span><span>责任人</span><span>要求完成</span><span>处置状态</span></div>{visible.map((item) => <button key={item.id} onClick={() => setSelected(item)}><i className={`riskDot ${item.level}`} /><span><strong>{item.title}</strong><small>{item.id} · {item.project}</small></span><span>{item.category}</span><em>{item.value}</em><span>{item.owner}</span><span>{item.due}</span><em className={`manager-status status-${item.status}`}>{item.status}</em></button>)}</div></section>
    {selected && <ManagerDialog title={selected.title} subtitle={`${selected.id} · ${selected.level}预警`} onClose={() => setSelected(null)} actions={<><button onClick={() => update('持续观察')}>转为观察</button><button onClick={() => update('已派单')}><UserRoundCheck size={15} />派发处置</button><button className="primaryAction" onClick={() => update('已关闭')}><CheckCircle2 size={15} />确认关闭</button></>}><DetailPairs rows={[["风险项目", selected.project], ["风险分类", selected.category], ["影响指标", selected.value], ["责任人", selected.owner], ["要求完成", selected.due], ["处置状态", selected.status]]} /><div className="manager-insight danger"><AlertTriangle size={18} /><p><strong>建议处置</strong>{selected.suggestion}</p></div><div className="manager-evidence"><span>关联证据</span><button onClick={() => notify('经营台账明细已打开')}><BarChart3 size={15} />经营台账</button><button onClick={() => notify('合同履约明细已打开')}><FileText size={15} />合同资料</button><button onClick={() => notify('相关闭环事项已打开')}><ListChecks size={15} />闭环事项</button></div></ManagerDialog>}
  </>
}

export default function ManagementCenter({ notify, initialTab = 'loop' }) {
  const [tab, setTab] = React.useState(initialTab)
  return <div className="pageContent manager-root">
    <div className="manager-nav" role="tablist" aria-label="管理中心模块">{tabs.map(([id,label,Icon]) => <button type="button" role="tab" aria-selected={tab === id} className={tab === id ? 'active' : ''} key={id} onClick={() => setTab(id)}><Icon size={17} />{label}</button>)}</div>
    {tab === 'loop' && <LoopView notify={notify} />}
    {tab === 'budget' && <BudgetView notify={notify} />}
    {tab === 'contract' && <ContractView notify={notify} />}
    {tab === 'approval' && <ApprovalView notify={notify} />}
    {tab === 'risk' && <RiskView notify={notify} />}
  </div>
}
