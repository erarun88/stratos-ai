export type EngineerStatus = 'active' | 'inactive' | 'on_leave'

export interface Engineer {
  id: number
  name: string
  email: string
  role: string
  status: EngineerStatus
  project_id: number
}
