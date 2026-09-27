import React from 'react'
import {
  getOperations, getProjectOperations, getTenantMix, getAdjustmentPlan,
  resolveProjectIdByName, fmtWan, fmtPct, fmtAreaWan,
} from './api'
import { AppDataProvider, useAppData } from './data'
import ProjectLayoutSandbox from './ProjectLayoutSandbox'
import ManagementCenter from './ManagementCenter'
import {
  Activity,
  ArrowRight,
  BadgeCheck,
  Bell,
  Building2,
  CalendarClock,
  CheckCircle2,
  ChevronDown,
  CircleUserRound,
  ClipboardCheck,
  Clock3,
  Database,
  Download,
  ExternalLink,
  FileSpreadsheet,
  FileUp,
  Filter,
  History,
  Info,
  LayoutDashboard,
  ListFilter,
  Map,
  MapPin,
  MessageSquareText,
  Plus,
  RefreshCw,
  Save,
  Search,
  Settings2,
  ShieldCheck,
  Sparkles,
  Target,
  UploadCloud,
  UsersRound,
  X,
} from 'lucide-react'

const nav = [
  { id: 'dashboard', label: '管理驾驶舱', icon: LayoutDashboard },
  { id: 'map', label: '地图资源中心', icon: Map },
  { id: 'brands', label: '品牌资源库', icon: Database },
  { id: 'projects', label: '项目资源库', icon: Building2 },
  { id: 'operations', label: '经营中心', icon: Activity },
  { id: 'matching', label: '匹配工作台', icon: Target, badge: '12' },
  { id: 'followup', label: '候选与跟进', icon: UsersRound, badge: '5' },
  { id: 'management', label: '管理中心', icon: ClipboardCheck, badge: '6' },
]

const projects = [
  { id: 1, name: '重庆龙兴足球场', shortName: '足球场', type: '体育场馆商业', status: '招商中', grade: 'A', x: 58, y: 37, lng: 106.7315, lat: 29.6902, area: '16.1万㎡', occupancy: '82.6%', revenue: '1,280万元', cost: '736万元', collection: '96.4%', matches: 12, next: '联系首批运动品牌', owner: '陈昱' },
  { id: 2, name: '两江悦荟城', shortName: '悦荟城', type: '购物中心', status: '招商中', grade: 'B', x: 43, y: 49, lng: 106.7208, lat: 29.6688, area: '1.8万㎡', occupancy: '91.2%', revenue: '386万元', cost: '218万元', collection: '98.1%', matches: 8, next: '复核主力店物业条件', owner: '李然' },
  { id: 3, name: '两江云中街', shortName: '云中街', type: '商业街区', status: '已开业', grade: 'B', x: 68, y: 61, lng: 106.6905, lat: 29.7602, area: '2.4万㎡', occupancy: '88.5%', revenue: '452万元', cost: '271万元', collection: '95.7%', matches: 6, next: '补充非赛事日客群', owner: '赵青' },
  { id: 4, name: '鱼复星光', shortName: '鱼复星光', type: '社区商业', status: '招商中', grade: 'C', x: 32, y: 67, lng: 106.7788, lat: 29.6205, area: '2.8万㎡', occupancy: '76.3%', revenue: '298万元', cost: '194万元', collection: '92.4%', matches: 4, next: '确认经营合作模式', owner: '李然' },
  { id: 5, name: '三洞桥 PARK', shortName: '三洞桥', type: '商业街区', status: '招商中', grade: 'B', x: 79, y: 31, lng: 106.5450, lat: 29.6060, area: '2.9万㎡', occupancy: '84.7%', revenue: '512万元', cost: '306万元', collection: '97.2%', matches: 9, next: '形成候选品牌清单', owner: '陈昱' },
  { id: 6, name: '江北嘴网球馆', shortName: '网球馆', type: '体育场馆商业', status: '招商中', grade: 'B', x: 72, y: 76, lng: 106.5480, lat: 29.6080, area: '3432㎡', occupancy: '79.6%', revenue: '116万元', cost: '78万元', collection: '94.9%', matches: 7, next: '核对赛事计划', owner: '赵青' },
  { id: 7, name: 'h87御临河商业', shortName: '御临河', type: '商业街区', status: '筹备', grade: 'B', lng: 106.794565, lat: 29.695644, area: '5584㎡' },
  { id: 8, name: '龙盛能量仓（临时建筑物）', shortName: '能量仓', type: '社区商业', status: '招商中', grade: 'C', lng: 106.755376, lat: 29.623105, area: '1325㎡' },
  { id: 9, name: '两江新新集', shortName: '新新集', type: '社区商业', status: '招商中', grade: 'B', lng: 106.794565, lat: 29.695644, area: '2.0万㎡' },
  { id: 10, name: '曲院风荷社区（一期）', shortName: '曲院风荷', type: '社区商业', status: '招商中', grade: 'C', lng: 106.794565, lat: 29.695644, area: '4220㎡' },
  { id: 11, name: '溪岸云蔚E09底商', shortName: '溪岸云蔚', type: '社区商业', status: '招商中', grade: 'C', lng: 106.794565, lat: 29.695644, area: '4017㎡' },
  { id: 12, name: '地王广场商业', shortName: '地王广场', type: '购物中心', status: '招商中', grade: 'A', lng: 106.577005, lat: 29.558009, area: '6.0万㎡' },
  { id: 13, name: '江北嘴中央公园管理用房（桂花街商业街）', shortName: '桂花街', type: '商业街区', status: '招商中', grade: 'B', lng: 106.574366, lat: 29.573134, area: '6000㎡' },
  { id: 14, name: '三洞桥风情外街项目', shortName: '风情外街', type: '商业街区', status: '招商中', grade: 'B', lng: 106.574366, lat: 29.573134, area: '5966㎡' },
  { id: 15, name: '渝海城北区B1层11#-20#商铺', shortName: '渝海B1', type: '社区商业', status: '招商中', grade: 'C', lng: 106.577005, lat: 29.558009, area: '4363㎡' },
  { id: 16, name: '渝海城北区A7-A9', shortName: '渝海A7', type: '商业街区', status: '招商中', grade: 'B', lng: 106.577005, lat: 29.558009, area: '2.4万㎡' },
  { id: 17, name: '中央广场商业B1层', shortName: '中央广场', type: '购物中心', status: '招商中', grade: 'B', lng: 106.566022, lat: 29.642726, area: '9881㎡' },
  { id: 18, name: '嘉陵江索道北站房整栋1号', shortName: '索道北站', type: '文旅商业', status: '招商中', grade: 'B', lng: 106.574366, lat: 29.573134, area: '1722㎡' },
  { id: 19, name: '金融城2号', shortName: '金融城2', type: '商业街区', status: '招商中', grade: 'B', lng: 106.574366, lat: 29.573134, area: '2.1万㎡' },
  { id: 20, name: '金融城3号', shortName: '金融城3', type: '商业街区', status: '招商中', grade: 'B', lng: 106.574366, lat: 29.573134, area: '1.4万㎡' },
  { id: 21, name: '金融城4号', shortName: '金融城4', type: '社区商业', status: '招商中', grade: 'C', lng: 106.574366, lat: 29.573134, area: '7822㎡' },
  { id: 22, name: '金融城8号', shortName: '金融城8', type: '社区商业', status: '招商中', grade: 'C', lng: 106.574366, lat: 29.573134, area: '2035㎡' },
  { id: 23, name: '公园里', shortName: '公园里', type: '社区商业', status: '招商中', grade: 'C', lng: 106.574366, lat: 29.573134, area: '1792㎡' },
  { id: 24, name: '重庆龙兴足球场商业门面', shortName: '球场门面', type: '体育场馆商业', status: '招商中', grade: 'B', lng: 106.794565, lat: 29.695644, area: '5942㎡' },
  { id: 25, name: '龙兴足球训练场', shortName: '训练场', type: '体育场馆商业', status: '招商中', grade: 'A', lng: 106.794565, lat: 29.695644, area: '3.5万㎡' },
  { id: 26, name: '龙兴足球训练场配套用房', shortName: '训练配套', type: '体育场馆商业', status: '招商中', grade: 'B', lng: 106.794565, lat: 29.695644, area: '4894㎡' },
  { id: 27, name: '两江国际影视城一期和二期一组团房屋', shortName: '影视城', type: '商业街区', status: '招商中', grade: 'B', lng: 106.794565, lat: 29.695644, area: '1.4万㎡' },
  { id: 28, name: '两江智慧创谷', shortName: '智慧创谷', type: '写字楼或公寓配套', status: '招商中', grade: 'A', lng: 106.500599, lat: 29.782120, area: '19.7万㎡' },
].map((project) => ({
  x: Math.max(5, Math.min(95, ((project.lng - 106.45) / .4) * 80 + 10)),
  y: Math.max(7, Math.min(93, ((29.80 - project.lat) / .26) * 72 + 14)),
  occupancy: `${(72 + (project.id * 3.7) % 23).toFixed(1)}%`,
  revenue: `${Math.round(86 + project.id * 37)}万元`,
  cost: `${Math.round(48 + project.id * 21)}万元`,
  collection: `${(91 + (project.id * 1.3) % 8).toFixed(1)}%`,
  matches: 3 + (project.id * 5) % 11,
  next: '完善项目经营与招商资料',
  owner: '新盛公司',
  ...project,
}))

const brands = [
  { code: 'XS-BRD-0001', name: '迪卡侬', category: '零售 · 运动户外', level1: '零售', level2: '运动户外', level3: '运动集合店', grade: 'A', intent: '较强', area: '800–2500㎡', engineering: '电量250kW · 可设上下水', property: '首层/跨层 · 层高≥4.5m', opening: '6–12个月', tags: ['全国连锁', '体育相关', '主力店'] },
  { code: 'XS-BRD-0002', name: '超级猩猩', category: '文体娱乐 · 运动健身', level1: '文体娱乐', level2: '运动健身', level3: '团体健身', grade: 'B', intent: '强', area: '300–600㎡', engineering: '上下水 · 新风 · 电量120kW', property: '2–4层 · 层高≥3.6m', opening: '3–6个月', tags: ['体育相关', '潮流品牌'] },
  { code: 'XS-BRD-0003', name: '海底捞', category: '餐饮 · 正餐', level1: '餐饮', level2: '正餐', level3: '火锅', grade: 'A', intent: '一般', area: '600–1200㎡', engineering: '上下水 · 燃气 · 排烟 · 隔油', property: '餐饮层 · 独立卸货', opening: '6–9个月', tags: ['全国连锁', '主力店'] },
  { code: 'XS-BRD-0004', name: '孩子王', category: '零售 · 母婴儿童', level1: '零售', level2: '母婴儿童', level3: '母婴集合店', grade: 'B', intent: '较强', area: '500–1500㎡', engineering: '电量180kW · 可设上下水', property: '低楼层 · 大面宽', opening: '6–10个月', tags: ['全国连锁', '亲子业态'] },
  { code: 'XS-BRD-0005', name: '名创优品', category: '零售 · 生活方式', level1: '零售', level2: '生活方式', level3: '精品集合店', grade: 'B', intent: '较强', area: '150–400㎡', engineering: '电量80kW · 无排烟要求', property: '首层优先 · 临主通道', opening: '3–5个月', tags: ['全国连锁', '生活方式'] },
  { code: 'XS-BRD-0006', name: '瑞幸咖啡', category: '餐饮 · 咖啡茶饮', level1: '餐饮', level2: '咖啡茶饮', level3: '咖啡店', grade: 'A', intent: '强', area: '40–120㎡', engineering: '上下水 · 电量60kW · 排水', property: '首层 · 临街/主通道', opening: '2–3个月', tags: ['全国连锁', '快速拓展'] },
]

const matchRows = [
  { brand: '超级猩猩', category: '运动健身', score: 91, coverage: 88, level: '优先推进', intent: '强', area: '300–600㎡', engineeringFit: '高度适配', propertyFit: '高度适配', opening: '3–6个月', dims: [100, 100, 100, 100, 75, 75, 75, 100] },
  { brand: '迪卡侬', category: '运动零售', score: 87, coverage: 94, level: '优先推进', intent: '较强', area: '800–2500㎡', engineeringFit: '适配', propertyFit: '适配', opening: '6–12个月', dims: [100, 100, 100, 75, 100, 50, 100, 75] },
  { brand: '瑞幸咖啡', category: '咖啡茶饮', score: 78, coverage: 81, level: '重点储备', intent: '强', area: '40–120㎡', engineeringFit: '适配', propertyFit: '部分适配', opening: '2–3个月', dims: [75, 100, 100, 75, 75, 50, 75, 100] },
  { brand: '海底捞', category: '餐饮正餐', score: null, coverage: 75, level: '门槛未通过', intent: '一般', area: '600–1200㎡', engineeringFit: '不适配', propertyFit: '部分适配', opening: '6–9个月', dims: [75, 100, 0, 75, 25, 50, 50, 50], gate: '品牌明确不接受体育场馆商业' },
  { brand: '名创优品', category: '生活方式零售', score: 66, coverage: 69, level: '初步结论', intent: '较强', area: '150–400㎡', engineeringFit: '部分适配', propertyFit: '适配', opening: '3–5个月', dims: [75, 75, 50, 50, 75, null, 75, 75] },
]

const tasks = [
  { title: '联系超级猩猩重庆拓展负责人', related: '重庆龙兴足球场 × 超级猩猩', due: '今天 17:00', owner: '陈昱', level: '高' },
  { title: '补充龙兴足球场非赛事日客流资料', related: '重庆龙兴足球场', due: '9月8日', owner: '赵青', level: '高' },
  { title: '确认迪卡侬电力与卸货条件', related: '迪卡侬 × 重庆龙兴足球场', due: '9月9日', owner: '李然', level: '中' },
  { title: '整理悦荟城首批候选品牌', related: '两江悦荟城', due: '9月10日', owner: '陈昱', level: '中' },
]

let amapLoader

function loadAmap() {
  if (window.AMap) return Promise.resolve(window.AMap)
  if (amapLoader) return amapLoader
  const key = import.meta.env.VITE_AMAP_JS_KEY
  if (!key) return Promise.reject(new Error('未配置高德地图 Key'))
  const securityCode = import.meta.env.VITE_AMAP_SECURITY_JSCODE
  if (securityCode) window._AMapSecurityConfig = { securityJsCode: securityCode }
  amapLoader = new Promise((resolve, reject) => {
    const script = document.createElement('script')
    script.src = `https://webapi.amap.com/maps?v=2.0&key=${encodeURIComponent(key)}&plugin=AMap.Scale,AMap.ToolBar`
    script.async = true
    script.onload = () => window.AMap ? resolve(window.AMap) : reject(new Error('高德地图加载失败'))
    script.onerror = () => reject(new Error('高德地图网络加载失败'))
    document.head.appendChild(script)
  })
  return amapLoader
}

function GlassSelect({ label, value, onChange, options, className = '' }) {
  return <label className={`glassSelect ${className}`}>
    <span className="srOnly">{label}</span>
    <select aria-label={label} value={value} onChange={(e) => onChange(e.target.value)}>
      {options.map((option) => {
        const item = typeof option === 'string' ? { value: option, label: option } : option
        return <option key={item.value} value={item.value}>{item.label}</option>
      })}
    </select>
    <ChevronDown size={15} aria-hidden="true" />
  </label>
}

