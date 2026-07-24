import type { ProjectStatus } from '../../types/project'

const STATUS_STYLES: Record<ProjectStatus, string> = {
  planning: 'bg-blue-50 text-blue-700 ring-blue-600/20',
  active: 'bg-emerald-50 text-emerald-700 ring-emerald-600/20',
  on_hold: 'bg-amber-50 text-amber-700 ring-amber-600/20',
  completed: 'bg-slate-100 text-slate-600 ring-slate-500/20',
  cancelled: 'bg-red-50 text-red-700 ring-red-600/20',
}

const STATUS_LABELS: Record<ProjectStatus, string> = {
  planning: 'Planning',
  active: 'Active',
  on_hold: 'On Hold',
  completed: 'Completed',
  cancelled: 'Cancelled',
}

export default function ProjectStatusBadge({ status }: { status: ProjectStatus }) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset ${STATUS_STYLES[status]}`}
    >
      {STATUS_LABELS[status]}
    </span>
  )
}
