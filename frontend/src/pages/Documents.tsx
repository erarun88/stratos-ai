import { useCallback, useEffect, useState } from 'react'
import {
  deleteDocument,
  documentDownloadUrl,
  getDocuments,
  updateDocument,
  uploadDocument,
} from '../api/documents'
import { getProjects } from '../api/projects'
import type {
  Document,
  DocumentMetadataInput,
  DocumentType,
  DocumentUploadInput,
} from '../types/document'
import { DOCUMENT_TYPE_OPTIONS, formatFileSize } from '../types/document'
import type { Project } from '../types/project'
import DocumentTypeBadge from '../components/documents/DocumentTypeBadge'
import DocumentUploadModal from '../components/documents/DocumentUploadModal'
import DocumentEditModal from '../components/documents/DocumentEditModal'
import DeleteDocumentModal from '../components/documents/DeleteDocumentModal'

const PAGE_SIZE = 20

function formatDateTime(value: string | null): string {
  if (!value) return '—'
  const d = new Date(value)
  if (Number.isNaN(d.getTime())) return value
  return d.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })
}

const controlClass =
  'rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-500'

export default function Documents() {
  const [documents, setDocuments] = useState<Document[]>([])
  const [total, setTotal] = useState(0)
  const [totalPages, setTotalPages] = useState(1)
  const [projects, setProjects] = useState<Project[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Filters. `search` is what the user is typing; `debouncedSearch` is what
  // actually hits the API, so keystrokes don't produce a request each.
  const [search, setSearch] = useState('')
  const [debouncedSearch, setDebouncedSearch] = useState('')
  const [typeFilter, setTypeFilter] = useState<DocumentType | ''>('')
  const [projectFilter, setProjectFilter] = useState<string>('')
  const [page, setPage] = useState(1)

  // Modal state
  const [uploadOpen, setUploadOpen] = useState(false)
  const [editing, setEditing] = useState<Document | null>(null)
  const [deleting, setDeleting] = useState<Document | null>(null)

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedSearch(search), 300)
    return () => clearTimeout(timer)
  }, [search])

  // Any filter change starts again from the first page.
  useEffect(() => {
    setPage(1)
  }, [debouncedSearch, typeFilter, projectFilter])

  const loadDocuments = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const result = await getDocuments({
        search: debouncedSearch,
        document_type: typeFilter,
        project_id: projectFilter ? Number(projectFilter) : null,
        page,
        page_size: PAGE_SIZE,
      })
      setDocuments(result.items)
      setTotal(result.total)
      setTotalPages(Math.max(result.total_pages, 1))
    } catch {
      setError('Could not load documents. Is the backend running?')
    } finally {
      setLoading(false)
    }
  }, [debouncedSearch, typeFilter, projectFilter, page])

  useEffect(() => {
    loadDocuments()
  }, [loadDocuments])

  // Projects populate the filter and the upload/edit dropdowns.
  useEffect(() => {
    getProjects()
      .then(setProjects)
      .catch(() => setProjects([]))
  }, [])

  async function handleUpload(input: DocumentUploadInput) {
    await uploadDocument(input)
    await loadDocuments()
  }

  async function handleEditSave(input: DocumentMetadataInput) {
    if (!editing) return
    await updateDocument(editing.id, input)
    await loadDocuments()
  }

  async function handleDelete() {
    if (!deleting) return
    await deleteDocument(deleting.id)
    // Stepping back a page avoids landing on an empty last page.
    if (documents.length === 1 && page > 1) {
      setPage(page - 1)
    } else {
      await loadDocuments()
    }
  }

  const hasFilters = Boolean(debouncedSearch || typeFilter || projectFilter)

  return (
    <div>
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Documents</h1>
          <p className="mt-1 text-sm text-slate-500">
            Central repository for project and customer documents.
          </p>
        </div>

        <button
          type="button"
          onClick={() => setUploadOpen(true)}
          className="inline-flex items-center gap-1.5 rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white shadow-sm transition-colors hover:bg-slate-700"
        >
          <span className="text-base leading-none">+</span>
          Upload Document
        </button>
      </div>

      {/* Search & filters */}
      <div className="mt-6 flex flex-wrap items-end gap-3">
        <div className="min-w-56 flex-1">
          <label className="block text-xs font-medium text-slate-500" htmlFor="doc-search">
            Search
          </label>
          <input
            id="doc-search"
            type="search"
            className={`mt-1 w-full ${controlClass}`}
            placeholder="Title, file name, description or customer"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>

        <div>
          <label className="block text-xs font-medium text-slate-500" htmlFor="doc-type-filter">
            Type
          </label>
          <select
            id="doc-type-filter"
            className={`mt-1 ${controlClass}`}
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value as DocumentType | '')}
          >
            <option value="">All types</option>
            {DOCUMENT_TYPE_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-medium text-slate-500" htmlFor="doc-project-filter">
            Project
          </label>
          <select
            id="doc-project-filter"
            className={`mt-1 ${controlClass}`}
            value={projectFilter}
            onChange={(e) => setProjectFilter(e.target.value)}
          >
            <option value="">All projects</option>
            {projects.map((project) => (
              <option key={project.id} value={project.id}>
                {project.name}
              </option>
            ))}
          </select>
        </div>

        {hasFilters && (
          <button
            type="button"
            onClick={() => {
              setSearch('')
              setTypeFilter('')
              setProjectFilter('')
            }}
            className="rounded-md border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100"
          >
            Clear
          </button>
        )}
      </div>

      <div className="mt-4 overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
        {loading ? (
          <div className="p-8 text-center text-sm text-slate-500">Loading documents…</div>
        ) : error ? (
          <div className="p-8 text-center text-sm text-red-600">{error}</div>
        ) : documents.length === 0 ? (
          <div className="flex flex-col items-center justify-center p-10 text-center">
            <p className="text-sm font-medium text-slate-600">
              {hasFilters ? 'No documents match your filters' : 'No documents yet'}
            </p>
            <p className="mt-1 text-xs text-slate-400">
              {hasFilters
                ? 'Try a different search term or clear the filters.'
                : 'Upload your first PDF to start building the repository.'}
            </p>
            {!hasFilters && (
              <button
                type="button"
                onClick={() => setUploadOpen(true)}
                className="mt-4 rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700"
              >
                + Upload Document
              </button>
            )}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-sm">
              <thead className="bg-slate-50">
                <tr>
                  <th className="px-4 py-3 text-left font-medium text-slate-500">Title</th>
                  <th className="px-4 py-3 text-left font-medium text-slate-500">Type</th>
                  <th className="px-4 py-3 text-left font-medium text-slate-500">Project</th>
                  <th className="px-4 py-3 text-left font-medium text-slate-500">Customer</th>
                  <th className="px-4 py-3 text-left font-medium text-slate-500">Size</th>
                  <th className="px-4 py-3 text-left font-medium text-slate-500">Uploaded</th>
                  <th className="px-4 py-3 text-right font-medium text-slate-500">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {documents.map((doc) => (
                  <tr key={doc.id} className="hover:bg-slate-50">
                    <td className="px-4 py-3">
                      <div className="font-medium text-slate-900">{doc.title}</div>
                      <div className="text-xs text-slate-400">{doc.filename}</div>
                    </td>
                    <td className="px-4 py-3">
                      <DocumentTypeBadge type={doc.document_type} />
                    </td>
                    <td className="px-4 py-3 text-slate-600">{doc.project_name ?? '—'}</td>
                    <td className="px-4 py-3 text-slate-600">{doc.customer ?? '—'}</td>
                    <td className="px-4 py-3 text-slate-600">{formatFileSize(doc.file_size)}</td>
                    <td className="px-4 py-3 text-slate-600">{formatDateTime(doc.created_at)}</td>
                    <td className="px-4 py-3">
                      <div className="flex justify-end gap-2">
                        <a
                          href={documentDownloadUrl(doc.id)}
                          download={doc.filename}
                          className="rounded-md border border-slate-300 px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-100"
                        >
                          Download
                        </a>
                        <button
                          type="button"
                          onClick={() => setEditing(doc)}
                          className="rounded-md border border-slate-300 px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-100"
                        >
                          Edit
                        </button>
                        <button
                          type="button"
                          onClick={() => setDeleting(doc)}
                          className="rounded-md border border-red-200 px-3 py-1.5 text-xs font-medium text-red-600 hover:bg-red-50"
                        >
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {!loading && !error && documents.length > 0 && (
        <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
          <p className="text-xs text-slate-500">
            Showing {(page - 1) * PAGE_SIZE + 1}–{(page - 1) * PAGE_SIZE + documents.length} of{' '}
            {total} document{total === 1 ? '' : 's'}
          </p>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setPage((p) => Math.max(p - 1, 1))}
              disabled={page <= 1}
              className="rounded-md border border-slate-300 px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-100 disabled:opacity-40"
            >
              Previous
            </button>
            <span className="text-xs text-slate-500">
              Page {page} of {totalPages}
            </span>
            <button
              type="button"
              onClick={() => setPage((p) => Math.min(p + 1, totalPages))}
              disabled={page >= totalPages}
              className="rounded-md border border-slate-300 px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-100 disabled:opacity-40"
            >
              Next
            </button>
          </div>
        </div>
      )}

      <DocumentUploadModal
        open={uploadOpen}
        projects={projects}
        onClose={() => setUploadOpen(false)}
        onUpload={handleUpload}
      />

      <DocumentEditModal
        open={editing !== null}
        document={editing}
        projects={projects}
        onClose={() => setEditing(null)}
        onSave={handleEditSave}
      />

      <DeleteDocumentModal
        open={deleting !== null}
        document={deleting}
        onClose={() => setDeleting(null)}
        onConfirm={handleDelete}
      />
    </div>
  )
}
