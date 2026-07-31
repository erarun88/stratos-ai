/**
 * MessageBubble - Display a single chat message
 */

import type { Citation } from '../../api/chat'

interface MessageBubbleProps {
  role: 'user' | 'assistant'
  content: string
  citations?: Citation[]
  confidence?: number
  timestamp?: Date
  isLoading?: boolean
}

export default function MessageBubble({
  role,
  content,
  citations,
  confidence,
  timestamp,
  isLoading,
}: MessageBubbleProps) {
  const isUser = role === 'user'

  return (
    <div className={`flex gap-3 mb-4 ${isUser ? 'flex-row-reverse' : ''}`}>
      {/* Avatar */}
      <div
        className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-white text-sm font-semibold ${
          isUser ? 'bg-purple-600' : 'bg-blue-600'
        }`}
      >
        {isUser ? 'You' : 'AI'}
      </div>

      {/* Message bubble */}
      <div className={`flex-1 max-w-2xl ${isUser ? 'items-end flex flex-col' : ''}`}>
        <div
          className={`px-4 py-3 rounded-lg ${
            isUser
              ? 'bg-purple-600 text-white rounded-br-none'
              : 'bg-gray-100 text-gray-900 rounded-bl-none'
          } ${isLoading ? 'animate-pulse' : ''}`}
        >
          <p className="whitespace-pre-wrap text-sm leading-relaxed">{content}</p>

          {/* Confidence score for assistant */}
          {!isUser && confidence !== undefined && (
            <div className="mt-2 pt-2 border-t border-gray-300 flex items-center gap-2">
              <span className="text-xs font-medium">Confidence:</span>
              <div className="flex-1 bg-gray-200 rounded-full h-2">
                <div
                  className={`h-2 rounded-full transition-all ${
                    confidence > 0.8
                      ? 'bg-green-500'
                      : confidence > 0.6
                        ? 'bg-yellow-500'
                        : 'bg-red-500'
                  }`}
                  style={{ width: `${confidence * 100}%` }}
                />
              </div>
              <span className="text-xs font-semibold">{(confidence * 100).toFixed(0)}%</span>
            </div>
          )}
        </div>

        {/* Citations */}
        {citations && citations.length > 0 && (
          <div className={`mt-2 text-xs ${isUser ? 'text-right' : ''}`}>
            <p className="text-gray-600 font-medium mb-1">Sources:</p>
            <ul className="space-y-1">
              {citations.map((citation, idx) => (
                <li key={idx} className="text-gray-500 flex items-start gap-1">
                  <span className="text-gray-400 mt-0.5">•</span>
                  <div>
                    <p className="font-medium text-gray-700">{citation.source}</p>
                    {citation.content && (
                      <p className="text-gray-600 italic">"{citation.content.substring(0, 60)}..."</p>
                    )}
                    {citation.relevance && (
                      <p className="text-gray-500">Relevance: {citation.relevance}</p>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Timestamp */}
        {timestamp && (
          <div className="text-xs text-gray-500 mt-1">
            {timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </div>
        )}
      </div>
    </div>
  )
}
