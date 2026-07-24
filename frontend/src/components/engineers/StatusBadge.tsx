import type { EngineerStatus } from '../../types/engineer'

const STATUS_STYLES: Record<EngineerStatus, string> = {
  active: 'bg-emerald-50 text-emerald-700 ring-emerald-600/20',
  inactive: 'bg-slate-100 text-slate-600 ring-slate-500/20',
  on_leave: 'bg-amber-50 text-amber-700 ring-amber-600/20',
}

const STATUS_LABELS: Record<EngineerStatus, string> = {
  active: 'Active',
  inactive: 'Inactive',
  on_leave: 'On Leave',
}

export default function StatusBadge({ status }: { status: EngineerStatus }) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset ${STATUS_STYLES[status]}`}
    >
      {STATUS_LABELS[status]}
    </span>
  )
}
