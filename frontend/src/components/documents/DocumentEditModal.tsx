import { useEffect, useState } from 'react'
import Modal from '../ui/Modal'
import type {
  Document,
  DocumentMetadataInput,
  DocumentType,
} from '../../types/document'
import { DOCUMENT_TYPE_OPTIONS } from '../../types/document'
import type { Project } from '../../types/project'

interface DocumentEditModalProps {
  open: boolean
  document: Document | null
  projects: Project[]
  onClose: () => void
  onSave: (input: DocumentMetadataInput) => Promise<void>
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
}

function toForm(document: Document): FormState {
  return {
    title: document.title,
    description: document.description ?? '',
    document_type: document.document_type,
    project_id: document.project_id ? String(document.project_id) : '',
    customer: document.customer ?? '',
  }
}

export default function DocumentEditModal({
  open,
  document,
  projects,
  onClose,
  onSave,
}: DocumentEditModalProps) {
  const [form, setForm] = useState<FormState>({
    title: '',
    description: '',
    document_type: 'other',
    project_id: '',
    customer: '',
  })
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (open && document) {
      setForm(toForm(document))
      setError(null)
      setSaving(false)
    }
  }, [open, document])

  function update<K extends keyof FormState>(key: K, value: FormState[K]) {
    setForm((prev) => ({ ...prev, [key]: value }))
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setSaving(true)
    setError(null)
    try {
      await onSave({
        title: form.title.trim(),
        description: form.description.trim() || null,
        document_type: form.document_type,
        project_id: form.project_id ? Number(form.project_id) : null,
        customer: form.customer.trim() || null,
      })
      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong.')
      setSaving(false)
    }
  }

  return (
    <Modal
      open={open}
      title="Edit Document"
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
            form="document-edit-form"
            disabled={saving}
            className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-50"
          >
            {saving ? 'Saving…' : 'Save Changes'}
          </button>
        </>
      }
    >
      <form id="document-edit-form" onSubmit={handleSubmit} className="space-y-4">
        {error && (
          <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
            {error}
          </div>
        )}

        <p className="text-xs text-slate-500">
          The stored file is immutable — upload a new document to replace its
          contents. Only the metadata below can be edited.
        </p>

        <div>
          <label className={labelClass} htmlFor="edit-title">
            Title <span className="text-red-500">*</span>
          </label>
          <input
            id="edit-title"
            className={inputClass}
            value={form.title}
            onChange={(e) => update('title', e.target.value)}
            maxLength={255}
            required
          />
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <label className={labelClass} htmlFor="edit-type">
              Type <span className="text-red-500">*</span>
            </label>
            <select
              id="edit-type"
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
            <label className={labelClass} htmlFor="edit-project">
              Project
            </label>
            <select
              id="edit-project"
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

        <div>
          <label className={labelClass} htmlFor="edit-customer">
            Customer
          </label>
          <input
            id="edit-customer"
            className={inputClass}
            value={form.customer}
            onChange={(e) => update('customer', e.target.value)}
            maxLength={255}
          />
        </div>

        <div>
          <label className={labelClass} htmlFor="edit-description">
            Description
          </label>
          <textarea
            id="edit-description"
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