function GlassDialog({ title, subtitle, onClose, children, actions, wide = false }) {
  React.useEffect(() => {
    const onKeyDown = (event) => event.key === 'Escape' && onClose()
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [onClose])
  return <div className="dialogBackdrop" role="presentation" onMouseDown={(event) => event.target === event.currentTarget && onClose()}>
    <section className={`glassDialog ${wide ? 'wide' : ''}`} role="dialog" aria-modal="true" aria-labelledby="dialog-title">
      <header><div><h2 id="dialog-title">{title}</h2>{subtitle && <p>{subtitle}</p>}</div><button type="button" className="dialogClose" onClick={onClose} aria-label="关闭"><X size={19} /></button></header>
      <div className="dialogBody">{children}</div>
      {actions && <footer>{actions}</footer>}
    </section>
  </div>
}

function DialogField({ label, children, full = false }) {
  return <label className={`dialogField ${full ? 'full' : ''}`}><span>{label}</span>{children}</label>
}

function EmptyState({ text = '没有符合条件的数据' }) {
  return <div className="emptyState"><Search size={22} /><strong>{text}</strong><span>可以调整筛选条件后重试</span></div>
}

function Logo() {
  return <div className="logo"><span className="logoMark">XS</span><div><strong>新盛资源管理</strong><small>BRAND × PROJECT</small></div></div>
}

function SideNav({ current, onNavigate }) {
  const { user, logout } = useAppData()
  const [panel, setPanel] = React.useState('')
  const actionsRef = React.useRef(null)
  React.useEffect(() => setPanel(''), [current])
  React.useEffect(() => {
    const closePanel = (event) => {
      if (!actionsRef.current?.contains(event.target)) setPanel('')
    }
    document.addEventListener('mousedown', closePanel)
    return () => document.removeEventListener('mousedown', closePanel)
  }, [])
  return <aside className="sidebar">
    <Logo />
    <div className="workspaceLabel">业务工作台</div>
    <nav>
      {nav.map(({ id, label, icon: Icon, badge }) => (
        <button type="button" aria-label={label} title={label} className={`navItem ${current === id ? 'active' : ''}`} key={label} onClick={() => onNavigate(id)}>
          <Icon size={19} strokeWidth={1.8} />
          <span>{label}</span>
          {badge && <em>{badge}</em>}
        </button>
      ))}
    </nav>
    <div className="globalUtilities">
      <button type="button" aria-label="Excel 导入" title="Excel 导入" className={`navItem ${current === 'import' ? 'active' : ''}`} onClick={() => onNavigate('import')}><FileSpreadsheet size={19} /><span>Excel 导入</span></button>
      <button type="button" aria-label="系统配置" title="系统配置" className={`navItem ${current === 'settings' ? 'active' : ''}`} onClick={() => onNavigate('settings')}><Settings2 size={19} /><span>系统配置</span></button>
      <div className="topActions globalActions" ref={actionsRef}>
        <div className="topPopoverWrap"><button type="button" className="iconButton" aria-label="通知" aria-expanded={panel === 'notice'} onClick={() => setPanel(panel === 'notice' ? '' : 'notice')}><Bell size={19} /><span className="notificationDot" /></button>{panel === 'notice' && <div className="topPopover noticePopover"><strong>待处理通知</strong><button type="button" onClick={() => { onNavigate('matching'); setPanel('') }}>12 个品牌匹配结果待研判 <ArrowRight size={13} /></button><button type="button" onClick={() => { onNavigate('followup'); setPanel('') }}>5 项候选跟进即将到期 <ArrowRight size={13} /></button></div>}</div>
        <div className="topPopoverWrap"><button type="button" className="user" aria-expanded={panel === 'user'} onClick={() => setPanel(panel === 'user' ? '' : 'user')}><CircleUserRound size={31} /><div><strong>{user?.display_name || user?.username}</strong><small>{user?.role_label || user?.role}</small></div><ChevronDown size={15} /></button>{panel === 'user' && <div className="topPopover userPopover userMenuPanel"><div className="userMenuHead"><strong>{user?.display_name || user?.username}</strong><small>@{user?.username} · {user?.role_label}</small></div><button type="button" onClick={() => { onNavigate('settings'); setPanel('') }}>账户与权限设置</button><button type="button" onClick={() => { onNavigate('import'); setPanel('') }}>数据导入中心</button><button type="button" className="userMenuLogout" onClick={() => { setPanel(''); logout() }}>退出登录</button></div>}</div>
      </div>
    </div>
    <div className="sidebarFoot"><span className="statusDot" />UI 原型 · 演示数据</div>
  </aside>
}

function Stat({ value, label, meta, tone }) {
  return <div className="stat"><div className={tone || ''}>{value}</div><span>{label}</span><small>{meta}</small></div>
}

function FilterBar({ filters, onFiltersChange, view, onViewChange, advanced, onAdvancedChange }) {
  const [draftQuery, setDraftQuery] = React.useState(filters.query)
  React.useEffect(() => setDraftQuery(filters.query), [filters.query])
  const submitSearch = (event) => {
    event.preventDefault()
    onFiltersChange({ ...filters, query: draftQuery.trim() })
  }
  return <div className="filterBar">
    <form className="searchBox submitSearchBox" role="search" onSubmit={submitSearch}><Search size={17} /><input aria-label="搜索项目" value={draftQuery} onChange={(event) => setDraftQuery(event.target.value)} placeholder="搜索项目、地址或运营方" /><button type="submit" className="searchSubmit">搜索</button></form>
    <GlassSelect label="城市" value={filters.city} onChange={(city) => onFiltersChange({ ...filters, city })} options={['重庆市', '全部城市']} />
    <GlassSelect label="项目类型" value={filters.type} onChange={(type) => onFiltersChange({ ...filters, type })} options={['全部类型', '体育场馆商业', '购物中心', '商业街区', '社区商业', '文旅商业', '写字楼或公寓配套']} />
    <GlassSelect label="项目状态" value={filters.status} onChange={(status) => onFiltersChange({ ...filters, status })} options={['全部状态', '筹备', '招商中', '已开业']} />
    <button type="button" className={advanced ? 'activeFilterButton' : ''} onClick={() => onAdvancedChange(!advanced)}><ListFilter size={16} /> 更多筛选 <span className="filterCount">{filters.grade === '全部等级' ? 3 : 4}</span></button>
    <div className="viewSwitch">{['地图', '列表', '分屏'].map((item) => <button type="button" className={view === item ? 'selected' : ''} key={item} onClick={() => onViewChange(item)}>{item === '地图' && <Map size={15} />}{item}</button>)}</div>
  </div>
}

function spreadProjectLocations(items) {
  const groups = new globalThis.Map()
  items.forEach((project) => {
    const key = `${project.lng.toFixed(6)},${project.lat.toFixed(6)}`
    groups.set(key, [...(groups.get(key) || []), project.id])
  })
  return items.map((project) => {
    const group = groups.get(`${project.lng.toFixed(6)},${project.lat.toFixed(6)}`)
    if (group.length === 1) return project
    const index = group.indexOf(project.id)
    const ring = Math.floor(index / 8)
    const angle = (index % 8) / Math.min(8, group.length) * Math.PI * 2
    const radius = .024 + ring * .020
    const lng = project.lng + Math.cos(angle) * radius * 1.18
    const lat = project.lat + Math.sin(angle) * radius
    return {
      ...project,
      lng,
      lat,
      x: Math.max(5, Math.min(95, ((lng - 106.45) / .4) * 80 + 10)),
      y: Math.max(7, Math.min(93, ((29.80 - lat) / .26) * 72 + 14)),
    }
  })
}

function DemoMap({ selected, onSelect, items = projects }) {
  const canvasRef = React.useRef(null)
  const mapRef = React.useRef(null)
  const markerRefs = React.useRef(new globalThis.Map())
  const [mapStatus, setMapStatus] = React.useState('loading')
  const visibleItems = React.useMemo(() => spreadProjectLocations(items), [items])

  React.useEffect(() => {
    let disposed = false
    loadAmap().then((AMap) => {
      if (disposed || !canvasRef.current) return
      const map = new AMap.Map(canvasRef.current, {
        center: [106.68, 29.68], zoom: 10, viewMode: '2D', mapStyle: 'amap://styles/whitesmoke',
      })
      map.addControl(new AMap.Scale())
      mapRef.current = map
      setMapStatus('ready')
    }).catch(() => {
      if (!disposed) setMapStatus('fallback')
    })
    return () => {
      disposed = true
      markerRefs.current.clear()
      if (mapRef.current) mapRef.current.destroy()
      mapRef.current = null
    }
  }, [])

  React.useEffect(() => {
    const map = mapRef.current
    if (!map || !window.AMap || mapStatus !== 'ready') return
    map.clearMap()
    markerRefs.current.clear()
    const markers = visibleItems.map((project) => {
      const content = document.createElement('button')
      content.type = 'button'
      content.className = `amapProjectMarker type-${project.id % 3}${selected.id === project.id ? ' selected' : ''}`
      content.setAttribute('aria-label', project.name)
      const label = document.createElement('span')
      label.textContent = project.shortName
      content.appendChild(label)
      content.addEventListener('click', () => onSelect(project))
      const marker = new window.AMap.Marker({ position: [project.lng, project.lat], content, anchor: 'bottom-center' })
      markerRefs.current.set(project.id, content)
      return marker
    })
    if (markers.length) {
      map.add(markers)
      map.setFitView(markers, false, [88, 62, 64, 62], 11)
    }
  }, [visibleItems, mapStatus, onSelect, selected.id])

  return <section className={`mapSurface ${mapStatus === 'ready' ? 'hasRealMap' : ''}`} aria-label="项目资源地图">
    <div className="amapCanvas" ref={canvasRef} />
    {mapStatus !== 'ready' && <div className="mapFallback">
      <div className="mapGrid" />
      <div className="district d1">两江新区</div><div className="district d2">江北区</div><div className="district d3">渝北区</div>
      <div className="river river1" /><div className="river river2" /><div className="road road1" /><div className="road road2" />
      {visibleItems.map((p) => <button key={p.id} className={`marker ${selected.id === p.id ? 'selected' : ''} type-${p.id % 3}`} style={{ left: `${p.x}%`, top: `${p.y}%` }} onClick={() => onSelect(p)} aria-label={p.name}><span>{p.shortName}</span><i /></button>)}
    </div>}
    <div className="mapHint"><MapPin size={15} />{mapStatus === 'ready' ? `高德地图 · ${items.length} 个项目` : mapStatus === 'loading' ? '正在加载高德地图…' : '地图暂未加载，已切换示意视图'}</div>
    <div className="mapTools"><button type="button" onClick={() => mapRef.current?.zoomIn()} aria-label="放大">＋</button><button type="button" onClick={() => mapRef.current?.zoomOut()} aria-label="缩小">−</button><button type="button" onClick={() => { mapRef.current?.setZoomAndCenter(10, [106.68, 29.68]) }} aria-label="回到重庆">◎</button></div>
    <div className="legend"><span><i className="stadium" />体育场馆</span><span><i className="mall" />购物中心</span><span><i className="street" />街区及社区</span></div>
  </section>
}

function DetailCard({ project, onMatch, onOpen }) {
  return <aside className="detailCard">
    <div className="cardHead"><div><span className="code">XS-PRJ-{String(project.id).padStart(4, '0')}</span><h2>{project.name}</h2></div><span className={`grade grade${project.grade}`}>{project.grade}</span></div>
    <div className="tagRow"><span>{project.type}</span><span className="green">{project.status}</span></div>
    <div className="heroMetric"><strong>{project.matches}</strong><span>个匹配品牌</span><small>其中 3 个优先推进</small></div>
    <dl className="projectFacts"><div><dt>商业体量</dt><dd>{project.area}</dd></div><div><dt>项目定位</dt><dd>运动生活目的地</dd></div><div><dt>招商阶段</dt><dd>招商启动</dd></div><div><dt>合作意愿</dt><dd className="positive">较强</dd></div></dl>
    <div className="progressBlock"><div><span>资料完整度</span><strong>82%</strong></div><div className="progress"><i style={{ width: '82%' }} /></div></div>
    <div className="nextAction"><span>下一步任务</span><strong>{project.next}</strong><small>负责人 {project.owner} · 9月8日前</small></div>
    <div className="cardActions"><button type="button" className="primary" onClick={onMatch}><Sparkles size={16} />查看匹配品牌</button><button type="button" onClick={onOpen}>打开完整档案</button></div>
  </aside>
}

function ProjectTenantMixPanel({ projectName }) {
  const [state, setState] = React.useState({ loading: true, mix: null, plan: null, error: false })
  React.useEffect(() => {
    let alive = true
    ;(async () => {
      try {
        const id = await resolveProjectIdByName(projectName)
        if (!id) { if (alive) setState({ loading: false, mix: null, plan: null, error: false }); return }
        const [mix, plan] = await Promise.all([getTenantMix(id), getAdjustmentPlan(id)])
        if (alive) setState({ loading: false, mix, plan, error: false })
      } catch {
        if (alive) setState({ loading: false, mix: null, plan: null, error: true })
      }
    })()
    return () => { alive = false }
  }, [projectName])

  const wan = (x) => `${((x || 0) / 10000).toFixed(1)}万`
  const pct = (x) => `${((x || 0) * 100).toFixed(1)}%`
  if (state.loading) return <div className="tenantMixPanel"><p className="tenantMixHint">正在载入业态与调改数据…</p></div>
  if (state.error) return <div className="tenantMixPanel"><p className="tenantMixHint">后端未连接，暂无法载入业态与调改数据。</p></div>
  if (!state.mix) return <div className="tenantMixPanel"><p className="tenantMixHint">该项目在后端暂无台账数据，无法生成业态与调改。</p></div>

  const { mix, plan } = state
  const s = plan?.summary
  const cur = s?.current, plan2 = s?.planned, delta = s?.delta
  return <div className="tenantMixPanel">
    <div className="tenantMixSection">
      <h3>现有业态构成</h3>
      <div className="tenantMixStat">
        <span>铺位 {mix.totals.unit_total} 个</span><span>出租率 {pct(mix.totals.occupancy_rate)}</span>
        <span>月租金 {wan(mix.totals.rent_total)}</span><span>空置 {mix.vacant.units} 个</span>
      </div>
      <div className="tenantMixTable">
        <div className="tenantMixHead"><span>业态</span><span>铺位</span><span>计租面积㎡</span><span>月租金</span><span>租金占比</span></div>
        {mix.by_format.map((r) => <div className="tenantMixRow" key={r.format}><strong>{r.format}</strong><span>{r.units}</span><span>{Math.round(r.area)}</span><span className="incomeText">{wan(r.rent)}</span><span>{pct(r.rent_pct)}</span></div>)}
        {mix.vacant.units > 0 && <div className="tenantMixRow vacantRow"><strong>空置</strong><span>{mix.vacant.units}</span><span>{Math.round(mix.vacant.area)}</span><span>—</span><span>—</span></div>}
      </div>
    </div>

    {s && <div className="tenantMixSection">
      <h3>调改后测算 <em>（现状 → 计划）</em></h3>
      <div className="tenantMixCompare">
        <div><span>出租率</span><strong>{pct(cur.occupancy_rate)} → {pct(plan2.occupancy_rate)}</strong><b className={delta.occupancy_pts >= 0 ? 'up' : 'down'}>{delta.occupancy_pts >= 0 ? '+' : ''}{(delta.occupancy_pts * 100).toFixed(1)}pt</b></div>
        <div><span>月租金</span><strong>{wan(cur.rent_total)} → {wan(plan2.rent_total)}</strong><b className={delta.rent_total >= 0 ? 'up' : 'down'}>{delta.rent_total >= 0 ? '+' : ''}{wan(delta.rent_total)}</b></div>
        <div><span>租金坪效</span><strong>{cur.rent_psm} → {plan2.rent_psm}</strong><b>元/㎡/月</b></div>
        <div><span>经营净收益 NOI</span><strong>{wan(cur.noi)} → {wan(plan2.noi)}</strong><b className={delta.noi >= 0 ? 'up' : 'down'}>{delta.noi >= 0 ? '+' : ''}{wan(delta.noi)}</b></div>
      </div>
    </div>}

    <div className="tenantMixSection">
      <h3>调改计划清单 <em>（{plan?.items?.length || 0} 条）</em></h3>
      {plan?.items?.length ? <div className="tenantMixTable">
        <div className="tenantMixHead planHead"><span>铺位</span><span>动作</span><span>业态调整</span><span>预期月租金</span><span>状态</span></div>
        {plan.items.map((it) => <div className="tenantMixRow planRow" key={it.unit_id}><strong>{it.unit_code}</strong><span className={`planAction act-${it.action}`}>{it.action}</span><span>{(it.from_format || '空置')} → {it.to_format || '—'}</span><span className="incomeText">{wan(it.expected_rent)}</span><span>{it.plan_status}</span></div>)}
      </div> : <p className="tenantMixHint">暂无调改计划。</p>}
    </div>
  </div>
}

function ProjectArchive({ project }) {
  const [tab, setTab] = React.useState('overview')
  return <div className="projectArchive">
    <div className="projectArchiveTabs" role="tablist" aria-label="项目档案视图">
      <button type="button" role="tab" aria-selected={tab === 'overview'} onClick={() => setTab('overview')}>概览</button>
      <button type="button" role="tab" aria-selected={tab === 'tenant'} onClick={() => setTab('tenant')}>业态与调改</button>
      <button type="button" role="tab" aria-selected={tab === 'sandbox'} onClick={() => setTab('sandbox')}>铺位沙盘</button>
    </div>
    {tab === 'overview' && <div className="archiveGrid">
      <div><span>项目编号</span><strong>XS-PRJ-{String(project.id).padStart(4, '0')}</strong></div><div><span>项目等级</span><strong>{project.grade} 级</strong></div>
      <div><span>项目类型</span><strong>{project.type}</strong></div><div><span>招商状态</span><strong>{project.status}</strong></div>
      <div><span>经营面积</span><strong>{project.area}</strong></div><div><span>综合出租率</span><strong>{project.occupancy}</strong></div>
      <div><span>本月经营收入</span><strong>{project.revenue}</strong></div><div><span>本月经营成本</span><strong>{project.cost}</strong></div>
      <div><span>租金收缴率</span><strong>{project.collection}</strong></div><div><span>项目负责人</span><strong>{project.owner}</strong></div>
      <div className="full"><span>项目定位</span><p>运动生活目的地，覆盖赛事消费、家庭客群与周边社区的复合型商业场景。</p></div>
    </div>}
    {tab === 'tenant' && <ProjectTenantMixPanel projectName={project.name} />}
    {tab === 'sandbox' && <ProjectLayoutSandbox projectName={project.name} />}
  </div>
}

function BrandArchive({ brand }) {
  return <div className="archiveGrid">
    <div><span>品牌编号</span><strong>{brand.code}</strong></div><div><span>品牌等级</span><strong>{brand.grade} 级</strong></div>
    <div><span>一级业态</span><strong>{brand.level1}</strong></div><div><span>二级业态</span><strong>{brand.level2}</strong></div>
    <div><span>三级业态</span><strong>{brand.level3}</strong></div><div><span>合作意愿</span><strong>{brand.intent}</strong></div>
    <div><span>面积需求</span><strong>{brand.area}</strong></div><div><span>预计开店周期</span><strong>{brand.opening}</strong></div>
    <div className="full"><span>工程条件</span><strong>{brand.engineering}</strong></div>
    <div className="full"><span>物业偏好</span><strong>{brand.property}</strong></div>
    <div className="full"><span>品牌标签</span><div className="tagCloud">{brand.tags.map((tag) => <span key={tag}>{tag}</span>)}</div></div>
    <div className="full"><span>最近沟通</span><p>已发送项目资料，等待品牌拓展负责人反馈；建议 3 个工作日内再次跟进。</p></div>
  </div>
}

function SectionTitle({ title, meta, action }) {
  return <div className="sectionTitle"><div><h2>{title}</h2>{meta && <span>{meta}</span>}</div>{action}</div>
}

function AdvancedFilterPanel({ children, onReset, onClose, className = '' }) {
  return <section className={`advancedFilterPanel ${className}`} aria-label="高级筛选">
    <div className="advancedFilterHeading"><div><strong>高级筛选</strong><span>组合条件可进一步缩小结果范围</span></div><button type="button" onClick={onClose}>收起</button></div>
    <div className="advancedFilterFields">{children}<button type="button" className="filterReset" onClick={onReset}>重置筛选</button></div>
  </section>
}

function DataDetailTable({ columns, rows, note }) {
  return <div className="dataDetail">
    <div className="dataDetailScroll"><table><thead><tr>{columns.map((column) => <th key={column}>{column}</th>)}</tr></thead><tbody>{rows.map((row, index) => <tr key={`${row[0]}-${index}`}>{row.map((cell, cellIndex) => <td key={`${cellIndex}-${cell}`}>{cell}</td>)}</tr>)}</tbody></table></div>
    {note && <p className="dataDetailNote">{note}</p>}
  </div>
}

function DashboardPage({ onNavigate }) {
  const { projects, brands, ops, risk } = useAppData()
  const [selected, setSelected] = React.useState(null)
  const [filters, setFilters] = React.useState({ city: '重庆市', type: '全部类型', status: '全部状态' })
  const [detailKey, setDetailKey] = React.useState('')
  const filteredProjects = React.useMemo(() => projects.filter((project) =>
    (filters.type === '全部类型' || project.type === filters.type) &&
    (filters.status === '全部状态' || project.status === filters.status)
  ), [filters, projects])
  React.useEffect(() => {
    if (filteredProjects.length && (!selected || !filteredProjects.some((project) => project.id === selected.id))) {
      setSelected(filteredProjects[0])
    }
  }, [filteredProjects, selected])
  const kpi = ops?.kpi
  const dashboardDetails = {
    projects: { title: '在管项目明细', subtitle: `项目总数 ${projects.length}`, columns: ['项目名称', '项目类型', '经营面积', '出租率', '本期实收', '本期成本'], rows: projects.map((item) => [item.name, item.type, item.area, item.occupancy, item.revenue, item.cost]), note: `已展示全部 ${projects.length} 个在管项目；出租率/收支来自经营台账实时口径。` },
    brands: { title: '品牌资源明细', subtitle: `品牌资源总数 ${brands.length}`, columns: ['品牌名称', '一级业态', '二级业态', '三级业态', '面积需求', '工程条件'], rows: brands.map((item) => [item.name, item.level1, item.level2, item.level3, item.area, item.engineering]), note: '品牌资源按资产方拓店条件统计。' },
    occupancy: { title: '项目出租率明细', subtitle: `组合出租率 ${fmtPct(kpi?.occupancy_rate)}`, columns: ['项目名称', '经营面积', '出租率', '租金收缴率'], rows: projects.map((item) => [item.name, item.area, item.occupancy, item.collection]), note: '出租率 =（在租+自营）铺位数 / 铺位总数，按项目经营台账实时计算。' },
    revenue: { title: '项目经营收支明细', subtitle: `本期实收合计 ${fmtWan(kpi?.revenue_received)}`, columns: ['项目名称', '本期实收', '本期成本', '租金收缴率'], rows: projects.map((item) => [item.name, item.revenue, item.cost, item.collection]), note: '实收/成本均为经营台账现金口径实时汇总。' },
    noi: { title: '经营净收益明细', subtitle: `本期 NOI ${fmtWan(kpi?.noi)}`, columns: ['项目名称', '本期实收', '本期成本', '经营净收益 NOI'], rows: projects.filter((p) => p.noi != null).sort((a, b) => b.noi - a.noi).map((item) => [item.name, item.revenue, item.cost, fmtWan(item.noi)]), note: 'NOI = 实收收入 − 经营成本；按项目排序，越靠前贡献越大。' },
    collection: { title: '租金收缴明细', subtitle: `综合收缴率 ${fmtPct(kpi?.collect_rate)}`, columns: ['项目名称', '收缴率', '欠租金额', '负责人'], rows: projects.filter((p) => p.arrears != null).sort((a, b) => b.arrears - a.arrears).map((item) => [item.name, item.collection, fmtWan(item.arrears), item.owner]), note: '按欠租金额从高到低排序，用于优先跟进。' },
  }
  const activeDetail = dashboardDetails[detailKey]
  const riskFocus = risk ? [
    ...risk.arrears_top.slice(0, 2).map((r) => ({ tone: 'warning', title: `${r.project_name} 存在欠租`, meta: `欠租 ${fmtWan(r.arrears)} · 建议跟进催收` })),
    ...risk.expiring_leases.slice(0, 2).map((e) => ({ tone: e.days_left <= 30 ? 'critical' : 'warning', title: `${e.project_name} · ${e.tenant} 租约将到期`, meta: `${e.days_left} 天后到期(${e.lease_end}) · 月租 ${fmtWan(e.monthly_rent)}` })),
  ] : []
  if (!projects.length) return <div className="pageContent dashboardPage"><EmptyState text="正在加载真实经营数据…" /></div>
  return <div className="pageContent dashboardPage dashboardMapPage">
    <section className="cockpit-commandBar">
      <div><span>集团经营快照</span><strong>{kpi ? `${projects.length} 个项目 · 组合出租率 ${fmtPct(kpi.occupancy_rate)}` : '经营台账加载中'}</strong><small>实时数据 · 来自经营台账聚合</small></div>
      <div className="cockpit-commandMetrics">
        <button onClick={() => setDetailKey('occupancy')}><span>组合出租率</span><strong>{fmtPct(kpi?.occupancy_rate)}</strong><small>{kpi?.unit_total ?? '—'} 个铺位</small></button>
        <button onClick={() => setDetailKey('noi')}><span>本期 NOI</span><strong>{fmtWan(kpi?.noi)}</strong><small>实收 − 成本</small></button>
        <button onClick={() => setDetailKey('collection')}><span>租金收缴率</span><strong>{fmtPct(kpi?.collect_rate)}</strong><small>欠租 {fmtWan(kpi?.arrears)}</small></button>
        <button onClick={() => onNavigate('management')}><span>待处理风险</span><strong>{(risk?.summary.projects_with_arrears || 0) + (risk?.summary.expiring_lease_count || 0)}项</strong><small className={risk?.summary.expiring_lease_count ? 'warn' : ''}>欠租+90天内到期租约</small></button>
      </div>
      <button className="cockpit-manageEntry" onClick={() => onNavigate('management')}>进入管理中心 <ArrowRight size={15} /></button>
    </section>
    <section className="dashboardOperatingLayout">
      <div className="dashboardMapHero">
        <DemoMap selected={selected || filteredProjects[0]} onSelect={setSelected} items={filteredProjects} />
        <div className="dashboardFilterGroup dashboardMapFilters">
          <GlassSelect label="城市" value={filters.city} onChange={(city) => setFilters({ ...filters, city })} options={['重庆市', '全部城市']} />
          <GlassSelect label="项目类型" value={filters.type} onChange={(type) => setFilters({ ...filters, type })} options={['全部类型', '体育场馆商业', '购物中心', '商业街区', '社区商业', '文旅商业', '写字楼或公寓配套']} />
          <GlassSelect label="项目状态" value={filters.status} onChange={(status) => setFilters({ ...filters, status })} options={['全部状态', '筹备', '招商中', '已开业']} />
        </div>
        {selected && <aside className="dashboardMapSelection">
          <div className="dashboardSelectionHead"><div><span>当前项目</span><h3>{selected.name}</h3><p>{selected.type} · {selected.status}</p></div><i className={`grade grade${selected.grade}`}>{selected.grade}</i></div>
          <div className="dashboardSelectionFacts"><div><span>经营面积</span><strong>{selected.area}</strong></div><div><span>出租率</span><strong>{selected.occupancy}</strong></div><div><span>本期实收</span><strong>{selected.revenue}</strong></div></div>
          <button onClick={() => onNavigate('map')}>查看项目地图详情 <ArrowRight size={14} /></button>
        </aside>}
      </div>
      <div className="dashboardMetricVisuals" aria-label="核心经营指标">
        <button type="button" className="metricVisualCard" onClick={() => setDetailKey('projects')}><div className="metricVisualHead"><span>在管项目</span><small>资产经营管理范围</small></div><div className="metricVisualBody"><strong>{projects.length}<em>个</em></strong><div className="projectBars"><i /><i /><i /><i /></div></div><p>品牌资源 {brands.length} 个</p><span className="metricLink">查看明细 <ArrowRight size={13} /></span></button>
        <button type="button" className="metricVisualCard" onClick={() => setDetailKey('noi')}><div className="metricVisualHead"><span>经营净收益 NOI</span><small>实收扣除经营成本</small></div><div className="metricVisualBody"><strong>{fmtWan(kpi?.noi)}</strong><div className="brandStack"><i /><i /><i /></div></div><p>实收 {fmtWan(kpi?.revenue_received)} · 成本 {fmtWan(kpi?.cost)}</p><span className="metricLink">查看明细 <ArrowRight size={13} /></span></button>
        <button type="button" className="metricVisualCard" onClick={() => setDetailKey('occupancy')}><div className="metricVisualHead"><span>组合出租率</span><small>按铺位数计算</small></div><div className="metricVisualBody"><strong>{fmtPct(kpi?.occupancy_rate)}</strong><div className="occupancyRing"><span>{kpi ? Math.round(kpi.occupancy_rate * 100) : 0}%</span></div></div><p>{kpi?.unit_total ?? '—'} 个铺位</p><span className="metricLink">查看明细 <ArrowRight size={13} /></span></button>
        <button type="button" className="metricVisualCard revenueMetric" onClick={() => setDetailKey('collection')}><div className="metricVisualHead"><span>租金收缴率</span><small>实收 / 应收</small></div><div className="metricVisualBody"><strong>{fmtPct(kpi?.collect_rate)}</strong></div><p>欠租合计 {fmtWan(kpi?.arrears)}</p><span className="metricLink">查看明细 <ArrowRight size={13} /></span></button>
      </div>
    </section>
    <section className="cockpit-decisionGrid">
      <div className="panel cockpit-focusPanel"><SectionTitle title="经营风险焦点" meta="欠租 / 临期租约自动汇总" action={<button className="textAction" onClick={() => onNavigate('management')}>查看全部 <ArrowRight size={14} /></button>} />{riskFocus.length ? riskFocus.map((item, i) => <button key={i} onClick={() => onNavigate('management')}><i className={item.tone} /><span><strong>{item.title}</strong><small>{item.meta}</small></span><em>{item.tone === 'critical' ? '需尽快处理' : '关注中'}</em></button>) : <p className="permDisabledHint" style={{ padding: '14px 18px' }}>暂无欠租或临期租约风险。</p>}</div>
      <div className="panel cockpit-approvalPanel"><SectionTitle title="空置铺位 Top" meta="按空置面积排序，招商优先级参考" />{risk?.vacant_top.length ? risk.vacant_top.slice(0, 3).map((v) => <button key={v.project_id} onClick={() => onNavigate('projects')}><span><strong>{v.project_name}</strong><small>空置 {v.vacant_units} 个铺位 · {Math.round(v.vacant_area)}㎡</small></span><ArrowRight size={14} /></button>) : <p className="permDisabledHint" style={{ padding: '14px 18px' }}>暂无空置铺位数据。</p>}</div>
    </section>
    {activeDetail && <GlassDialog title={activeDetail.title} subtitle={activeDetail.subtitle} onClose={() => setDetailKey('')} wide actions={<button type="button" className="primaryAction" onClick={() => setDetailKey('')}>关闭</button>}><DataDetailTable columns={activeDetail.columns} rows={activeDetail.rows} note={activeDetail.note} /></GlassDialog>}
  </div>
}

function MapPage({ onNavigate }) {
  const { projects, ops } = useAppData()
  const [selected, setSelected] = React.useState(null)
  const [filters, setFilters] = React.useState({ query: '', city: '重庆市', type: '全部类型', status: '全部状态', grade: '全部等级' })
  const [view, setView] = React.useState('分屏')
  const [advanced, setAdvanced] = React.useState(false)
  const [archiveOpen, setArchiveOpen] = React.useState(false)
  const filteredProjects = React.useMemo(() => projects.filter((project) =>
    (!filters.query || `${project.name}${project.type}${project.owner}`.includes(filters.query)) &&
    (filters.type === '全部类型' || project.type === filters.type) &&
    (filters.status === '全部状态' || project.status === filters.status) &&
    (filters.grade === '全部等级' || project.grade === filters.grade)
  ), [filters, projects])
  React.useEffect(() => {
    if (filteredProjects.length && (!selected || !filteredProjects.some((project) => project.id === selected.id))) {
      setSelected(filteredProjects[0])
    }
  }, [filteredProjects, selected])
  const kpi = ops?.kpi
  const totalArea = projects.reduce((s, p) => s + (p.areaM2 || 0), 0)
  if (!projects.length) return <div className="pageContent"><section className="panel"><EmptyState text="正在加载项目数据…" /></section></div>
  return <>
    <section className="overviewStrip">
      <Stat value={String(projects.length)} label="项目总数" meta="全部在管项目" />
      <Stat value={fmtAreaWan(totalArea)} label="总经营面积" meta="资产经营口径" tone="cyan" />
      <Stat value={fmtAreaWan(kpi?.area_total)} label="可租赁面积" meta="可经营铺位面积" />
      <Stat value={fmtAreaWan(kpi?.area_rented)} label="已出租面积" meta="当前有效合同" tone="orange" />
      <div className="coverage"><div><strong>{fmtPct(kpi?.area_occupancy_rate)}</strong><span>综合出租率</span></div><div className="progress"><i style={{ width: fmtPct(kpi?.area_occupancy_rate) }} /></div><small>按可租赁面积加权统计</small></div>
    </section>
    <FilterBar filters={filters} onFiltersChange={setFilters} view={view} onViewChange={setView} advanced={advanced} onAdvancedChange={setAdvanced} />
    {advanced && <AdvancedFilterPanel onClose={() => setAdvanced(false)} onReset={() => setFilters({ query: '', city: '重庆市', type: '全部类型', status: '全部状态', grade: '全部等级' })}><label className="advancedFilterField"><span>项目等级</span><GlassSelect label="项目等级" value={filters.grade} onChange={(grade) => setFilters({ ...filters, grade })} options={['全部等级', 'A', 'B', 'C']} /></label></AdvancedFilterPanel>}
    {filteredProjects.length === 0 || !selected ? <div className="pageContent"><section className="panel"><EmptyState /></section></div> : view === '列表' ? <div className="mapListView" role="table" aria-label="项目资源列表"><div className="mapListHeader" role="row"><span role="columnheader">等级</span><span role="columnheader">项目名称</span><span role="columnheader">商业体量</span><span role="columnheader">负责人</span><span role="columnheader">操作</span></div>{filteredProjects.map((project) => <button type="button" key={project.id} className={`mapListRow ${selected.id === project.id ? 'selected' : ''}`} aria-label={`打开${project.name}项目档案`} onClick={() => { setSelected(project); setArchiveOpen(true) }}><span className={`grade grade${project.grade}`}>{project.grade}</span><div><strong>{project.name}</strong><small>{project.type} · {project.status}</small></div><span>{project.area}</span><span>{project.owner}</span><span className="rowAction">查看 <ArrowRight size={14} /></span></button>)}</div> : view === '地图' ? <div className="mapOnlyLayout"><DemoMap selected={selected} onSelect={setSelected} items={filteredProjects} /></div> : <div className="mapLayout"><DemoMap selected={selected} onSelect={setSelected} items={filteredProjects} /><DetailCard project={selected} onMatch={() => onNavigate('matching')} onOpen={() => setArchiveOpen(true)} /></div>}
    {archiveOpen && selected && <GlassDialog title={selected.name} subtitle="项目完整档案" onClose={() => setArchiveOpen(false)} wide actions={<><button type="button" onClick={() => setArchiveOpen(false)}>关闭</button><button type="button" className="primaryAction" onClick={() => { setArchiveOpen(false); onNavigate('matching') }}>进入匹配工作台</button></>}><ProjectArchive project={selected} /></GlassDialog>}
  </>
}

function BrandsPage({ onNavigate, notify }) {
  const { brands, can } = useAppData()
  const [brandList, setBrandList] = React.useState(brands)
  const [selected, setSelected] = React.useState(null)
  React.useEffect(() => { setBrandList(brands) }, [brands])
  const [queryDraft, setQueryDraft] = React.useState('')
  const [query, setQuery] = React.useState('')
  const [category, setCategory] = React.useState('全部业态')
  const [grade, setGrade] = React.useState('全部等级')
  const [intent, setIntent] = React.useState('全部意愿')
  const [showAdvanced, setShowAdvanced] = React.useState(false)
  const [createOpen, setCreateOpen] = React.useState(false)
  const [archiveOpen, setArchiveOpen] = React.useState(false)
  const [form, setForm] = React.useState({ name: '', level1: '零售', level2: '运动户外', level3: '运动集合店', grade: 'B', intent: '一般', area: '100–300㎡', engineering: '可设上下水 · 电量120kW', property: '首层优先 · 层高≥4.2m', opening: '6–9个月' })
  const visibleBrands = brandList.filter((brand) =>
    (!query || `${brand.name}${brand.category}${brand.level3}${brand.engineering}${brand.property}${brand.tags.join('')}`.includes(query)) &&
    (category === '全部业态' || brand.category.startsWith(category)) &&
    (grade === '全部等级' || brand.grade === grade) &&
    (intent === '全部意愿' || brand.intent === intent)
  )
  React.useEffect(() => {
    if (visibleBrands.length && (!selected || !visibleBrands.some((brand) => brand.code === selected.code))) {
      setSelected(visibleBrands[0])
    }
  }, [visibleBrands, selected])
  const createBrand = (event) => {
    event.preventDefault()
    const brand = { ...form, category: `${form.level1} · ${form.level2}`, code: `XS-BRD-${String(brandList.length + 1).padStart(4, '0')}`, tags: ['新建品牌', form.level1] }
    setBrandList((list) => [...list, brand])
    setSelected(brand)
    setQueryDraft(''); setQuery(''); setCategory('全部业态'); setGrade('全部等级'); setIntent('全部意愿'); setCreateOpen(false)
    notify(`品牌“${brand.name}”已加入当前清单`)
  }
  return <div className="pageContent resourcePage">
    <div className="actionBar"><form className="searchBox submitSearchBox" role="search" onSubmit={(event) => { event.preventDefault(); setQuery(queryDraft.trim()) }}><Search size={17} /><input aria-label="搜索品牌" value={queryDraft} onChange={(e) => setQueryDraft(e.target.value)} placeholder="搜索品牌名称、业态或拓店条件" /><button type="submit" className="searchSubmit">搜索</button></form><GlassSelect label="一级业态" value={category} onChange={setCategory} options={['全部业态', '零售', '餐饮', '文体娱乐', '生活服务']} /><GlassSelect label="品牌等级" value={grade} onChange={setGrade} options={['全部等级', 'A', 'B', 'C']} /><button type="button" className={showAdvanced ? 'activeFilterButton' : ''} onClick={() => setShowAdvanced(!showAdvanced)}><Filter size={16} />更多筛选</button>{can('brand:write') && <button className="primaryAction" type="button" onClick={() => setCreateOpen(true)}><Plus size={16} />新建品牌</button>}</div>
    {showAdvanced && <AdvancedFilterPanel className="inPage" onClose={() => setShowAdvanced(false)} onReset={() => { setQueryDraft(''); setQuery(''); setCategory('全部业态'); setGrade('全部等级'); setIntent('全部意愿') }}><label className="advancedFilterField"><span>合作意愿</span><GlassSelect label="合作意愿" value={intent} onChange={setIntent} options={['全部意愿', '强', '较强', '一般']} /></label></AdvancedFilterPanel>}
    <div className="resourceLayout brandResourceLayout">
      <section className="panel tablePanel"><SectionTitle title="品牌拓店需求清单" meta={`当前显示 ${visibleBrands.length} 个品牌`} /><div className="dataTable brandTable"><div className="tableHeader"><span>品牌</span><span>一级业态</span><span>二级业态</span><span>三级业态</span><span>面积需求</span><span>工程条件</span><span>物业偏好</span><span>开店计划</span><span>操作</span></div>{visibleBrands.map((b) => <button type="button" aria-label={`查看${b.name}拓店需求`} className={`tableRow ${selected?.code === b.code ? 'selected' : ''}`} key={b.code} onClick={() => setSelected(b)}><span className="nameCell"><i>{b.name[0]}</i><span><strong>{b.name}</strong><small>{b.code}</small></span></span><span>{b.level1}</span><span>{b.level2}</span><span>{b.level3}</span><span>{b.area}</span><span className="conditionCell">{b.engineering}</span><span className="conditionCell">{b.property}</span><span>{b.opening}</span><span className="rowAction">查看 <ArrowRight size={14} /></span></button>)}{visibleBrands.length === 0 && <EmptyState />}</div></section>
      {selected && <aside className="panel profilePanel"><div className="profileTop"><div className="profileLogo">{selected.name[0]}</div><div><span>{selected.code}</span><h2>{selected.name}</h2><p>{selected.level1} · {selected.level2} · {selected.level3}</p></div><i className={`grade grade${selected.grade}`}>{selected.grade}</i></div><div className="tagCloud">{selected.tags.map(t => <span key={t}>{t}</span>)}</div><div className="profileStats"><div><span>面积需求</span><strong>{selected.area}</strong></div><div><span>开店计划</span><strong>{selected.opening}</strong></div><div><span>合作意愿</span><strong className="positive">{selected.intent}</strong></div></div><div className="profileSection"><h3>资产适配条件</h3><dl><div><dt>工程条件</dt><dd>{selected.engineering}</dd></div><div><dt>物业偏好</dt><dd>{selected.property}</dd></div><div><dt>面积区间</dt><dd>{selected.area}</dd></div><div><dt>开店周期</dt><dd>{selected.opening}</dd></div></dl></div><div className="profileSection"><h3>最近沟通</h3><p className="recordText">9月5日 · 已确认拓店需求，等待匹配适配铺位与工程条件。</p></div><div className="cardActions"><button type="button" className="primary" onClick={() => setArchiveOpen(true)}>打开品牌档案</button><button type="button" onClick={() => onNavigate('matching')}>查看推荐项目</button></div></aside>}
    </div>
    {createOpen && <GlassDialog title="新建品牌" subtitle="录入品牌拓店与资产适配条件" onClose={() => setCreateOpen(false)} actions={<><button type="button" onClick={() => setCreateOpen(false)}>取消</button><button type="submit" form="brand-create-form" className="primaryAction">保存品牌</button></>}><form id="brand-create-form" className="dialogForm" onSubmit={createBrand}><DialogField label="品牌名称" full><input required autoFocus value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} placeholder="请输入品牌名称" /></DialogField><DialogField label="一级业态"><select value={form.level1} onChange={(event) => setForm({ ...form, level1: event.target.value })}><option>零售</option><option>餐饮</option><option>文体娱乐</option><option>生活服务</option></select></DialogField><DialogField label="二级业态"><input required value={form.level2} onChange={(event) => setForm({ ...form, level2: event.target.value })} /></DialogField><DialogField label="三级业态"><input required value={form.level3} onChange={(event) => setForm({ ...form, level3: event.target.value })} /></DialogField><DialogField label="品牌等级"><select value={form.grade} onChange={(event) => setForm({ ...form, grade: event.target.value })}><option>A</option><option>B</option><option>C</option></select></DialogField><DialogField label="合作意愿"><select value={form.intent} onChange={(event) => setForm({ ...form, intent: event.target.value })}><option>强</option><option>较强</option><option>一般</option></select></DialogField><DialogField label="面积需求"><input value={form.area} onChange={(event) => setForm({ ...form, area: event.target.value })} /></DialogField><DialogField label="开店计划"><input value={form.opening} onChange={(event) => setForm({ ...form, opening: event.target.value })} /></DialogField><DialogField label="工程条件" full><input value={form.engineering} onChange={(event) => setForm({ ...form, engineering: event.target.value })} /></DialogField><DialogField label="物业偏好" full><input value={form.property} onChange={(event) => setForm({ ...form, property: event.target.value })} /></DialogField></form></GlassDialog>}
    {archiveOpen && selected && <GlassDialog title={selected.name} subtitle="品牌完整档案" onClose={() => setArchiveOpen(false)} wide actions={<><button type="button" onClick={() => setArchiveOpen(false)}>关闭</button><button type="button" className="primaryAction" onClick={() => { setArchiveOpen(false); onNavigate('matching') }}>查看匹配项目</button></>}><BrandArchive brand={selected} /></GlassDialog>}
  </div>
}

