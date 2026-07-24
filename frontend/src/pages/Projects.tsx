import { useEffect, useState } from 'react'
import {
  getProjects,
  createProject,
  updateProject,
  updateProjectStatus,
} from '../api/projects'
import type { Project, ProjectInput, ProjectStatus } from '../types/project'
import ProjectStatusBadge from '../components/projects/ProjectStatusBadge'
import ProjectFormModal from '../components/projects/ProjectFormModal'
import ChangeStatusModal from '../components/projects/ChangeStatusModal'

function formatDate(value: string | null): string {
  if (!value) return '—'
  const d = new Date(value)
  if (Number.isNaN(d.getTime())) return value
  return d.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })
}

export default function Projects() {
  const [projects, setProjects] = useState<Project[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Modal state
  const [formOpen, setFormOpen] = useState(false)
  const [editing, setEditing] = useState<Project | null>(null)
  const [statusTarget, setStatusTarget] = useState<Project | null>(null)

  async function loadProjects() {
    setLoading(true)
    setError(null)
    try {
      setProjects(await getProjects())
    } catch {
      setError('Could not load projects. Is the backend running?')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadProjects()
  }, [])

  function openAdd() {
    setEditing(null)
    setFormOpen(true)
  }

  function openEdit(project: Project) {
    setEditing(project)
    setFormOpen(true)
  }

  async function handleSave(input: ProjectInput) {
    if (editing) {
      await updateProject(editing.id, input)
    } else {
      await createProject(input)
    }
    await loadProjects()
  }

  async function handleStatusSave(status: ProjectStatus) {
    if (!statusTarget) return
    await updateProjectStatus(statusTarget.id, status)
    await loadProjects()
  }

  return (
    <div>
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Projects</h1>
          <p className="mt-1 text-sm text-slate-500">
            Manage the projects engineers are staffed on.
          </p>
        </div>

        <button
          type="button"
          onClick={openAdd}
          className="inline-flex items-center gap-1.5 rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white shadow-sm transition-colors hover:bg-slate-700"
        >
          <span className="text-base leading-none">+</span>
          Add Project
        </button>
      </div>

      <div className="mt-6 overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
        {loading ? (
          <div className="p-8 text-center text-sm text-slate-500">Loading projects…</div>
        ) : error ? (
          <div className="p-8 text-center text-sm text-red-600">{error}</div>
        ) : projects.length === 0 ? (
          <div className="flex flex-col items-center justify-center p-10 text-center">
            <p className="text-sm font-medium text-slate-600">No projects yet</p>
            <p className="mt-1 text-xs text-slate-400">
              Get started by adding your first project.
            </p>
            <button
              type="button"
              onClick={openAdd}
              className="mt-4 rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700"
            >
              + Add Project
            </button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-sm">
              <thead className="bg-slate-50">
                <tr>
                  <th className="px-4 py-3 text-left font-medium text-slate-500">Name</th>
                  <th className="px-4 py-3 text-left font-medium text-slate-500">Customer</th>
                  <th className="px-4 py-3 text-left font-medium text-slate-500">Manager</th>
                  <th className="px-4 py-3 text-left font-medium text-slate-500">Status</th>
                  <th className="px-4 py-3 text-left font-medium text-slate-500">Start</th>
                  <th className="px-4 py-3 text-left font-medium text-slate-500">End</th>
                  <th className="px-4 py-3 text-right font-medium text-slate-500">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {projects.map((project) => (
                  <tr key={project.id} className="hover:bg-slate-50">
                    <td className="px-4 py-3 font-medium text-slate-900">{project.name}</td>
                    <td className="px-4 py-3 text-slate-600">{project.customer}</td>
                    <td className="px-4 py-3 text-slate-600">
                      {project.project_manager ?? '—'}
                    </td>
                    <td className="px-4 py-3">
                      <ProjectStatusBadge status={project.status} />
                    </td>
                    <td className="px-4 py-3 text-slate-600">{formatDate(project.start_date)}</td>
                    <td className="px-4 py-3 text-slate-600">{formatDate(project.end_date)}</td>
                    <td className="px-4 py-3">
                      <div className="flex justify-end gap-2">
                        <button
                          type="button"
                          onClick={() => openEdit(project)}
                          className="rounded-md border border-slate-300 px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-100"
                        >
                          Edit
                        </button>
                        <button
                          type="button"
                          onClick={() => setStatusTarget(project)}
                          className="rounded-md border border-slate-300 px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-100"
                        >
                          Change Status
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

      <ProjectFormModal
        open={formOpen}
        project={editing}
        onClose={() => setFormOpen(false)}
        onSave={handleSave}
      />

      <ChangeStatusModal
        open={statusTarget !== null}
        project={statusTarget}
        onClose={() => setStatusTarget(null)}
        onSave={handleStatusSave}
      />
    </div>
  )
}
