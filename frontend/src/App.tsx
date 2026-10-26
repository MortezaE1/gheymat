import { useQuery } from '@tanstack/react-query'
import { useEffect, useMemo, useState } from 'react'
import { Footer } from './components/Footer'
import { Header } from './components/Header'
import { Highlights, HighlightsSkeleton } from './components/Highlights'
import { HistoryModal } from './components/HistoryModal'
import { Market } from './components/Market'
import { Newsletter } from './components/Newsletter'
import { api, type Asset } from './lib/api'
import { formatToman, persianDate, timeAgo, type Unit } from './lib/format'
import { useStoredState } from './lib/useStoredState'
import { useTheme } from './lib/useTheme'

const HIGHLIGHTS = ['usd', 'gold_18k', 'coin_emami', 'bitcoin']
const REFRESH_MS = 30_000

const NEWSLETTER_NOTICES: Record<string, string> = {
  confirmed: 'عضویت شما در خبرنامه تأیید شد. از فردا ساعت ۱۰ صبح منتظر ایمیل ما باشید.',
  unsubscribed: 'عضویت شما در خبرنامه لغو شد.',
}

function useNow(interval = 15_000) {
  const [now, setNow] = useState(Date.now)
  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), interval)
    return () => clearInterval(id)
  }, [interval])
  return now
}

export default function App() {
  const { theme, toggle } = useTheme()
  const [unit, setUnit] = useStoredState<Unit>('gheymat:unit', 'toman', ['toman', 'usd'])
  const [selected, setSelected] = useState<Asset | null>(null)
  const [notice, setNotice] = useState<string | null>(() => {
    const key = new URLSearchParams(window.location.search).get('newsletter')
    return (key && NEWSLETTER_NOTICES[key]) || null
  })
  const now = useNow()

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['prices'],
    queryFn: api.prices,
    refetchInterval: REFRESH_MS,
  })

  // The confirm / unsubscribe links in emails redirect here with ?newsletter=…;
  // the notice is read above, then the parameter is removed from the address bar.
  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    if (!params.has('newsletter')) return
    params.delete('newsletter')
    const qs = params.toString()
    window.history.replaceState(null, '', window.location.pathname + (qs ? `?${qs}` : ''))
  }, [])

  const highlights = useMemo(() => {
    const all = data ? Object.values(data.categories).flat() : []
    return HIGHLIGHTS.map((slug) => all.find((a) => a.slug === slug)).filter((a): a is Asset => !!a)
  }, [data])

  // Keep the open modal in sync with fresh prices.
  const selectedLive = selected
    ? (data && Object.values(data.categories).flat().find((a) => a.slug === selected.slug)) ?? selected
    : null

  return (
    <>
      <Header unit={unit} onUnit={setUnit} theme={theme} onTheme={toggle} />

      <main className="container">
        {notice && (
          <div className="notice notice--success toast" role="status">
            {notice}
            <button type="button" onClick={() => setNotice(null)} aria-label="بستن">✕</button>
          </div>
        )}

        <section className="hero">
          <div>
            <h1>قیمت لحظه‌ای بازار</h1>
            <p className="hero__sub">{persianDate()}</p>
          </div>
          <div className="hero__meta">
            {data?.is_demo && <span className="badge badge--warn">داده‌ی نمایشی</span>}
            {data?.usd_toman && (
              <span className="badge">دلار آزاد: {formatToman(data.usd_toman)} تومان</span>
            )}
            <span className="live">
              <span className={`live__dot ${isError ? 'is-error' : ''}`} />
              {isError ? 'اتصال برقرار نیست' : `به‌روزرسانی ${timeAgo(data?.updated_at ?? null, now)}`}
            </span>
          </div>
        </section>

        {isError && !data ? (
          <div className="card empty">
            دریافت قیمت‌ها ممکن نشد.
            <button type="button" className="button button--ghost" onClick={() => refetch()}>
              تلاش دوباره
            </button>
          </div>
        ) : isLoading ? (
          <HighlightsSkeleton />
        ) : (
          <Highlights assets={highlights} unit={unit} onSelect={setSelected} />
        )}

        <Market data={data} isLoading={isLoading} unit={unit} onSelect={setSelected} />
        <Newsletter />
      </main>

      <Footer />

      {selectedLive && (
        <HistoryModal asset={selectedLive} unit={unit} onClose={() => setSelected(null)} />
      )}
    </>
  )
}
