import { useState, useEffect } from 'react'
import PropTypes from 'prop-types'
import IconTabSidebar from './IconTabSidebar'
import DocumentViewer from './DocumentViewer'
import ConversationViewer from './ConversationViewer'
import StyleConfigurator from './StyleConfigurator'
import TransformationPanel from './panels/TransformationPanel'
// import PhilosophyPanel from './panels/PhilosophyPanel'
import MadhyamakaPanel from './panels/MadhyamakaPanel'
import ArchivePanel from './panels/ArchivePanel'
import PipelinePanel from './panels/PipelinePanel'

/**
 * Workstation - Main full-screen layout component
 *
 * Zed-like professional workstation for text archaeology and transformation.
 * Features:
 * - Icon-based sidebar with hierarchical navigation
 * - Large document viewing/editing panel
 * - Split pane support for comparison
 * - Phrase flagging and highlighting
 * - Mobile responsive
 */
function Workstation() {
  const [sidebarVisible, setSidebarVisible] = useState(true)
  const [sidebarWidth, setSidebarWidth] = useState(450)
  const [currentView, setCurrentView] = useState('library') // sessions, library, conversations, messages
  const [selectedCollection, setSelectedCollection] = useState(null)
  const [selectedSession, setSelectedSession] = useState(null)
  const [selectedConversation, setSelectedConversation] = useState(null)
  const [selectedMessage, setSelectedMessage] = useState(null)
  const [splitView, setSplitView] = useState(false)
  const [secondaryDocument, setSecondaryDocument] = useState(null)
  const [showStyleConfig, setShowStyleConfig] = useState(false)
  const [isMobile, setIsMobile] = useState(false)

  // Panel states
  const [activePanel, setActivePanel] = useState(null) // 'transform', 'philosophy', 'madhyamaka', 'archive'

  // Current document state
  const [document, setDocument] = useState({
    content: '',
    type: 'markdown', // markdown, code, latex, text
    language: 'markdown',
    metadata: {}
  })

  // Detect mobile viewport
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768)
      if (window.innerWidth < 768) {
        setSidebarVisible(false)
      }
    }
    checkMobile()
    window.addEventListener('resize', checkMobile)
    return () => window.removeEventListener('resize', checkMobile)
  }, [])

  const handleSidebarResize = (newWidth) => {
    setSidebarWidth(Math.max(300, Math.min(800, newWidth)))
  }

  const handleCollectionSelect = (collection) => {
    setSelectedCollection(collection)
    // Load conversation data and display it
    setDocument({
      content: '', // Will be populated by ConversationViewer
      type: 'conversation',
      metadata: collection
    })
  }

  const handleSessionSelect = (session) => {
    setSelectedSession(session)
    setCurrentView('conversations')
  }

  const handleConversationSelect = (conversation) => {
    setSelectedConversation(conversation)
    setCurrentView('messages')
  }

  const handleMessageSelect = (message) => {
    setSelectedMessage(message)
    setDocument({
      content: message.content,
      type: message.type || 'markdown',
      language: message.language || 'markdown',
      metadata: message.metadata || {}
    })
  }

  const handleCompareDocument = (doc) => {
    setSecondaryDocument(doc)
    setSplitView(true)
  }

  const togglePanel = (panelName) => {
    setActivePanel(activePanel === panelName ? null : panelName)
  }

  const handleResultReady = (newDocument) => {
    setDocument(newDocument)
    setActivePanel(null) // Close panel after viewing result
  }

  return (
    <div className="h-screen w-screen flex overflow-hidden bg-gray-950 font-structural">
      {/* Icon Tab Sidebar */}
      <IconTabSidebar
        visible={sidebarVisible}
        width={isMobile ? Math.min(sidebarWidth, window.innerWidth - 40) : sidebarWidth}
        currentView={currentView}
        onViewChange={setCurrentView}
        onResize={handleSidebarResize}
        selectedCollection={selectedCollection}
        selectedSession={selectedSession}
        selectedConversation={selectedConversation}
        selectedMessage={selectedMessage}
        onCollectionSelect={handleCollectionSelect}
        onSessionSelect={handleSessionSelect}
        onConversationSelect={handleConversationSelect}
        onMessageSelect={handleMessageSelect}
        isMobile={isMobile}
        onClose={() => isMobile && setSidebarVisible(false)}
      />

      {/* Main Document Area */}
      <main
        className="flex-1 flex transition-all duration-300"
        style={{
          marginLeft: sidebarVisible ? `${sidebarWidth}px` : '0'
        }}
      >
        {/* Sidebar Toggle Button (when hidden) */}
        {!sidebarVisible && (
          <button
            onClick={() => setSidebarVisible(true)}
            className="fixed top-4 left-4 z-40 p-2 bg-realm-symbolic hover:bg-realm-symbolic-light text-white rounded-md shadow-lg transition-colors"
            aria-label="Show sidebar"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
        )}

        {/* Document Viewer(s) or Conversation Viewer */}
        {selectedCollection ? (
          <ConversationViewer
            collection={selectedCollection}
            onBack={() => setSelectedCollection(null)}
          />
        ) : !splitView ? (
          <DocumentViewer
            document={document}
            onDocumentChange={setDocument}
            onCompare={handleCompareDocument}
            selectedMessage={selectedMessage}
          />
        ) : (
          <div className="flex flex-1 divide-x divide-gray-800">
            <DocumentViewer
              document={document}
              onDocumentChange={setDocument}
              className="flex-1"
              splitMode={true}
            />
            <DocumentViewer
              document={secondaryDocument}
              className="flex-1"
              splitMode={true}
              readOnly={true}
            />
          </div>
        )}
      </main>

      {/* Split View Controls */}
      {splitView && (
        <button
          onClick={() => {
            setSplitView(false)
            setSecondaryDocument(null)
          }}
          className="fixed bottom-4 right-4 px-4 py-2 bg-realm-symbolic hover:bg-realm-symbolic-light text-white rounded-md shadow-lg transition-colors z-30"
        >
          Close Split View
        </button>
      )}

      {/* Function Panel Toolbar (right side) */}
      <div className="fixed right-4 top-1/2 -translate-y-1/2 flex flex-col space-y-2 z-30">
        <button
          onClick={() => togglePanel('transform')}
          className={`p-3 rounded-lg shadow-lg transition-all ${
            activePanel === 'transform'
              ? 'bg-realm-symbolic text-white scale-110'
              : 'bg-gray-800 text-gray-400 hover:bg-gray-700 hover:text-white'
          }`}
          title="Transform Text"
        >
          <span className="text-xl">🎭</span>
        </button>

        <button
          onClick={() => togglePanel('philosophy')}
          className={`p-3 rounded-lg shadow-lg transition-all ${
            activePanel === 'philosophy'
              ? 'bg-realm-symbolic text-white scale-110'
              : 'bg-gray-800 text-gray-400 hover:bg-gray-700 hover:text-white'
          }`}
          title="Philosophy & Perspectives"
        >
          <span className="text-xl">🔮</span>
        </button>

        <button
          onClick={() => togglePanel('madhyamaka')}
          className={`p-3 rounded-lg shadow-lg transition-all ${
            activePanel === 'madhyamaka'
              ? 'bg-realm-symbolic text-white scale-110'
              : 'bg-gray-800 text-gray-400 hover:bg-gray-700 hover:text-white'
          }`}
          title="Middle Path Detection"
        >
          <span className="text-xl">☯️</span>
        </button>

        <button
          onClick={() => togglePanel('archive')}
          className={`p-3 rounded-lg shadow-lg transition-all ${
            activePanel === 'archive'
              ? 'bg-realm-symbolic text-white scale-110'
              : 'bg-gray-800 text-gray-400 hover:bg-gray-700 hover:text-white'
          }`}
          title="Archive Analysis"
        >
          <span className="text-xl">🗄️</span>
        </button>

        <button
          onClick={() => togglePanel('pipeline')}
          className={`p-3 rounded-lg shadow-lg transition-all ${
            activePanel === 'pipeline'
              ? 'bg-realm-symbolic text-white scale-110'
              : 'bg-gray-800 text-gray-400 hover:bg-gray-700 hover:text-white'
          }`}
          title="Pipeline Operations"
        >
          <span className="text-xl">⚙️</span>
        </button>

        {/* Divider */}
        <div className="h-px bg-gray-700 my-2" />

        {/* Settings */}
        <button
          onClick={() => setShowStyleConfig(true)}
          className="p-3 bg-gray-800 text-gray-400 hover:bg-gray-700 hover:text-white rounded-lg shadow-lg transition-colors"
          title="Style Settings"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
          </svg>
        </button>
      </div>

      {/* Function Panels */}
      <TransformationPanel
        isOpen={activePanel === 'transform'}
        onClose={() => setActivePanel(null)}
        currentDocument={document}
        onResultReady={handleResultReady}
      />

      {/* <PhilosophyPanel
        isOpen={activePanel === 'philosophy'}
        onClose={() => setActivePanel(null)}
        currentDocument={document}
        onResultReady={handleResultReady}
      /> */}

      <MadhyamakaPanel
        isOpen={activePanel === 'madhyamaka'}
        onClose={() => setActivePanel(null)}
        currentDocument={document}
        onResultReady={handleResultReady}
      />

      <ArchivePanel
        isOpen={activePanel === 'archive'}
        onClose={() => setActivePanel(null)}
        currentDocument={document}
      />

      <PipelinePanel
        isOpen={activePanel === 'pipeline'}
        onClose={() => setActivePanel(null)}
        currentMessage={selectedMessage}
      />

      {/* Style Configurator Modal */}
      <StyleConfigurator
        isOpen={showStyleConfig}
        onClose={() => setShowStyleConfig(false)}
      />

      {/* Mobile Overlay */}
      {isMobile && sidebarVisible && (
        <div
          className="fixed inset-0 bg-black/50 z-20"
          onClick={() => setSidebarVisible(false)}
        />
      )}
    </div>
  )
}

Workstation.propTypes = {
  initialSession: PropTypes.object,
}

export default Workstation
