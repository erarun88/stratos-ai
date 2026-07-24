import { apiGet } from './client'
import type { Engineer } from '../types/engineer'

export function getEngineers(): Promise<Engineer[]> {
  return apiGet<Engineer[]>('/engineers')
}
