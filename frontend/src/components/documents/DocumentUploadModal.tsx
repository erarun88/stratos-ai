import { useEffect, useRef, useState } from 'react'
import Modal from '../ui/Modal'
import type { DocumentType, DocumentUploadInput } from '../../types/document'
import {
  DOCUMENT_TYPE_OPTIONS,
  MAX_DOCUMENT_SIZE_MB,
  formatFileSize,
} from '../../types/document'
import type { Project } from '../../types/project'

interface DocumentUploadModalProps {
  open: boolean
  projects: Project[]
  onClose: () => void
  onUpload: (input: DocumentUploadInput) => Promise<void>
}

const inputClass =
  'mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-500'
const labelClass = 'block text-sm font-medium text-slate-700'

interface FormState {
  title: string
  description: string
  document_type: DocumentType
  project_id: string
  customer: string
  uploaded_by: string
}

function emptyForm(): FormState {
  return {
    title: '',
    description: '',
    document_type: 'other',
    project_id: '',
    customer: '',
    uploaded_by: '',
  }
}

export default function DocumentUploadModal({
  open,
  projects,
  onClose,
  onUpload,
}: DocumentUploadModalProps) {
  const [form, setForm] = useState<FormState>(emptyForm())
  const [file, setFile] = useState<File | null>(null)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (open) {
      setForm(emptyForm())
      setFile(null)
      setError(null)
      setSaving(false)
      if (fileInputRef.current) fileInputRef.current.value = ''
    }
  }, [open])

  function update<K extends keyof FormState>(key: K, value: FormState[K]) {
    setForm((prev) => ({ ...prev, [key]: value }))
  }

  function handleFileChange(selected: File | null) {
    setFile(selected)
    setError(null)
    // Default the title to the filename (without extension) so the common
    // case needs no extra typing.
    if (selected && !form.title.trim()) {
      update('title', selected.name.replace(/\.pdf$/i, ''))
    }
  }

  /** Fast client-side checks. The backend re-validates everything. */
  function validate(): string | null {
    if (!file) return 'Please choose a PDF file to upload.'
    if (!/\.pdf$/i.test(file.name)) return 'Only PDF files are supported.'
    if (file.size === 0) return 'The selected file is empty.'
    if (file.size > MAX_DOCUMENT_SIZE_MB * 1024 * 1024) {
      return `File is too large (${formatFileSize(file.size)}). Maximum is ${MAX_DOCUMENT_SIZE_MB} MB.`
    }
    if (!form.title.trim()) return 'Title is required.'
    return null
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const validationError = validate()
    if (validationError || !file) {
      setError(validationError)
      return
    }

    setSaving(true)
    setError(null)
    try {
      await onUpload({
        file,
        title: form.title.trim(),
        description: form.description.trim() || null,
        document_type: form.document_type,
        project_id: form.project_id ? Number(form.project_id) : null,
        customer: form.customer.trim() || null,
        uploaded_by: form.uploaded_by.trim() || null,
      })
      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed.')
      setSaving(false)
    }
  }

  return (
    <Modal
      open={open}
      title="Upload Document"
      onClose={onClose}
      footer={
        <>
          <button
            type="button"
            onClick={onClose}
            className="rounded-md border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100"
          >
            Cancel
          </button>
          <button
            type="submit"
            form="document-upload-form"
            disabled={saving}
            className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-50"
          >
            {saving ? 'Uploading…' : 'Upload'}
          </button>
        </>
      }
    >
      <form id="document-upload-form" onSubmit={handleSubmit} className="space-y-4">
        {error && (
          <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
            {error}
          </div>
        )}

        <div>
          <label className={labelClass} htmlFor="document-file">
            PDF File <span className="text-red-500">*</span>
          </label>
          <input
            id="document-file"
            ref={fileInputRef}
            type="file"
            accept="application/pdf,.pdf"
            required
            onChange={(e) => handleFileChange(e.target.files?.[0] ?? null)}
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-600 file:mr-3 file:rounded-md file:border-0 file:bg-slate-900 file:px-3 file:py-1.5 file:text-sm file:font-medium file:text-white hover:file:bg-slate-700"
          />
          <p className="mt-1 text-xs text-slate-400">
            {file
              ? `${file.name} · ${formatFileSize(file.size)}`
              : `PDF only, up to ${MAX_DOCUMENT_SIZE_MB} MB.`}
          </p>
        </div>

        <div>
          <label className={labelClass} htmlFor="document-title">
            Title <span className="text-red-500">*</span>
          </label>
          <input
            id="document-title"
            className={inputClass}
            value={form.title}
            onChange={(e) => update('title', e.target.value)}
            maxLength={255}
            required
          />
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <label className={labelClass} htmlFor="document-type">
              Type <span className="text-red-500">*</span>
            </label>
            <select
              id="document-type"
              className={inputClass}
              value={form.document_type}
              onChange={(e) => update('document_type', e.target.value as DocumentType)}
            >
              {DOCUMENT_TYPE_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className={labelClass} htmlFor="document-project">
              Project
            </label>
            <select
              id="document-project"
              className={inputClass}
              value={form.project_id}
              onChange={(e) => update('project_id', e.target.value)}
            >
              <option value="">— Not project-specific —</option>
              {projects.map((project) => (
                <option key={project.id} value={project.id}>
                  {project.name}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <label className={labelClass} htmlFor="document-customer">
              Customer
            </label>
            <input
              id="document-customer"
              className={inputClass}
              value={form.customer}
              onChange={(e) => update('customer', e.target.value)}
              maxLength={255}
              placeholder="Defaults to the project's customer"
            />
          </div>
          <div>
            <label className={labelClass} htmlFor="document-uploaded-by">
              Uploaded By
            </label>
            <input
              id="document-uploaded-by"
              className={inputClass}
              value={form.uploaded_by}
              onChange={(e) => update('uploaded_by', e.target.value)}
              maxLength={255}
            />
          </div>
        </div>

        <div>
          <label className={labelClass} htmlFor="document-description">
            Description
          </label>
          <textarea
            id="document-description"
            rows={3}
            className={inputClass}
            value={form.description}
            onChange={(e) => update('description', e.target.value)}
            maxLength={5000}
          />
        </div>
      </form>
    </Modal>
  )
}
