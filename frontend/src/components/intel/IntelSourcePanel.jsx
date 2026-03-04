import React from 'react'
import { formatDate, formatMoney, truncateText } from '../../lib/intel'

export default function IntelSourcePanel({ group, theme = 'news', onOpenDetail }) {
  const [lead, ...rest] = group.items
  const rows = rest.slice(0, 7)

  return (
    <article className={`intel-source-panel intel-source-panel--${theme}`}>
      <div className="intel-source-panel-head">
        <div>
          <strong>{group.source}</strong>
          <small>{group.sourceCategory || (theme === 'tender' ? '招采情报' : '新闻来源')}</small>
        </div>
        <span className="intel-source-count">{group.items.length} 条</span>
      </div>

      {lead ? (
        <button type="button" className="intel-source-lead" onClick={() => onOpenDetail(lead.id)}>
          <span className="intel-source-lead-time">{formatDate(lead.published_at)}</span>
          <h3>{lead.title}</h3>
          <p>{truncateText(lead.summary, 40)}</p>
          {theme === 'tender' ? (
            <div className="intel-source-lead-meta">
              <span>{lead.issuer || '发布方待补充'}</span>
              <span>{lead.deadline_at ? `截止 ${formatDate(lead.deadline_at)}` : '截止时间待补充'}</span>
              <span>{lead.budget_amount ? `预算 ${formatMoney(lead.budget_amount)}` : '预算待补充'}</span>
            </div>
          ) : null}
        </button>
      ) : null}

      {rows.length ? (
        <div className="intel-source-list">
          {rows.map((item, index) => (
            <button key={item.id} type="button" className="intel-source-row" onClick={() => onOpenDetail(item.id)}>
              <span className="intel-source-row-index">{index + 1}</span>
              <div className="intel-source-row-copy">
                <strong>{item.title}</strong>
                <small>{formatDate(item.published_at)}{theme === 'tender' && item.issuer ? ` · ${item.issuer}` : ''}</small>
              </div>
            </button>
          ))}
        </div>
      ) : null}
    </article>
  )
}
