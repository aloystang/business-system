export const INTEL_PAGE_SIZE = 18
export const INTEL_AGGREGATE_PAGE_SIZE = 200

const INTEL_AGGREGATE_MAX_PAGES = 50

export function toQuery(params) {
  const search = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      search.set(key, String(value))
    }
  })
  return search.toString()
}

export function formatDate(value) {
  if (!value) return '-'
  return String(value).replace('T', ' ').slice(0, 16)
}

export function formatMoney(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return '-'
  return Number(value).toLocaleString('zh-CN', {
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  })
}

export function itemTypeLabel(itemType) {
  return itemType === 'tender' ? '招投标' : '新闻'
}

export function sourceCategoryLabel(sourceCategory) {
  return sourceCategory || '未分类'
}

export function truncateText(value, maxLength = 40) {
  const text = String(value || '').replace(/\s+/g, ' ').trim()
  if (!text) return '暂无摘要。'
  if (text.length <= maxLength) return text
  if (maxLength <= 1) return '…'
  return `${text.slice(0, maxLength - 1)}…`
}

export function groupBySource(items) {
  const buckets = new Map()
  for (const item of items || []) {
    const key = item.source_name || '未标注来源'
    if (!buckets.has(key)) {
      buckets.set(key, {
        source: key,
        sourceCategory: item.source_category || '',
        items: [],
      })
    }
    buckets.get(key).items.push(item)
  }
  return Array.from(buckets.values()).map((group) => ({
    ...group,
    items: group.items.sort((a, b) => String(b.published_at || '').localeCompare(String(a.published_at || ''))),
  }))
}

export async function fetchAllIntelItems(loadJson, baseParams) {
  let page = 1
  let total = 0
  const mergedItems = []

  while (page <= INTEL_AGGREGATE_MAX_PAGES) {
    const response = await loadJson(
      `/api/intel/items?${toQuery({
        ...baseParams,
        page,
        page_size: INTEL_AGGREGATE_PAGE_SIZE,
      })}`
    )

    const pageItems = Array.isArray(response.items) ? response.items : []
    total = Number(response.total || 0)
    mergedItems.push(...pageItems)

    if (!pageItems.length || mergedItems.length >= total || pageItems.length < INTEL_AGGREGATE_PAGE_SIZE) {
      break
    }

    page += 1
  }

  return {
    items: mergedItems,
    total,
  }
}
