import { useState, useEffect } from 'react'
import { Panel, PanelGroup, PanelResizeHandle } from 'react-resizable-panels'
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
import ImageViewer from './ImageViewer'
import BookViewer from './BookViewer'
import MarkdownEditorTab from './MarkdownEditorTab'
import ComparisonViewer from './ComparisonViewer'
import EmbeddingStats from './EmbeddingStats'
import FrameworkBrowser from './FrameworkBrowser'
import ClusterExplorer from './ClusterExplorer'
import TransformationLab from './TransformationLab'
import ChunkBrowser from './ChunkBrowser'
import LibraryBrowser from './LibraryBrowser'
import AgentChat from './AgentChat'
import Personifier from './Personifier'

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
    updateTabData,
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
  const [showAgentChat, setShowAgentChat] = useState(false)

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

  // Agent chat toggle shortcut (Cmd+`)
  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === '`') {
        e.preventDefault()
        setShowAgentChat(prev => !prev)
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [])

  // Expose openers to sidebar (temporary until sidebar uses context)
  useEffect(() => {
    window.openImageBrowser = () => {
      addTab('imageBrowser', '🖼️ Image Browser', {})
    }
    window.openEmbeddingStats = () => {
      addTab('embeddingStats', '📊 Embedding Statistics', {})
    }
    window.openFrameworks = () => {
      addTab('frameworks', '🎭 Frameworks', {})
    }
    window.openClusterExplorer = () => {
      addTab('clusterExplorer', '🌌 Cluster Explorer', {})
    }
    window.openTransformationLab = () => {
      addTab('transformationLab', '⚗️ Transformation Lab', {})
    }
    window.openPersonifier = () => {
      addTab('personifier', '✨ Personifier', {})
    }
    return () => {
      delete window.openImageBrowser
      delete window.openEmbeddingStats
      delete window.openFrameworks
      delete window.openClusterExplorer
      delete window.openTransformationLab
      delete window.openPersonifier
    }
  }, [addTab])

  // Handlers for sidebar (these will be simplified when sidebar uses context)
  const handleCollectionSelect = (collection) => {
    addTab('conversation', collection.title || 'Conversation', { collection })
  }

  const handleBookSelect = (book) => {
    addTab('book', book.title || 'Book', { book })
  }

  const handleArtifactSelect = (artifact) => {
    addTab('artifact', `${artifact.artifact_type}: ${artifact.operation}`, { artifact })
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
    setActivePanel(activePanel === panelName ? null : panelName);
  }

  const handleResultReady = (newDocument) => {
    // Get the original content from the active tab (if it's a markdownEditor)
    const originalContent = activeTabIndex >= 0 && tabs[activeTabIndex]?.type === 'markdownEditor'
      ? tabs[activeTabIndex].data.content || ''
      : document.content || '';

    // Open comparison view in a new tab
    addTab('comparison', `Transformation: ${newDocument.metadata?.persona || 'Result'}`, {
      originalContent: originalContent,
      transformedContent: newDocument.content,
      transformationMetadata: newDocument.metadata || {}
    });

    // Close the transform panel
    setActivePanel(null);
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
            title={activeTab.title}
            readOnly={activeTab.data.readOnly || false}
            // Navigation props (for message/image/chunk lists)
            messageList={activeTab.data.messageList}
            currentIndex={activeTab.data.currentIndex}
            conversationData={activeTab.data.conversationData}
            onNavigate={(newContent, newMetadata, newTitle, newIndex) => {
              // Update current tab with new message content via context
              updateTabData(activeTabIndex, {
                title: newTitle,
                data: {
                  content: newContent,
                  metadata: newMetadata,
                  currentIndex: newIndex
                }
              });
            }}
          />
        )

      case 'artifact':
        const artifact = activeTab.data.artifact;
        return (
          <div className="h-full overflow-y-auto bg-base-200 p-6">
            <div className="max-w-4xl mx-auto space-y-4">
              {/* Header */}
              <div className="card bg-base-100 shadow-lg">
                <div className="card-body">
                  <h2 className="card-title text-2xl">{artifact.artifact_type}</h2>
                  <p className="text-base-content/70">{artifact.operation}</p>
                </div>
              </div>

              {/* Metadata */}
              <div className="card bg-base-100 shadow-lg">
                <div className="card-body">
                  <h3 className="text-lg font-semibold mb-3">Metadata</h3>
                  <div className="grid grid-cols-2 gap-3 text-sm">
                    <div><strong>Type:</strong> {artifact.artifact_type}</div>
                    <div><strong>Operation:</strong> {artifact.operation}</div>
                    <div><strong>Created:</strong> {new Date(artifact.created_at).toLocaleString()}</div>
                    <div><strong>Format:</strong> {artifact.content_format}</div>
                    {artifact.token_count && <div><strong>Tokens:</strong> {artifact.token_count}</div>}
                    {artifact.generation_model && <div><strong>Model:</strong> {artifact.generation_model}</div>}
                  </div>
                  {artifact.topics && artifact.topics.length > 0 && (
                    <div className="mt-3">
                      <strong>Topics:</strong>
                      <div className="flex flex-wrap gap-2 mt-2">
                        {artifact.topics.map((topic, idx) => (
                          <span key={idx} className="badge badge-primary">{topic}</span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Content */}
              <div className="card bg-base-100 shadow-lg">
                <div className="card-body">
                  <h3 className="text-lg font-semibold mb-3">Content</h3>
                  <div className="prose prose-sm max-w-none">
                    <pre className="whitespace-pre-wrap bg-base-200 p-4 rounded text-sm font-mono">
                      {artifact.content}
                    </pre>
                  </div>
                </div>
              </div>

              {/* Operation Parameters */}
              {artifact.source_operation_params && Object.keys(artifact.source_operation_params).length > 0 && (
                <div className="card bg-base-100 shadow-lg">
                  <div className="card-body">
                    <h3 className="text-lg font-semibold mb-3">Operation Parameters</h3>
                    <pre className="bg-base-200 p-4 rounded text-xs overflow-x-auto">
                      {JSON.stringify(artifact.source_operation_params, null, 2)}
                    </pre>
                  </div>
                </div>
              )}
            </div>
          </div>
        )

      case 'image':
        return (
          <ImageViewer
            image={activeTab.data.image}
            imageList={activeTab.data.imageList}
            currentIndex={activeTab.data.currentIndex}
            onNavigate={(newImage, newIndex, newMetadata) => {
              // Update current tab with new image via context
              updateTabData(activeTabIndex, {
                title: newImage.filename || 'Image',
                data: {
                  image: newImage,
                  imageList: activeTab.data.imageList,
                  currentIndex: newIndex,
                  metadata: newMetadata
                }
              });
            }}
          />
        )

      case 'embeddingStats':
        return <EmbeddingStats />

      case 'frameworks':
        return <FrameworkBrowser />

      case 'clusterExplorer':
        return <ClusterExplorer />

      case 'transformationLab':
        return <TransformationLab />

      case 'chunks':
        return (
          <ChunkBrowser
            onChunkSelect={(chunk) => {
              console.log('Chunk selected:', chunk);
            }}
            onNavigateToSource={(chunk) => {
              if (chunk.source?.collection_id) {
                addTab('conversation', chunk.source.collection_title || 'Conversation', {
                  collection: {
                    id: chunk.source.collection_id,
                    title: chunk.source.collection_title
                  }
                });
              }
            }}
          />
        )

      case 'library':
        return (
          <LibraryBrowser
            onSelect={(collection) => {
              addTab('conversation', collection.title || 'Conversation', { collection });
            }}
          />
        )

      case 'comparison':
        return (
          <ComparisonViewer
            originalContent={activeTab.data.originalContent || ''}
            transformedContent={activeTab.data.transformedContent || ''}
            transformationMetadata={activeTab.data.transformationMetadata || {}}
            title={activeTab.title}
            evaluationMode={activeTab.data.transformationMetadata?.needsEvaluation || false}
            onFeedbackSubmitted={(feedback) => {
              console.log('Feedback submitted:', feedback);
              // Could add notification here or update tab title
            }}
          />
        )

      case 'personifier':
        return <Personifier />

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
      onArtifactSelect={handleArtifactSelect}
      isMobile={isMobile}
    />
  )

  // Render main content (tabs + active content)
  const mainContent = (
    <div className="h-full flex flex-col bg-gray-950">
      {/* Interest List (collapsible breadcrumb trail) */}
      <InterestList />

      {/* Tab Bar - Always visible (contains Agent Chat toggle) */}
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

        {/* Agent Chat Toggle Button */}
        <button
          onClick={() => setShowAgentChat(prev => !prev)}
          className={`px-3 py-2 transition-colors border-l border-gray-800 ${
            showAgentChat
              ? 'bg-realm-accent text-white'
              : 'text-gray-400 hover:bg-gray-800 hover:text-white'
          }`}
          title="Agent Chat (Cmd+`)"
        >
          <span className="text-lg">🤖</span>
        </button>

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

      {/* Main Content Area with Vertical Split (Tab Content | Agent Chat) */}
      <div className="flex-1 overflow-hidden">
        {showAgentChat ? (
          <PanelGroup direction="vertical">
            {/* Top: Active Tab Content */}
            <Panel defaultSize={75} minSize={30}>
              <div className="h-full overflow-hidden">
                {renderTabContent()}
              </div>
            </Panel>

            <PanelResizeHandle className="h-1 hover:h-2 bg-gray-800 hover:bg-realm-accent transition-all cursor-row-resize" />

            {/* Bottom: Agent Chat */}
            <Panel defaultSize={25} minSize={15} maxSize={50}>
              <AgentChat />
            </Panel>
          </PanelGroup>
        ) : (
          <div className="h-full overflow-hidden">
            {renderTabContent()}
          </div>
        )}
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
        currentDocument={
          // Get content from active tab if it's a markdownEditor, otherwise use legacy document
          activeTabIndex >= 0 && tabs[activeTabIndex]?.type === 'markdownEditor'
            ? {
                content: tabs[activeTabIndex].data.content || '',
                type: 'markdown',
                metadata: tabs[activeTabIndex].data.metadata || {}
              }
            : document
        }
        onResultReady={handleResultReady}
      />

      <MadhyamakaPanel
        isOpen={activePanel === 'madhyamaka'}
        onClose={() => setActivePanel(null)}
        currentDocument={
          // Get content from active tab if it's a markdownEditor, otherwise use legacy document
          activeTabIndex >= 0 && tabs[activeTabIndex]?.type === 'markdownEditor'
            ? {
                content: tabs[activeTabIndex].data.content || '',
                type: 'markdown',
                metadata: tabs[activeTabIndex].data.metadata || {}
              }
            : document
        }
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
