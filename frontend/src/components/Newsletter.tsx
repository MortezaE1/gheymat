import { useMutation } from '@tanstack/react-query'
import { useState, type FormEvent } from 'react'
import { api } from '../lib/api'

export function Newsletter() {
  const [email, setEmail] = useState('')
  const mutation = useMutation({ mutationFn: api.subscribe })

  const submit = (event: FormEvent) => {
    event.preventDefault()
    if (email.trim()) mutation.mutate(email.trim())
  }

  return (
    <section id="newsletter" className="section">
      <div className="card newsletter">
        <div className="newsletter__text">
          <span className="eyebrow">خبرنامه‌ی روزانه</span>
          <h2>هر روز ساعت ۱۰ صبح، قیمت‌ها در ایمیل شما</h2>
          <p>
            خلاصه‌ای مرتب از قیمت طلا، سکه، ارز و رمزارزها به تومان و دلار. بدون تبلیغ، و لغو
            عضویت با یک کلیک.
          </p>
        </div>

        {mutation.isSuccess ? (
          <div className="notice notice--success" role="status">
            {mutation.data.detail}
          </div>
        ) : (
          <form className="newsletter__form" onSubmit={submit} noValidate>
            <input
              type="email"
              inputMode="email"
              autoComplete="email"
              dir="ltr"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              aria-label="ایمیل"
              required
            />
            <button type="submit" className="button" disabled={mutation.isPending}>
              {mutation.isPending ? 'در حال ارسال…' : 'عضویت'}
            </button>
            {mutation.isError && (
              <p className="form-error" role="alert">
                {mutation.error.message}
              </p>
            )}
          </form>
        )}
      </div>
    </section>
  )
}
