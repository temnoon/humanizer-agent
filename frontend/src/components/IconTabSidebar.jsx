import { useState, useEffect } from 'react'
import PropTypes from 'prop-types'
import axios from 'axios'
import LibraryBrowser from './LibraryBrowser'
import TransformationsLibrary from './TransformationsLibrary'
import BookBuilder from './BookBuilder'
import ImageGallery from './ImageGallery'
import ChunkBrowser from './ChunkBrowser'
import AgentConversationsLibrary from './AgentConversationsLibrary'
import ArtifactBrowser from './ArtifactBrowser'

/**
 * IconTabSidebar - Hierarchical navigation with icon tabs
 *
 * Features:
 * - Icon-based tab switching (Library, Sessions, Conversations, Messages)
 * - Hierarchical drillable navigation
 * - Resizable sidebar
 * - Search and filtering
 * - Mobile responsive
 */
function IconTabSidebar({
  visible,
  width,
  currentView,
  onViewChange,
  onResize,
  selectedCollection,
  selectedSession,
  selectedConversation,
  selectedMessage,
  onCollectionSelect,
  onSessionSelect,
  onConversationSelect,
  onMessageSelect,
  onBookSelect,
  onArtifactSelect,
  isMobile = false,
  onClose
}) {
  const [sessions, setSessions] = useState([])
  const [conversations, setConversations] = useState([])
  const [messages, setMessages] = useState([])
  const [searchQuery, setSearchQuery] = useState('')
  const [isResizing, setIsResizing] = useState(false)
  const [currentUserId, setCurrentUserId] = useState(null)

  const API_BASE = 'http://localhost:8000'

  // Initialize user
  useEffect(() => {
    const initUser = async () => {
      const storedUserId = localStorage.getItem('humanizer_user_id')
      if (storedUserId) {
        setCurrentUserId(storedUserId)
      } else {
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

  // Load data based on current view
  useEffect(() => {
    if (!currentUserId) return

    if (currentView === 'sessions') {
      loadSessions()
    } else if (currentView === 'conversations' && selectedSession) {
      loadConversations(selectedSession.id)
    } else if (currentView === 'messages' && selectedConversation) {
      loadMessages(selectedConversation.id)
    }
  }, [currentView, currentUserId, selectedSession, selectedConversation])

  const loadSessions = async () => {
    try {
      const response = await axios.get(`${API_BASE}/api/sessions`, {
        params: { user_id: currentUserId, limit: 100 }
      })
      setSessions(response.data)
    } catch (err) {
      console.error('Error loading sessions:', err)
    }
  }

  const loadConversations = async (sessionId) => {
    // Mock data for now - replace with actual API when available
    setConversations([
      {
        id: 'conv-1',
        title: 'Transformation Discussion',
        message_count: 15,
        updated_at: new Date().toISOString()
      },
      {
        id: 'conv-2',
        title: 'Philosophy Integration',
        message_count: 8,
        updated_at: new Date(Date.now() - 86400000).toISOString()
      }
    ])
  }

  const loadMessages = async (conversationId) => {
    try {
      const response = await fetch(`http://localhost:8000/api/library/conversations/${conversationId}/messages`)
      const data = await response.json()
      setMessages(data.messages || [])
    } catch (err) {
      console.error('Failed to load messages:', err)
      setMessages([])
    }
  }

  const handleMouseDown = (e) => {
    e.preventDefault()
    setIsResizing(true)
  }

  useEffect(() => {
    const handleMouseMove = (e) => {
      if (isResizing) {
        onResize(e.clientX)
      }
    }

    const handleMouseUp = () => {
      setIsResizing(false)
    }

    if (isResizing) {
      document.addEventListener('mousemove', handleMouseMove)
      document.addEventListener('mouseup', handleMouseUp)
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', handleMouseUp)
    }
  }, [isResizing, onResize])

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

  const tabs = [
    { id: 'library', icon: '📚', label: 'Library' },
    { id: 'transformations', icon: '🔧', label: 'Transformations' },
    { id: 'books', icon: '📖', label: 'Books' },
    { id: 'images', icon: '🖼️', label: 'Images' },
    { id: 'chunks', icon: '🧩', label: 'Chunks' },
    { id: 'artifacts', icon: '🗂️', label: 'Artifacts' },
    { id: 'agentConversations', icon: '🤖', label: 'Agent Conversations', separator: true },
    { id: 'personifier', icon: '✨', label: 'Personifier', separator: true },
    { id: 'embeddings', icon: '🧠', label: 'Embeddings', separator: true },
    { id: 'embeddingStats', icon: '📊', label: 'Embedding Stats' },
    { id: 'frameworks', icon: '🎭', label: 'Frameworks' },
    { id: 'clusterExplorer', icon: '🌌', label: 'Cluster Explorer' },
    { id: 'transformationLab', icon: '⚗️', label: 'Transformation Lab' },
    { id: 'sessions', icon: '🗂️', label: 'Sessions', separator: true },
    { id: 'conversations', icon: '💬', label: 'Conversations', disabled: !selectedSession },
    { id: 'messages', icon: '📝', label: 'Messages', disabled: !selectedConversation }
  ]

  const filterItems = (items, query) => {
    if (!query) return items
    const lowerQuery = query.toLowerCase()
    return items.filter(item =>
      item.title?.toLowerCase().includes(lowerQuery) ||
      item.content?.toLowerCase().includes(lowerQuery)
    )
  }

  if (!visible) return null

  return (
    <aside
      data-testid="sidebar"
      className="h-full bg-gray-900 border-r border-gray-800 flex"
    >
      {/* Icon Tab Bar */}
      <div className="w-14 bg-gray-950 border-r border-gray-800 flex flex-col items-center py-4 space-y-2">
        {tabs.map((tab, idx) => (
          <div key={tab.id}>
            {tab.separator && idx > 0 && (
              <div className="w-8 h-px bg-gray-700 my-2 mx-auto" />
            )}
            <button
              onClick={() => !tab.disabled && onViewChange(tab.id)}
              disabled={tab.disabled}
              className={`w-10 h-10 flex items-center justify-center rounded-lg transition-all ${
                currentView === tab.id
                  ? 'bg-realm-symbolic text-white'
                  : tab.disabled
                  ? 'text-gray-700 cursor-not-allowed'
                  : 'text-gray-400 hover:bg-gray-800 hover:text-white'
              }`}
              title={tab.label}
            >
              <span className="text-xl">{tab.icon}</span>
            </button>
          </div>
        ))}

        {/* Spacer */}
        <div className="flex-1" />

        {/* Settings */}
        <button
          className="w-10 h-10 flex items-center justify-center rounded-lg text-gray-400 hover:bg-gray-800 hover:text-white transition-all"
          title="Settings"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
        </button>
      </div>

      {/* Content Area */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header with Search */}
        <div className="p-4 border-b border-gray-800 flex-shrink-0">
          <h2 className="text-lg font-semibold text-white mb-3 capitalize">
            {currentView === 'conversations' && selectedSession && (
              <button
                onClick={() => onViewChange('sessions')}
                className="inline-flex items-center text-gray-400 hover:text-white mr-2"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
              </button>
            )}
            {currentView === 'messages' && selectedConversation && (
              <button
                onClick={() => onViewChange('conversations')}
                className="inline-flex items-center text-gray-400 hover:text-white mr-2"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
              </button>
            )}
            {currentView}
          </h2>

          <div className="relative">
            <input
              type="text"
              placeholder={`Search ${currentView}...`}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full px-3 py-2 pl-9 bg-gray-800 border border-gray-700 rounded-md text-sm text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-realm-symbolic"
            />
            <svg className="w-4 h-4 absolute left-3 top-2.5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
        </div>

        {/* List Content */}
        <div className="flex-1 overflow-y-auto">
          {currentView === 'library' && (
            <LibraryBrowser onSelect={onCollectionSelect} />
          )}

          {currentView === 'transformations' && (
            <TransformationsLibrary />
          )}

          {currentView === 'books' && (
            <BookBuilder onBookSelect={onBookSelect} />
          )}

          {currentView === 'images' && (
            <div className="p-4">
              <button
                onClick={() => {
                  // Signal to parent to open ImageBrowser in main pane
                  if (window.openImageBrowser) {
                    window.openImageBrowser();
                  }
                }}
                className="w-full px-4 py-3 bg-realm-symbolic hover:bg-realm-symbolic-light text-white rounded-lg font-medium transition-colors mb-4 flex items-center justify-center gap-2"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
                Open Full Image Browser
              </button>
              <ImageGallery selectedCollection={selectedCollection} />
            </div>
          )}

          {currentView === 'chunks' && (
            <ChunkBrowser
              onChunkSelect={(chunk) => {
                console.log('Chunk selected:', chunk);
              }}
              onNavigateToSource={(chunk) => {
                if (chunk.source?.collection_id) {
                  // Navigate to the conversation containing this chunk
                  onCollectionSelect({
                    id: chunk.source.collection_id,
                    title: chunk.source.collection_title
                  });
                }
              }}
            />
          )}

          {currentView === 'artifacts' && (
            <ArtifactBrowser
              onArtifactSelect={onArtifactSelect}
            />
          )}

          {currentView === 'agentConversations' && (
            <AgentConversationsLibrary
              onConversationSelect={(conversation) => {
                console.log('Agent conversation selected:', conversation);
                // TODO: Wire this to open the agent chat panel and load the conversation
                // This would need to communicate with Workstation to:
                // 1. Open the agent chat panel (setShowAgentChat(true))
                // 2. Load the conversation into AgentChat
              }}
            />
          )}

          {/* Personifier - Gateway Feature */}
          {currentView === 'personifier' && (
            <div className="p-4">
              <button
                onClick={() => {
                  if (window.openPersonifier) {
                    window.openPersonifier();
                  }
                }}
                className="w-full px-4 py-3 bg-realm-symbolic hover:bg-realm-symbolic-light text-white rounded-lg font-medium transition-colors flex items-center justify-center gap-2"
              >
                <span className="text-xl">✨</span>
                Open Personifier
              </button>
              <p className="text-sm text-gray-400 mt-3">
                Transform AI writing → conversational. Add "person-ness" through
                geometric transformation in semantic space.
              </p>
              <div className="mt-4 p-3 bg-gray-800 rounded-lg border border-gray-700">
                <h4 className="text-xs font-semibold text-gray-300 mb-2">What it does:</h4>
                <ul className="text-xs text-gray-400 space-y-1 list-disc list-inside">
                  <li>Detects AI patterns</li>
                  <li>Applies learned transformations</li>
                  <li>Shows conversational examples</li>
                  <li>Educational, not deception</li>
                </ul>
              </div>
            </div>
          )}

          {/* Embedding Features - Open in main pane */}
          {currentView === 'embeddingStats' && (
            <div className="p-4">
              <button
                onClick={() => {
                  if (window.openEmbeddingStats) {
                    window.openEmbeddingStats();
                  }
                }}
                className="w-full px-4 py-3 bg-realm-symbolic hover:bg-realm-symbolic-light text-white rounded-lg font-medium transition-colors flex items-center justify-center gap-2"
              >
                <span className="text-xl">📊</span>
                Open Embedding Statistics
              </button>
              <p className="text-sm text-gray-400 mt-3">
                View embedding coverage and quality metrics across your {' '}
                <span className="text-realm-symbolic font-semibold">125,799 embeddings</span>
              </p>
            </div>
          )}

          {currentView === 'frameworks' && (
            <div className="p-4">
              <button
                onClick={() => {
                  if (window.openFrameworks) {
                    window.openFrameworks();
                  }
                }}
                className="w-full px-4 py-3 bg-realm-symbolic hover:bg-realm-symbolic-light text-white rounded-lg font-medium transition-colors flex items-center justify-center gap-2"
              >
                <span className="text-xl">🎭</span>
                Discover Frameworks
              </button>
              <p className="text-sm text-gray-400 mt-3">
                Auto-discover belief frameworks through embedding clustering (UMAP + HDBSCAN)
              </p>
            </div>
          )}

          {currentView === 'clusterExplorer' && (
            <div className="p-4">
              <button
                onClick={() => {
                  if (window.openClusterExplorer) {
                    window.openClusterExplorer();
                  }
                }}
                className="w-full px-4 py-3 bg-realm-symbolic hover:bg-realm-symbolic-light text-white rounded-lg font-medium transition-colors flex items-center justify-center gap-2"
              >
                <span className="text-xl">🌌</span>
                Open 3D Cluster Explorer
              </button>
              <p className="text-sm text-gray-400 mt-3">
                Interactive 3D visualization of embeddings in semantic space
              </p>
            </div>
          )}

          {currentView === 'transformationLab' && (
            <div className="p-4">
              <button
                onClick={() => {
                  if (window.openTransformationLab) {
                    window.openTransformationLab();
                  }
                }}
                className="w-full px-4 py-3 bg-realm-symbolic hover:bg-realm-symbolic-light text-white rounded-lg font-medium transition-colors flex items-center justify-center gap-2"
              >
                <span className="text-xl">⚗️</span>
                Open Transformation Lab
              </button>
              <p className="text-sm text-gray-400 mt-3">
                Experiment with transformation arithmetic: "chunk + skeptical_vector = skeptical version"
              </p>
            </div>
          )}

          {currentView === 'embeddings' && (
            <div className="p-4">
              <h3 className="text-lg font-bold text-white mb-4">Embedding Tools</h3>
              <div className="space-y-2">
                <button
                  onClick={() => onViewChange('embeddingStats')}
                  className="w-full px-4 py-2 bg-gray-800 hover:bg-gray-700 text-white rounded-lg text-left transition-colors flex items-center gap-3"
                >
                  <span className="text-2xl">📊</span>
                  <span>Statistics</span>
                </button>
                <button
                  onClick={() => onViewChange('frameworks')}
                  className="w-full px-4 py-2 bg-gray-800 hover:bg-gray-700 text-white rounded-lg text-left transition-colors flex items-center gap-3"
                >
                  <span className="text-2xl">🎭</span>
                  <span>Frameworks</span>
                </button>
                <button
                  onClick={() => onViewChange('clusterExplorer')}
                  className="w-full px-4 py-2 bg-gray-800 hover:bg-gray-700 text-white rounded-lg text-left transition-colors flex items-center gap-3"
                >
                  <span className="text-2xl">🌌</span>
                  <span>3D Explorer</span>
                </button>
                <button
                  onClick={() => onViewChange('transformationLab')}
                  className="w-full px-4 py-2 bg-gray-800 hover:bg-gray-700 text-white rounded-lg text-left transition-colors flex items-center gap-3"
                >
                  <span className="text-2xl">⚗️</span>
                  <span>Transformation Lab</span>
                </button>
              </div>
            </div>
          )}

          {currentView === 'sessions' && (
            <div className="p-3 space-y-2">
              {filterItems(sessions, searchQuery).map(session => (
                <div
                  key={session.id}
                  onClick={() => onSessionSelect(session)}
                  className={`p-3 rounded-lg cursor-pointer transition-all ${
                    selectedSession?.id === session.id
                      ? 'bg-realm-symbolic/30 border border-realm-symbolic'
                      : 'hover:bg-gray-800 border border-transparent'
                  }`}
                >
                  <div className="text-sm font-medium text-white">{session.title}</div>
                  <div className="text-xs text-gray-400 mt-1">
                    {session.transformation_count} items • {formatDate(session.updated_at)}
                  </div>
                </div>
              ))}
            </div>
          )}

          {currentView === 'conversations' && (
            <div className="p-3 space-y-2">
              {filterItems(conversations, searchQuery).map(conv => (
                <div
                  key={conv.id}
                  onClick={() => onConversationSelect(conv)}
                  className={`p-3 rounded-lg cursor-pointer transition-all ${
                    selectedConversation?.id === conv.id
                      ? 'bg-realm-symbolic/30 border border-realm-symbolic'
                      : 'hover:bg-gray-800 border border-transparent'
                  }`}
                >
                  <div className="text-sm font-medium text-white">{conv.title}</div>
                  <div className="text-xs text-gray-400 mt-1">
                    {conv.message_count} messages • {formatDate(conv.updated_at)}
                  </div>
                </div>
              ))}
            </div>
          )}

          {currentView === 'messages' && (
            <div className="p-3 space-y-2">
              {filterItems(messages, searchQuery).map(msg => (
                <div
                  key={msg.id}
                  onClick={() => onMessageSelect(msg)}
                  className={`p-3 rounded-lg cursor-pointer transition-all ${
                    selectedMessage?.id === msg.id
                      ? 'bg-realm-symbolic/30 border border-realm-symbolic'
                      : 'hover:bg-gray-800 border border-transparent'
                  }`}
                >
                  <div className="text-sm text-white line-clamp-2">
                    {msg.content.substring(0, 100)}...
                  </div>
                  <div className="text-xs text-gray-400 mt-1">
                    {formatDate(msg.created_at)}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Resize Handle */}
      <div
        onMouseDown={handleMouseDown}
        className={`w-1 cursor-col-resize hover:bg-realm-symbolic transition-colors ${
          isResizing ? 'bg-realm-symbolic' : 'bg-transparent'
        }`}
      />
    </aside>
  )
}

IconTabSidebar.propTypes = {
  visible: PropTypes.bool.isRequired,
  width: PropTypes.number.isRequired,
  currentView: PropTypes.string.isRequired,
  onViewChange: PropTypes.func.isRequired,
  onResize: PropTypes.func.isRequired,
  selectedCollection: PropTypes.object,
  selectedSession: PropTypes.object,
  selectedConversation: PropTypes.object,
  selectedMessage: PropTypes.object,
  onCollectionSelect: PropTypes.func.isRequired,
  onSessionSelect: PropTypes.func.isRequired,
  onConversationSelect: PropTypes.func.isRequired,
  onMessageSelect: PropTypes.func.isRequired,
  onBookSelect: PropTypes.func,
  isMobile: PropTypes.bool,
  onClose: PropTypes.func,
}

export default IconTabSidebar
