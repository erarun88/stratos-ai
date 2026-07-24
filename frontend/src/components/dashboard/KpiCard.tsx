interface KpiCardProps {
  label: string
  value: number
  // Optional colored accent dot to visually tie a card to a status.
  accentClass?: string
}

export default function KpiCard({ label, value, accentClass }: KpiCardProps) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <div className="flex items-center gap-2">
        {accentClass && <span className={`h-2 w-2 rounded-full ${accentClass}`} />}
        <p className="text-xs font-medium uppercase tracking-wide text-slate-500">{label}</p>
      </div>
      <p className="mt-2 text-3xl font-semibold text-slate-900">{value}</p>
    </div>
  )
}
