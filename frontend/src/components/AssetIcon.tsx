import type { Asset } from '../lib/api'

const CRYPTO_COLORS: Record<string, string> = {
  BTC: '#f7931a',
  ETH: '#627eea',
  USDT: '#26a17b',
  BNB: '#f0b90b',
  SOL: '#9945ff',
  XRP: '#23292f',
  TON: '#0098ea',
  DOGE: '#c2a633',
  ADA: '#0033ad',
  TRX: '#eb0029',
}

/** A round badge: gold gradient for gold, brand colour for crypto, currency code for fiat. */
export function AssetIcon({ asset }: { asset: Asset }) {
  if (asset.category === 'gold') {
    return (
      <span className="icon icon--gold" aria-hidden="true">
        {asset.slug.startsWith('coin') ? '◎' : 'Au'}
      </span>
    )
  }
  if (asset.category === 'fiat') {
    return (
      <span className="icon icon--fiat" aria-hidden="true">
        {asset.symbol}
      </span>
    )
  }
  return (
    <span
      className={`icon icon--crypto ${asset.symbol.length > 3 ? 'icon--long' : ''}`}
      style={{ background: CRYPTO_COLORS[asset.symbol] ?? 'var(--accent)' }}
      aria-hidden="true"
    >
      {asset.symbol}
    </span>
  )
}
