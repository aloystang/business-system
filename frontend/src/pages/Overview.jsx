import React, { useEffect, useMemo, useRef, useState } from 'react'
import DashboardLayout from '../components/DashboardLayout'
import { apiJson } from '../lib/api'
import { DEFAULT_AMAP_CENTER, loadAmapSdk } from '../lib/amap'
import { CHONGQING_DISTRICTS } from '../lib/options'

const AMAP_JS_KEY = import.meta.env.VITE_AMAP_JS_KEY || ''
const DEFAULT_CITY = import.meta.env.VITE_MAP_DEFAULT_CITY || '重庆市'

function buildQuery(params) {
  const search = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => {
    if (value === undefined || value === null || value === '') return
    search.set(key, String(value))
  })
  const query = search.toString()
  return query ? `?${query}` : ''
}

function formatNumber(value, digits = 1) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return '—'
  return Number(value).toFixed(digits)
}

function formatPercent(value, digits = 1) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return '—'
  return `${Number(value).toFixed(digits)}%`
}

function escapeHtml(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;')
}

function getCityCandidates(cityValue) {
  const raw = String(cityValue || '').trim()
  if (!raw) return []
  const candidates = [raw]
  if (raw.endsWith('市')) {
    candidates.push(raw.slice(0, -1))
  } else {
    candidates.push(`${raw}市`)
  }
  return Array.from(new Set(candidates.filter(Boolean)))
}

function normalizeCityText(value) {
  return String(value || '').trim().replace(/\s+/g, '')
}

function cityMatches(itemCity, candidates) {
  if (!Array.isArray(candidates) || candidates.length === 0) return true
  const cityText = normalizeCityText(itemCity)
  if (!cityText) return false
  return candidates.some((candidate) => {
    const c = normalizeCityText(candidate)
    if (!c) return false
    return cityText === c || cityText.startsWith(c) || c.startsWith(cityText)
  })
}

function calcKpisFromPoints(rows) {
  const safeRows = Array.isArray(rows) ? rows : []
  const merchants = safeRows.filter((item) => item.point_type === 'merchant')
  const competitors = safeRows.filter((item) => item.point_type === 'competitor')
  const districtSet = new Set(safeRows.map((item) => item.district).filter(Boolean))
  const merchantRents = merchants
    .map((item) => Number(item.rent_unit_price))
    .filter((value) => Number.isFinite(value))
  const competitorVacancies = competitors
    .map((item) => Number(item.vacancy_rate))
    .filter((value) => Number.isFinite(value))
  const merchantFlows = merchants
    .map((item) => Number(item.daily_flow))
    .filter((value) => Number.isFinite(value))

  const avg = (values) => {
    if (!values.length) return null
    return Number((values.reduce((sum, value) => sum + value, 0) / values.length).toFixed(2))
  }

  return {
    total_points: safeRows.length,
    merchant_count: merchants.length,
    competitor_count: competitors.length,
    covered_district_count: districtSet.size,
    avg_rent_unit_price: avg(merchantRents),
    avg_vacancy_rate: avg(competitorVacancies),
    avg_daily_flow: avg(merchantFlows),
  }
}

function normalizeTextKey(value) {
  return String(value || '').trim().toLowerCase()
}

function parseTimeMs(value) {
  if (!value) return 0
  const ts = Date.parse(value)
  return Number.isFinite(ts) ? ts : 0
}

function normalizeAddressKey(value) {
  return String(value || '')
    .trim()
    .toLowerCase()
    .replace(/\s+/g, '')
    .replace(/[，,。.;；\-_/]/g, '')
}

