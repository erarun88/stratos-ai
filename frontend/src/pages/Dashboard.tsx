import { useEffect, useState } from 'react'
import {
  getDashboardSummary,
  getProjectStatusBreakdown,
  getRecentProjects,
  getRecentEngineers,
} from '../api/dashboard'
import type { DashboardSummary, ProjectStatusCount } from '../types/dashboard'
import type { Project } from '../types/project'
import type { Engineer } from '../types/engineer'
import KpiCard from '../components/dashboard/KpiCard'
import ProjectStatusChart from '../components/dashboard/ProjectStatusChart'
import ProjectStatusBadge from '../components/projects/ProjectStatusBadge'
import StatusBadge from '../components/engineers/StatusBadge'

function formatDate(value: string | null): string {
  if (!value) return '—'
  const d = new Date(value)
  if (Number.isNaN(d.getTime())) return value
  return d.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })
}

export default function Dashboard() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null)
  const [statusBreakdown, setStatusBreakdown] = useState<ProjectStatusCount[]>([])
  const [recentProjects, setRecentProjects] = useState<Project[]>([])
  const [recentEngineers, setRecentEngineers] = useState<Engineer[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false

    Promise.all([
      getDashboardSummary(),
      getProjectStatusBreakdown(),
      getRecentProjects(),
      getRecentEngineers(),
    ])
      .then(([summaryData, statusData, projectsData, engineersData]) => {
        if (cancelled) return
        setSummary(summaryData)
        setStatusBreakdown(statusData)
        setRecentProjects(projectsData)
        setRecentEngineers(engineersData)
      })
      .catch(() => {
        if (!cancelled) setError('Could not load the dashboard. Is the backend running?')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [])

  return (
    <div>
      <h1 className="text-2xl font-semibold text-slate-900">Executive Dashboard</h1>
      <p className="mt-1 text-sm text-slate-500">
        A real-time overview of the project portfolio and engineering team.
      </p>

      {loading ? (
        <div className="mt-8 flex min-h-64 items-center justify-center rounded-lg border border-slate-200 bg-white text-sm text-slate-500">
          Loading dashboard…
        </div>
      ) : error ? (
        <div className="mt-8 flex min-h-64 items-center justify-center rounded-lg border border-slate-200 bg-white text-sm text-red-600">
          {error}
        </div>
      ) : summary ? (
        <div className="mt-6 space-y-8">
          {/* Project KPIs */}
          <section>
            <h2 className="mb-3 text-sm font-semibold text-slate-700">Projects</h2>
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6">
              <KpiCard label="Total" value={summary.total_projects} />
              <KpiCard label="Planning" value={summary.planning_projects} accentClass="bg-blue-600" />
              <KpiCard label="Active" value={summary.active_projects} accentClass="bg-emerald-600" />
              <KpiCard label="On Hold" value={summary.on_hold_projects} accentClass="bg-amber-600" />
              <KpiCard label="Completed" value={summary.completed_projects} accentClass="bg-slate-500" />
              <KpiCard label="Cancelled" value={summary.cancelled_projects} accentClass="bg-red-600" />
            </div>
          </section>

          {/* Engineer KPIs */}
          <section>
            <h2 className="mb-3 text-sm font-semibold text-slate-700">Engineers</h2>
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
              <KpiCard label="Total" value={summary.total_engineers} />
              <KpiCard label="Active" value={summary.active_engineers} accentClass="bg-emerald-600" />
              <KpiCard label="Inactive" value={summary.inactive_engineers} accentClass="bg-slate-500" />
            </div>
          </section>

          {/* Chart */}
          <section>
            <h2 className="mb-3 text-sm font-semibold text-slate-700">Projects by Status</h2>
            <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
              <ProjectStatusChart data={statusBreakdown} />
            </div>
          </section>

          {/* Recent tables */}
          <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
            <section>
              <h2 className="mb-3 text-sm font-semibold text-slate-700">Recent Projects</h2>
              <div className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
                {recentProjects.length === 0 ? (
                  <div className="p-6 text-center text-sm text-slate-500">No projects yet.</div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-slate-200 text-sm">
                      <thead className="bg-slate-50">
                        <tr>
                          <th className="px-4 py-3 text-left font-medium text-slate-500">Name</th>
                          <th className="px-4 py-3 text-left font-medium text-slate-500">Customer</th>
                          <th className="px-4 py-3 text-left font-medium text-slate-500">Status</th>
                          <th className="px-4 py-3 text-left font-medium text-slate-500">Start</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100">
                        {recentProjects.map((project) => (
                          <tr key={project.id} className="hover:bg-slate-50">
                            <td className="px-4 py-3 font-medium text-slate-900">{project.name}</td>
                            <td className="px-4 py-3 text-slate-600">{project.customer}</td>
                            <td className="px-4 py-3">
                              <ProjectStatusBadge status={project.status} />
                            </td>
                            <td className="px-4 py-3 text-slate-600">{formatDate(project.start_date)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </section>

            <section>
              <h2 className="mb-3 text-sm font-semibold text-slate-700">Recent Engineers</h2>
              <div className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
                {recentEngineers.length === 0 ? (
                  <div className="p-6 text-center text-sm text-slate-500">No engineers yet.</div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-slate-200 text-sm">
                      <thead className="bg-slate-50">
                        <tr>
                          <th className="px-4 py-3 text-left font-medium text-slate-500">Name</th>
                          <th className="px-4 py-3 text-left font-medium text-slate-500">Role</th>
                          <th className="px-4 py-3 text-left font-medium text-slate-500">Status</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100">
                        {recentEngineers.map((engineer) => (
                          <tr key={engineer.id} className="hover:bg-slate-50">
                            <td className="px-4 py-3 font-medium text-slate-900">{engineer.name}</td>
                            <td className="px-4 py-3 text-slate-600">{engineer.role}</td>
                            <td className="px-4 py-3">
                              <StatusBadge status={engineer.status} />
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </section>
          </div>
        </div>
      ) : null}
    </div>
  )
}
