export type ProjectStatus =
  | 'planning'
  | 'active'
  | 'on_hold'
  | 'completed'
  | 'cancelled'

export interface Project {
  id: number
  name: string
  customer: string
  project_manager: string | null
  status: ProjectStatus
  start_date: string | null
  end_date: string | null
  description: string | null
  created_at: string | null
  updated_at: string | null
}

// Payload for creating / fully updating a project (matches the backend
// ProjectCreate / ProjectUpdate schemas).
export interface ProjectInput {
  name: string
  customer: string
  project_manager: string
  status: ProjectStatus
  start_date: string | null
  end_date: string | null
  description: string | null
}

export const PROJECT_STATUS_OPTIONS: { value: ProjectStatus; label: string }[] = [
  { value: 'planning', label: 'Planning' },
  { value: 'active', label: 'Active' },
  { value: 'on_hold', label: 'On Hold' },
  { value: 'completed', label: 'Completed' },
  { value: 'cancelled', label: 'Cancelled' },
]
