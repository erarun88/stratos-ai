import type { DocumentType } from '../../types/document'

const TYPE_STYLES: Record<DocumentType, string> = {
  contract: 'bg-indigo-50 text-indigo-700 ring-indigo-600/20',
  sow: 'bg-violet-50 text-violet-700 ring-violet-600/20',
  proposal: 'bg-blue-50 text-blue-700 ring-blue-600/20',
  report: 'bg-emerald-50 text-emerald-700 ring-emerald-600/20',
  specification: 'bg-amber-50 text-amber-700 ring-amber-600/20',
  meeting_minutes: 'bg-sky-50 text-sky-700 ring-sky-600/20',
  other: 'bg-slate-100 text-slate-600 ring-slate-500/20',
}

const TYPE_LABELS: Record<DocumentType, string> = {
  contract: 'Contract',
  sow: 'Statement of Work',
  proposal: 'Proposal',
  report: 'Report',
  specification: 'Specification',
  meeting_minutes: 'Meeting Minutes',
  other: 'Other',
}

export default function DocumentTypeBadge({ type }: { type: DocumentType }) {
  const style = TYPE_STYLES[type] ?? TYPE_STYLES.other
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset ${style}`}
    >
      {TYPE_LABELS[type] ?? type}
    </span>
  )
}
