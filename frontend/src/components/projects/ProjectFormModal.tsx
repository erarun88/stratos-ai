import { useEffect, useState } from 'react'
import Modal from '../ui/Modal'
import type { Project, ProjectInput, ProjectStatus } from '../../types/project'
import { PROJECT_STATUS_OPTIONS } from '../../types/project'

interface ProjectFormModalProps {
  open: boolean
  // When provided, the modal is in "edit" mode; otherwise "create" mode.
  project?: Project | null
  onClose: () => void
  onSave: (input: ProjectInput) => Promise<void>
}

function emptyForm(): ProjectInput {
  return {
    name: '',
    customer: '',
    project_manager: '',
    status: 'planning',
    start_date: null,
    end_date: null,
    description: null,
  }
}

function toForm(project: Project): ProjectInput {
  return {
    name: project.name,
    customer: project.customer,
    project_manager: project.project_manager ?? '',
    status: project.status,
    start_date: project.start_date,
    end_date: project.end_date,
    description: project.description,
  }
}

const inputClass =
  'mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-500'
const labelClass = 'block text-sm font-medium text-slate-700'

export default function ProjectFormModal({
  open,
  project,
  onClose,
  onSave,
}: ProjectFormModalProps) {
  const isEdit = Boolean(project)
  const [form, setForm] = useState<ProjectInput>(emptyForm())
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Reset the form whenever the modal opens (with the project being edited,
  // or blank for a new project).
  useEffect(() => {
    if (open) {
      setForm(project ? toForm(project) : emptyForm())
      setError(null)
      setSaving(false)
    }
  }, [open, project])

  function update<K extends keyof ProjectInput>(key: K, value: ProjectInput[K]) {
    setForm((prev) => ({ ...prev, [key]: value }))
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setSaving(true)
    setError(null)
    try {
      await onSave({
        ...form,
        // Send null instead of empty strings for optional fields.
        start_date: form.start_date || null,
        end_date: form.end_date || null,
        description: form.description?.trim() ? form.description : null,
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
      title={isEdit ? 'Edit Project' : 'Add Project'}
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
            form="project-form"
            disabled={saving}
            className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-50"
          >
            {saving ? 'Saving…' : isEdit ? 'Save Changes' : 'Create Project'}
          </button>
        </>
      }
    >
      <form id="project-form" onSubmit={handleSubmit} className="space-y-4">
        {error && (
          <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
            {error}
          </div>
        )}

        <div>
          <label className={labelClass} htmlFor="name">
            Name <span className="text-red-500">*</span>
          </label>
          <input
            id="name"
            className={inputClass}
            value={form.name}
            onChange={(e) => update('name', e.target.value)}
            required
          />
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <label className={labelClass} htmlFor="customer">
              Customer <span className="text-red-500">*</span>
            </label>
            <input
              id="customer"
              className={inputClass}
              value={form.customer}
              onChange={(e) => update('customer', e.target.value)}
              required
            />
          </div>
          <div>
            <label className={labelClass} htmlFor="project_manager">
              Project Manager <span className="text-red-500">*</span>
            </label>
            <input
              id="project_manager"
              className={inputClass}
              value={form.project_manager}
              onChange={(e) => update('project_manager', e.target.value)}
              required
            />
          </div>
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <div>
            <label className={labelClass} htmlFor="status">
              Status <span className="text-red-500">*</span>
            </label>
            <select
              id="status"
              className={inputClass}
              value={form.status}
              onChange={(e) => update('status', e.target.value as ProjectStatus)}
            >
              {PROJECT_STATUS_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className={labelClass} htmlFor="start_date">
              Start Date
            </label>
            <input
              id="start_date"
              type="date"
              className={inputClass}
              value={form.start_date ?? ''}
              onChange={(e) => update('start_date', e.target.value || null)}
            />
          </div>
          <div>
            <label className={labelClass} htmlFor="end_date">
              End Date
            </label>
            <input
              id="end_date"
              type="date"
              className={inputClass}
              value={form.end_date ?? ''}
              onChange={(e) => update('end_date', e.target.value || null)}
            />
          </div>
        </div>

        <div>
          <label className={labelClass} htmlFor="description">
            Description
          </label>
          <textarea
            id="description"
            rows={3}
            className={inputClass}
            value={form.description ?? ''}
            onChange={(e) => update('description', e.target.value || null)}
          />
        </div>
      </form>
    </Modal>
  )
}