function projectSummary(project) {
  const summaries = {
    '体育场馆商业': '围绕赛事、运动消费与城市公共空间打造复合经营场景。',
    '购物中心': '面向区域家庭客群，统筹零售、餐饮与生活服务业态。',
    '商业街区': '以开放街区和特色场景承接餐饮、零售及体验型消费。',
    '社区商业': '服务周边常住客群，重点完善高频生活与便民消费。',
    '文旅商业': '依托城市文旅节点，发展体验消费与特色配套服务。',
    '写字楼或公寓配套': '服务办公与居住客群，强化商务和生活配套能力。',
  }
  return summaries[project.type] || '统筹项目招商、经营和资产价值提升。'
}

function ProjectsPage({ notify }) {
  const { projects, can } = useAppData()
  const [projectList, setProjectList] = React.useState(projects)
  React.useEffect(() => { setProjectList(projects) }, [projects])
  const [queryDraft, setQueryDraft] = React.useState('')
  const [query, setQuery] = React.useState('')
  const [city, setCity] = React.useState('重庆市')
  const [type, setType] = React.useState('全部类型')
  const [status, setStatus] = React.useState('全部状态')
  const [createOpen, setCreateOpen] = React.useState(false)
  const [archiveProject, setArchiveProject] = React.useState(null)
  const [form, setForm] = React.useState({ name: '', type: '购物中心', status: '招商中', grade: 'B', area: '2.0万㎡', owner: '陈昱', occupancy: '80.0%', revenue: '200万元', cost: '120万元', collection: '95.0%' })
  const visibleProjects = projectList.filter((project) =>
    (!query || `${project.name}${project.type}${project.owner}`.includes(query)) &&
    (type === '全部类型' || project.type === type) &&
    (status === '全部状态' || project.status === status)
  )
  const createProject = (event) => {
    event.preventDefault()
    const id = Math.max(...projectList.map((item) => item.id), 0) + 1
    const project = { ...form, id, shortName: form.name.slice(0, 4), matches: 0, lng: 106.68, lat: 29.68, x: 50, y: 50 }
    setProjectList((list) => [...list, project])
    setCreateOpen(false)
    notify(`项目“${project.name}”已加入当前清单`)
  }
  return <div className="pageContent resourcePage">
    <div className="actionBar"><form className="searchBox submitSearchBox" role="search" onSubmit={(event) => { event.preventDefault(); setQuery(queryDraft.trim()) }}><Search size={17} /><input aria-label="搜索项目资源" value={queryDraft} onChange={(e) => setQueryDraft(e.target.value)} placeholder="搜索项目、地区或运营方" /><button type="submit" className="searchSubmit">搜索</button></form><GlassSelect label="城市" value={city} onChange={setCity} options={['重庆市', '全部城市']} /><GlassSelect label="项目类型" value={type} onChange={setType} options={['全部类型', '体育场馆商业', '购物中心', '商业街区', '社区商业']} /><GlassSelect label="项目状态" value={status} onChange={setStatus} options={['全部状态', '招商中', '已开业']} />{can('project:write') && <button className="primaryAction" type="button" onClick={() => setCreateOpen(true)}><Plus size={16} />新建项目</button>}</div>
    <section className="projectCards">{visibleProjects.map((p) => <article className="projectCard" key={p.id}><div className="projectBody"><header className="projectCardHead"><div><h2>{p.name}</h2><p>{projectSummary(p)}</p></div><i className={`grade grade${p.grade}`}>{p.grade}</i></header><div className="tagRow"><span>{p.type}</span><span className="green">{p.status}</span></div><div className="projectMetricVisualGrid"><div className="projectMetricBlock areaMetric"><span>经营面积</span><strong>{p.area}</strong><div className="areaMiniBars"><i /><i /><i /><i /></div></div><div className="projectMetricBlock"><span>综合出租率</span><div className="miniMetricRing" style={{ '--progress': p.occupancy }}><strong>{p.occupancy}</strong></div></div><div className="projectMetricBlock cashMetric"><span>本月收入</span><strong className="incomeValue">{p.revenue}</strong><div className="miniSpark"><i /><i /><i /><i /><i /></div></div><div className="projectMetricBlock cashMetric"><span>本月成本</span><strong className="costValue">{p.cost}</strong><div className="miniSpark cost"><i /><i /><i /><i /><i /></div></div><div className="projectMetricBlock collectionMetric"><div><span>租金收缴率</span><strong>{p.collection}</strong></div><div className="projectCollectionBar"><i style={{ width: p.collection }} /></div></div></div><button className="wideButton" type="button" onClick={() => setArchiveProject(p)}>查看项目经营档案 <ArrowRight size={15} /></button></div></article>)}{visibleProjects.length === 0 && <EmptyState />}</section>
    {createOpen && <GlassDialog title="新建项目" subtitle="录入项目基础资料与经营数据" onClose={() => setCreateOpen(false)} actions={<><button type="button" onClick={() => setCreateOpen(false)}>取消</button><button type="submit" form="project-create-form" className="primaryAction">保存项目</button></>}><form id="project-create-form" className="dialogForm" onSubmit={createProject}><DialogField label="项目名称" full><input required autoFocus value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} placeholder="请输入项目名称" /></DialogField><DialogField label="项目类型"><select value={form.type} onChange={(event) => setForm({ ...form, type: event.target.value })}><option>体育场馆商业</option><option>购物中心</option><option>商业街区</option><option>社区商业</option></select></DialogField><DialogField label="招商状态"><select value={form.status} onChange={(event) => setForm({ ...form, status: event.target.value })}><option>招商中</option><option>已开业</option></select></DialogField><DialogField label="项目等级"><select value={form.grade} onChange={(event) => setForm({ ...form, grade: event.target.value })}><option>A</option><option>B</option><option>C</option></select></DialogField><DialogField label="经营面积"><input value={form.area} onChange={(event) => setForm({ ...form, area: event.target.value })} /></DialogField><DialogField label="负责人"><input value={form.owner} onChange={(event) => setForm({ ...form, owner: event.target.value })} /></DialogField><DialogField label="综合出租率"><input value={form.occupancy} onChange={(event) => setForm({ ...form, occupancy: event.target.value })} /></DialogField><DialogField label="租金收缴率"><input value={form.collection} onChange={(event) => setForm({ ...form, collection: event.target.value })} /></DialogField><DialogField label="本月收入"><input value={form.revenue} onChange={(event) => setForm({ ...form, revenue: event.target.value })} /></DialogField><DialogField label="本月成本"><input value={form.cost} onChange={(event) => setForm({ ...form, cost: event.target.value })} /></DialogField></form></GlassDialog>}
    {archiveProject && <GlassDialog title={archiveProject.name} subtitle="项目完整档案" onClose={() => setArchiveProject(null)} wide actions={<button type="button" className="primaryAction" onClick={() => setArchiveProject(null)}>关闭档案</button>}><ProjectArchive project={archiveProject} /></GlassDialog>}
  </div>
}

