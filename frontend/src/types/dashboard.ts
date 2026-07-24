import type { ProjectStatus } from './project'

export interface DashboardSummary {
  total_projects: number
  active_projects: number
  planning_projects: number
  on_hold_projects: number
  completed_projects: number
  cancelled_projects: number
  total_engineers: number
  active_engineers: number
  inactive_engineers: number
}

export interface ProjectStatusCount {
  status: ProjectStatus
  label: string
  count: number
}
