import { useState, useEffect } from 'react';
import axios from 'axios';
import PropTypes from 'prop-types';
import MessageLightbox from './MessageLightbox';
import PipelinePanel from './panels/PipelinePanel';
import BookSectionSelector from './modals/BookSectionSelector';

/**
 * ConversationViewer Component
 *
 * Displays a full conversation from the library with:
 * - Metadata page (title, dates, model, Custom GPTs used)
 * - List of all messages with full content
 * - Editable gizmo_id names (double-click to edit)
 * - Navigation and search within conversation
 */
export default function ConversationViewer({ collection, onBack }) {
  const [conversationData, setConversationData] = useState(null);
  const [gizmoMappings, setGizmoMappings] = useState({});
  const [gizmoInfo, setGizmoInfo] = useState([]);
  const [editingGizmo, setEditingGizmo] = useState(null);
  const [editValue, setEditValue] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [userId, setUserId] = useState(null);
  const [showMetadata, setShowMetadata] = useState(true);
  const [lightboxMessage, setLightboxMessage] = useState(null);
  const [showSystemMessages, setShowSystemMessages] = useState(false);
  const [expandedToolMessages, setExpandedToolMessages] = useState(new Set());
  const [showPipelinePanel, setShowPipelinePanel] = useState(false);
  const [pipelineMessage, setPipelineMessage] = useState(null);
  const [showBookSelector, setShowBookSelector] = useState(false);
  const [bookSelectorData, setBookSelectorData] = useState({ message: null, chunks: null });

  // Get user ID from localStorage
  useEffect(() => {
    const storedUserId = localStorage.getItem('humanizer_user_id');
    setUserId(storedUserId);
  }, []);

  // Load conversation data
  useEffect(() => {
    if (collection && userId) {
      loadConversation();
      loadGizmoMappings();
      loadGizmoInfo();
    }
  }, [collection, userId]);

  const loadConversation = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get(`/api/library/collections/${collection.id}`, {
        params: { include_chunks: true }
      });
      setConversationData(response.data);
    } catch (err) {
      setError('Failed to load conversation');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const loadGizmoMappings = async () => {
    if (!userId) return;

    try {
      const response = await axios.get('/api/gizmos/mappings', {
        params: { user_id: userId }
      });
      setGizmoMappings(response.data);
    } catch (err) {
      console.error('Failed to load gizmo mappings:', err);
    }
  };

  const loadGizmoInfo = async () => {
    if (!userId || !collection) return;

    try {
      const response = await axios.get('/api/gizmos/info', {
        params: {
          user_id: userId,
          collection_id: collection.id
        }
      });
      setGizmoInfo(response.data);
    } catch (err) {
      console.error('Failed to load gizmo info:', err);
    }
  };

  const handleGizmoDoubleClick = (gizmoId) => {
    setEditingGizmo(gizmoId);
    setEditValue(gizmoMappings[gizmoId] || '');
  };

  const handleGizmoSave = async () => {
    if (!editingGizmo || !userId) return;

    try {
      const response = await axios.put(
        '/api/gizmos/mappings',
        {
          gizmo_id: editingGizmo,
          custom_name: editValue
        },
        {
          params: { user_id: userId }
        }
      );

      setGizmoMappings(response.data);
      setEditingGizmo(null);
      setEditValue('');

      // Reload gizmo info to reflect changes
      loadGizmoInfo();
    } catch (err) {
      console.error('Failed to save gizmo mapping:', err);
      alert('Failed to save custom name. Please try again.');
    }
  };

  const handleGizmoCancel = () => {
    setEditingGizmo(null);
    setEditValue('');
  };

  const getGizmoDisplay = (gizmoId) => {
    return gizmoMappings[gizmoId] || gizmoId;
  };

  const getRoleIcon = (role) => {
    const icons = {
      user: '👤',
      assistant: '🤖',
      system: '⚙️',
      tool: '🔧'
    };
    return icons[role] || '💬';
  };

  const hasToolContent = (message) => {
    // Check if tool message has meaningful content
    if (message.role !== 'tool') return false;

    // Check for images in metadata
    if (message.metadata?.attachments && message.metadata.attachments.length > 0) {
      return true;
    }

    // Check if there's actual content
    if (message.summary && message.summary.trim().length > 0) {
      return true;
    }

    return false;
  };

  const toggleToolMessage = (messageId) => {
    setExpandedToolMessages(prev => {
      const newSet = new Set(prev);
      if (newSet.has(messageId)) {
        newSet.delete(messageId);
      } else {
        newSet.add(messageId);
      }
      return newSet;
    });
  };

  const handlePipelineOpen = (message) => {
    setPipelineMessage(message);
    setShowPipelinePanel(true);
  };

  const handleAddToBook = (message, chunks) => {
    setBookSelectorData({ message, chunks });
    setShowBookSelector(true);
  };

  const handleBookSelectorSuccess = (book, section) => {
    console.log('Content added to book:', book.title, 'section:', section.title);
    // Optionally show success message
  };

  const shouldShowMessage = (message) => {
    // Always show user and assistant messages
    if (message.role === 'user' || message.role === 'assistant') {
      return true;
    }

    // Show system/tool messages only if toggle is on
    return showSystemMessages;
  };

  const getFilteredMessages = () => {
    if (!messages) return [];
    return messages.filter(shouldShowMessage);
  };

  /**
   * Parse message content and extract renderable elements
   * - Checks metadata.attachments for images first (PRIORITY)
   * - Detects image references in content and hides JSON
   * - Extracts text/markdown from JSON structures
   * - Returns raw text if not JSON
   */
  const parseMessageContent = (content, message) => {
    // PRIORITY 1: Check metadata.attachments for images FIRST
    // If we have an image attachment, show ONLY the image, hide any JSON content
    if (message?.metadata?.attachments && message.metadata.attachments.length > 0) {
      const imageAttachment = message.metadata.attachments.find(
        att => att.id && (att.id.startsWith('file-') || att.name?.match(/\.(jpg|jpeg|png|gif|webp)$/i))
      );

      if (imageAttachment) {
        return {
          type: 'image',
          url: `http://localhost:8000/api/library/media/${imageAttachment.id}/file`,
          width: imageAttachment.width,
          height: imageAttachment.height,
          size: imageAttachment.size
        };
      }
    }

    // No content to parse
    if (!content || typeof content !== 'string') {
      return null;
    }

    // PRIORITY 2: Check for Python dict representation of image_asset_pointer
    if (content.includes("'image_asset_pointer'") && content.includes("'asset_pointer'")) {
      // Extract file ID using regex
      const match = content.match(/['"]asset_pointer['"]\s*:\s*['"]file-service:\/\/([^'"]+)['"]/);
      if (match) {
        const fileId = match[1];
        return {
          type: 'image',
          url: `http://localhost:8000/api/library/media/${fileId}/file`,
          width: null,
          height: null,
          size: null
        };
      }
    }

    // PRIORITY 3: Try to parse as JSON
    let parsed;
    try {
      parsed = JSON.parse(content.trim());
    } catch (e) {
      // Not JSON, return as-is
      return { type: 'text', content };
    }

    // Check if it's an image_asset_pointer JSON
    if (parsed.content_type === 'image_asset_pointer' && parsed.asset_pointer) {
      const fileId = parsed.asset_pointer.replace(/^file-service:\/\//, '').replace(/^file-/, '');
      return {
        type: 'image',
        url: `http://localhost:8000/api/library/media/file-${fileId}/file`,
        width: parsed.width,
        height: parsed.height,
        size: parsed.size_bytes
      };
    }

    // Check for text content in various JSON structures
    if (parsed.text) {
      return { type: 'text', content: parsed.text };
    }
    if (parsed.content) {
      return { type: 'text', content: parsed.content };
    }

    // Check for HTML/CSS content
    if (parsed.html || parsed.css) {
      return {
        type: 'code',
        language: parsed.html ? 'html' : 'css',
        content: parsed.html || parsed.css
      };
    }

    // Default: return JSON string
    return { type: 'json', content: JSON.stringify(parsed, null, 2) };
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Unknown date';
    const date = new Date(dateString);
    return date.toLocaleString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className="flex flex-col h-full items-center justify-center bg-gray-950 text-white">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mb-4"></div>
        <p className="text-gray-400">Loading conversation...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col h-full items-center justify-center bg-gray-950 text-white p-8">
        <div className="bg-red-900/50 border border-red-700 rounded-lg p-6 max-w-md">
          <h3 className="text-lg font-semibold mb-2">Error Loading Conversation</h3>
          <p className="text-sm text-gray-300">{error}</p>
          <button
            onClick={onBack}
            className="mt-4 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded text-sm"
          >
            ← Back to Library
          </button>
        </div>
      </div>
    );
  }

  if (!conversationData) {
    return null;
  }

  const { collection: collectionData, messages } = conversationData;

  return (
    <div className="flex flex-col h-full bg-gray-950 text-white overflow-hidden">
      {/* Header */}
      <div className="bg-gray-900 border-b border-gray-800 p-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button
            onClick={onBack}
            className="p-2 hover:bg-gray-800 rounded transition-colors"
            title="Back to Library"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </button>
          <div>
            <h1 className="text-xl font-bold">{collectionData.title}</h1>
            <p className="text-sm text-gray-400">
              {messages.length} messages • {formatDate(collectionData.original_date || collectionData.created_at)}
            </p>
          </div>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setShowSystemMessages(!showSystemMessages)}
            className="px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded text-sm transition-colors"
            title={showSystemMessages ? 'Hide system/tool messages' : 'Show system/tool messages'}
          >
            {showSystemMessages ? '⚙️ Hide' : '⚙️ Show'} System
          </button>
          <button
            onClick={() => setShowMetadata(!showMetadata)}
            className="px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded text-sm transition-colors"
          >
            {showMetadata ? '📋 Hide' : '📋 Show'} Metadata
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto">
        {/* Metadata Page */}
        {showMetadata && (
          <div className="max-w-4xl mx-auto p-8">
            <div className="bg-gray-900 border border-gray-800 rounded-lg p-6 mb-6">
              <h2 className="text-2xl font-bold mb-4">{collectionData.title}</h2>

              {collectionData.description && (
                <p className="text-gray-300 mb-6">{collectionData.description}</p>
              )}

              <div className="grid grid-cols-2 gap-4 mb-6">
                <div>
                  <h3 className="text-sm font-semibold text-gray-400 mb-2">Platform</h3>
                  <p className="text-white">{collectionData.source_platform}</p>
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-gray-400 mb-2">Type</h3>
                  <p className="text-white capitalize">{collectionData.collection_type}</p>
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-gray-400 mb-2">Original Date</h3>
                  <p className="text-white">{formatDate(collectionData.original_date)}</p>
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-gray-400 mb-2">Imported</h3>
                  <p className="text-white">{formatDate(collectionData.import_date)}</p>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4 mb-6">
                <div>
                  <h3 className="text-sm font-semibold text-gray-400 mb-2">Messages</h3>
                  <p className="text-white">{collectionData.message_count}</p>
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-gray-400 mb-2">Chunks</h3>
                  <p className="text-white">{collectionData.chunk_count}</p>
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-gray-400 mb-2">Words</h3>
                  <p className="text-white">{collectionData.word_count?.toLocaleString() || 'N/A'}</p>
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-gray-400 mb-2">Tokens</h3>
                  <p className="text-white">{collectionData.total_tokens?.toLocaleString() || 'N/A'}</p>
                </div>
              </div>

              {/* Metadata fields */}
              {collectionData.metadata && Object.keys(collectionData.metadata).length > 0 && (
                <div className="mb-6">
                  <h3 className="text-sm font-semibold text-gray-400 mb-2">Metadata</h3>
                  <div className="bg-gray-800 rounded p-4 space-y-2">
                    {Object.entries(collectionData.metadata).map(([key, value]) => (
                      <div key={key} className="flex items-start gap-2">
                        <span className="text-gray-400 text-sm">{key}:</span>
                        <span className="text-gray-200 text-sm flex-1">
                          {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Custom GPTs Used */}
              {gizmoInfo.length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold mb-3">Custom GPTs Used in this Conversation</h3>
                  <div className="space-y-2">
                    {gizmoInfo.map((gizmo) => (
                      <div
                        key={gizmo.gizmo_id}
                        className="bg-gray-800 rounded-lg p-4 border border-gray-700"
                      >
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex-1">
                            {editingGizmo === gizmo.gizmo_id ? (
                              <div className="flex gap-2">
                                <input
                                  type="text"
                                  value={editValue}
                                  onChange={(e) => setEditValue(e.target.value)}
                                  className="flex-1 px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white text-sm focus:outline-none focus:border-blue-500"
                                  placeholder="Enter Custom GPT name"
                                  autoFocus
                                  onKeyDown={(e) => {
                                    if (e.key === 'Enter') handleGizmoSave();
                                    if (e.key === 'Escape') handleGizmoCancel();
                                  }}
                                />
                                <button
                                  onClick={handleGizmoSave}
                                  className="px-3 py-2 bg-blue-600 hover:bg-blue-700 rounded text-sm transition-colors"
                                >
                                  Save
                                </button>
                                <button
                                  onClick={handleGizmoCancel}
                                  className="px-3 py-2 bg-gray-600 hover:bg-gray-500 rounded text-sm transition-colors"
                                >
                                  Cancel
                                </button>
                              </div>
                            ) : (
                              <div
                                onDoubleClick={() => handleGizmoDoubleClick(gizmo.gizmo_id)}
                                className="cursor-pointer hover:bg-gray-700 rounded px-2 py-1 -mx-2 transition-colors select-none"
                                title="Double-click to edit name"
                                style={{ userSelect: 'none' }}
                              >
                                <span className="text-lg font-medium">
                                  {gizmo.custom_name ? (
                                    <>
                                      🤖 {gizmo.custom_name}
                                      <span className="text-xs text-gray-500 ml-2">({gizmo.gizmo_id})</span>
                                    </>
                                  ) : (
                                    <>
                                      <span className="text-gray-400">Gizmo ID:</span> {gizmo.gizmo_id}
                                      <span className="text-xs text-blue-400 ml-2">(double-click to name)</span>
                                    </>
                                  )}
                                </span>
                              </div>
                            )}
                          </div>
                        </div>
                        <div className="flex gap-4 text-sm text-gray-400">
                          <span>Used in {gizmo.message_count} messages</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Messages List */}
        <div className="max-w-4xl mx-auto p-8 space-y-4">
          <h2 className="text-xl font-bold mb-4">
            Messages
            <span className="text-sm text-gray-400 ml-3 font-normal">
              ({getFilteredMessages().length} of {messages.length} shown)
            </span>
          </h2>
          {getFilteredMessages().map((message, index) => (
            <div
              key={message.id}
              className="bg-gray-900 border border-gray-800 rounded-lg p-4"
            >
              <div className="flex items-start gap-3 mb-3">
                <span className="text-2xl">{getRoleIcon(message.role)}</span>
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-sm font-semibold text-gray-300">
                      #{message.sequence_number} • {message.role}
                    </span>
                    {message.message_type && (
                      <span className="text-xs px-2 py-1 bg-blue-900/50 rounded">
                        {message.message_type}
                      </span>
                    )}
                    {message.metadata?.gizmo_id && (
                      <span
                        className="text-xs px-2 py-1 bg-purple-900/50 rounded cursor-pointer hover:bg-purple-800/50 transition-colors select-none"
                        onDoubleClick={() => handleGizmoDoubleClick(message.metadata.gizmo_id)}
                        title="Double-click to edit Custom GPT name"
                        style={{ userSelect: 'none' }}
                      >
                        🤖 {getGizmoDisplay(message.metadata.gizmo_id)}
                      </span>
                    )}

                    {/* Tool message with image indicator */}
                    {message.role === 'tool' && message.metadata?.attachments?.some(att => att.mimeType?.startsWith('image/')) && (
                      <span className="text-xs px-2 py-1 bg-green-900/50 rounded flex items-center gap-1" title="Contains generated image">
                        🖼️ Generated Image
                      </span>
                    )}

                    {/* Tool message with content indicator */}
                    {message.role === 'tool' && hasToolContent(message) && (
                      <button
                        onClick={() => toggleToolMessage(message.id)}
                        className="text-xs px-2 py-1 bg-yellow-900/50 hover:bg-yellow-800/50 rounded cursor-pointer transition-colors flex items-center gap-1"
                        title="Toggle tool output"
                      >
                        <svg
                          className={`w-3 h-3 transition-transform ${expandedToolMessages.has(message.id) ? 'rotate-180' : ''}`}
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                        </svg>
                        Tool Output
                      </button>
                    )}
                  </div>

                  {/* Render message content based on type */}
                  {(() => {
                    const parsed = parseMessageContent(message.summary, message);
                    if (!parsed) {
                      return <div className="text-sm text-gray-400">No content preview available</div>;
                    }

                    switch (parsed.type) {
                      case 'image':
                        return (
                          <div className="mt-2 flex justify-center">
                            <img
                              src={parsed.url}
                              alt="Message content"
                              className="max-w-full max-h-[500px] rounded border border-gray-700 object-contain cursor-pointer hover:opacity-90 transition-opacity"
                              style={{ width: 'auto', height: 'auto' }}
                              onClick={() => window.open(parsed.url, '_blank')}
                              onError={(e) => {
                                e.target.style.display = 'none';
                                e.target.nextSibling.style.display = 'block';
                              }}
                              title="Click to open in new tab"
                            />
                            <div className="hidden text-xs text-red-400 mt-2">
                              Image failed to load
                            </div>
                          </div>
                        );

                      case 'code':
                        return (
                          <div className="mt-2">
                            <div className="text-xs text-gray-500 mb-1">{parsed.language.toUpperCase()}:</div>
                            <pre className="text-xs text-gray-300 bg-gray-800 p-2 rounded border border-gray-700 overflow-x-auto max-h-32">
                              <code>{parsed.content}</code>
                            </pre>
                          </div>
                        );

                      case 'json':
                        return (
                          <pre className="text-xs text-gray-400 bg-gray-800 p-2 rounded border border-gray-700 overflow-x-auto max-h-32">
                            {parsed.content}
                          </pre>
                        );

                      case 'text':
                      default:
                        return (
                          <div className="text-sm text-gray-300 whitespace-pre-wrap line-clamp-3">
                            {parsed.content}
                          </div>
                        );
                    }
                  })()}

                  {/* Expanded tool message content */}
                  {message.role === 'tool' && expandedToolMessages.has(message.id) && (
                    <div className="mt-3 p-3 bg-gray-800 rounded border border-gray-700">
                      <div className="text-xs text-yellow-400 font-semibold mb-2">Tool Output:</div>

                      {/* Render images from attachments */}
                      {message.metadata?.attachments && message.metadata.attachments.length > 0 && (
                        <div className="space-y-2 mb-3">
                          {message.metadata.attachments.map((attachment, idx) => {
                            // Check if attachment has image data or URL
                            if (attachment.mimeType?.startsWith('image/') || attachment.type === 'image') {
                              // Construct image URL from fileId or id
                              const imageUrl = attachment.url ||
                                (attachment.fileId ? `http://localhost:8000/api/library/media/${attachment.fileId}/file` : null) ||
                                (attachment.id ? `http://localhost:8000/api/library/media/${attachment.id}/file` : null);

                              return (
                                <div key={idx} className="border border-gray-600 rounded overflow-hidden">
                                  {imageUrl ? (
                                    <img
                                      src={imageUrl}
                                      alt={attachment.name || `Tool output ${idx + 1}`}
                                      className="max-w-full h-auto cursor-pointer hover:opacity-90 transition-opacity"
                                      onClick={() => window.open(imageUrl, '_blank')}
                                      onError={(e) => {
                                        e.target.style.display = 'none';
                                        e.target.nextSibling.style.display = 'block';
                                      }}
                                      title="Click to open in new tab"
                                    />
                                  ) : null}
                                  <div className="hidden p-2 text-xs text-red-400">
                                    Image failed to load: {attachment.name || attachment.fileId || attachment.id}
                                  </div>
                                </div>
                              );
                            }
                            return null;
                          })}
                        </div>
                      )}

                      {/* Full content preview */}
                      {message.summary && (
                        <div className="text-sm text-gray-300 whitespace-pre-wrap max-h-60 overflow-y-auto">
                          {message.summary}
                        </div>
                      )}
                    </div>
                  )}

                  <div className="flex gap-3 mt-2 text-xs text-gray-500">
                    <span>{message.chunk_count} chunks</span>
                    <span>{message.token_count} tokens</span>
                    {message.timestamp && (
                      <span>{formatDate(message.timestamp)}</span>
                    )}
                  </div>
                </div>
                <button
                  onClick={() => setLightboxMessage(message)}
                  className="px-3 py-2 bg-blue-600 hover:bg-blue-700 rounded text-sm transition-colors flex items-center gap-2"
                  title="View full message"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                  </svg>
                  View
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Message Lightbox */}
      {lightboxMessage && (
        <MessageLightbox
          message={lightboxMessage}
          messages={getFilteredMessages()}
          onNavigate={(newMessage) => setLightboxMessage(newMessage)}
          onClose={() => setLightboxMessage(null)}
          onPipelineOpen={handlePipelineOpen}
          onAddToBook={handleAddToBook}
        />
      )}

      {/* Pipeline Panel */}
      <PipelinePanel
        isOpen={showPipelinePanel}
        onClose={() => setShowPipelinePanel(false)}
        currentMessage={pipelineMessage}
      />

      {/* Book Section Selector Modal */}
      {showBookSelector && bookSelectorData.message && (
        <BookSectionSelector
          message={bookSelectorData.message}
          chunks={bookSelectorData.chunks}
          onClose={() => setShowBookSelector(false)}
          onSuccess={handleBookSelectorSuccess}
        />
      )}
    </div>
  );
}

ConversationViewer.propTypes = {
  collection: PropTypes.object.isRequired,
  onBack: PropTypes.func.isRequired
};
