export const STAGES = [
  { key: 'evaluation', label: '评估' },
  { key: 'estimation', label: '测算' },
  { key: 'initiation', label: '立项' },
  { key: 'planning', label: '方案' },
  { key: 'bidding', label: '投标' },
  { key: 'contracting', label: '签约' },
  { key: 'preopen', label: '筹开' },
  { key: 'operation', label: '运营' },
  { key: 'review', label: '复盘/续约' },
]

export function stageLabel(key) {
  const found = STAGES.find((stage) => stage.key === key)
  return found ? found.label : key
}

export function nextStage(current) {
  const idx = STAGES.findIndex((s) => s.key === current)
  if (idx < 0 || idx + 1 >= STAGES.length) return null
  return STAGES[idx + 1].key
}
