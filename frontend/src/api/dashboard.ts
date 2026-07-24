import { apiGet } from './client'
import type { DashboardSummary, ProjectStatusCount } from '../types/dashboard'
import type { Project } from '../types/project'
import type { Engineer } from '../types/engineer'

export function getDashboardSummary(): Promise<DashboardSummary> {
  return apiGet<DashboardSummary>('/dashboard/summary')
}

export function getProjectStatusBreakdown(): Promise<ProjectStatusCount[]> {
  return apiGet<ProjectStatusCount[]>('/dashboard/project-status')
}

export function getRecentProjects(): Promise<Project[]> {
  return apiGet<Project[]>('/dashboard/recent-projects')
}

export function getRecentEngineers(): Promise<Engineer[]> {
  return apiGet<Engineer[]>('/dashboard/recent-engineers')
}
