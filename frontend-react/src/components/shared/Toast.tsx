import { useToastStore } from '@/store/appStore'

const ICONS: Record<string, string> = {
  success: '✓', error: '✕', warning: '⚠', info: 'ℹ',
}
const COLORS: Record<string, string> = {
  success: 'bg-surface-800 border-bull/30 text-bull',
  error:   'bg-surface-800 border-bear/30 text-bear',
  warning: 'bg-surface-800 border-side/30 text-side',
  info:    'bg-surface-800 border-primary-500/30 text-primary-400',
}

export default function Toast() {
  const { toasts, remove } = useToastStore()
  return (
    <div className="fixed bottom-5 right-5 z-[9999] flex flex-col gap-2 pointer-events-none">
      {toasts.map(t => (
        <div key={t.id}
          className={`pointer-events-auto flex items-start gap-3 px-4 py-3 rounded-xl shadow-card-lg border max-w-sm w-full animate-slide-up ${COLORS[t.type]}`}>
          <span className="shrink-0 mt-0.5 w-5 h-5 rounded-full flex items-center justify-center text-xs font-bold border border-current">
            {ICONS[t.type]}
          </span>
          <p className="flex-1 text-sm text-surface-100 leading-snug">{t.message}</p>
          <button onClick={() => remove(t.id)} className="text-surface-400 hover:text-surface-200 shrink-0">✕</button>
        </div>
      ))}
    </div>
  )
}
