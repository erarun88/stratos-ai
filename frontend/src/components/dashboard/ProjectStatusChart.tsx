import type { ProjectStatusCount } from '../../types/dashboard'
import type { ProjectStatus } from '../../types/project'

// Validated categorical/status fills (see the dataviz palette validator).
// Every bar is directly labeled, so identity is never carried by color alone.
const STATUS_FILL: Record<ProjectStatus, string> = {
  planning: '#2563eb',
  active: '#059669',
  on_hold: '#d97706',
  completed: '#64748b',
  cancelled: '#dc2626',
}

interface ProjectStatusChartProps {
  data: ProjectStatusCount[]
}

export default function ProjectStatusChart({ data }: ProjectStatusChartProps) {
  const total = data.reduce((sum, d) => sum + d.count, 0)
  const max = Math.max(...data.map((d) => d.count), 1)

  if (total === 0) {
    return (
      <div className="flex h-48 items-center justify-center text-sm text-slate-400">
        No projects to chart yet.
      </div>
    )
  }

  return (
    <div className="space-y-3" role="img" aria-label="Projects by status">
      {data.map((item) => (
        <div key={item.status} className="flex items-center gap-3">
          <span className="w-20 shrink-0 text-xs font-medium text-slate-600">
            {item.label}
          </span>
          <div className="flex h-5 flex-1 items-center">
            <div
              className="h-full rounded-r-[4px]"
              style={{
                width: `${(item.count / max) * 100}%`,
                minWidth: item.count > 0 ? '6px' : '0',
                backgroundColor: STATUS_FILL[item.status],
              }}
              title={`${item.label}: ${item.count}`}
            />
            <span className="ml-2 text-xs font-semibold tabular-nums text-slate-700">
              {item.count}
            </span>
          </div>
        </div>
      ))}
    </div>
  )
}
