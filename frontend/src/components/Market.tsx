import { useMemo, useState } from 'react'
import type { Asset, Category, PricesResponse } from '../lib/api'
import { formatToman, formatUsd, formatPrice, trend, unitLabel, type Unit } from '../lib/format'
import { useStoredState } from '../lib/useStoredState'
import { AssetIcon } from './AssetIcon'
import { ChangeBadge } from './ChangeBadge'
import { Sparkline } from './Sparkline'

const TABS: { key: Category; label: string }[] = [
  { key: 'gold', label: 'طلا و سکه' },
  { key: 'crypto', label: 'ارز دیجیتال' },
  { key: 'fiat', label: 'ارزهای رسمی' },
]
const TAB_KEYS = TABS.map((t) => t.key)

interface Props {
  data: PricesResponse | undefined
  isLoading: boolean
  unit: Unit
  onSelect: (asset: Asset) => void
}

export function Market({ data, isLoading, unit, onSelect }: Props) {
  const [tab, setTab] = useStoredState<Category>('gheymat:tab', 'gold', TAB_KEYS)
  const [query, setQuery] = useState('')

  const rows = useMemo(() => {
    const list = data?.categories[tab] ?? []
    const q = query.trim().toLowerCase()
    if (!q) return list
    return list.filter((a) =>
      [a.name_fa, a.name_en, a.symbol].some((field) => field.toLowerCase().includes(q)),
    )
  }, [data, tab, query])

  return (
    <section id="market" className="section">
      <div className="market__toolbar">
        <div className="segmented" role="tablist" aria-label="دسته‌بندی بازار">
          {TABS.map((t) => (
            <button
              key={t.key}
              type="button"
              role="tab"
              aria-selected={tab === t.key}
              className={tab === t.key ? 'is-active' : ''}
              onClick={() => setTab(t.key)}
            >
              {t.label}
              {data && <span className="count">{data.categories[t.key].length.toLocaleString('fa-IR')}</span>}
            </button>
          ))}
        </div>
        <label className="search">
          <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true">
            <circle cx="11" cy="11" r="7" fill="none" stroke="currentColor" strokeWidth="2" />
            <path d="m20 20-3.5-3.5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
          </svg>
          <input
            type="search"
            placeholder="جستجو، مثلاً بیت‌کوین یا EUR"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            aria-label="جستجو در قیمت‌ها"
          />
        </label>
      </div>

      <div className="card table">
        <div className="table__head" aria-hidden="true">
          <span>نام</span>
          <span className="hide-sm">۲۴ ساعت اخیر</span>
          <span className="num">قیمت ({unitLabel(unit)})</span>
          <span className="num">تغییر</span>
        </div>

        {isLoading &&
          Array.from({ length: 6 }, (_, i) => <div key={i} className="table__row skeleton-row" />)}

        {!isLoading && rows.length === 0 && (
          <div className="empty">موردی پیدا نشد.</div>
        )}

        {rows.map((asset) => (
          <button
            key={asset.slug}
            type="button"
            className="table__row"
            onClick={() => onSelect(asset)}
          >
            <span className="asset">
              <AssetIcon asset={asset} />
              <span>
                <span className="asset__name">{asset.name_fa}</span>
                <span className="asset__meta">
                  {asset.category === 'gold' ? asset.unit : asset.symbol}
                </span>
              </span>
            </span>
            <span className="hide-sm">
              <Sparkline values={asset.spark} trend={trend(asset.change_24h)} />
            </span>
            <span className="num price">
              {formatPrice(asset, unit)}
              <span className="price__alt">
                {unit === 'toman'
                  ? asset.price_usd != null && `$${formatUsd(asset.price_usd)}`
                  : asset.price_toman != null && `${formatToman(asset.price_toman)} تومان`}
              </span>
            </span>
            <span className="num">
              <ChangeBadge value={asset.change_24h} />
            </span>
          </button>
        ))}
      </div>
    </section>
  )
}
