import type { Asset } from '../lib/api'
import { formatPrice, trend, unitLabel, type Unit } from '../lib/format'
import { ChangeBadge } from './ChangeBadge'
import { Sparkline } from './Sparkline'

interface Props {
  assets: Asset[]
  unit: Unit
  onSelect: (asset: Asset) => void
}

export function Highlights({ assets, unit, onSelect }: Props) {
  return (
    <div className="highlights">
      {assets.map((asset) => {
        // The dollar priced in dollars says nothing: always show it in Toman.
        const shownUnit: Unit = asset.slug === 'usd' ? 'toman' : unit
        return (
          <button key={asset.slug} type="button" className="card highlight" onClick={() => onSelect(asset)}>
            <div className="highlight__top">
              <span className="highlight__name">{asset.name_fa}</span>
              <ChangeBadge value={asset.change_24h} />
            </div>
            <div className="highlight__price">
              {formatPrice(asset, shownUnit)}
              <small>{unitLabel(shownUnit)}</small>
            </div>
            <Sparkline values={asset.spark} width={220} height={44} trend={trend(asset.change_24h)} />
          </button>
        )
      })}
    </div>
  )
}

export function HighlightsSkeleton() {
  return (
    <div className="highlights">
      {Array.from({ length: 4 }, (_, i) => (
        <div key={i} className="card highlight skeleton" style={{ height: 150 }} />
      ))}
    </div>
  )
}
