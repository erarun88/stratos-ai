import { useEffect, useState } from 'react'
import Modal from '../ui/Modal'
import type { Document } from '../../types/document'

interface DeleteDocumentModalProps {
  open: boolean
  document: Document | null
  onClose: () => void
  onConfirm: () => Promise<void>
}

export default function DeleteDocumentModal({
  open,
  document,
  onClose,
  onConfirm,
}: DeleteDocumentModalProps) {
  const [deleting, setDeleting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (open) {
      setError(null)
      setDeleting(false)
    }
  }, [open])

  async function handleConfirm() {
    setDeleting(true)
    setError(null)
    try {
      await onConfirm()
      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not delete the document.')
      setDeleting(false)
    }
  }

  return (
    <Modal
      open={open}
      title="Delete Document"
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
            type="button"
            onClick={handleConfirm}
            disabled={deleting}
            className="rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 disabled:opacity-50"
          >
            {deleting ? 'Deleting…' : 'Delete'}
          </button>
        </>
      }
    >
      <div className="space-y-3">
        {error && (
          <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
            {error}
          </div>
        )}

        <p className="text-sm text-slate-600">
          Delete <span className="font-medium text-slate-900">{document?.title}</span>?
          It will be removed from the repository and can no longer be downloaded.
        </p>
        <p className="text-xs text-slate-400">
          The record is retained for audit purposes and permanently removed by
          the retention job.
        </p>
      </div>
    </Modal>
  )
}
