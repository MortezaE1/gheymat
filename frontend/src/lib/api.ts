export type Category = 'gold' | 'crypto' | 'fiat'

export interface Asset {
  slug: string
  category: Category
  name_fa: string
  name_en: string
  symbol: string
  unit: string
  price_toman: number | null
  price_usd: number | null
  change_24h: number | null
  source: string
  updated_at: string | null
  spark: number[]
}

export interface PricesResponse {
  updated_at: string | null
  usd_toman: number | null
  is_demo: boolean
  categories: Record<Category, Asset[]>
}

export interface HistoryResponse {
  slug: string
  name_fa: string
  days: number
  points: { t: string; toman: number | null; usd: number | null }[]
}

const BASE = (import.meta.env.VITE_API_URL ?? '').replace(/\/$/, '')

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE}${path}`, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...init?.headers },
  })
  const body = await response.json().catch(() => ({}))
  if (!response.ok) {
    const message =
      body?.email?.[0] ?? body?.detail ?? 'خطا در ارتباط با سرور. لطفاً دوباره تلاش کنید.'
    throw new Error(message)
  }
  return body as T
}

export const api = {
  prices: () => request<PricesResponse>('/api/prices/'),
  history: (slug: string, days: number) =>
    request<HistoryResponse>(`/api/prices/${slug}/history/?days=${days}`),
  subscribe: (email: string) =>
    request<{ detail: string }>('/api/newsletter/subscribe/', {
      method: 'POST',
      body: JSON.stringify({ email }),
    }),
}
