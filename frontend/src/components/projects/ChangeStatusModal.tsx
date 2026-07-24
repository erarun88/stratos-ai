import { useEffect, useState } from 'react'
import Modal from '../ui/Modal'
import type { Project, ProjectStatus } from '../../types/project'
import { PROJECT_STATUS_OPTIONS } from '../../types/project'

interface ChangeStatusModalProps {
  open: boolean
  project: Project | null
  onClose: () => void
  onSave: (status: ProjectStatus) => Promise<void>
}

const inputClass =
  'mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-500'

export default function ChangeStatusModal({
  open,
  project,
  onClose,
  onSave,
}: ChangeStatusModalProps) {
  const [status, setStatus] = useState<ProjectStatus>('planning')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (open && project) {
      setStatus(project.status)
      setError(null)
      setSaving(false)
    }
  }, [open, project])

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setSaving(true)
    setError(null)
    try {
      await onSave(status)
      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong.')
      setSaving(false)
    }
  }

  return (
    <Modal
      open={open}
      title="Change Status"
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
            form="status-form"
            disabled={saving}
            className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-50"
          >
            {saving ? 'Saving…' : 'Update Status'}
          </button>
        </>
      }
    >
      <form id="status-form" onSubmit={handleSubmit} className="space-y-4">
        {error && (
          <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
            {error}
          </div>
        )}

        <p className="text-sm text-slate-600">
          Update the status for{' '}
          <span className="font-medium text-slate-900">{project?.name}</span>.
        </p>

        <div>
          <label className="block text-sm font-medium text-slate-700" htmlFor="new-status">
            Status
          </label>
          <select
            id="new-status"
            className={inputClass}
            value={status}
            onChange={(e) => setStatus(e.target.value as ProjectStatus)}
          >
            {PROJECT_STATUS_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>
      </form>
    </Modal>
  )
}
