import type { Unit } from '../lib/format'
import type { Theme } from '../lib/useTheme'

interface Props {
  unit: Unit
  onUnit: (unit: Unit) => void
  theme: Theme
  onTheme: () => void
}

export function Header({ unit, onUnit, theme, onTheme }: Props) {
  return (
    <header className="header">
      <div className="container header__inner">
        <a href="#" className="logo" aria-label="قیمت، صفحه‌ی اصلی">
          <span className="logo__dot" />
          قیمت
        </a>
        <nav className="nav" aria-label="بخش‌ها">
          <a href="#market">بازار</a>
          <a href="#newsletter">خبرنامه</a>
        </nav>
        <div className="header__actions">
          <div className="segmented segmented--sm" role="group" aria-label="واحد نمایش قیمت">
            {(['toman', 'usd'] as const).map((u) => (
              <button
                key={u}
                type="button"
                className={unit === u ? 'is-active' : ''}
                aria-pressed={unit === u}
                onClick={() => onUnit(u)}
              >
                {u === 'toman' ? 'تومان' : 'دلار'}
              </button>
            ))}
          </div>
          <button
            type="button"
            className="icon-button"
            onClick={onTheme}
            aria-label={theme === 'dark' ? 'حالت روشن' : 'حالت تیره'}
            title={theme === 'dark' ? 'حالت روشن' : 'حالت تیره'}
          >
            {theme === 'dark' ? (
              <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true">
                <circle cx="12" cy="12" r="4.5" fill="currentColor" />
                <g stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                  <path d="M12 2v2M12 20v2M2 12h2M20 12h2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" />
                </g>
              </svg>
            ) : (
              <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true">
                <path fill="currentColor" d="M21 14.5A9 9 0 0 1 9.5 3a9 9 0 1 0 11.5 11.5Z" />
              </svg>
            )}
          </button>
        </div>
      </div>
    </header>
  )
}
