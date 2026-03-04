import React from 'react'
import { formatDate, formatMoney, itemTypeLabel } from '../../lib/intel'

export default function IntelStoryCard({ item, featured = false, onOpenDetail, theme = 'news' }) {
  return (
    <article className={`intel-story-card ${featured ? 'featured' : ''} ${theme === 'tender' ? 'tender' : 'news'}`}>
      <div className="intel-story-topline">
        <span className={`dash-pill ${item.item_type === 'tender' ? 'warning' : 'muted'}`}>
          {itemTypeLabel(item.item_type)}
        </span>
        <span className="intel-story-time">{formatDate(item.published_at)}</span>
      </div>
      <h3>{item.title}</h3>
      <p className="intel-story-source">
        {item.source_name || '-'}
        {item.source_category ? ` · ${item.source_category}` : ''}
      </p>
      <p className="intel-story-summary">{item.summary || '暂无摘要。'}</p>
      <div className="intel-story-metrics">
        {item.issuer ? (
          <span>
            <strong>发布方</strong>
            <small>{item.issuer}</small>
          </span>
        ) : null}
        {item.deadline_at ? (
          <span>
            <strong>截止</strong>
            <small>{formatDate(item.deadline_at)}</small>
          </span>
        ) : null}
        {item.budget_amount ? (
          <span>
            <strong>预算</strong>
            <small>{formatMoney(item.budget_amount)}</small>
          </span>
        ) : null}
      </div>
      <div className="intel-story-actions">
        <button type="button" className="intel-story-link" onClick={() => onOpenDetail(item.id)}>
          查看详情
        </button>
        {item.raw_url ? (
          <a className="intel-story-link" href={item.raw_url} target="_blank" rel="noreferrer">
            查看原文
          </a>
        ) : null}
      </div>
    </article>
  )
}
