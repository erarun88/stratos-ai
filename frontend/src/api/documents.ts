import { apiDelete, apiGet, apiPatch, apiPostForm, apiUrl } from './client'
import type {
  Document,
  DocumentFilters,
  DocumentList,
  DocumentMetadataInput,
  DocumentUploadInput,
} from '../types/document'

function buildQuery(filters: DocumentFilters): string {
  const params = new URLSearchParams()
  if (filters.search?.trim()) params.set('search', filters.search.trim())
  if (filters.document_type) params.set('document_type', filters.document_type)
  if (filters.project_id) params.set('project_id', String(filters.project_id))
  if (filters.page) params.set('page', String(filters.page))
  if (filters.page_size) params.set('page_size', String(filters.page_size))
  const query = params.toString()
  return query ? `?${query}` : ''
}

export function getDocuments(filters: DocumentFilters = {}): Promise<DocumentList> {
  return apiGet<DocumentList>(`/documents${buildQuery(filters)}`)
}

export function getProjectDocuments(
  projectId: number,
  filters: DocumentFilters = {},
): Promise<DocumentList> {
  return apiGet<DocumentList>(`/projects/${projectId}/documents${buildQuery(filters)}`)
}

export function uploadDocument(input: DocumentUploadInput): Promise<Document> {
  const form = new FormData()
  form.append('file', input.file)
  form.append('title', input.title)
  form.append('document_type', input.document_type)
  // Optional fields are only sent when set, so the backend applies its own
  // defaults (e.g. inheriting the customer from the selected project).
  if (input.description) form.append('description', input.description)
  if (input.project_id) form.append('project_id', String(input.project_id))
  if (input.customer) form.append('customer', input.customer)
  if (input.uploaded_by) form.append('uploaded_by', input.uploaded_by)

  return apiPostForm<Document>('/documents', form)
}

export function updateDocument(
  id: number,
  input: DocumentMetadataInput,
): Promise<Document> {
  return apiPatch<Document>(`/documents/${id}`, input)
}

export function deleteDocument(id: number): Promise<void> {
  return apiDelete(`/documents/${id}`)
}

/** Direct link the browser downloads; the API sets Content-Disposition. */
export function documentDownloadUrl(id: number): string {
  return apiUrl(`/documents/${id}/download`)
}
