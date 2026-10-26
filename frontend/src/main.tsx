import '@fontsource/vazirmatn/400.css'
import '@fontsource/vazirmatn/600.css'
import '@fontsource/vazirmatn/800.css'
import './index.css'

import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App'

const queryClient = new QueryClient({
  defaultOptions: { queries: { staleTime: 15_000, retry: 2, refetchOnWindowFocus: true } },
})

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>
  </StrictMode>,
)
