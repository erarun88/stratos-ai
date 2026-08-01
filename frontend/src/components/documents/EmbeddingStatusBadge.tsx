interface EmbeddingStatusBadgeProps {
  status: string | null
  error?: string | null
}

const STATUS_STYLES: Record<string, string> = {
  queued: 'bg-gray-50 text-gray-700 ring-gray-600/20',
  processing: 'bg-blue-50 text-blue-700 ring-blue-600/20',
  completed: 'bg-green-50 text-green-700 ring-green-600/20',
  failed: 'bg-red-50 text-red-700 ring-red-600/20',
}

const STATUS_LABELS: Record<string, string> = {
  queued: 'Queued',
  processing: 'Processing',
  completed: 'Embedded',
  failed: 'Failed',
}

export default function EmbeddingStatusBadge({ status, error }: EmbeddingStatusBadgeProps) {
  if (!status) return <span className="text-xs text-slate-400">—</span>

  const style = STATUS_STYLES[status] ?? STATUS_STYLES.queued
  const label = STATUS_LABELS[status] ?? status

  return (
    <div className="group relative inline-block">
      <span
        className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset ${style}`}
      >
        {status === 'processing' && <span className="mr-1 inline-block h-1.5 w-1.5 animate-pulse rounded-full bg-blue-600" />}
        {status === 'completed' && <span className="mr-1">✓</span>}
        {status === 'failed' && <span className="mr-1">✕</span>}
        {label}
      </span>
      {error && (
        <div className="absolute bottom-full left-1/2 mb-2 -translate-x-1/2 scale-0 rounded-md bg-slate-900 px-3 py-2 text-xs text-white shadow-lg group-hover:scale-100 transition-transform duration-200 whitespace-nowrap z-10">
          {error}
        </div>
      )}
    </div>
  )
}
