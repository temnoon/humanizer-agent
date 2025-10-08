import { useState, useEffect } from 'react'
import { useWorkspace } from '../contexts/WorkspaceContext'
import { useKeyboardShortcuts } from '../hooks/useKeyboardShortcuts'
import LayoutManager from './layout/LayoutManager'
import InterestList from './layout/InterestList'
import IconTabSidebar from './IconTabSidebar'
import DocumentViewer from './DocumentViewer'
import ConversationViewer from './ConversationViewer'
import MessageViewer from './MessageViewer'
import StyleConfigurator from './StyleConfigurator'
import SettingsModal from './SettingsModal'
import TransformationPanel from './panels/TransformationPanel'
import MadhyamakaPanel from './panels/MadhyamakaPanel'
import ArchivePanel from './panels/ArchivePanel'
import PipelinePanel from './panels/PipelinePanel'
import ImageBrowser from './ImageBrowser'
import BookViewer from './BookViewer'
import MarkdownEditorTab from './MarkdownEditorTab'

/**
 * Workstation - Simplified main layout using LayoutManager + WorkspaceContext
 *
 * REFACTORED VERSION:
 * - Uses LayoutManager for all pane management (no manual DOM manipulation)
 * - Uses WorkspaceContext for state (no scattered useState)
 * - Much simpler: ~250 lines instead of 492
 * - Single source of truth for tabs, navigation, preferences
 */
