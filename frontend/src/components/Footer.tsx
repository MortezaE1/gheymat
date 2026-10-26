const YEAR = new Date().toLocaleDateString('fa-IR-u-ca-persian', { year: 'numeric' })

export function Footer() {
  return (
    <footer className="footer">
      <div className="container footer__inner">
        <div className="logo logo--sm">
          <span className="logo__dot" />
          قیمت
        </div>
        <p>
          قیمت‌ها از منابع عمومی بازار جمع‌آوری می‌شوند و فقط جنبه‌ی اطلاع‌رسانی دارند؛ پیش از هر
          معامله، قیمت را از مرجع معاملاتی خود بپرسید.
        </p>
        <p className="footer__copy">© {YEAR} قیمت</p>
      </div>
    </footer>
  )
}