function dedupePoints(rows) {
  const source = Array.isArray(rows) ? rows : []
  const latestByKey = new Map()
  source.forEach((item) => {
    const key = [
      normalizeTextKey(item.point_type),
      normalizeTextKey(item.name),
      normalizeAddressKey(item.address),
    ].join('|')
    const prev = latestByKey.get(key)
    if (!prev || parseTimeMs(item.created_at) >= parseTimeMs(prev.created_at)) {
      latestByKey.set(key, item)
    }
  })
  return Array.from(latestByKey.values()).sort(
    (a, b) => parseTimeMs(b.created_at) - parseTimeMs(a.created_at)
  )
}

const DETAIL_FIELDS = {
  merchant: [
    { key: 'category', label: '品类' },
    { key: 'area_m2', label: '面积', unit: '㎡' },
    { key: 'rent_unit_price', label: '租金单价', unit: '元/㎡/月' },
    { key: 'daily_flow', label: '日均客流', unit: '人' },
    { key: 'address', label: '地址', type: 'text' },
  ],
  competitor: [
    { key: 'scale_m2', label: '商业体量', unit: '㎡' },
    { key: 'avg_rent_unit_price', label: '平均租金单价', unit: '元/㎡/月' },
    { key: 'vacancy_rate', label: '空置率', unit: '%' },
    { key: 'target_people', label: '目标人群', type: 'text' },
    { key: 'address', label: '地址', type: 'text' },
  ],
}

const DETAIL_HIGHLIGHTS = {
  merchant: [
    ['rent_unit_price', '租金单价', '元/㎡/月'],
    ['daily_flow', '日均客流', '人'],
    ['area_m2', '面积', '㎡'],
  ],
  competitor: [
    ['avg_rent_unit_price', '平均租金', '元/㎡/月'],
    ['vacancy_rate', '空置率', '%'],
    ['scale_m2', '商业体量', '㎡'],
  ],
}

function formatHighlightValue(value, unit) {
  if (value === null || value === undefined || value === '') return '—'
  const numberValue = Number(value)
  if (!Number.isFinite(numberValue)) return String(value)
  return `${numberValue.toLocaleString()}${unit}`
}

function formatPopupValue(value, unit = '') {
  if (value === null || value === undefined || value === '') return '—'
  const numeric = Number(value)
  if (Number.isFinite(numeric)) return `${numeric.toLocaleString()}${unit}`
  return `${value}${unit}`
}

