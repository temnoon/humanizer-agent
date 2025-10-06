import { useState, useEffect } from 'react'
import PropTypes from 'prop-types'
import axios from 'axios'

/**
 * Session Sidebar Component
 *
 * Displays session history and allows navigation between sessions.
 * Supports creating new sessions, cloning, archiving, and continuing work.
 */
function SessionSidebar({
  currentSessionId,
  onSessionSelect,
  onNewSession,
  isVisible,
  onToggleVisibility
}) {
  const [sessions, setSessions] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [showArchived, setShowArchived] = useState(false)
  const [currentUserId, setCurrentUserId] = useState(null)

  const API_BASE = 'http://localhost:8000'

  // Load or create anonymous user on mount
  useEffect(() => {
    const initUser = async () => {
      const storedUserId = localStorage.getItem('humanizer_user_id')

      if (storedUserId) {
        setCurrentUserId(storedUserId)
      } else {
        // Create anonymous user
        try {
          const response = await axios.post(`${API_BASE}/api/sessions/users`, {
            is_anonymous: true
          })
          const userId = response.data.id
          localStorage.setItem('humanizer_user_id', userId)
          setCurrentUserId(userId)
        } catch (err) {
          console.error('Error creating user:', err)
        }
      }
    }

    initUser()
  }, [])

  // Load sessions when user is set or showArchived changes
  useEffect(() => {
    if (currentUserId) {
      loadSessions()
    }
  }, [currentUserId, showArchived])

  const loadSessions = async () => {
    if (!currentUserId) return

    setLoading(true)
    setError(null)

    try {
      const response = await axios.get(`${API_BASE}/api/sessions`, {
        params: {
          user_id: currentUserId,
          include_archived: showArchived,
          limit: 50
        }
      })
      setSessions(response.data)
    } catch (err) {
      console.error('Error loading sessions:', err)
      setError('Failed to load sessions')
    } finally {
      setLoading(false)
    }
  }

  const handleCreateSession = async () => {
    if (!currentUserId) return

    const title = prompt('Enter session title:')
    if (!title) return

    try {
      const response = await axios.post(`${API_BASE}/api/sessions`, {
        title,
        user_id: currentUserId
      })

      const newSession = response.data
      setSessions([newSession, ...sessions])

      if (onNewSession) {
        onNewSession(newSession)
      }
    } catch (err) {
      console.error('Error creating session:', err)
      setError('Failed to create session')
    }
  }

  const handleCloneSession = async (sessionId, e) => {
    e.stopPropagation()

    try {
      const response = await axios.post(
        `${API_BASE}/api/sessions/${sessionId}/clone`
      )

      const clonedSession = response.data
      setSessions([clonedSession, ...sessions])

      if (onSessionSelect) {
        onSessionSelect(clonedSession)
      }
    } catch (err) {
      console.error('Error cloning session:', err)
      setError('Failed to clone session')
    }
  }

  const handleArchiveSession = async (sessionId, e) => {
    e.stopPropagation()

    try {
      await axios.patch(`${API_BASE}/api/sessions/${sessionId}`, {
        is_archived: true
      })

      // Reload sessions
      await loadSessions()
    } catch (err) {
      console.error('Error archiving session:', err)
      setError('Failed to archive session')
    }
  }

  const handleDeleteSession = async (sessionId, e) => {
    e.stopPropagation()

    if (!confirm('Delete this session? This cannot be undone.')) {
      return
    }

    try {
      await axios.delete(`${API_BASE}/api/sessions/${sessionId}`)
      setSessions(sessions.filter(s => s.id !== sessionId))
    } catch (err) {
      console.error('Error deleting session:', err)
      setError('Failed to delete session')
    }
  }

  const formatDate = (dateString) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffMs = now - date
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)

    if (diffMins < 1) return 'Just now'
    if (diffMins < 60) return `${diffMins}m ago`
    if (diffHours < 24) return `${diffHours}h ago`
    if (diffDays < 7) return `${diffDays}d ago`

    return date.toLocaleDateString()
  }

  return (
    <>
      {/* Toggle Button */}
      <button
        onClick={onToggleVisibility}
        className={`fixed top-6 z-50 bg-realm-symbolic hover:bg-realm-symbolic-light text-white p-3 rounded-r-lg shadow-lg transition-all ${
          isVisible ? 'left-80' : 'left-0'
        }`}
        title={isVisible ? 'Hide sidebar' : 'Show sidebar'}
      >
        <svg
          className={`w-5 h-5 transition-transform ${isVisible ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
        </svg>
      </button>

      {/* Sidebar */}
      <div
        className={`fixed left-0 top-0 h-full w-80 bg-gray-900 border-r border-gray-700 transform transition-transform duration-300 z-40 ${
          isVisible ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="flex flex-col h-full">
          {/* Header */}
          <div className="p-4 border-b border-gray-700">
            <h2 className="text-xl font-structural font-semibold text-white mb-3">
              Sessions
            </h2>

            <button
              onClick={handleCreateSession}
              className="w-full px-4 py-2 bg-realm-symbolic hover:bg-realm-symbolic-light text-white rounded-md font-structural transition-colors"
              disabled={!currentUserId}
            >
              + New Session
            </button>

            <div className="mt-3">
              <label className="flex items-center text-sm text-gray-400 cursor-pointer">
                <input
                  type="checkbox"
                  checked={showArchived}
                  onChange={(e) => setShowArchived(e.target.checked)}
                  className="mr-2"
                />
                Show archived
              </label>
            </div>
          </div>

          {/* Sessions List */}
          <div className="flex-1 overflow-y-auto">
            {loading && (
              <div className="p-4 text-center text-gray-400">
                Loading sessions...
              </div>
            )}

            {error && (
              <div className="p-4 text-sm text-red-400 bg-red-900/20 m-4 rounded">
                {error}
              </div>
            )}

            {!loading && sessions.length === 0 && (
              <div className="p-4 text-center text-gray-500 text-sm">
                No sessions yet. Create your first session to begin.
              </div>
            )}

            <div className="space-y-2 p-4">
              {sessions.map((session) => (
                <div
                  key={session.id}
                  onClick={() => onSessionSelect && onSessionSelect(session)}
                  className={`p-3 rounded-lg cursor-pointer transition-all group ${
                    currentSessionId === session.id
                      ? 'bg-realm-symbolic border border-realm-symbolic-light'
                      : 'bg-gray-800 hover:bg-gray-750 border border-gray-700'
                  }`}
                >
                  {/* Session Title */}
                  <div className="flex items-start justify-between mb-2">
                    <h3 className="text-sm font-structural font-semibold text-white flex-1 mr-2">
                      {session.title}
                      {session.is_archived && (
                        <span className="ml-2 text-xs text-gray-500">(Archived)</span>
                      )}
                    </h3>
                  </div>

                  {/* Session Metadata */}
                  <div className="text-xs text-gray-400 mb-2">
                    {session.transformation_count} transformation{session.transformation_count !== 1 ? 's' : ''}
                    <span className="mx-2">•</span>
                    {formatDate(session.updated_at)}
                  </div>

                  {/* Action Buttons */}
                  <div className="flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button
                      onClick={(e) => handleCloneSession(session.id, e)}
                      className="px-2 py-1 text-xs bg-realm-subjective hover:bg-realm-subjective-light text-white rounded transition-colors"
                      title="Clone session"
                    >
                      Clone
                    </button>
                    {!session.is_archived && (
                      <button
                        onClick={(e) => handleArchiveSession(session.id, e)}
                        className="px-2 py-1 text-xs bg-gray-700 hover:bg-gray-600 text-white rounded transition-colors"
                        title="Archive session"
                      >
                        Archive
                      </button>
                    )}
                    <button
                      onClick={(e) => handleDeleteSession(session.id, e)}
                      className="px-2 py-1 text-xs bg-red-900 hover:bg-red-800 text-white rounded transition-colors"
                      title="Delete session"
                    >
                      Delete
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Footer */}
          <div className="p-4 border-t border-gray-700 text-xs text-gray-500">
            <p className="italic">
              Witness your belief frameworks evolve through time
            </p>
          </div>
        </div>
      </div>
    </>
  )
}

SessionSidebar.propTypes = {
  currentSessionId: PropTypes.string,
  onSessionSelect: PropTypes.func,
  onNewSession: PropTypes.func,
  isVisible: PropTypes.bool.isRequired,
  onToggleVisibility: PropTypes.func.isRequired,
}

export default SessionSidebar
