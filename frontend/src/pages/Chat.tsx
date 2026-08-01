/**
 * Chat Page - AI Project Assistant
 */

import { useState } from 'react'
import ChatInterface from '../components/chat/ChatInterface'

export default function Chat() {
  const [selectedProjectId, setSelectedProjectId] = useState<number | undefined>()

  return (
    <div className="flex flex-col h-full">
      {/* Page header */}
      <div className="border-b bg-gray-50 p-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">StratOS AI Assistant</h1>
        <p className="text-gray-600">
          Multi-agent AI system: Ask about projects, risks, schedules, and documents. Get intelligent answers from specialized agents working in parallel.
        </p>
      </div>

      {/* Main content */}
      <div className="flex-1 overflow-hidden p-6 flex flex-col">
        {/* Project selector (optional) */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Filter by Project (Optional)
          </label>
          <select
            value={selectedProjectId || ''}
            onChange={(e) => setSelectedProjectId(e.target.value ? parseInt(e.target.value) : undefined)}
            className="w-full max-w-sm px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-600"
          >
            <option value="">All Projects</option>
            <option value="1">CloudSync</option>
            <option value="2">DataPipeline</option>
            <option value="3">SecurityAudit</option>
          </select>
        </div>

        {/* Chat interface */}
        <div className="flex-1 overflow-hidden max-w-4xl mx-auto w-full">
          <ChatInterface projectId={selectedProjectId} />
        </div>
      </div>
    </div>
  )
}
