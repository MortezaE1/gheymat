import { useEffect, useState } from 'react'

/** useState that remembers its value in localStorage (best effort). */
export function useStoredState<T extends string>(key: string, fallback: T, allowed: readonly T[]) {
  const [value, setValue] = useState<T>(() => {
    try {
      const saved = localStorage.getItem(key) as T | null
      if (saved && allowed.includes(saved)) return saved
    } catch {
      /* storage unavailable */
    }
    return fallback
  })
  useEffect(() => {
    try {
      localStorage.setItem(key, value)
    } catch {
      /* storage unavailable */
    }
  }, [key, value])
  return [value, setValue] as const
}