function projectCostBreakdown(project) {
  const total = Number(String(project.cost).replace(/[^\d.]/g, '')) || 0
  const definitions = [['人工及外包', .31], ['能源及公用事业', .24], ['维修维护', .18], ['营销及活动', .15], ['行政及其他', .12]]
  return definitions.map(([name, ratio]) => [name, `${total < 100 ? (total * ratio).toFixed(1) : Math.round(total * ratio)}万元`, `${Math.round(ratio * 100)}%`])
}

function formatOperationPeriod(code) {
  const [year, month] = String(code).split('-')
  return year && month ? `${year}年${Number(month)}月` : code
}

function recentOperationPeriods(count = 24) {
  const now = new Date()
  return Array.from({ length: count }, (_, index) => {
    const date = new Date(now.getFullYear(), now.getMonth() - index, 1)
    const code = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`
    return { value: code, label: formatOperationPeriod(code) }
  })
}

function operationHistoryRow(data, code) {
  const isPortfolio = Boolean(data?.kpi)
  const revenue = isPortfolio ? data.kpi.revenue_received : data?.revenue?.revenue_received_total
  const cost = isPortfolio ? data.kpi.cost : data?.cost?.cost_total
  const noi = isPortfolio ? data.kpi.noi : data?.noi
  const occupancy = isPortfolio ? data.kpi.occupancy_rate : data?.occupancy?.occupancy_rate
  const collection = isPortfolio ? data.kpi.collect_rate : data?.revenue?.collect_rate
  return { code, label: formatOperationPeriod(code), revenue: revenue || 0, cost: cost || 0, noi: noi || 0, occupancy: occupancy || 0, collection: collection || 0, hasData: Boolean(revenue || cost) }
}

function MonthlyOperationHistory({ rows, loading, title = '月度经营历史', meta }) {
  const chronological = [...rows].reverse()
  const maxValue = Math.max(...chronological.flatMap((row) => [row.revenue, row.cost]), 1)
  return <section className="panel monthlyHistoryPanel">
    <div className="monthlyHistoryHead"><div><strong>{title}</strong><span>{meta || '最近 12 个月 · 收入与成本对比'}</span></div><div className="operationLegend"><span><i className="incomeDot" />实收收入</span><span><i className="costDot" />经营成本</span></div></div>
    {loading ? <div className="historyLoading">正在读取月度数据…</div> : <>
      <div className="monthlyHistoryBars" role="img" aria-label={`${title}收入成本柱状图`}>{chronological.map((row) => <div className={`monthlyBarGroup ${row.hasData ? '' : 'empty'}`} key={row.code} title={`${row.label}：收入 ${(row.revenue / 10000).toFixed(1)} 万元，成本 ${(row.cost / 10000).toFixed(1)} 万元`}><div><i className="historyIncomeBar" style={{ height: row.hasData ? `${Math.max(7, row.revenue / maxValue * 100)}%` : '3px' }} /><i className="historyCostBar" style={{ height: row.hasData ? `${Math.max(7, row.cost / maxValue * 100)}%` : '3px' }} /></div><span>{Number(row.code.slice(5))}月</span></div>)}</div>
      <div className="monthlyHistoryTable"><div className="monthlyHistoryTableHead"><span>月份</span><span>实收收入</span><span>经营成本</span><span>NOI</span><span>出租率</span><span>收缴率</span></div>{rows.map((row) => <div key={row.code}><strong>{row.label}</strong><span>{row.hasData ? `${(row.revenue / 10000).toFixed(1)}万元` : '—'}</span><span>{row.hasData ? `${(row.cost / 10000).toFixed(1)}万元` : '—'}</span><span className={row.noi < 0 ? 'warningText' : 'incomeText'}>{row.hasData ? `${(row.noi / 10000).toFixed(1)}万元` : '—'}</span><span>{row.hasData ? `${(row.occupancy * 100).toFixed(1)}%` : '—'}</span><span>{row.hasData ? `${(row.collection * 100).toFixed(1)}%` : '—'}</span></div>)}</div>
    </>}
  </section>
}

function ProjectOperatingDetail({ project, onOpenMetric }) {
  return <div className="operationProjectDetail">
    <header><div><span>{project.type} · {project.status}</span><h3>{project.name}</h3><p>{projectSummary(project)}</p></div><i className={`grade grade${project.grade}`}>{project.grade}</i></header>
    <div className="operationProjectVisuals">
      <div className="operationProjectMetric"><span>经营面积</span><strong>{project.area}</strong><div className="areaMiniBars large"><i /><i /><i /><i /></div></div>
      <div className="operationProjectMetric"><span>综合出租率</span><div className="miniMetricRing large" style={{ '--progress': project.occupancy }}><strong>{project.occupancy}</strong></div></div>
      <button type="button" className="operationProjectMetric" onClick={() => onOpenMetric('income')}><span>本月经营收入</span><strong className="incomeValue">{project.revenue}</strong><svg viewBox="0 0 120 38" aria-hidden="true"><path className="incomeLine" d="M2 33 C18 31 22 24 36 26 S57 18 69 20 S91 11 101 13 S113 5 118 4" /></svg><small>点击查看收入构成</small></button>
      <button type="button" className="operationProjectMetric costClickable" onClick={() => onOpenMetric('cost')}><span>本月经营成本</span><strong className="costValue">{project.cost}</strong><div className="costComposition"><i /><i /><i /><i /><i /></div><small>点击查看成本科目</small></button>
      <div className="operationProjectMetric collectionVisual"><div><span>租金收缴率</span><strong>{project.collection}</strong></div><div className="projectCollectionBar"><i style={{ width: project.collection }} /></div><small>按当期应收租金统计</small></div>
    </div>
    <MonthlyOperationHistory rows={project.history || []} loading={project.historyLoading} title="项目月度经营历史" meta="随经营账期留存 · 最近 12 个月" />
  </div>
}

function OperationMetricVisualDetail({ metric, rows = [] }) {
  const [selectedIndex, setSelectedIndex] = React.useState(0)
  const selected = rows[selectedIndex] || []
  const chartRows = rows.slice(0, 7)
  const heights = chartRows.map((_, index) => 38 + ((index * 19 + 23) % 58))
  return <div className="operationMetricDrilldown">
    <div className="operationMetricHero">
      <div><span>{metric.label}</span><strong>{metric.value}<em>{metric.unit}</em></strong><small>{metric.meta}</small></div>
      <div className="operationMetricTrend" role="img" aria-label={`${metric.label}近六期趋势`}>
        {['4月', '5月', '6月', '7月', '8月', '9月'].map((month, index) => <i key={month} style={{ height: `${42 + ((index * 13 + metric.label.length * 3) % 52)}%` }} title={month}><b>{month}</b></i>)}
      </div>
    </div>
    <div className="operationMetricBreakdown">
      <section><header><strong>构成与分布</strong><span>点击柱形或数据项继续查看</span></header><div className="operationBreakdownBars">{chartRows.map((row, index) => <button type="button" className={selectedIndex === index ? 'active' : ''} key={`${row[0]}-${index}`} onClick={() => setSelectedIndex(index)}><span><i style={{ height: `${heights[index]}%` }} /></span><small>{String(row[0]).slice(0, 7)}</small></button>)}</div></section>
      <section className="operationBreakdownList"><header><strong>具体数据</strong><span>{rows.length} 项</span></header>{rows.map((row, index) => <button type="button" className={selectedIndex === index ? 'active' : ''} key={`${row[0]}-${index}`} onClick={() => setSelectedIndex(index)}><i className={`drillDot d${index % 4}`} /><span><strong>{row[0]}</strong><small>{row.slice(1).join(' · ')}</small></span><ArrowRight size={13} /></button>)}</section>
    </div>
    {selected.length > 0 && <div className="operationRecordDetail"><div><span>当前查看</span><strong>{selected[0]}</strong></div>{selected.slice(1).map((value, index) => <div key={`${value}-${index}`}><span>{index === 0 ? '指标值' : index === 1 ? '占比/状态' : `关联信息 ${index}`}</span><strong>{value}</strong></div>)}<div><span>数据口径</span><strong>{metric.label}统计口径 · {metric.meta}</strong></div></div>}
  </div>
}

function ProjectContractLedger({ rows, onOpen }) {
  const groups = React.useMemo(() => Object.entries(rows.reduce((result, row) => {
    if (!result[row.project]) result[row.project] = []
    result[row.project].push(row)
    return result
  }, {})), [rows])
  const [expanded, setExpanded] = React.useState(() => new Set(groups.map(([name]) => name)))
  const toggle = (name) => setExpanded((current) => {
    const next = new Set(current)
    next.has(name) ? next.delete(name) : next.add(name)
    return next
  })
  return <div className="projectContractLedger">{groups.map(([project, contracts]) => {
    const isOpen = expanded.has(project)
    const attention = contracts.filter((row) => row.status !== '履约中').length
    return <section key={project} className="contractProjectGroup">
      <button type="button" className="contractProjectHead" aria-expanded={isOpen} onClick={() => toggle(project)}><span><Building2 size={18} /><span><strong>{project}</strong><small>{contracts.length} 份合同 · {attention ? `${attention} 份需要关注` : '履约正常'}</small></span></span><span><em>合同租金 {contracts.reduce((sum, row) => sum + Number(row.monthly || 0), 0).toFixed(1)} 万元/月</em><ChevronDown size={16} /></span></button>
      {isOpen && <div className="contractGroupTable"><div className="operationTableHeader"><span>合同编号</span><span>租户/品牌</span><span>铺位</span><span>租赁面积</span><span>租金标准</span><span>合同期限</span><span>状态</span></div>{contracts.map((row) => <button type="button" key={row.no} onClick={() => onOpen(row)}><strong>{row.no}</strong><span>{row.tenant}</span><span>{row.unit}</span><span>{row.area}</span><span>{row.rent}</span><span>{row.term}</span><span className={row.status === '履约中' ? 'incomeText' : 'warningText'}>{row.status}</span></button>)}</div>}
    </section>
  })}</div>
}

function OperationsPage({ notify }) {
  const [tab, setTab] = React.useState('overview')
  const [projectId, setProjectId] = React.useState('all')
  const periodOptions = React.useMemo(() => recentOperationPeriods(), [])
  const [period, setPeriod] = React.useState(() => periodOptions[0].value)
  const [detail, setDetail] = React.useState(null)
  const tabs = [['overview', '经营总览'], ['leasing', '租赁经营'], ['rent', '租金台账'], ['contracts', '合同台账']]
  const selectedProject = projectId === 'all' ? null : projects.find((item) => String(item.id) === projectId)
  const historyPeriods = React.useMemo(() => {
    const start = Math.max(periodOptions.findIndex((item) => item.value === period), 0)
    return periodOptions.slice(start, start + 12)
  }, [period, periodOptions])
  // 项目与账期是经营中心的统一数据控制器。
  const [live, setLive] = React.useState(null)
  const [dataLoading, setDataLoading] = React.useState(false)
  const [historyRows, setHistoryRows] = React.useState([])
  const [historyLoading, setHistoryLoading] = React.useState(false)
  const projectOperationsAsDashboard = (operations, project) => ({
    period: operations.period,
    kpi: {
      project_count: 1,
      unit_total: operations.occupancy?.unit_total || 0,
      occupancy_rate: operations.occupancy?.occupancy_rate || 0,
      revenue_received: operations.revenue?.revenue_received_total || 0,
      revenue_due: operations.revenue?.revenue_due_total || 0,
      cost: operations.cost?.cost_total || 0,
      noi: operations.noi || 0,
      collect_rate: operations.revenue?.collect_rate || 0,
      arrears: operations.revenue?.arrears_total || 0,
    },
    projects: [{
      project_id: project.id,
      project_name: project.name,
      unit_total: operations.occupancy?.unit_total || 0,
      occupancy_rate: operations.occupancy?.occupancy_rate || 0,
      revenue_received: operations.revenue?.revenue_received_total || 0,
      cost: operations.cost?.cost_total || 0,
      noi: operations.noi || 0,
      collect_rate: operations.revenue?.collect_rate || 0,
      arrears: operations.revenue?.arrears_total || 0,
    }],
    revenue_structure: operations.revenue?.revenue_received_by_item || {},
    cost_structure: operations.cost?.cost_by_type || {},
  })
  React.useEffect(() => {
    let cancelled = false
    setDataLoading(true)
    const request = selectedProject ? getProjectOperations(selectedProject.id, period).then((data) => projectOperationsAsDashboard(data, selectedProject)) : getOperations(period)
    request.then((data) => { if (!cancelled) setLive(data) }).catch(() => {}).finally(() => { if (!cancelled) setDataLoading(false) })
    return () => { cancelled = true }
  }, [projectId, period])
  React.useEffect(() => {
    let cancelled = false
    setHistoryLoading(true)
    Promise.all(historyPeriods.map((item) => {
      const request = selectedProject ? getProjectOperations(selectedProject.id, item.value) : getOperations(item.value)
      return request.then((data) => operationHistoryRow(data, item.value)).catch(() => operationHistoryRow(null, item.value))
    })).then((rows) => { if (!cancelled) setHistoryRows(rows) }).finally(() => { if (!cancelled) setHistoryLoading(false) })
    return () => { cancelled = true }
  }, [projectId, historyPeriods])
  const wan = (x) => `${((x || 0) / 10000).toFixed(1)}万元`
  const pct = (x) => `${((x || 0) * 100).toFixed(1)}%`
  const breakdownRows = (items, total) => Object.entries(items || {}).map(([name, value]) => [name, wan(value), total ? `${Math.round((value / total) * 100)}%` : '0%'])
  const liveRows = live?.projects || null
  const rentRows = [
    { project: '重庆龙兴足球场', tenant: '超级猩猩', period: '2026年9月', receivable: '86.0万元', received: '86.0万元', unpaid: '0', status: '已收清' },
    { project: '两江悦荟城', tenant: '迪卡侬', period: '2026年9月', receivable: '64.5万元', received: '58.0万元', unpaid: '6.5万元', status: '部分欠缴' },
    { project: '两江云中街', tenant: '瑞幸咖啡', period: '2026年9月', receivable: '18.2万元', received: '18.2万元', unpaid: '0', status: '已收清' },
    { project: '三洞桥 PARK', tenant: '名创优品', period: '2026年9月', receivable: '32.8万元', received: '30.1万元', unpaid: '2.7万元', status: '待补缴' },
  ]
  const contractRows = [
    { no: 'XS-HT-2026-018', project: '重庆龙兴足球场', tenant: '超级猩猩', unit: 'L1-101/102', area: '520㎡', rent: '165元/㎡/月', monthly: 8.6, term: '2026.01–2031.12', status: '履约中' },
    { no: 'XS-HT-2026-019', project: '重庆龙兴足球场', tenant: '瑞幸咖啡', unit: 'L1-106', area: '96㎡', rent: '285元/㎡/月', monthly: 2.7, term: '2026.02–2029.01', status: '履约中' },
    { no: 'XS-HT-2025-088', project: '重庆龙兴足球场', tenant: '滔搏运动', unit: 'L2-201/202', area: '680㎡', rent: '142元/㎡/月', monthly: 9.7, term: '2025.10–2030.09', status: '履约中' },
    { no: 'XS-HT-2024-061', project: '重庆龙兴足球场', tenant: '运动康复中心', unit: 'L2-208', area: '310㎡', rent: '118元/㎡/月', monthly: 3.7, term: '2024.12–2026.11', status: '临期关注' },
    { no: 'XS-HT-2026-021', project: '两江悦荟城', tenant: '迪卡侬', unit: 'L1-001', area: '1800㎡', rent: '138元/㎡/月', monthly: 24.8, term: '2026.03–2032.02', status: '履约中' },
    { no: 'XS-HT-2025-036', project: '两江悦荟城', tenant: '海底捞', unit: 'L3-301', area: '920㎡', rent: '126元/㎡/月', monthly: 11.6, term: '2025.05–2030.04', status: '履约中' },
    { no: 'XS-HT-2024-029', project: '两江悦荟城', tenant: '孩子王', unit: 'L2-206', area: '860㎡', rent: '112元/㎡/月', monthly: 9.6, term: '2024.11–2027.10', status: '履约中' },
    { no: 'XS-HT-2025-046', project: '两江云中街', tenant: '瑞幸咖啡', unit: 'A1-08', area: '96㎡', rent: '285元/㎡/月', monthly: 2.7, term: '2025.10–2028.09', status: '履约中' },
    { no: 'XS-HT-2024-033', project: '两江云中街', tenant: '名创优品', unit: 'B2-11/12', area: '420㎡', rent: '156元/㎡/月', monthly: 6.6, term: '2024.11–2026.10', status: '临期关注' },
    { no: 'XS-HT-2026-052', project: '两江云中街', tenant: '百果园', unit: 'A1-15', area: '128㎡', rent: '192元/㎡/月', monthly: 2.5, term: '2026.06–2029.05', status: '履约中' },
    { no: 'XS-HT-2024-078', project: '江北嘴网球馆', tenant: '社区药房', unit: 'L1-103', area: '180㎡', rent: '145元/㎡/月', monthly: 2.6, term: '2024.09–2026.08', status: '已到期待交接' },
    { no: 'XS-HT-2025-014', project: '江北嘴网球馆', tenant: '美宜佳', unit: 'L1-105', area: '116㎡', rent: '176元/㎡/月', monthly: 2.0, term: '2025.02–2028.01', status: '履约中' },
  ]
  const openProject = (project) => setDetail({ type: 'project', title: project.name, subtitle: '项目经营数据', project })
  const openRow = (title, subtitle, rows) => setDetail({ type: 'table', title, subtitle, rows })
  const costRows = [['人工及外包', '453万元', '31%'], ['能源及公用事业', '351万元', '24%'], ['维修维护', '263万元', '18%'], ['营销及活动', '219万元', '15%'], ['行政及其他', '177万元', '12%']]
  const k = live?.kpi
  const projectFromLiveRow = (row) => {
    const normalize = (value) => String(value || '').replace(/\s+/g, '').toLowerCase()
    const base = projects.find((project) => normalize(project.name) === normalize(row.project_name))
    return {
      ...(base || {}),
      id: row.project_id,
      name: row.project_name,
      type: base?.type || '经营项目',
      status: base?.status || '运营中',
      grade: base?.grade || 'B',
      area: base?.area || `${row.unit_total || 0} 个经营单元`,
      occupancy: pct(row.occupancy_rate),
      revenue: wan(row.revenue_received),
      cost: wan(row.cost),
      collection: pct(row.collect_rate),
    }
  }
  const openLiveProject = (row) => {
    const project = { ...projectFromLiveRow(row), historyLoading: true, history: [] }
    openProject(project)
    Promise.all([
      getProjectOperations(row.project_id, period),
      Promise.all(historyPeriods.map((item) => getProjectOperations(row.project_id, item.value).then((data) => operationHistoryRow(data, item.value)).catch(() => operationHistoryRow(null, item.value)))),
    ]).then(([operations, projectHistory]) => {
      const nextProject = {
        ...project,
        area: operations.occupancy?.area_total ? `${operations.occupancy.area_total.toLocaleString('zh-CN')}㎡` : project.area,
        occupancy: pct(operations.occupancy?.occupancy_rate),
        revenue: wan(operations.revenue?.revenue_received_total),
        cost: wan(operations.cost?.cost_total),
        collection: pct(operations.revenue?.collect_rate),
        incomeRows: breakdownRows(operations.revenue?.revenue_received_by_item, operations.revenue?.revenue_received_total),
        costRows: breakdownRows(operations.cost?.cost_by_type, operations.cost?.cost_total),
        history: projectHistory,
        historyLoading: false,
      }
      setDetail((current) => current?.type === 'project' && current.project.id === row.project_id ? { ...current, project: nextProject } : current)
    }).catch(() => setDetail((current) => current?.type === 'project' && current.project.id === row.project_id ? { ...current, project: { ...current.project, historyLoading: false } } : current))
  }
  const incomeSummary = k && Object.keys(live?.revenue_structure || {}).length ? {
    total: ((k.revenue_received || 0) / 10000).toFixed(1),
    items: Object.entries(live.revenue_structure).slice(0, 4).map(([name, value]) => ({
      name,
      value: `${((value || 0) / 10000).toFixed(1)}万`,
      share: k.revenue_received ? Math.round((value / k.revenue_received) * 100) : 0,
    })),
  } : {
    total: '2,486',
    items: [
      { name: '租金收入', value: '1,542万', share: 62 },
      { name: '运营服务', value: '547万', share: 22 },
      { name: '场地及活动', value: '273万', share: 11 },
      { name: '其他收入', value: '124万', share: 5 },
    ],
  }
  const overviewLive = k ? [
    { label: '本月经营收入（实收）', value: ((k.revenue_received || 0) / 10000).toFixed(1), unit: '万元', meta: `覆盖 ${k.project_count} 个项目`, tone: 'income', rows: Object.entries(live.revenue_structure || {}).map(([n, v]) => [n, wan(v)]) },
    { label: '本月经营成本', value: ((k.cost || 0) / 10000).toFixed(1), unit: '万元', meta: k.revenue_received ? `成本率 ${pct(k.cost / k.revenue_received)}` : '—', tone: 'cost', rows: Object.entries(live.cost_structure || {}).map(([n, v]) => [n, wan(v)]) },
    { label: '经营净收益 NOI', value: ((k.noi || 0) / 10000).toFixed(1), unit: '万元', meta: k.revenue_received ? `净收益率 ${pct(k.noi / k.revenue_received)}` : '—', tone: 'income', rows: [['经营收入(实收)', wan(k.revenue_received)], ['经营成本', wan(k.cost)], ['经营净收益 NOI', wan(k.noi)]] },
    { label: '综合出租率', value: (100 * (k.occupancy_rate || 0)).toFixed(1), unit: '%', meta: `铺位 ${k.unit_total} 个`, tone: 'ring', rows: [['铺位总数', `${k.unit_total} 个`]] },
    { label: '租金收缴率', value: (100 * (k.collect_rate || 0)).toFixed(1), unit: '%', meta: `欠租 ${wan(k.arrears)}`, tone: 'ring', rows: [['本期实收', wan(k.revenue_received)], ['欠租合计', wan(k.arrears)]] },
  ] : null
  const kpiSets = {
    overview: overviewLive || [
      { label: '本月经营收入', value: '2,486', unit: '万元', meta: '同比 +12.8%', tone: 'income', rows: [['租金收入', '1,542万元', '62%'], ['运营服务', '547万元', '22%'], ['场地及活动', '273万元', '11%'], ['其他收入', '124万元', '5%']] },
      { label: '本月经营成本', value: '1,463', unit: '万元', meta: '成本率 58.8%', tone: 'cost', rows: costRows },
      { label: '经营净收益', value: '1,023', unit: '万元', meta: '净收益率 41.2%', tone: 'income', rows: [['经营收入', '2,486万元'], ['经营成本', '1,463万元'], ['经营净收益', '1,023万元']] },
      { label: '综合出租率', value: '86.4', unit: '%', meta: '环比 +1.2pct', tone: 'ring', rows: [['可租赁面积', '31.2万㎡'], ['已出租面积', '26.9万㎡'], ['空置面积', '4.3万㎡']] },
      { label: '租金收缴率', value: '96.8', unit: '%', meta: '未收 82.6 万元', tone: 'ring', rows: [['本月应收', '2,581万元'], ['本月实收', '2,498万元'], ['未收金额', '82.6万元']] },
    ],
    leasing: [
      { label: '可租赁面积', value: '31.2', unit: '万㎡', meta: '全部可经营铺位' }, { label: '已出租面积', value: '26.9', unit: '万㎡', meta: '有效合同覆盖' }, { label: '空置面积', value: '4.3', unit: '万㎡', meta: '其中预警 0.8 万㎡', tone: 'cost' }, { label: '综合出租率', value: '86.4', unit: '%', meta: '环比 +1.2pct', tone: 'ring' }, { label: '本月新签面积', value: '0.8', unit: '万㎡', meta: '新签合同 11 份', tone: 'income' },
    ],
    rent: [
      { label: '本月应收租金', value: '2,581', unit: '万元', meta: '共 186 个应收项' }, { label: '本月实收租金', value: '2,498', unit: '万元', meta: '到账 96.8%', tone: 'income' }, { label: '未收金额', value: '82.6', unit: '万元', meta: '涉及 9 个租户', tone: 'cost' }, { label: '租金收缴率', value: '96.8', unit: '%', meta: '环比 +0.6pct', tone: 'ring' }, { label: '逾期租户', value: '3', unit: '户', meta: '2 户已进入催收', tone: 'cost' },
    ],
    contracts: [
      { label: '有效合同', value: '186', unit: '份', meta: '覆盖 28 个项目' }, { label: '本月新签', value: '11', unit: '份', meta: '新签面积 0.8 万㎡', tone: 'income' }, { label: '年内到期', value: '12', unit: '份', meta: '涉及租金 318 万元' }, { label: '临期关注', value: '4', unit: '份', meta: '90 天内需处理', tone: 'cost' }, { label: '平均剩余租期', value: '3.6', unit: '年', meta: '合同组合稳定' },
    ],
  }
  const rowsForKpi = (kpi) => {
    if (kpi.rows?.length) return kpi.rows
    if (tab === 'contracts') {
      const grouped = Object.entries(contractRows.reduce((result, row) => { result[row.project] = (result[row.project] || 0) + 1; return result }, {}))
      if (kpi.label === '有效合同') return grouped.map(([name, count]) => [name, `${count}份`, `${contractRows.filter((row) => row.project === name && row.status === '履约中').length}份履约正常`])
      if (kpi.label === '本月新签') return contractRows.slice(0, 5).map((row) => [row.tenant, row.project, row.no])
      if (kpi.label === '年内到期' || kpi.label === '临期关注') return contractRows.filter((row) => row.status !== '履约中').map((row) => [row.tenant, row.project, `${row.term} · ${row.status}`])
      return grouped.map(([name, count], index) => [name, `${(3.1 + index * .4).toFixed(1)}年`, `${count}份合同`])
    }
    if (tab === 'rent') return rentRows.map((row) => [row.tenant, row.project, `${row.received} / 应收${row.receivable}`])
    return projects.slice(0, 8).map((project, index) => [project.name, kpi.unit === '%' ? project.occupancy : project.area, index === 3 ? '重点关注' : '正常'])
  }
  const openKpi = (kpi) => setDetail({ type: 'visual', title: kpi.label, subtitle: `${formatOperationPeriod(period)} · ${selectedProject?.name || '全部项目'}`, metric: kpi, rows: rowsForKpi(kpi) })
  const openProjectMetric = (project, metric) => {
    if (metric === 'cost') return setDetail({ type: 'visual', title: `${project.name}成本明细`, subtitle: `${formatOperationPeriod(period)} · 本月成本 ${project.cost}`, metric: { label: '本月经营成本', value: project.cost.replace('万元', ''), unit: '万元', meta: '按成本科目统计' }, rows: project.costRows?.length ? project.costRows : projectCostBreakdown(project) })
    setDetail({ type: 'visual', title: `${project.name}收入构成`, subtitle: `${formatOperationPeriod(period)} · 本月收入 ${project.revenue}`, metric: { label: '本月经营收入', value: project.revenue.replace('万元', ''), unit: '万元', meta: '按收入科目统计' }, rows: project.incomeRows?.length ? project.incomeRows : [['租金收入', project.revenue, '62%'], ['运营服务', '示例 22%', '22%'], ['场地及活动', '示例 11%', '11%'], ['其他收入', '示例 5%', '5%']] })
  }
  return <div className="pageContent operationsPage">
    <div className="operationToolbar">
      <div className="operationTabs">{tabs.map(([id, label]) => <button type="button" className={tab === id ? 'active' : ''} key={id} onClick={() => setTab(id)}>{label}</button>)}</div>
      <GlassSelect label="选择项目" value={projectId} onChange={setProjectId} options={[{ value: 'all', label: '全部项目' }, ...projects.map((item) => ({ value: String(item.id), label: item.name }))]} />
      <GlassSelect label="统计月份" value={period} onChange={setPeriod} options={periodOptions} />
      {dataLoading && <span className="operationLoading">正在更新数据…</span>}
      <button type="button" className="operationExport" onClick={() => notify(`${selectedProject?.name || '全部项目'}经营数据已生成导出任务`)}><Download size={15} />导出数据</button>
    </div>

    <section className="operationKpis" aria-label={`${tabs.find(([id]) => id === tab)?.[1]}核心指标`}>{kpiSets[tab].map((kpi) => <button type="button" className={`operationKpi ${kpi.tone || ''}`} key={kpi.label} onClick={() => openKpi(kpi)}><span>{kpi.label}</span><strong>{kpi.value}<em>{kpi.unit}</em></strong><div className="operationKpiVisual"><i /><i /><i /><i /><i /></div><small>{kpi.meta}</small><b>查看明细 <ArrowRight size={12} /></b></button>)}</section>

    {tab === 'overview' && <>
      <div className="operationOverviewGrid">
        <MonthlyOperationHistory rows={historyRows} loading={historyLoading} title={`${selectedProject?.name || '全部项目'}月度经营趋势`} meta={`截至 ${formatOperationPeriod(period)} · 最近 12 个月`} />
        <section className="panel incomeStructure"><SectionTitle title="本月收入结构" meta="按收入类型统计" /><div className="incomeStructureVisual"><div className="incomeRing"><div><strong>{incomeSummary.total}</strong><span>万元</span></div></div><div className="incomeItems">{incomeSummary.items.map((item, index) => <button type="button" key={item.name} onClick={() => openKpi({ label: item.name, value: item.value.replace('万', ''), unit: '万元', meta: `占本月收入 ${item.share}%`, rows: projects.slice(0, 7).map((project, projectIndex) => [project.name, `${Math.max(1, Math.round((item.share * (8 - projectIndex)) / 9))}万元`, projectIndex < 2 ? '主要贡献项目' : '正常']) })}><i className={`r${index + 1}`} /><span>{item.name}</span><strong>{item.value} · {item.share}%</strong><b><em style={{ width: `${item.share}%` }} /></b></button>)}</div></div></section>
      </div>
      <section className="panel operationTablePanel"><SectionTitle title="项目经营概览" meta={liveRows ? `实时 · ${liveRows.length} 个项目（按 NOI 排序）· 点击项目查看经营档案` : '点击项目查看经营档案'} /><div className="operationDataTable"><div className="operationTableHeader"><span>项目名称</span><span>出租率</span><span>实收收入</span><span>经营成本</span><span>净收益 NOI</span><span>收缴率</span><span>欠租</span></div>{liveRows ? liveRows.map((r) => <button type="button" aria-label={`查看${r.project_name}经营档案`} key={r.project_id} onClick={() => openLiveProject(r)}><strong>{r.project_name}</strong><span>{pct(r.occupancy_rate)}</span><span className="incomeText">{wan(r.revenue_received)}</span><span className="costText">{wan(r.cost)}</span><span className="incomeText">{wan(r.noi)}</span><span>{pct(r.collect_rate)}</span><span className={r.arrears > 0 ? 'warningText' : ''}>{wan(r.arrears)}</span></button>) : projects.map((project) => <button type="button" key={project.id} onClick={() => openProject(project)}><strong>{project.name}</strong><span>{project.occupancy}</span><span className="incomeText">{project.revenue}</span><span className="costText">{project.cost}</span><span>—</span><span>{project.collection}</span><span>—</span></button>)}</div></section>
    </>}

    {tab === 'leasing' && <div className="operationSectionGrid"><section className="panel leasingSummary"><SectionTitle title="租赁面积结构" meta="全部项目合计" /><div className="leasingRing"><strong>86.4%</strong><span>综合出租率</span></div><dl><div><dt>可租赁面积</dt><dd>31.2万㎡</dd></div><div><dt>已出租面积</dt><dd>26.9万㎡</dd></div><div><dt>空置面积</dt><dd>4.3万㎡</dd></div><div><dt>本月新签面积</dt><dd>0.8万㎡</dd></div></dl></section><section className="panel operationTablePanel"><SectionTitle title="租赁经营明细" meta="按项目统计" /><div className="operationDataTable compact"><div className="operationTableHeader"><span>项目</span><span>经营面积</span><span>出租率</span><span>空置预警</span><span>操作</span></div>{projects.map((project, index) => <button type="button" key={project.id} onClick={() => openProject(project)}><strong>{project.name}</strong><span>{project.area}</span><span>{project.occupancy}</span><span className={index === 3 ? 'warningText' : ''}>{index === 3 ? '重点关注' : '正常'}</span><span className="rowAction">查看 <ArrowRight size={13} /></span></button>)}</div></section></div>}

    {tab === 'rent' && <section className="panel operationTablePanel ledgerPanel"><SectionTitle title="租金收缴台账" meta="2026年9月 · 点击记录查看明细" action={<button type="button" className="textAction" onClick={() => notify('租金台账已刷新')}>刷新台账</button>} /><div className="operationDataTable rentTable"><div className="operationTableHeader"><span>项目</span><span>租户/品牌</span><span>账期</span><span>应收金额</span><span>实收金额</span><span>未收金额</span><span>状态</span></div>{rentRows.map((row) => <button type="button" key={`${row.project}-${row.tenant}`} onClick={() => openRow(`${row.tenant}租金明细`, row.project, [['账期', row.period], ['应收金额', row.receivable], ['实收金额', row.received], ['未收金额', row.unpaid], ['收缴状态', row.status]])}><strong>{row.project}</strong><span>{row.tenant}</span><span>{row.period}</span><span>{row.receivable}</span><span className="incomeText">{row.received}</span><span className={row.unpaid !== '0' ? 'warningText' : ''}>{row.unpaid}</span><span>{row.status}</span></button>)}</div></section>}

    {tab === 'contracts' && <section className="panel operationTablePanel ledgerPanel"><SectionTitle title="经营合同台账" meta="按项目归集 · 展开项目查看全部合同" /><ProjectContractLedger rows={selectedProject ? contractRows.filter((row) => row.project === selectedProject.name) : contractRows} onOpen={(row) => openRow(row.no, `${row.project} · ${row.tenant}`, [['所属铺位', row.unit], ['租赁面积', row.area], ['月租金', `${row.monthly}万元`], ['租金标准', row.rent], ['合同期限', row.term], ['履约状态', row.status]])} /></section>}

    {detail?.type === 'project' && <GlassDialog title={detail.title} subtitle={detail.subtitle} onClose={() => setDetail(null)} wide actions={<button type="button" className="primaryAction" onClick={() => setDetail(null)}>关闭</button>}><ProjectOperatingDetail project={detail.project} onOpenMetric={(metric) => openProjectMetric(detail.project, metric)} /></GlassDialog>}
    {detail?.type === 'visual' && <GlassDialog title={detail.title} subtitle={detail.subtitle} onClose={() => setDetail(null)} wide actions={<button type="button" className="primaryAction" onClick={() => setDetail(null)}>关闭</button>}><OperationMetricVisualDetail metric={detail.metric} rows={detail.rows} /></GlassDialog>}
    {detail?.type === 'table' && <GlassDialog title={detail.title} subtitle={detail.subtitle} onClose={() => setDetail(null)} wide={detail.columns?.length > 2} actions={<button type="button" className="primaryAction" onClick={() => setDetail(null)}>关闭</button>}><DataDetailTable columns={detail.columns || ['数据项', '内容']} rows={detail.rows} /></GlassDialog>}
  </div>
}

function MatchingPage({ notify, onNavigate }) {
  const [selected, setSelected] = React.useState(matchRows[0])
  const [projectId, setProjectId] = React.useState('1')
  const [calculating, setCalculating] = React.useState(false)
  const [candidateBrands, setCandidateBrands] = React.useState([])
  const [adjustOpen, setAdjustOpen] = React.useState(false)
  const [adjustment, setAdjustment] = React.useState({ conclusion: '维持系统结论', note: '' })
  const currentProject = projects.find((project) => String(project.id) === projectId) || projects[0]
  const labels = ['业态适配', '面积适配', '层高承重', '给排水', '排烟燃气电力', '楼层临街', '商务条件', '拓店意愿']
  const isAdded = candidateBrands.includes(selected.brand)
  const addCandidate = () => {
    if (isAdded) return onNavigate('followup')
    setCandidateBrands((items) => [...items, selected.brand])
    notify(`“${selected.brand}”已加入${currentProject.name}候选清单`)
  }
  const recalculate = () => {
    setCalculating(true)
    window.setTimeout(() => { setCalculating(false); notify(`${currentProject.name}匹配结果已重新计算`) }, 850)
  }
  const saveAdjustment = (event) => {
    event.preventDefault()
    setAdjustOpen(false)
    notify(`已保存“${selected.brand}”的人工研判意见`)
  }
  return <div className="pageContent matchingPage">
    <section className="matchingHeader panel"><div><span className="code">当前项目</span><h2>{currentProject.name}</h2><p>{currentProject.type} · {currentProject.grade}级项目 · 资料覆盖率 82%</p></div><GlassSelect className="matchingProjectSelect" label="切换项目" value={projectId} onChange={setProjectId} options={projects.map((project) => ({ value: String(project.id), label: project.name }))} /><button className="primaryAction" type="button" disabled={calculating} onClick={recalculate}><RefreshCw size={16} className={calculating ? 'spin' : ''} />{calculating ? '正在计算…' : '重新计算匹配'}</button></section>
    <div className="matchingLayout">
      <section className="panel matchList">
        <SectionTitle title="推荐品牌" meta="资产合作条件 · 5 个候选" action={<button type="button" className="iconText" onClick={addCandidate}>{isAdded ? <CheckCircle2 size={15} /> : <Plus size={15} />}{isAdded ? '已加入候选' : '加入候选清单'}</button>} />
        <div className="matchTableScroll">
          <div className="matchListHeader"><span>品牌名称</span><span>业态</span><span>合作意愿</span><span>面积需求</span><span>工程适配</span><span>物业适配</span><span>开店计划</span><span>匹配结论</span><span>操作</span></div>
          <div className="matchRows">{matchRows.map(m => <button type="button" aria-label={`查看${m.brand}匹配分析`} className={`matchRow ${selected.brand === m.brand ? 'selected' : ''}`} key={m.brand} onClick={() => setSelected(m)}><div className="matchBrandCell"><div className="brandAvatar">{m.brand[0]}</div><strong>{m.brand}</strong></div><span>{m.category}</span><span className={`intentPill intent-${m.intent}`}>{m.intent}</span><span>{m.area}</span><span className={`fitStatus ${m.engineeringFit === '不适配' ? 'negative' : ''}`}>{m.engineeringFit}</span><span className="fitStatus">{m.propertyFit}</span><span>{m.opening}</span><div className={`matchConclusion ${m.score === null ? 'blocked' : ''}`}><strong>{m.score ?? '—'}</strong><small>{m.level}</small></div><ArrowRight className="rowArrow" size={17} /></button>)}</div>
        </div>
      </section>
      <aside className="panel matchDetail"><div className="matchDetailTop"><div><span>资产合作八维分析</span><h2>{selected.brand}</h2></div><div className={`scoreRing ${selected.score === null ? 'blocked' : ''}`}><strong>{selected.score ?? '—'}</strong><span>{selected.score === null ? '门槛' : '分'}</span></div></div>{selected.gate && <div className="gateAlert"><ShieldCheck size={18} /><div><strong>硬性门槛未通过</strong><span>{selected.gate}</span></div></div>}<div className="dimensionList">{labels.map((label, i) => <div key={label}><span>{label}</span><div><i style={{ width: `${selected.dims[i] || 0}%` }} /></div><strong>{selected.dims[i] ?? '待确认'}</strong></div>)}</div><div className="coverageCallout"><div><span>资料覆盖率</span><strong>{selected.coverage}%</strong></div><p>{selected.coverage >= 80 ? '资料足以形成正式匹配结论。' : selected.coverage >= 60 ? '仅形成初步结论，需要补充待确认资料。' : '资料不足，暂不输出匹配结论。'}</p></div><div className="cardActions"><button type="button" className="primary" onClick={addCandidate}>{isAdded ? '查看候选清单' : '加入候选清单'}</button><button type="button" onClick={() => setAdjustOpen(true)}>人工调整</button></div></aside>
    </div>
    {adjustOpen && <GlassDialog title={`人工研判 · ${selected.brand}`} subtitle="人工意见会作为独立记录保存，不覆盖系统原始评分" onClose={() => setAdjustOpen(false)} actions={<><button type="button" onClick={() => setAdjustOpen(false)}>取消</button><button type="submit" form="adjust-form" className="primaryAction">保存意见</button></>}><form id="adjust-form" className="dialogForm" onSubmit={saveAdjustment}><DialogField label="调整结论" full><select value={adjustment.conclusion} onChange={(event) => setAdjustment({ ...adjustment, conclusion: event.target.value })}><option>维持系统结论</option><option>提升为优先推进</option><option>调整为重点储备</option><option>暂不推进</option></select></DialogField><DialogField label="研判说明" full><textarea required rows="4" value={adjustment.note} onChange={(event) => setAdjustment({ ...adjustment, note: event.target.value })} placeholder="请填写调整原因、依据或后续建议" /></DialogField></form></GlassDialog>}
  </div>
}

function FollowupPage({ notify }) {
  const [listId, setListId] = React.useState('1')
  const [candidates, setCandidates] = React.useState({ reserve: matchRows.slice(1, 4), contacted: matchRows.slice(0, 2), negotiating: matchRows.slice(0, 1), signed: [{ brand: '瑞幸咖啡', category: '咖啡茶饮', score: 78, coverage: 100, level: '已签约' }] })
  const [completedTasks, setCompletedTasks] = React.useState(new Set())
  const [addStage, setAddStage] = React.useState('')
  const [candidateOpen, setCandidateOpen] = React.useState(null)
  const [newBrand, setNewBrand] = React.useState('迪卡侬')
  const listProject = projects.find((project) => String(project.id) === listId) || projects[0]
  const columns = [
    ['reserve', '储备', candidates.reserve], ['contacted', '已接触', candidates.contacted], ['negotiating', '洽谈中', candidates.negotiating], ['signed', '已签约', candidates.signed],
  ]
  const addCandidate = (event) => {
    event.preventDefault()
    const source = matchRows.find((item) => item.brand === newBrand) || matchRows[0]
    setCandidates((value) => ({ ...value, [addStage]: [...value[addStage], source] }))
    setAddStage('')
    notify(`“${newBrand}”已加入${listProject.name}候选清单`)
  }
  const toggleTask = (title) => {
    setCompletedTasks((current) => { const next = new Set(current); next.has(title) ? next.delete(title) : next.add(title); return next })
  }
  return <div className="pageContent">
    <div className="actionBar"><div className="pipelineTitle"><strong>{listProject.name}候选品牌清单</strong><span>负责人 {listProject.owner} · 最近更新 10:32</span></div><GlassSelect label="切换候选清单" value={listId} onChange={setListId} options={projects.map((project) => ({ value: String(project.id), label: project.name }))} /><button className="primaryAction" type="button" onClick={() => setAddStage('reserve')}><Plus size={16} />添加候选</button></div>
    <section className="pipeline">{columns.map(([key, title, items], idx) => <div className="pipelineColumn" key={key}><header><span><i className={`stage s${idx}`} />{title}</span><em>{items.length}</em></header><div>{items.map((m, i) => <button type="button" aria-label={`打开${m.brand}候选详情`} className="candidateCard" key={`${title}-${m.brand}-${i}`} onClick={() => setCandidateOpen({ ...m, stage: title })}><div className="candidateTop"><div className="brandAvatar">{m.brand[0]}</div><div className="grow"><strong>{m.brand}</strong><small>{m.category}</small></div><ArrowRight className="rowArrow" size={16} /></div><div className="candidateScore"><span>匹配分 <strong>{m.score ?? '—'}</strong></span><span>覆盖率 {m.coverage}%</span></div><div className="candidateTask"><Clock3 size={14} /><span>{idx === 0 ? '待首次联系' : idx === 1 ? '跟进资料反馈' : idx === 2 ? '安排商务会谈' : '已完成签约'}</span></div></button>)}</div><button className="addCard" type="button" onClick={() => setAddStage(key)}><Plus size={15} />添加品牌</button></div>)}</section>
    <section className="panel followupTasks"><SectionTitle title="近期跟进任务" meta={`${completedTasks.size}/${tasks.length} 项已完成`} /><div className="taskList horizontal">{tasks.map(t => <div className={`taskRow ${completedTasks.has(t.title) ? 'completed' : ''}`} key={t.title}><button type="button" aria-label={`${completedTasks.has(t.title) ? '取消完成' : '完成'}：${t.title}`} className="taskCheck" onClick={() => toggleTask(t.title)}>{completedTasks.has(t.title) && <CheckCircle2 size={14} />}</button><div className="grow"><strong>{t.title}</strong><small>{t.related}</small></div><span className={`priority priority${t.level}`}>{t.level}</span><div className="taskMeta"><span>{t.due}</span><small>{t.owner}</small></div></div>)}</div></section>
    {addStage && <GlassDialog title="添加候选品牌" subtitle={`添加到“${columns.find(([key]) => key === addStage)?.[1]}”阶段`} onClose={() => setAddStage('')} actions={<><button type="button" onClick={() => setAddStage('')}>取消</button><button type="submit" form="candidate-add-form" className="primaryAction">确认添加</button></>}><form id="candidate-add-form" className="dialogForm" onSubmit={addCandidate}><DialogField label="候选品牌" full><select value={newBrand} onChange={(event) => setNewBrand(event.target.value)}>{matchRows.map((item) => <option key={item.brand}>{item.brand}</option>)}</select></DialogField></form></GlassDialog>}
    {candidateOpen && <GlassDialog title={candidateOpen.brand} subtitle={`${listProject.name} · ${candidateOpen.stage}`} onClose={() => setCandidateOpen(null)} actions={<button type="button" className="primaryAction" onClick={() => { setCandidateOpen(null); notify('已创建下一次跟进提醒') }}>创建跟进提醒</button>}><div className="archiveGrid"><div><span>匹配得分</span><strong>{candidateOpen.score ?? '硬门槛未通过'}</strong></div><div><span>资料覆盖率</span><strong>{candidateOpen.coverage}%</strong></div><div><span>当前阶段</span><strong>{candidateOpen.stage}</strong></div><div><span>品牌业态</span><strong>{candidateOpen.category}</strong></div></div></GlassDialog>}
  </div>
}

function ImportPage({ notify }) {
  const inputRef = React.useRef(null)
  const [file, setFile] = React.useState(null)
  const [dataType, setDataType] = React.useState('brand')
  const [showAll, setShowAll] = React.useState(false)
  const [selectedBatch, setSelectedBatch] = React.useState(null)
  const importTypes = [
    { id: 'brand', label: '品牌数据', icon: Database, description: '品牌档案、业态、拓店需求与工程条件', fields: '品牌名称,一级业态,二级业态,三级业态,合作意愿,面积下限㎡,面积上限㎡,上下水,排烟,电量kW,计划开店时间', sample: '瑞幸咖啡,餐饮,咖啡茶饮,咖啡店,强,40,120,需要,不需要,60,2026Q4' },
    { id: 'project', label: '项目数据', icon: Building2, description: '项目档案、定位、体量和负责人信息', fields: '项目名称,项目类型,所在城市,经营面积㎡,项目状态,项目等级,负责人', sample: '重庆龙兴足球场,体育场馆商业,重庆市,161000,招商中,A,陈昱' },
    { id: 'unit', label: '铺位数据', icon: MapPin, description: '楼层铺位、面积、工程条件和当前状态', fields: '项目名称,铺位编码,楼层,计租面积㎡,状态,当前业态,租户名称,月租金,租约到期日', sample: '重庆龙兴足球场,L1-101,L1,86,在租,咖啡茶饮,瑞幸咖啡,27360,2029-01-31' },
    { id: 'operations', label: '经营数据', icon: Activity, description: '月度收入、成本、出租率和租金收缴', fields: '项目名称,统计月份,收入科目,收入金额,成本科目,成本金额,应收租金,实收租金,出租率', sample: '重庆龙兴足球场,2026-09,租金收入,693300,能源费用,39700,718000,693300,82.6%' },
    { id: 'contract', label: '合同数据', icon: ClipboardCheck, description: '租赁合同、期限、租金标准与履约状态', fields: '合同编号,项目名称,铺位编码,租户名称,开始日期,结束日期,租金标准元每㎡每月,保证金,履约状态', sample: 'XS-HT-2026-018,重庆龙兴足球场,L1-101,超级猩猩,2026-01-01,2031-12-31,165,516000,履约中' },
  ]
  const selectedType = importTypes.find((item) => item.id === dataType) || importTypes[0]
  const acceptFile = (nextFile) => {
    if (!nextFile) return
    if (!/\.(xlsx?|csv)$/i.test(nextFile.name)) return notify('仅支持 .xlsx、.xls 或 .csv 文件')
    if (nextFile.size > 20 * 1024 * 1024) return notify('文件超过 20MB，请压缩或拆分后重试')
    setFile(nextFile)
    notify(`已选择${selectedType.label}文件 ${nextFile.name}，正在执行 dry-run 校验`)
  }
  const downloadTemplate = () => {
    const csv = `\uFEFF${selectedType.fields}\n${selectedType.sample}\n`
    const link = document.createElement('a')
    link.href = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8' }))
    link.download = `${selectedType.label}导入模板_v1.0.csv`
    link.click()
    URL.revokeObjectURL(link.href)
    notify(`${selectedType.label} v1.0 模板已开始下载`)
  }
  const batches = [
    { name: '品牌拓店需求_0904.xlsx', type: '品牌数据', meta: '128 条 · 成功导入', time: '昨天 18:42', success: true, operator: '唐好', created: 42, updated: 86, rejected: 0 },
    { name: '项目基础资料_0902.xlsx', type: '项目数据', meta: '36 条 · 3 条待修正', time: '9月2日', success: false, operator: '赵青', created: 0, updated: 33, rejected: 3 },
    { name: '铺位及租约_0828.xlsx', type: '铺位数据', meta: '254 条 · 成功导入', time: '8月28日', success: true, operator: '李然', created: 12, updated: 242, rejected: 0 },
    { name: '八月经营月报_0820.xlsx', type: '经营数据', meta: '302 条 · 成功导入', time: '8月20日', success: true, operator: '陈昱', created: 302, updated: 0, rejected: 0 },
  ]
  return <div className="pageContent importPage">
    <section className="importIntro"><div><strong>分类数据导入</strong><p>先选择数据类型，下载对应模板后再上传，系统会按该类数据的字段规则进行校验。</p></div><button type="button" onClick={downloadTemplate}><Download size={16} />下载{selectedType.label}模板</button></section>
    <section className="importTypeGrid" aria-label="选择导入数据类型">{importTypes.map(({ id, label, icon: Icon, description }) => <button type="button" className={dataType === id ? 'active' : ''} key={id} onClick={() => { setDataType(id); setFile(null) }}><Icon size={20} /><span><strong>{label}</strong><small>{description}</small></span>{dataType === id && <CheckCircle2 size={16} />}</button>)}</section>
    <div className="importSteps">{['选择数据类型', '上传并校验', '预览变更', '确认导入'].map((s, i) => <div className={i <= (file ? 1 : 0) ? 'active' : ''} key={s}><i>{i + 1}</i><span>{s}</span>{i < 3 && <ArrowRight size={16} />}</div>)}</div>
    <section className="uploadPanel panel typedUploadPanel" onDragOver={(event) => event.preventDefault()} onDrop={(event) => { event.preventDefault(); acceptFile(event.dataTransfer.files[0]) }}><input ref={inputRef} className="srOnly" type="file" accept=".xlsx,.xls,.csv" onChange={(event) => acceptFile(event.target.files[0])} /><div className="uploadTypeBadge"><selectedType.icon size={17} />当前导入：{selectedType.label}</div><div className="uploadIcon">{file ? <FileSpreadsheet size={34} /> : <UploadCloud size={34} />}</div><h2>{file ? file.name : `拖放${selectedType.label}文件到此处`}</h2><p>{file ? '文件已接收，正按所选数据类型执行 dry-run 校验' : selectedType.description}</p><div className="uploadActions"><button type="button" onClick={downloadTemplate}><Download size={15} />下载模板</button><button type="button" className="primaryAction" onClick={() => inputRef.current?.click()}><FileUp size={16} />{file ? '重新选择文件' : '选择文件'}</button></div><small>模板与数据类型必须一致；默认校验不会直接写入数据库</small></section>
    <div className="importBottom"><section className="panel"><SectionTitle title={`${selectedType.label}校验规则`} meta={file ? '文件已进入校验队列' : '提交前自动完成'} /><div className="checkGrid"><div><BadgeCheck /><strong>模板版本</strong><span>必须使用{selectedType.label}当前版本</span></div><div><ClipboardCheck /><strong>专属字段</strong><span>校验该类数据的必填与枚举</span></div><div><Search /><strong>关联关系</strong><span>校验项目、铺位与业务编号</span></div><div><ShieldCheck /><strong>事务完整性</strong><span>失败不留下残缺数据</span></div></div></section><section className="panel"><SectionTitle title="最近导入批次" meta="按数据类型保留记录" action={<button type="button" className="textAction" onClick={() => setShowAll(!showAll)}>{showAll ? '收起' : '查看全部'}</button>} /><div className="batchList">{batches.slice(0, showAll ? batches.length : 2).map((batch) => <button type="button" key={batch.name} onClick={() => setSelectedBatch(batch)}><i className={batch.success ? 'successIcon' : 'warningIcon'}>{batch.success ? <CheckCircle2 /> : <Info />}</i><span><strong>{batch.name}</strong><small>{batch.type} · {batch.meta}</small></span><time>{batch.time}</time><ArrowRight size={14} /></button>)}</div></section></div>
    {selectedBatch && <GlassDialog title={selectedBatch.name} subtitle={`${selectedBatch.type} · 导入批次明细`} onClose={() => setSelectedBatch(null)} actions={<button type="button" className="primaryAction" onClick={() => setSelectedBatch(null)}>关闭</button>}><DataDetailTable columns={['处理项', '结果']} rows={[["数据类型", selectedBatch.type], ["批次状态", selectedBatch.success ? '导入成功' : '存在待修正数据'], ['操作人', selectedBatch.operator], ['处理时间', selectedBatch.time], ['新增记录', `${selectedBatch.created} 条`], ['更新记录', `${selectedBatch.updated} 条`], ['未导入记录', `${selectedBatch.rejected} 条`]]} note={selectedBatch.success ? '该批次已通过专属字段、枚举、重复与关联校验。' : '未导入记录保留在校验结果中，修正后可重新上传。'} /></GlassDialog>}
  </div>
}

function SettingsPage({ notify }) {
  const [tab, setTab] = React.useState('users')
  const [weights, setWeights] = React.useState([['业态适配', 20], ['面积适配', 15], ['层高承重', 10], ['给排水', 10], ['排烟燃气电力', 15], ['楼层临街', 10], ['商务条件', 10], ['拓店与合作意愿', 10]])
  const [historyOpen, setHistoryOpen] = React.useState(false)
  const [saveOpen, setSaveOpen] = React.useState(false)
  const [versionNote, setVersionNote] = React.useState('')
  const [userCreateOpen, setUserCreateOpen] = React.useState(false)
  const [selectedUser, setSelectedUser] = React.useState(null)
  const [userForm, setUserForm] = React.useState({ name: '', department: '资产经营部', role: '项目管理员', account: '', mfa: '强制启用' })
  const [userList, setUserList] = React.useState([
    { name: '唐好', account: 'tanghao', department: '系统管理', role: '超级管理员', status: '正常', mfa: '已启用', lastLogin: '今天 14:28' },
    { name: '陈昱', account: 'chenyu', department: '招商运营部', role: '招商管理员', status: '正常', mfa: '已启用', lastLogin: '今天 11:06' },
    { name: '李然', account: 'liran', department: '资产经营部', role: '项目管理员', status: '正常', mfa: '已启用', lastLogin: '昨天 18:42' },
    { name: '赵青', account: 'zhaoqing', department: '数据管理部', role: '数据管理员', status: '正常', mfa: '待启用', lastLogin: '9月4日 09:15' },
    { name: '王明', account: 'wangming', department: '外部协作', role: '只读用户', status: '已停用', mfa: '—', lastLogin: '8月21日 16:20' },
  ])
  const tabs = [
    ['users', '用户与权限', UsersRound], ['matching', '匹配规则', Target], ['scoring', '评分规则', Activity], ['dictionary', '分类与字典', Database], ['logs', '操作日志', History],
  ]
  const activeTab = tabs.find(([id]) => id === tab)
  const ActiveIcon = activeTab[2]
  const total = weights.reduce((sum, [, value]) => sum + Number(value || 0), 0)
  const saveVersion = (event) => {
    event.preventDefault()
    setSaveOpen(false)
    notify('匹配规则 v1.1 已保存为当前会话版本')
  }
  const createUser = (event) => {
    event.preventDefault()
    const user = { ...userForm, account: userForm.account || `user${userList.length + 1}`, status: '正常', mfa: userForm.mfa === '强制启用' ? '待绑定' : '未启用', lastLogin: '尚未登录' }
    setUserList((items) => [...items, user])
    setUserCreateOpen(false)
    notify(`管理人员“${user.name}”已创建，请通知本人完成首次登录与安全验证`)
  }
  const userManagement = <section className="userManagement">
    <section className="panel userSummaryPanel"><SectionTitle title="用户管理中心" meta={`${userList.filter((user) => user.status === '正常').length} 个启用账户 · 角色与安全策略统一管理`} action={<button type="button" className="primaryAction" onClick={() => setUserCreateOpen(true)}><Plus size={16} />新增管理人员</button>} /><div className="userSecurityKpis"><div><span>账户总数</span><strong>{userList.length}</strong><small>含 1 个停用账户</small></div><div><span>管理员账户</span><strong>4</strong><small>按最小权限分配</small></div><div><span>多因素认证</span><strong>80%</strong><small>1 人待完成绑定</small></div><div><span>安全风险</span><strong className="safeValue">0</strong><small>近 30 天无高危事件</small></div></div></section>
    <section className="panel userTablePanel"><SectionTitle title="管理人员与权限" meta="点击人员查看账户详情" /><div className="userTable"><div className="userTableHeader"><span>姓名/账户</span><span>所属部门</span><span>系统角色</span><span>账户状态</span><span>多因素认证</span><span>最近登录</span><span>操作</span></div>{userList.map((user) => <div className="userTableRow" key={user.account}><div><strong>{user.name}</strong><small>{user.account}</small></div><span>{user.department}</span><span>{user.role}</span><span className={`accountStatus ${user.status === '已停用' ? 'disabled' : ''}`}>{user.status}</span><span className={user.mfa.includes('启用') ? 'safeText' : 'warningText'}>{user.mfa}</span><span>{user.lastLogin}</span><button type="button" onClick={() => setSelectedUser(user)}>管理 <ArrowRight size={13} /></button></div>)}</div></section>
    <section className="panel securityPolicyPanel"><SectionTitle title="账户安全策略" meta="适用于全部管理账户" /><div className="securityPolicyGrid"><div><ShieldCheck size={20} /><span><strong>多因素认证</strong><small>超级管理员与业务管理员强制启用</small></span><em>已开启</em></div><div><Clock3 size={20} /><span><strong>登录会话</strong><small>连续 30 分钟无操作自动退出</small></span><em>30 分钟</em></div><div><ShieldCheck size={20} /><span><strong>异常登录保护</strong><small>连续 5 次失败后锁定并通知管理员</small></span><em>已开启</em></div><div><History size={20} /><span><strong>操作审计</strong><small>权限、导入及数据修改保留审计记录</small></span><em>180 天</em></div></div></section>
  </section>
  return <div className="pageContent settingsPage"><div className="settingsNav panel">{tabs.map(([id, label, Icon]) => <button type="button" className={tab === id ? 'active' : ''} onClick={() => setTab(id)} key={id} title={['matching', 'scoring', 'dictionary'].includes(id) ? '仅系统管理员可见' : undefined}><Icon />{label}{['matching', 'scoring', 'dictionary'].includes(id) && <small>管理员</small>}</button>)}</div>{tab === 'matching' ? <section className="panel rulePanel"><SectionTitle title="匹配规则 v1.0" meta="管理员专属配置 · 当前生效版本 · 2026年9月4日启用" action={<div className="ruleActions"><button type="button" onClick={() => setHistoryOpen(true)}>查看历史版本</button><button className="primaryAction" type="button" disabled={total !== 100} onClick={() => setSaveOpen(true)}><Save size={16} />另存新版本</button></div>} /><div className="ruleSection"><h3>八维权重</h3><p>所有权重合计必须为 100%。调整后需要另存版本，历史结果不会被重算覆盖。</p><div className="weightGrid">{weights.map(([name, value], index) => <label key={name}><span>{name}</span><div><input type="number" min="0" max="100" value={value} onChange={(event) => setWeights((items) => items.map((item, itemIndex) => itemIndex === index ? [item[0], event.target.value] : item))} /><em>%</em></div></label>)}</div><div className={`weightTotal ${total !== 100 ? 'invalid' : ''}`}><span>权重合计</span><strong>{total}%</strong>{total !== 100 && <small>请调整至 100% 后保存</small>}</div></div><div className="ruleColumns"><div className="ruleSection"><h3>结论阈值</h3><div className="thresholds"><label><i className="t1" /><span>优先推进</span><strong>≥ 85</strong></label><label><i className="t2" /><span>重点储备</span><strong>70–84</strong></label><label><i className="t3" /><span>持续观察</span><strong>55–69</strong></label><label><i className="t4" /><span>暂不匹配</span><strong>＜ 55</strong></label></div></div><div className="ruleSection"><h3>资料覆盖率</h3><div className="thresholds"><label><i className="t1" /><span>正式结论</span><strong>≥ 80%</strong></label><label><i className="t2" /><span>初步结论</span><strong>60%–79%</strong></label><label><i className="t4" /><span>资料不足</span><strong>＜ 60%</strong></label></div></div></div></section> : tab === 'users' ? userManagement : <section className="panel settingsPlaceholder"><ActiveIcon size={30} /><h2>{activeTab[1]}</h2><p>已切换到{activeTab[1]}模块。此区域将在接入后端管理接口后显示真实配置内容。</p></section>}
    {historyOpen && <GlassDialog title="匹配规则历史版本" subtitle="历史版本仅供追溯，不会影响当前匹配结果" onClose={() => setHistoryOpen(false)} actions={<button type="button" className="primaryAction" onClick={() => setHistoryOpen(false)}>关闭</button>}><div className="versionList"><div><strong>v1.0 · 当前生效</strong><span>2026年9月4日 · 唐好</span></div><div><strong>v0.9 · 初始评审版</strong><span>2026年8月28日 · 陈昱</span></div></div></GlassDialog>}
    {saveOpen && <GlassDialog title="另存匹配规则版本" subtitle="新版本将保留当前八维权重配置" onClose={() => setSaveOpen(false)} actions={<><button type="button" onClick={() => setSaveOpen(false)}>取消</button><button type="submit" form="version-save-form" className="primaryAction">保存 v1.1</button></>}><form id="version-save-form" className="dialogForm" onSubmit={saveVersion}><DialogField label="版本说明" full><textarea rows="4" required value={versionNote} onChange={(event) => setVersionNote(event.target.value)} placeholder="说明本次调整的业务原因" /></DialogField></form></GlassDialog>}
    {userCreateOpen && <GlassDialog title="新增管理人员" subtitle="创建账户并分配最小必要权限" onClose={() => setUserCreateOpen(false)} actions={<><button type="button" onClick={() => setUserCreateOpen(false)}>取消</button><button type="submit" form="user-create-form" className="primaryAction">创建账户</button></>}><form id="user-create-form" className="dialogForm" onSubmit={createUser}><DialogField label="姓名"><input required autoFocus value={userForm.name} onChange={(event) => setUserForm({ ...userForm, name: event.target.value })} placeholder="请输入姓名" /></DialogField><DialogField label="登录账户"><input value={userForm.account} onChange={(event) => setUserForm({ ...userForm, account: event.target.value })} placeholder="留空则自动生成" /></DialogField><DialogField label="所属部门"><select value={userForm.department} onChange={(event) => setUserForm({ ...userForm, department: event.target.value })}><option>资产经营部</option><option>招商运营部</option><option>数据管理部</option><option>系统管理</option></select></DialogField><DialogField label="系统角色"><select value={userForm.role} onChange={(event) => setUserForm({ ...userForm, role: event.target.value })}><option>项目管理员</option><option>招商管理员</option><option>数据管理员</option><option>只读用户</option></select></DialogField><DialogField label="安全验证" full><select value={userForm.mfa} onChange={(event) => setUserForm({ ...userForm, mfa: event.target.value })}><option>强制启用</option><option>首次登录提醒启用</option></select></DialogField></form></GlassDialog>}
    {selectedUser && <GlassDialog title={selectedUser.name} subtitle={`账户 ${selectedUser.account} · ${selectedUser.department}`} onClose={() => setSelectedUser(null)} actions={<><button type="button" onClick={() => { setUserList((items) => items.map((user) => user.account === selectedUser.account ? { ...user, status: user.status === '正常' ? '已停用' : '正常' } : user)); setSelectedUser(null); notify(`账户“${selectedUser.account}”状态已更新`) }}>{selectedUser.status === '正常' ? '停用账户' : '恢复账户'}</button><button type="button" className="primaryAction" onClick={() => setSelectedUser(null)}>完成</button></>}><div className="archiveGrid"><div><span>系统角色</span><strong>{selectedUser.role}</strong></div><div><span>账户状态</span><strong>{selectedUser.status}</strong></div><div><span>多因素认证</span><strong>{selectedUser.mfa}</strong></div><div><span>最近登录</span><strong>{selectedUser.lastLogin}</strong></div><div className="full"><span>权限范围</span><p>仅授予该角色所需的项目、品牌与经营数据访问权限；敏感操作将写入审计日志。</p></div></div></GlassDialog>}
  </div>
}

export default function App() {
  return <AppDataProvider><AppShell /></AppDataProvider>
}

function AppShell() {
  const [current, setCurrent] = React.useState('dashboard')
  const [toast, setToast] = React.useState('')
  const toastTimer = React.useRef()
  const notify = React.useCallback((message) => {
    setToast(message)
    window.clearTimeout(toastTimer.current)
    toastTimer.current = window.setTimeout(() => setToast(''), 2600)
  }, [])
  React.useEffect(() => () => window.clearTimeout(toastTimer.current), [])
  const pages = {
    dashboard: <DashboardPage onNavigate={setCurrent} />, map: <MapPage onNavigate={setCurrent} />, brands: <BrandsPage onNavigate={setCurrent} notify={notify} />,
    projects: <ProjectsPage notify={notify} />, operations: <OperationsPage notify={notify} />, matching: <MatchingPage onNavigate={setCurrent} notify={notify} />, followup: <FollowupPage notify={notify} />,
    management: <ManagementCenter notify={notify} onNavigate={setCurrent} />, import: <ImportPage notify={notify} />, settings: <SettingsPage notify={notify} />,
  }
  return <div className="appShell">
    <SideNav current={current} onNavigate={setCurrent} />
    <main className="main">
      {pages[current]}
    </main>
    {toast && <div className="appToast" role="status"><CheckCircle2 size={17} />{toast}</div>}
  </div>
}
