import { formatChange, trend } from '../lib/format'

export function ChangeBadge({ value }: { value: number | null }) {
  const t = trend(value)
  return (
    <span className={`change change--${t}`} dir="ltr">
      {t === 'up' ? '▲' : t === 'down' ? '▼' : ''} {formatChange(value)}
    </span>
  )
}