function Workstation() {
  // Get workspace state from context
  const {
    tabs,
    activeTabIndex,
    addTab,
    closeTab,
    switchToTab,
    navigateToNextTab,
    navigateToPrevTab,
    inspectorContent,
    showInspector,
    closeInspector
  } = useWorkspace()

  // Local UI state (not business logic)
  const [currentView, setCurrentView] = useState('library')
  const [activePanel, setActivePanel] = useState(null)
  const [showStyleConfig, setShowStyleConfig] = useState(false)
  const [showSettings, setShowSettings] = useState(false)
  const [isMobile, setIsMobile] = useState(false)
  const [sidebarWidth, setSidebarWidth] = useState(300)

  // Document state for legacy DocumentViewer (TODO: migrate to tabs)
  const [document, setDocument] = useState({
    content: '',
    type: 'markdown',
    language: 'markdown',
    metadata: {}
  })

  // Detect mobile viewport
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768)
    }
    checkMobile()
    window.addEventListener('resize', checkMobile)
    return () => window.removeEventListener('resize', checkMobile)
  }, [])

  // Global keyboard shortcuts
  useKeyboardShortcuts({
    onArrowLeft: tabs.length > 1 ? navigateToPrevTab : null,
    onArrowRight: tabs.length > 1 ? navigateToNextTab : null,
    onEscape: activePanel ? () => setActivePanel(null) : null,
    enabled: true
  })

  // Expose ImageBrowser opener to sidebar (temporary until sidebar uses context)
  useEffect(() => {
    window.openImageBrowser = () => {
      addTab('imageBrowser', '🖼️ Image Browser', {})
    }
    return () => {
      delete window.openImageBrowser
    }
  }, [addTab])

  // Handlers for sidebar (these will be simplified when sidebar uses context)
  const handleCollectionSelect = (collection) => {
    addTab('conversation', collection.title || 'Conversation', { collection })
  }

  const handleBookSelect = (book) => {
    addTab('book', book.title || 'Book', { book })
  }

  const handleMessageSelect = (message) => {
    setDocument({
      content: message.content,
      type: message.type || 'markdown',
      language: message.language || 'markdown',
      metadata: message.metadata || {}
    })
  }

  const handleSessionSelect = (session) => {
    // Session support coming soon
    console.log('Session selected:', session)
  }

  const handleConversationSelect = (conversation) => {
    // Conversation support coming soon
    console.log('Conversation selected:', conversation)
  }

  const handleSidebarResize = (newWidth) => {
    setSidebarWidth(Math.max(200, Math.min(600, newWidth)))
  }

  const togglePanel = (panelName) => {
    setActivePanel(activePanel === panelName ? null : panelName)
  }

  const handleResultReady = (newDocument) => {
    setDocument(newDocument)
    setActivePanel(null)
  }

  // Render active tab content
  const renderTabContent = () => {
    if (activeTabIndex < 0 || activeTabIndex >= tabs.length) {
      // No tabs open - show default DocumentViewer
      return (
        <DocumentViewer
          document={document}
          onDocumentChange={setDocument}
        />
      )
    }

    const activeTab = tabs[activeTabIndex]

    switch (activeTab.type) {
      case 'book':
        return (
          <BookViewer
            bookId={activeTab.data.book.id}
            onClose={() => closeTab(activeTabIndex)}
          />
        )

      case 'imageBrowser':
        return (
          <ImageBrowser
            onNavigateToConversation={(conversation) => {
              addTab('conversation', conversation.title || 'Conversation', { collection: conversation })
            }}
            onNavigateToTransformation={(transform) => {
              // TODO: Add transformation tab
              console.log('Navigate to transformation:', transform)
            }}
          />
        )

      case 'conversation':
        return (
          <ConversationViewer
            collection={activeTab.data.collection}
            onBack={() => closeTab(activeTabIndex)}
          />
        )

      case 'document':
        return (
          <DocumentViewer
            document={activeTab.data.document || document}
            onDocumentChange={setDocument}
          />
        )

      case 'markdownEditor':
        return (
          <MarkdownEditorTab
            content={activeTab.data.content || ''}
            onChange={(newContent) => {
              // Update tab data with new content
              const updatedTabs = [...tabs];
              updatedTabs[activeTabIndex].data.content = newContent;
              // This would need to integrate with workspace context to persist
            }}
            metadata={activeTab.data.metadata || {}}
            title={activeTab.label}
            readOnly={activeTab.data.readOnly || false}
          />
        )

      default:
        return (
          <div className="flex items-center justify-center h-full text-gray-500">
            <div className="text-center">
              <div className="text-6xl mb-4">📄</div>
              <div className="text-xl">Unknown tab type: {activeTab.type}</div>
            </div>
          </div>
        )
    }
  }

  // Render inspector pane content
  const renderInspectorContent = () => {
    if (!inspectorContent) return null;

    switch (inspectorContent.type) {
      case 'message':
        return (
          <MessageViewer
            message={inspectorContent.data.message}
            messages={inspectorContent.data.messages || []}
            onNavigate={(newMessage) => {
              showInspector('message', {
                message: newMessage,
                messages: inspectorContent.data.messages
              });
            }}
            onClose={closeInspector}
            onPipelineOpen={inspectorContent.data.onPipelineOpen}
            onAddToBook={inspectorContent.data.onAddToBook}
          />
        );

      default:
        return (
          <div className="flex items-center justify-center h-full text-gray-500">
            <div className="text-center">
              <div className="text-6xl mb-4">🔍</div>
              <div className="text-xl">Unknown inspector type: {inspectorContent.type}</div>
            </div>
          </div>
        );
    }
  };

  // Render sidebar
  const sidebarContent = (
    <IconTabSidebar
      visible={true}
      width={sidebarWidth}
      currentView={currentView}
      onViewChange={setCurrentView}
      onResize={handleSidebarResize}
      onCollectionSelect={handleCollectionSelect}
      onSessionSelect={handleSessionSelect}
      onConversationSelect={handleConversationSelect}
      onMessageSelect={handleMessageSelect}
      onBookSelect={handleBookSelect}
      isMobile={isMobile}
    />
  )

  // Render main content (tabs + active content)
  const mainContent = (
    <div className="h-full flex flex-col bg-gray-950">
      {/* Interest List (collapsible breadcrumb trail) */}
      <InterestList />

      {/* Tab Bar */}
      {tabs.length > 0 && (
        <div className="flex-none bg-gray-900 border-b border-gray-800 flex items-center">
          {/* Prev/Next Navigation */}
          <button
            onClick={navigateToPrevTab}
            disabled={tabs.length <= 1}
            className="px-3 py-2 hover:bg-gray-800 disabled:opacity-30 disabled:cursor-not-allowed transition-colors border-r border-gray-800"
            title="Previous tab"
          >
            <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </button>
          <button
            onClick={navigateToNextTab}
            disabled={tabs.length <= 1}
            className="px-3 py-2 hover:bg-gray-800 disabled:opacity-30 disabled:cursor-not-allowed transition-colors border-r border-gray-800"
            title="Next tab"
          >
            <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </button>

          {/* Tab List */}
          <div className="flex-1 flex overflow-x-auto">
            {tabs.map((tab, index) => (
              <div
                key={tab.id}
                className={`flex items-center gap-2 px-4 py-2 border-r border-gray-800 cursor-pointer transition-colors ${
                  index === activeTabIndex
                    ? 'bg-gray-800 text-white'
                    : 'text-gray-400 hover:bg-gray-850 hover:text-gray-300'
                }`}
                onClick={() => switchToTab(index)}
              >
                <span className="text-sm whitespace-nowrap truncate max-w-[200px]">
                  {tab.title}
                </span>
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    closeTab(index)
                  }}
                  className="text-gray-500 hover:text-white"
                  title="Close tab"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            ))}
          </div>

          {/* Settings Button */}
          <button
            onClick={() => setShowSettings(true)}
            className="px-3 py-2 hover:bg-gray-800 transition-colors border-l border-gray-800"
            title="Settings"
          >
            <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
          </button>
        </div>
      )}

      {/* Active Tab Content */}
      <div className="flex-1 overflow-hidden">
        {renderTabContent()}
      </div>
    </div>
  )

  return (
    <>
      <LayoutManager
        sidebar={sidebarContent}
        mainContent={mainContent}
        showPreview={false}
        showInspector={!!inspectorContent}
        inspectorPane={renderInspectorContent()}
      />

      {/* Function Panel Toolbar (right side overlays - kept as-is) */}
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

      {/* Function Panels (overlays) */}
      <TransformationPanel
        isOpen={activePanel === 'transform'}
        onClose={() => setActivePanel(null)}
        currentDocument={document}
        onResultReady={handleResultReady}
      />

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
      />

      {/* Style Configurator Modal */}
      <StyleConfigurator
        isOpen={showStyleConfig}
        onClose={() => setShowStyleConfig(false)}
      />

      {/* Settings Modal */}
      <SettingsModal
        isOpen={showSettings}
        onClose={() => setShowSettings(false)}
      />
    </>
  )
}

export default Workstation
