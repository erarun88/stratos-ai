export type DocumentType =
  | 'contract'
  | 'sow'
  | 'proposal'
  | 'report'
  | 'specification'
  | 'meeting_minutes'
  | 'other'

export interface Document {
  id: number
  title: string
  description: string | null
  document_type: DocumentType
  project_id: number | null
  project_name: string | null
  customer: string | null
  uploaded_by: string | null
  filename: string
  content_type: string
  file_size: number
  content_hash: string
  storage_backend: string
  created_at: string | null
  updated_at: string | null
}

/** Paginated envelope returned by GET /documents. */
export interface DocumentList {
  items: Document[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

/** Metadata sent alongside the file on upload (multipart form fields). */
export interface DocumentUploadInput {
  file: File
  title: string
  description: string | null
  document_type: DocumentType
  project_id: number | null
  customer: string | null
  uploaded_by: string | null
}

/** Partial metadata update (PATCH /documents/{id}). */
export interface DocumentMetadataInput {
  title: string
  description: string | null
  document_type: DocumentType
  project_id: number | null
  customer: string | null
}

export interface DocumentFilters {
  search?: string
  document_type?: DocumentType | ''
  project_id?: number | null
  page?: number
  page_size?: number
}

export const DOCUMENT_TYPE_OPTIONS: { value: DocumentType; label: string }[] = [
  { value: 'contract', label: 'Contract' },
  { value: 'sow', label: 'Statement of Work' },
  { value: 'proposal', label: 'Proposal' },
  { value: 'report', label: 'Report' },
  { value: 'specification', label: 'Specification' },
  { value: 'meeting_minutes', label: 'Meeting Minutes' },
  { value: 'other', label: 'Other' },
]

/** Mirrors MAX_DOCUMENT_SIZE_MB on the backend; used for a fast client-side check. */
export const MAX_DOCUMENT_SIZE_MB = 25

export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}
