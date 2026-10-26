import { useQuery } from '@tanstack/react-query'
import { useEffect, useMemo, useRef, useState } from 'react'
import { api, type Asset } from '../lib/api'
import { formatPrice, formatToman, formatUsd, unitLabel, type Unit } from '../lib/format'
import { AssetIcon } from './AssetIcon'
import { ChangeBadge } from './ChangeBadge'

const RANGES = [
  { days: 1, label: '۱ روز' },
  { days: 7, label: '۱ هفته' },
  { days: 30, label: '۱ ماه' },
]
const W = 640
const H = 220

interface Props {
  asset: Asset
  unit: Unit
  onClose: () => void
}

export function HistoryModal({ asset, unit, onClose }: Props) {
  const [days, setDays] = useState(7)
  const dialog = useRef<HTMLDialogElement>(null)
  const { data, isLoading, isError } = useQuery({
    queryKey: ['history', asset.slug, days],
    queryFn: () => api.history(asset.slug, days),
  })
  const shownUnit: Unit = asset.slug === 'usd' ? 'toman' : unit

  useEffect(() => {
    dialog.current?.showModal()
  }, [])

  const chart = useMemo(() => {
    const pts = (data?.points ?? [])
      .map((p) => ({ t: new Date(p.t), v: shownUnit === 'toman' ? p.toman : p.usd }))
      .filter((p): p is { t: Date; v: number } => p.v != null)
    if (pts.length < 2) return null
    const values = pts.map((p) => p.v)
    const min = Math.min(...values)
    const max = Math.max(...values)
    const range = max - min || 1
    const t0 = pts[0].t.getTime()
    const span = pts[pts.length - 1].t.getTime() - t0 || 1
    const xy = pts.map((p) => [((p.t.getTime() - t0) / span) * W, H - 12 - ((p.v - min) / range) * (H - 24)])
    const line = xy.map(([x, y], i) => `${i ? 'L' : 'M'}${x.toFixed(1)},${y.toFixed(1)}`).join(' ')
    const up = values[values.length - 1] >= values[0]
    return { line, area: `${line} L${W},${H} L0,${H} Z`, min, max, up, first: pts[0].t, last: pts[pts.length - 1].t }
  }, [data, shownUnit])

  const fmt = (v: number) => (shownUnit === 'toman' ? formatToman(v) : formatUsd(v))
  const dateFmt = new Intl.DateTimeFormat('fa-IR-u-ca-persian', {
    month: 'short',
    day: 'numeric',
    hour: days === 1 ? '2-digit' : undefined,
    minute: days === 1 ? '2-digit' : undefined,
  })

  return (
    <dialog
      ref={dialog}
      className="modal"
      onClose={onClose}
      onClick={(e) => e.target === dialog.current && dialog.current?.close()}
      aria-labelledby="modal-title"
    >
      <div className="modal__body">
        <div className="modal__header">
          <div className="asset">
            <AssetIcon asset={asset} />
            <div>
              <h2 id="modal-title" className="asset__name">{asset.name_fa}</h2>
              <span className="asset__meta">{asset.name_en}</span>
            </div>
          </div>
          <button type="button" className="icon-button" onClick={() => dialog.current?.close()} aria-label="بستن">
            ✕
          </button>
        </div>

        <div className="modal__price">
          <strong>{formatPrice(asset, shownUnit)}</strong>
          <span>{unitLabel(shownUnit)}</span>
          <ChangeBadge value={asset.change_24h} />
        </div>

        <div className="segmented segmented--sm">
          {RANGES.map((r) => (
            <button
              key={r.days}
              type="button"
              className={days === r.days ? 'is-active' : ''}
              aria-pressed={days === r.days}
              onClick={() => setDays(r.days)}
            >
              {r.label}
            </button>
          ))}
        </div>

        <div className="chart">
          {isLoading && <div className="skeleton" style={{ height: H }} />}
          {isError && <p className="empty">بارگذاری نمودار ممکن نشد.</p>}
          {!isLoading && !isError && !chart && (
            <p className="empty">هنوز داده‌ی کافی برای این بازه جمع نشده است.</p>
          )}
          {chart && (
            <>
              <svg viewBox={`0 0 ${W} ${H}`} className={`chart__svg ${chart.up ? 'is-up' : 'is-down'}`} preserveAspectRatio="none" role="img" aria-label={`نمودار قیمت ${asset.name_fa}`}>
                <path d={chart.area} className="chart__area" />
                <path d={chart.line} className="chart__line" vectorEffect="non-scaling-stroke" />
              </svg>
              <div className="chart__axis">
                <span>{dateFmt.format(chart.first)}</span>
                <span>کمینه {fmt(chart.min)} · بیشینه {fmt(chart.max)}</span>
                <span>{dateFmt.format(chart.last)}</span>
              </div>
            </>
          )}
        </div>
      </div>
    </dialog>
  )
}
