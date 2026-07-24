import { apiGet, apiPost, apiPut, apiPatch } from './client'
import type { Project, ProjectInput, ProjectStatus } from '../types/project'

export function getProjects(): Promise<Project[]> {
  return apiGet<Project[]>('/projects')
}

export function getProject(id: number): Promise<Project> {
  return apiGet<Project>(`/projects/${id}`)
}

export function createProject(input: ProjectInput): Promise<Project> {
  return apiPost<Project>('/projects', input)
}

export function updateProject(id: number, input: ProjectInput): Promise<Project> {
  return apiPut<Project>(`/projects/${id}`, input)
}

export function updateProjectStatus(
  id: number,
  status: ProjectStatus,
): Promise<Project> {
  return apiPatch<Project>(`/projects/${id}/status`, { status })
}
