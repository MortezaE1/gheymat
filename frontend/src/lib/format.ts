import type { Asset } from './api'

export type Unit = 'toman' | 'usd'

const fa = (options: Intl.NumberFormatOptions) => new Intl.NumberFormat('fa-IR', options)

const integer = fa({ maximumFractionDigits: 0 })
const twoDecimals = fa({ minimumFractionDigits: 2, maximumFractionDigits: 2 })

export function formatToman(value: number | null): string {
  if (value == null) return '—'
  return value >= 100 ? integer.format(value) : twoDecimals.format(value)
}

export function formatUsd(value: number | null): string {
  if (value == null) return '—'
  if (value >= 1000) return integer.format(value)
  if (value >= 1) return twoDecimals.format(value)
  if (value >= 0.01) return fa({ maximumFractionDigits: 4 }).format(value)
  return fa({ maximumSignificantDigits: 4 }).format(value)
}

export function formatPrice(asset: Asset, unit: Unit): string {
  return unit === 'toman' ? formatToman(asset.price_toman) : formatUsd(asset.price_usd)
}

export const unitLabel = (unit: Unit) => (unit === 'toman' ? 'تومان' : 'دلار')

export function formatChange(value: number | null): string {
  if (value == null) return '—'
  const sign = value > 0 ? '+' : value < 0 ? '−' : ''
  return `${sign}${twoDecimals.format(Math.abs(value))}٪`
}

export function trend(value: number | null): 'up' | 'down' | 'flat' {
  if (value == null || value === 0) return 'flat'
  return value > 0 ? 'up' : 'down'
}

const relative = new Intl.RelativeTimeFormat('fa-IR', { numeric: 'auto' })

export function timeAgo(iso: string | null, now = Date.now()): string {
  if (!iso) return '—'
  const seconds = Math.round((new Date(iso).getTime() - now) / 1000)
  if (Math.abs(seconds) < 45) return 'همین الان'
  const minutes = Math.round(seconds / 60)
  if (Math.abs(minutes) < 60) return relative.format(minutes, 'minute')
  const hours = Math.round(minutes / 60)
  if (Math.abs(hours) < 24) return relative.format(hours, 'hour')
  return relative.format(Math.round(hours / 24), 'day')
}

const persianParts = new Intl.DateTimeFormat('fa-IR-u-ca-persian', {
  weekday: 'long',
  day: 'numeric',
  month: 'long',
  year: 'numeric',
})

/** e.g. «دوشنبه ۴ آبان ۱۴۰۵». Built from parts because ICU's fa order varies by engine. */
export function persianDate(date = new Date()): string {
  const part = (type: Intl.DateTimeFormatPartTypes) =>
    persianParts.formatToParts(date).find((p) => p.type === type)?.value ?? ''
  return `${part('weekday')} ${part('day')} ${part('month')} ${part('year')}`
}