function formatDateTime(value) {
  if (!value) return '—'
  const time = new Date(value)
  if (Number.isNaN(time.getTime())) return '—'
  return time.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function formatDetailValue(field, value) {
  if (value === null || value === undefined || value === '') return '—'
  if (field?.type === 'text') return String(value)
  if (field?.unit) {
    const numeric = Number(value)
    if (Number.isFinite(numeric)) return `${numeric.toLocaleString()} ${field.unit}`.trim()
  }
  return String(value)
}

export default function Overview() {
  const mapContainerRef = useRef(null)
  const mapInstanceRef = useRef(null)
  const markerClusterRef = useRef(null)
  const markerListRef = useRef([])
  const markerPointPositionRef = useRef({})
  const infoWindowRef = useRef(null)
  const hasAutoFitRef = useRef(false)
  const pointsRef = useRef([])

  const [filters, setFilters] = useState({
    city: DEFAULT_CITY,
    district: '',
    type: 'all',
    keyword: '',
  })
  const [kpis, setKpis] = useState(null)
  const [points, setPoints] = useState([])
  const [activePointId, setActivePointId] = useState('')
  const [activePointDetail, setActivePointDetail] = useState(null)
  const [sourceProjectLoading, setSourceProjectLoading] = useState(false)
  const [sourceProjectError, setSourceProjectError] = useState('')
  const [sourceProjectDetail, setSourceProjectDetail] = useState(null)
  const [loading, setLoading] = useState(false)
  const [mapReady, setMapReady] = useState(false)
  const [mapError, setMapError] = useState('')
  const [error, setError] = useState('')

  const districtOptions = useMemo(() => {
    const set = new Set()
    if ((filters.city || '').includes('重庆')) {
      CHONGQING_DISTRICTS.forEach((item) => set.add(item))
    }
    points.forEach((item) => {
      if (item.district) set.add(item.district)
    })
    return Array.from(set)
  }, [filters.city, points])

  const recentPoints = useMemo(() => {
    return [...points]
      .sort((a, b) => parseTimeMs(b.created_at) - parseTimeMs(a.created_at))
      .slice(0, 6)
  }, [points])

  const buildInfoWindowContent = (detail) => {
    if (!detail) return ''
    const payload = detail.payload || {}
    const typeLabel = detail.point_type === 'merchant' ? '商家调研' : '竞争关系'
    const typeShort = detail.point_type === 'merchant' ? '商' : '竞'
    const metrics =
      detail.point_type === 'merchant'
        ? [
            ['租金单价', formatPopupValue(payload.rent_unit_price, '元/㎡/月')],
            ['面积', formatPopupValue(payload.area_m2, '㎡')],
            ['日均客流', formatPopupValue(payload.daily_flow, '人')],
          ]
        : [
            ['平均租金', formatPopupValue(payload.avg_rent_unit_price, '元/㎡/月')],
            ['商业体量', formatPopupValue(payload.scale_m2, '㎡')],
            ['空置率', formatPopupValue(payload.vacancy_rate, '%')],
          ]
    const metricsHtml = metrics
      .map(
        ([label, value]) => `<article class="dash-map-iw-metric">
          <span>${escapeHtml(label)}</span>
          <strong>${escapeHtml(value)}</strong>
        </article>`
      )
      .join('')
    return `<section class="dash-map-iw">
      <header class="dash-map-iw-head ${detail.point_type === 'merchant' ? 'merchant' : 'competitor'}">
        <div class="dash-map-iw-icon ${detail.point_type === 'merchant' ? 'merchant' : 'competitor'}">
          ${escapeHtml(typeShort)}
        </div>
        <div class="dash-map-iw-title-wrap">
          <strong>${escapeHtml(payload.name || '未命名点位')}</strong>
          <p>${escapeHtml(payload.city || '—')} · ${escapeHtml(payload.district || '—')}</p>
        </div>
        <span class="dash-map-iw-badge ${detail.point_type === 'merchant' ? 'merchant' : 'competitor'}">${escapeHtml(
        typeLabel
      )}</span>
      </header>
      <div class="dash-map-iw-metrics">${metricsHtml}</div>
      <div class="dash-map-iw-address">
        <span class="dash-map-iw-address-label">地址</span>
        <span>${escapeHtml(payload.address || '—')}</span>
      </div>
      <div class="dash-map-iw-meta-row">
        <span class="dash-map-iw-project">来源：${escapeHtml(detail.project_name || detail.project_id || '—')}</span>
        <span class="dash-map-iw-time">${escapeHtml(formatDateTime(payload.created_at))}</span>
      </div>
      <div class="dash-map-iw-foot">点击右侧“点位详情”查看完整信息</div>
    </section>`
  }

  const updateFilter = (key, value) => {
    setFilters((prev) => ({ ...prev, [key]: value }))
  }

  const drawPointsOnMap = (rows) => {
    const map = mapInstanceRef.current
    const AMap = window.AMap
    if (!map || !AMap) return

    if (markerListRef.current.length > 0) {
      map.remove(markerListRef.current)
      markerListRef.current = []
    }

    if (!rows || rows.length === 0) return

    const grouped = new Map()
    rows.forEach((point) => {
      const lng = Number(point.longitude)
      const lat = Number(point.latitude)
      if (!Number.isFinite(lng) || !Number.isFinite(lat)) return
      const key = `${lng.toFixed(6)},${lat.toFixed(6)}`
      if (!grouped.has(key)) grouped.set(key, [])
      grouped.get(key).push(point)
    })

    const pointPositionMap = {}
    const markers = []
    grouped.forEach((group) => {
      const total = group.length
      group.forEach((point, index) => {
        const baseLng = Number(point.longitude)
        const baseLat = Number(point.latitude)
        if (!Number.isFinite(baseLng) || !Number.isFinite(baseLat)) return

        let markerLng = baseLng
        let markerLat = baseLat
        if (total > 1) {
          const angle = (2 * Math.PI * index) / total
          const radius = 0.00015 + Math.min(total - 1, 6) * 0.00002
          const cosLat = Math.max(Math.cos((baseLat * Math.PI) / 180), 0.35)
          markerLng = baseLng + (radius * Math.cos(angle)) / cosLat
          markerLat = baseLat + radius * Math.sin(angle)
        }

        const markerNode = document.createElement('div')
        markerNode.className = `dash-map-pin ${point.point_type === 'merchant' ? 'merchant' : 'competitor'}`
        markerNode.innerHTML = `
          <div class="dash-map-pin-cloud"></div>
          <div class="dash-map-pin-drop"></div>
          <div class="dash-map-pin-word">${point.point_type === 'merchant' ? '商' : '竞'}</div>
        `

        const marker = new AMap.Marker({
          position: [markerLng, markerLat],
          zIndex: 120,
          offset: new AMap.Pixel(-16, -36),
          content: markerNode,
          title: point.name,
        })
        marker.on('click', () => {
          setActivePointId(point.point_id)
        })
        markers.push(marker)
        pointPositionMap[point.point_id] = [markerLng, markerLat]
      })
    })

    if (markers.length === 0) {
      return
    }
    markerListRef.current = markers
    markerPointPositionRef.current = pointPositionMap
    map.add(markers)

    if (!hasAutoFitRef.current && markers.length > 0) {
      map.setFitView(markers, false, [80, 80, 80, 80])
      hasAutoFitRef.current = true
    }
  }

  const errorMessage = (reason, fallback) => {
    if (reason instanceof Error && reason.message) return reason.message
    if (typeof reason === 'string' && reason.trim()) return reason
    return fallback
  }

  const refreshData = async () => {
    setLoading(true)
    setError('')
    try {
      const queryBase = {
        city: '',
        district: filters.district,
        type: filters.type,
        keyword: filters.keyword,
      }
      const cityCandidates = getCityCandidates(filters.city)
      const pointsResp = await apiJson(
        `/api/overview/map/points${buildQuery({
          ...queryBase,
          page: 1,
          page_size: 300,
        })}`
      )
      const rawItems = Array.isArray(pointsResp.items) ? pointsResp.items : []
      const cityMatchedPoints = rawItems.filter((item) => cityMatches(item.city, cityCandidates))
      const sourcePoints =
        cityMatchedPoints.length === 0 && rawItems.length > 0 ? rawItems : cityMatchedPoints
      const nextPoints = dedupePoints(sourcePoints)
      setPoints(nextPoints)
      pointsRef.current = nextPoints
      setKpis(calcKpisFromPoints(nextPoints))
      if (activePointId) {
        const exists = nextPoints.some((item) => item.point_id === activePointId)
        if (!exists) {
          setActivePointId('')
          setActivePointDetail(null)
        }
      }
      setError('')
    } catch (err) {
      setError(errorMessage(err, '加载地图数据失败'))
      setKpis(null)
      setPoints([])
      pointsRef.current = []
      setActivePointId('')
      setActivePointDetail(null)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (!AMAP_JS_KEY) {
      setMapError('未配置 VITE_AMAP_JS_KEY，无法显示地图底图。')
      return
    }
    let disposed = false
    loadAmapSdk(AMAP_JS_KEY)
      .then((AMap) => {
        if (disposed || !mapContainerRef.current) return
        const map = new AMap.Map(mapContainerRef.current, {
          zoom: 11,
          center: DEFAULT_AMAP_CENTER,
          mapStyle: 'amap://styles/normal',
        })
        map.addControl(new AMap.Scale())
        if (DEFAULT_CITY) {
          map.setCity(DEFAULT_CITY)
        }
        mapInstanceRef.current = map
        setMapReady(true)
      })
      .catch((err) => {
        if (disposed) return
        setMapError(err.message || '地图初始化失败')
      })
    return () => {
      disposed = true
      if (markerClusterRef.current) {
        markerClusterRef.current.setMap(null)
        markerClusterRef.current = null
      }
      if (infoWindowRef.current) {
        infoWindowRef.current.close()
        infoWindowRef.current = null
      }
      if (mapInstanceRef.current) {
        mapInstanceRef.current.destroy()
        mapInstanceRef.current = null
      }
    }
  }, [])

  useEffect(() => {
    refreshData()
  }, [filters])

  useEffect(() => {
    hasAutoFitRef.current = false
  }, [filters.city, filters.district, filters.type, filters.keyword])

  useEffect(() => {
    if (!mapReady) return
    drawPointsOnMap(points)
  }, [mapReady, points])

  useEffect(() => {
    if (!activePointId) {
      setActivePointDetail(null)
      setSourceProjectDetail(null)
      setSourceProjectError('')
      if (infoWindowRef.current) {
        infoWindowRef.current.close()
      }
      return
    }
    let cancelled = false
    apiJson(`/api/overview/map/point/${encodeURIComponent(activePointId)}`)
      .then((detail) => {
        if (!cancelled) setActivePointDetail(detail)
      })
      .catch((err) => {
        if (!cancelled) setError(err.message || '加载点位详情失败')
      })
    return () => {
      cancelled = true
    }
  }, [activePointId])

  useEffect(() => {
    if (!activePointDetail) return
    const map = mapInstanceRef.current
    const AMap = window.AMap
    if (!map || !AMap) return
    const point = points.find((item) => item.point_id === activePointDetail.point_id)
    if (!point) return
    const mappedPosition = markerPointPositionRef.current[activePointDetail.point_id]
    const lng = mappedPosition ? Number(mappedPosition[0]) : Number(point.longitude)
    const lat = mappedPosition ? Number(mappedPosition[1]) : Number(point.latitude)
    if (!Number.isFinite(lng) || !Number.isFinite(lat)) return
    if (!infoWindowRef.current) {
      infoWindowRef.current = new AMap.InfoWindow({
        isCustom: true,
        closeWhenClickMap: true,
        offset: new AMap.Pixel(0, -20),
      })
    }
    infoWindowRef.current.setContent(buildInfoWindowContent(activePointDetail))
    infoWindowRef.current.open(map, [lng, lat])
  }, [activePointDetail, points])

  const loadSourceProject = async () => {
    if (!activePointDetail?.project_id) return
    setSourceProjectLoading(true)
    setSourceProjectError('')
    try {
      const project = await apiJson(`/api/projects/${encodeURIComponent(activePointDetail.project_id)}`)
      setSourceProjectDetail(project)
    } catch (err) {
      setSourceProjectDetail(null)
      setSourceProjectError(errorMessage(err, '加载来源项目失败'))
    } finally {
      setSourceProjectLoading(false)
    }
  }

  const handleReset = () => {
    setFilters({
      city: DEFAULT_CITY,
      district: '',
      type: 'all',
      keyword: '',
    })
  }

  return (
    <DashboardLayout title="业务全览" overline="OVERVIEW">
      <section className="dash-overview-map-page">
        {error && <div className="notice">{error}</div>}

        <div className="dash-card dash-card-primary dash-page-intro dash-overview-hero">
          <div className="dash-module-header">
            <div>
              <h2>重庆市商业调研看板</h2>
              <p className="dash-module-desc">围绕城市区域、商家调研与竞争关系数据，形成可追溯的地图化工作台。</p>
            </div>
            <div className="dash-collect-statuses">
              <span className="dash-status merchant">默认城市：{DEFAULT_CITY}</span>
              <span className={`dash-status ${points.length ? 'merchant' : 'deleted'}`}>
                {points.length ? `已加载 ${points.length} 个点位` : '当前无点位'}
              </span>
            </div>
          </div>
          <div className="dash-collect-kpis dash-overview-hero-kpis">
            <article className="dash-collect-kpi">
              <span>城市范围</span>
              <strong>{DEFAULT_CITY}</strong>
              <small>聚焦商业调研主战场</small>
            </article>
            <article className="dash-collect-kpi">
              <span>当前筛选</span>
              <strong>{filters.district || '全部区域'}</strong>
              <small>{filters.type === 'all' ? '商家 + 竞品' : filters.type === 'merchant' ? '仅商家调研' : '仅竞争关系'}</small>
            </article>
            <article className="dash-collect-kpi">
              <span>覆盖区域</span>
              <strong>{kpis?.covered_district_count ?? 0} 个</strong>
              <small>基于已上图点位自动汇总</small>
            </article>
            <article className="dash-collect-kpi">
              <span>最近更新</span>
              <strong>{recentPoints[0]?.name || '等待数据'}</strong>
              <small>{recentPoints[0]?.created_at ? formatDateTime(recentPoints[0].created_at) : '录入后自动刷新'}</small>
            </article>
          </div>
        </div>

        <div className="dash-card dash-card-muted dash-map-filter-card">
          <div className="dash-map-locked-city">当前城市：{DEFAULT_CITY}</div>
          <div className="dash-map-filter-grid">
            <label className="dash-field">
              <span>区域</span>
              <select
                className="dash-select"
                value={filters.district}
                onChange={(event) => updateFilter('district', event.target.value)}
              >
                <option value="">全部区域</option>
                {districtOptions.map((district) => (
                  <option key={district} value={district}>
                    {district}
                  </option>
                ))}
              </select>
            </label>
            <label className="dash-field">
              <span>类型</span>
              <select
                className="dash-select"
                value={filters.type}
                onChange={(event) => updateFilter('type', event.target.value)}
              >
                <option value="all">全部</option>
                <option value="merchant">商家调研</option>
                <option value="competitor">竞争关系</option>
              </select>
            </label>
            <label className="dash-field">
              <span>关键词</span>
              <input
                className="dash-input"
                value={filters.keyword}
                onChange={(event) => updateFilter('keyword', event.target.value)}
                placeholder="商家/竞品/项目名称"
              />
            </label>
            <label className="dash-field">
              <span>操作</span>
              <button className="dash-btn secondary dash-map-filter-clear-btn" type="button" onClick={handleReset}>
                清空筛选
              </button>
            </label>
          </div>
          <div className="dash-helper">已加载点位：{points.length}</div>
        </div>

        <div className="dash-overview-kpi-grid">
          <div className="dash-card dash-card-primary dash-overview-kpi-card dash-overview-kpi-card-main">
            <span>总点位</span>
            <strong>{kpis?.total_points ?? 0}</strong>
            <small>规模组</small>
          </div>
          <div className="dash-card dash-card-secondary dash-overview-kpi-card">
            <span>商家 / 竞品</span>
            <strong>
              {(kpis?.merchant_count ?? 0).toLocaleString()} / {(kpis?.competitor_count ?? 0).toLocaleString()}
            </strong>
            <small>规模组</small>
          </div>
          <div className="dash-card dash-card-secondary dash-overview-kpi-card">
            <span>商家平均租金单价（元/㎡/月）</span>
            <strong>{formatNumber(kpis?.avg_rent_unit_price, 2)}</strong>
            <small>经营组</small>
          </div>
          <div className="dash-card dash-card-muted dash-overview-kpi-card">
            <span>竞品平均空置率</span>
            <strong>{formatPercent(kpis?.avg_vacancy_rate, 1)}</strong>
            <small>经营组</small>
          </div>
        </div>

        <div className="dash-overview-map-layout">
          <div className="dash-card dash-card-primary dash-overview-map-card">
            {mapError ? (
              <div className="dash-map-empty">
                <strong>{mapError}</strong>
                <p>请在前端环境变量中配置 `VITE_AMAP_JS_KEY` 后刷新页面。</p>
              </div>
            ) : (
              <div ref={mapContainerRef} className="dash-overview-map-canvas" />
            )}
            {!loading && !mapError && points.length === 0 && (
              <div className="dash-map-empty overlay dash-map-empty-fancy">
                <div className="dash-map-empty-logo">
                  <div className="dash-map-empty-cloud" />
                  <div className="dash-map-empty-pin">
                    <span className="material-symbols-outlined">location_on</span>
                  </div>
                  <div className="dash-map-empty-word">城</div>
                </div>
                <strong>当前区域暂无点位</strong>
                <p>请切换区域或先录入调研数据。</p>
                <div className="dash-map-empty-suggest">
                  <article className="dash-map-empty-card">
                    <h4>商家调研</h4>
                    <p>录入商家租金、面积、客流后可自动上图。</p>
                  </article>
                  <article className="dash-map-empty-card">
                    <h4>竞争关系</h4>
                    <p>录入竞品体量、空置率等信息形成区域对比。</p>
                  </article>
                </div>
              </div>
            )}
          </div>

          <aside className="dash-card dash-card-secondary dash-overview-drawer">
            <h3>点位详情</h3>
            {!activePointDetail && (
              <div className="dash-overview-detail-empty">
                <div className="dash-overview-detail-empty-head">
                  <div className="dash-overview-detail-empty-icon">
                    <span className="material-symbols-outlined">pin_drop</span>
                  </div>
                  <div>
                    <strong>等待选择点位</strong>
                    <p className="dash-helper">点击地图点位后，这里展示核心商业指标与来源项目。</p>
                  </div>
                </div>
                <div className="dash-overview-empty-cards">
                  <article className="dash-overview-empty-card">
                    <span className="material-symbols-outlined">storefront</span>
                    <h4>商家核心数据</h4>
                    <p>查看租金、面积、客流等关键指标。</p>
                  </article>
                  <article className="dash-overview-empty-card">
                    <span className="material-symbols-outlined">conversion_path</span>
                    <h4>竞品对照信息</h4>
                    <p>快速定位体量、空置率与目标人群。</p>
                  </article>
                  <article className="dash-overview-empty-card">
                    <span className="material-symbols-outlined">hub</span>
                    <h4>来源可追溯</h4>
                    <p>支持跳转来源项目，核验采集批次与更新时间。</p>
                  </article>
                </div>
              </div>
            )}
            {activePointDetail && (
              <div className="dash-overview-detail">
                <div className="dash-overview-detail-head">
                  <div className="dash-overview-detail-title">
                    <strong>{activePointDetail.payload?.name || '未命名点位'}</strong>
                    <p className="dash-helper">
                      {(activePointDetail.payload?.city || '—') + ' · ' + (activePointDetail.payload?.district || '—')}
                    </p>
                  </div>
                  <div className="dash-overview-detail-tags">
                    <span className={`dash-status ${activePointDetail.point_type}`}>
                      {activePointDetail.point_type === 'merchant' ? '商家调研' : '竞争关系'}
                    </span>
                    <span className="dash-status">
                      更新时间：{formatDateTime(activePointDetail.payload?.created_at)}
                    </span>
                  </div>
                </div>
                <div className="dash-overview-detail-banner">
                  <span className="material-symbols-outlined">insights</span>
                  <div>
                    <strong>核心洞察</strong>
                    <p>
                      {activePointDetail.point_type === 'merchant'
                        ? '聚焦租金、面积与客流，快速判断商家经营状态与落位价值。'
                        : '聚焦体量、租金与空置率，快速判断竞品压力与区域竞争格局。'}
                    </p>
                  </div>
                </div>
                <div className="dash-overview-detail-source">
                  <span className="material-symbols-outlined">link</span>
                  <strong>来源项目：</strong>
                  <span>{activePointDetail.project_name || activePointDetail.project_id || '未挂接项目'}</span>
                </div>
                <div className="dash-overview-highlight-grid">
                  {(DETAIL_HIGHLIGHTS[activePointDetail.point_type] || []).map(([key, label, unit]) => (
                    <article key={key} className="dash-overview-highlight-card">
                      <span>{label}</span>
                      <strong>{formatHighlightValue(activePointDetail.payload?.[key], unit)}</strong>
                    </article>
                  ))}
                </div>
                <div className="dash-overview-detail-grid">
                  {(DETAIL_FIELDS[activePointDetail.point_type] || []).map((field) => {
                    const value = activePointDetail.payload?.[field.key]
                    return (
                      <div key={field.key} className="dash-overview-detail-item">
                        <span>{field.label}</span>
                        <strong>{formatDetailValue(field, value)}</strong>
                      </div>
                    )
                  })}
                </div>
                {activePointDetail.project_id ? (
                  <button className="dash-btn secondary" type="button" onClick={loadSourceProject} disabled={sourceProjectLoading}>
                    {sourceProjectLoading ? '加载中...' : '打开来源项目详情'}
                  </button>
                ) : (
                  <button className="dash-btn secondary" type="button" disabled>
                    暂无来源项目
                  </button>
                )}
                {sourceProjectError && <div className="notice">{sourceProjectError}</div>}
                {sourceProjectDetail && (
                  <div className="dash-overview-project-panel">
                    <h4>来源项目详情</h4>
                    <div className="dash-overview-project-grid">
                      <div><span>项目名称</span><strong>{sourceProjectDetail.project_name || '—'}</strong></div>
                      <div><span>城市·区域</span><strong>{(sourceProjectDetail.city || '—') + ' · ' + (sourceProjectDetail.district || '—')}</strong></div>
                      <div><span>总建筑面积</span><strong>{sourceProjectDetail.total_area ?? '—'}</strong></div>
                      <div><span>确认状态</span><strong>{sourceProjectDetail.is_confirmed ? '已确认' : '未确认'}</strong></div>
                      <div><span>当前阶段</span><strong>{sourceProjectDetail.current_stage || '—'}</strong></div>
                      <div><span>更新时间</span><strong>{formatDateTime(sourceProjectDetail.updated_at || sourceProjectDetail.created_at)}</strong></div>
                    </div>
                  </div>
                )}
              </div>
            )}
          </aside>
        </div>

        <div className="dash-card dash-card-secondary dash-overview-updates-card">
          <div className="dash-card-header">
            <strong className="dash-section-title">
              <span className="material-symbols-outlined">history</span>
              最近更新
            </strong>
            <span className="dash-section-note">最新采集与点位更新记录</span>
          </div>
          <div className="dash-table-scroll">
            <table className="table dash-overview-updates-table">
              <thead>
                <tr>
                  <th>名称</th>
                  <th>类型</th>
                  <th>区域</th>
                  <th>来源项目</th>
                  <th>时间</th>
                </tr>
              </thead>
              <tbody>
                {recentPoints.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="dash-helper">
                      当前暂无更新记录
                    </td>
                  </tr>
                ) : (
                  recentPoints.map((item) => (
                    <tr key={item.point_id}>
                      <td>{item.name || '未命名点位'}</td>
                      <td>
                        <span className={`dash-status ${item.point_type}`}>
                          {item.point_type === 'merchant' ? '商家调研' : '竞争关系'}
                        </span>
                      </td>
                      <td>{[item.city, item.district].filter(Boolean).join(' · ') || '—'}</td>
                      <td>{item.project_name || item.project_id || '—'}</td>
                      <td>{formatDateTime(item.created_at)}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </section>
    </DashboardLayout>
  )
}
