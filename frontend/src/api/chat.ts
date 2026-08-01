/**
 * Chat API client - Communicate with ProjectAgent backend
 */

export interface Citation {
  source: string
  content?: string
  relevance?: string
  tool?: string
}

export interface ChatResponse {
  answer: string
  citations: Citation[]
  confidence: number
  response_mode: string
  agents_used?: string[]  // NEW: which agents contributed
  metadata?: Record<string, any>
}

export interface ChatRequest {
  query: string
  project_id?: number
  response_mode?: 'concise' | 'detailed' | 'executive'
  conversation_id?: string
}

export interface ChatHealth {
  status: 'healthy' | 'unhealthy'
  tools?: string[]
  tool_count?: number
  error?: string
}

/**
 * Send a chat message and get a response from ProjectAgent
 */
export async function sendChatMessage(request: ChatRequest): Promise<ChatResponse> {
  const response = await fetch('/api/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(error.detail || `Chat error: ${response.statusText}`)
  }

  return response.json()
}

/**
 * Stream a chat response (Server-Sent Events)
 * Returns an async generator that yields message chunks
 */
export async function* streamChatMessage(
  request: ChatRequest
): AsyncGenerator<{ type: string; content?: string; citations?: Citation[] }, void, unknown> {
  const response = await fetch('/api/chat/stream', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  })

  if (!response.ok) {
    throw new Error(`Stream error: ${response.statusText}`)
  }

  if (!response.body) {
    throw new Error('No response body')
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()

  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      const chunk = decoder.decode(value)
      const lines = chunk.split('\n')

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6)
          if (data === '[DONE]') {
            return
          }
          try {
            const parsed = JSON.parse(data)
            yield parsed
          } catch {
            // Ignore parse errors for incomplete data
          }
        }
      }
    }
  } finally {
    reader.releaseLock()
  }
}

/**
 * Check chat service health
 */
export async function checkChatHealth(): Promise<ChatHealth> {
  try {
    const response = await fetch('/api/chat/health')
    if (!response.ok) {
      return {
        status: 'unhealthy',
        error: `HTTP ${response.status}`,
      }
    }
    return response.json()
  } catch (error) {
    return {
      status: 'unhealthy',
      error: error instanceof Error ? error.message : 'Unknown error',
    }
  }
}
