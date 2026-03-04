import React from 'react'
import { formatDate, formatMoney, itemTypeLabel } from '../../lib/intel'

export default function IntelDetailDrawer({ open, loading, error, detail, onClose, theme = 'news' }) {
  return (
    <aside className={`intel-detail-drawer ${open ? 'open' : ''} ${theme === 'tender' ? 'tender' : 'news'}`}>
      <div className="intel-detail-head">
        <h3>情报详情</h3>
        <button type="button" className="intel-detail-close" onClick={onClose}>
          关闭
        </button>
      </div>
      {loading ? <p className="dash-subtext">加载中...</p> : null}
      {error ? <p className="dash-error-text">{error}</p> : null}
      {!loading && !error && detail ? (
        <div className="intel-detail-body">
          <div className="intel-detail-hero">
            <div className="intel-detail-badges">
              <span className={`dash-pill ${detail.item_type === 'tender' ? 'warning' : 'muted'}`}>
                {itemTypeLabel(detail.item_type)}
              </span>
              {detail.source_category ? <span className="dash-pill muted">{detail.source_category}</span> : null}
            </div>
            <h4>{detail.title}</h4>
            <p className="intel-detail-subline">
              {detail.source_name || '-'} · {formatDate(detail.published_at)}
            </p>
          </div>
          <dl>
            <div>
              <dt>来源</dt>
              <dd>{detail.source_name || '-'}</dd>
            </div>
            <div>
              <dt>发布时间</dt>
              <dd>{formatDate(detail.published_at)}</dd>
            </div>
            <div>
              <dt>区域</dt>
              <dd>{[detail.city, detail.district].filter(Boolean).join(' · ') || '-'}</dd>
            </div>
            <div>
              <dt>发布方</dt>
              <dd>{detail.issuer || '-'}</dd>
            </div>
            <div>
              <dt>预算</dt>
              <dd>{formatMoney(detail.budget_amount)}</dd>
            </div>
            <div>
              <dt>截止时间</dt>
              <dd>{formatDate(detail.deadline_at)}</dd>
            </div>
          </dl>
          <div className="intel-detail-summary">
            <strong>摘要</strong>
            <p>{detail.summary || '暂无摘要。'}</p>
          </div>
          {detail.raw_url ? (
            <a className="dash-btn primary intel-detail-link" href={detail.raw_url} target="_blank" rel="noreferrer">
              查看原文
            </a>
          ) : (
            <p className="dash-subtext">暂无原文链接</p>
          )}
        </div>
      ) : null}
    </aside>
  )
}
