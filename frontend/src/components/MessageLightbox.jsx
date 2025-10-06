import { useState, useEffect } from 'react';
import axios from 'axios';
import PropTypes from 'prop-types';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import 'katex/dist/katex.min.css';
import '../styles/lightbox.css';

/**
 * MessageLightbox Component
 *
 * Displays a single message as a fully-rendered markdown/LaTeX document
 * in a lightbox overlay with:
 * - Full content from all chunks
 * - Collapsible metadata section
 * - Proper timestamp formatting (YYYYMMDD::HH:MM:SS)
 * - Parent/child message relationships
 * - Null value filtering
 */
export default function MessageLightbox({ message, messages, onNavigate, onClose, onPipelineOpen, onAddToBook }) {
  const [chunks, setChunks] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showMetadata, setShowMetadata] = useState(false);
  const [lightboxHeight, setLightboxHeight] = useState('80vh');

  useEffect(() => {
    if (message) {
      loadMessageContent();
    }
  }, [message]);

  // Calculate maximum height needed for all messages on mount
  useEffect(() => {
    if (messages && messages.length > 0) {
      // Use 80vh as the maximum, but could calculate based on content if needed
      // This ensures consistent height regardless of message size
      const maxHeight = Math.min(window.innerHeight * 0.8, window.innerHeight * 0.8);
      setLightboxHeight(`${maxHeight}px`);
    }
  }, [messages]);

  const currentIndex = messages ? messages.findIndex(m => m.id === message.id) : -1;
  const hasPrevious = currentIndex > 0;
  const hasNext = currentIndex >= 0 && currentIndex < messages.length - 1;

  const handlePrevious = () => {
    if (hasPrevious && onNavigate) {
      // Prevent scroll jump by maintaining scroll position
      const scrollContainer = document.querySelector('.lightbox-content-scroll');
      const currentScrollTop = scrollContainer?.scrollTop || 0;

      onNavigate(messages[currentIndex - 1]);

      // Reset scroll to top for new message
      setTimeout(() => {
        if (scrollContainer) {
          scrollContainer.scrollTop = 0;
        }
      }, 0);
    }
  };

  const handleNext = () => {
    if (hasNext && onNavigate) {
      // Prevent scroll jump by maintaining scroll position
      const scrollContainer = document.querySelector('.lightbox-content-scroll');
      const currentScrollTop = scrollContainer?.scrollTop || 0;

      onNavigate(messages[currentIndex + 1]);

      // Reset scroll to top for new message
      setTimeout(() => {
        if (scrollContainer) {
          scrollContainer.scrollTop = 0;
        }
      }, 0);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'ArrowLeft' && hasPrevious) {
      handlePrevious();
    } else if (e.key === 'ArrowRight' && hasNext) {
      handleNext();
    } else if (e.key === 'Escape') {
      onClose();
    }
  };

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);

    // Prevent body scroll when lightbox is open
    document.body.classList.add('lightbox-open');

    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      document.body.classList.remove('lightbox-open');
    };
  }, [currentIndex, messages]);

  const loadMessageContent = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get(`/api/library/messages/${message.id}/chunks`);
      setChunks(response.data);
    } catch (err) {
      setError('Failed to load message content');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const formatTimestamp = (isoString) => {
    if (!isoString) return null;

    try {
      const date = new Date(isoString);
      const year = date.getFullYear();
      const month = String(date.getMonth() + 1).padStart(2, '0');
      const day = String(date.getDate()).padStart(2, '0');
      const hours = String(date.getHours()).padStart(2, '0');
      const minutes = String(date.getMinutes()).padStart(2, '0');
      const seconds = String(date.getSeconds()).padStart(2, '0');

      return `${year}${month}${day}::${hours}:${minutes}:${seconds}`;
    } catch (e) {
      return isoString;
    }
  };

  const renderMetadataField = (key, value) => {
    // Skip null, undefined, or empty values
    if (value === null || value === undefined || value === '') {
      return null;
    }

    // Format timestamps
    if (key.includes('time') || key.includes('date') || key.includes('at')) {
      const formatted = formatTimestamp(value);
      if (formatted) {
        return (
          <div key={key} className="flex gap-2 text-sm mb-1">
            <span className="text-gray-400 font-medium min-w-[140px]">{key}:</span>
            <span className="text-gray-200 font-mono">{formatted}</span>
          </div>
        );
      }
    }

    // Handle objects and arrays
    if (typeof value === 'object') {
      // Skip empty objects/arrays
      if (Array.isArray(value) && value.length === 0) return null;
      if (!Array.isArray(value) && Object.keys(value).length === 0) return null;

      return (
        <div key={key} className="flex gap-2 text-sm mb-1">
          <span className="text-gray-400 font-medium min-w-[140px]">{key}:</span>
          <pre className="text-gray-200 text-xs bg-gray-800 p-2 rounded overflow-x-auto flex-1">
            {JSON.stringify(value, null, 2)}
          </pre>
        </div>
      );
    }

    // Regular values
    return (
      <div key={key} className="flex gap-2 text-sm mb-1">
        <span className="text-gray-400 font-medium min-w-[140px]">{key}:</span>
        <span className="text-gray-200">{String(value)}</span>
      </div>
    );
  };

  const preprocessLatex = (content) => {
    if (!content) return '';

    // Convert LaTeX-style delimiters to dollar signs for remark-math
    let processed = content;

    // Convert display math: \[ ... \] to $$ ... $$
    // Using a regex that handles escaped backslashes and nested brackets
    processed = processed.replace(/\\\[([\s\S]*?)\\\]/g, (match, equation) => {
      return `$$${equation}$$`;
    });

    // Convert inline math: \( ... \) to $ ... $
    processed = processed.replace(/\\\(([\s\S]*?)\\\)/g, (match, equation) => {
      return `$${equation}$`;
    });

    return processed;
  };

  const insertImages = (content) => {
    if (!content) return '';

    let processed = content;

    // Build a map of file IDs to attachment metadata
    const attachmentMap = new Map();
    if (message.metadata?.attachments) {
      message.metadata.attachments.forEach(attachment => {
        // Store by various ID patterns
        if (attachment.id) {
          attachmentMap.set(attachment.id, attachment);
          // Also store without 'file-' prefix
          const idWithoutPrefix = attachment.id.replace(/^file-/, '');
          attachmentMap.set(idWithoutPrefix, attachment);
        }
      });
    }

    // Pattern 1: ChatGPT attachment IDs in text: file-<hash>
    processed = processed.replace(/file-([a-zA-Z0-9]+)/g, (match, hash) => {
      const attachment = attachmentMap.get(match) || attachmentMap.get(hash);
      if (attachment && (attachment.mime_type?.startsWith('image/') || attachment.mimeType?.startsWith('image/'))) {
        // Generate URL to our media endpoint
        const imageUrl = `/api/library/media/${attachment.id}`;
        return `![${attachment.name || 'Image'}](${imageUrl})`;
      }
      return match;
    });

    // Pattern 2: file-service://file-<hash> (ChatGPT file service)
    processed = processed.replace(/file-service:\/\/file-([a-zA-Z0-9]+)/g, (match, hash) => {
      const fileId = `file-${hash}`;
      const attachment = attachmentMap.get(fileId) || attachmentMap.get(hash);
      if (attachment && (attachment.mime_type?.startsWith('image/') || attachment.mimeType?.startsWith('image/'))) {
        const imageUrl = `/api/library/media/${attachment.id}`;
        return `![${attachment.name || 'Image'}](${imageUrl})`;
      }
      return match;
    });

    // Pattern 3: sandbox:/mnt/data/filename references
    processed = processed.replace(/sandbox:\/mnt\/data\/([^\s\)]+\.(png|jpg|jpeg|gif|webp|svg))/gi, (match, filename) => {
      // Try to find matching attachment by filename
      for (const [id, att] of attachmentMap) {
        if (att.name?.includes(filename)) {
          const imageUrl = `/api/library/media/${att.id}`;
          return `![${filename}](${imageUrl})`;
        }
      }
      return match;
    });

    // Pattern 4: sediment://file_<hash> (DALL-E and new format)
    processed = processed.replace(/sediment:\/\/file_([a-zA-Z0-9]+)/g, (match, hash) => {
      // This is a DALL-E or file reference - for now, just note it
      // We'll need to handle this differently as these aren't in attachments
      return match; // Keep as-is for now
    });

    return processed;
  };

  const getFullContent = () => {
    if (chunks.length === 0) return '';

    // Concatenate all chunk contents in sequence order
    const rawContent = chunks
      .sort((a, b) => a.chunk_sequence - b.chunk_sequence)
      .map(chunk => chunk.content)
      .join('\n\n');

    // Process content: insert images first, then convert LaTeX delimiters
    let processed = insertImages(rawContent);
    processed = preprocessLatex(processed);

    return processed;
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

  if (!message) return null;

  return (
    <div
      className="fixed inset-0 bg-black bg-opacity-80 z-50 flex items-center justify-center p-4"
      onClick={onClose}
    >
      <div
        className="bg-gray-900 rounded-lg shadow-2xl max-w-4xl w-full flex flex-col"
        style={{ height: lightboxHeight }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="bg-gray-800 border-b border-gray-700 p-4 flex items-center justify-between rounded-t-lg">
          {/* Left side: Previous arrow */}
          <button
            onClick={handlePrevious}
            disabled={!hasPrevious}
            className={`p-2 rounded transition-colors ${
              hasPrevious
                ? 'hover:bg-gray-700 text-white'
                : 'text-gray-600 cursor-not-allowed'
            }`}
            title="Previous message (←)"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </button>

          {/* Center: Title and info */}
          <div className="flex items-center gap-3 flex-1 justify-center">
            <span className="text-2xl">{getRoleIcon(message.role)}</span>
            <div className="text-center">
              <h2 className="text-lg font-bold text-white">
                Message #{message.sequence_number}
                {messages && (
                  <span className="text-sm text-gray-400 font-normal ml-2">
                    ({currentIndex + 1} of {messages.length})
                  </span>
                )}
              </h2>
              <p className="text-sm text-gray-400">
                {message.role}
                {message.message_type && ` • ${message.message_type}`}
                {message.parent_message_id && (
                  <span className="ml-2 text-xs bg-gray-700 px-2 py-0.5 rounded">
                    ↳ Reply to parent
                  </span>
                )}
              </p>
            </div>
          </div>

          {/* Right side: Controls and next arrow */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowMetadata(!showMetadata)}
              className="px-3 py-1 bg-gray-700 hover:bg-gray-600 rounded text-sm transition-colors flex items-center gap-2"
            >
              <svg
                className={`w-4 h-4 transition-transform ${showMetadata ? 'rotate-180' : ''}`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
              Metadata
            </button>
            {onPipelineOpen && (
              <button
                onClick={() => onPipelineOpen(message)}
                className="px-3 py-1 bg-blue-700 hover:bg-blue-600 rounded text-sm transition-colors flex items-center gap-2"
                title="Open Pipeline Panel"
              >
                <span className="text-base">⚙️</span>
                Pipeline
              </button>
            )}
            {onAddToBook && (
              <button
                onClick={() => onAddToBook(message, chunks)}
                className="px-3 py-1 bg-green-700 hover:bg-green-600 rounded text-sm transition-colors flex items-center gap-2"
                title="Add to Book"
              >
                <span className="text-base">📖</span>
                Add to Book
              </button>
            )}
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-700 rounded transition-colors"
              title="Close (Esc)"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
            <button
              onClick={handleNext}
              disabled={!hasNext}
              className={`p-2 rounded transition-colors ${
                hasNext
                  ? 'hover:bg-gray-700 text-white'
                  : 'text-gray-600 cursor-not-allowed'
              }`}
              title="Next message (→)"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </button>
          </div>
        </div>

        {/* Metadata Section (Collapsible) */}
        {showMetadata && (
          <div className="bg-gray-850 border-b border-gray-700 p-4 max-h-60 overflow-y-auto">
            <h3 className="text-sm font-semibold text-gray-300 mb-3">Message Metadata</h3>
            <div className="space-y-1">
              {renderMetadataField('message_id', message.id)}
              {renderMetadataField('sequence_number', message.sequence_number)}
              {renderMetadataField('role', message.role)}
              {renderMetadataField('message_type', message.message_type)}
              {renderMetadataField('timestamp', message.timestamp)}
              {renderMetadataField('created_at', message.created_at)}
              {renderMetadataField('parent_message_id', message.parent_message_id)}
              {renderMetadataField('chunk_count', message.chunk_count)}
              {renderMetadataField('token_count', message.token_count)}
              {renderMetadataField('media_count', message.media_count)}

              {/* Render additional metadata fields */}
              {message.metadata && Object.entries(message.metadata).map(([key, value]) =>
                renderMetadataField(key, value)
              )}
            </div>
          </div>
        )}

        {/* Content Section */}
        <div className="flex-1 overflow-y-auto p-8 lightbox-content-scroll">
          {loading && (
            <div className="flex flex-col items-center justify-center h-full">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mb-4"></div>
              <p className="text-gray-400">Loading message content...</p>
            </div>
          )}

          {error && (
            <div className="bg-red-900/50 border border-red-700 rounded-lg p-4">
              <p className="text-red-200">{error}</p>
            </div>
          )}

          {!loading && !error && chunks.length === 0 && (
            <div className="text-center text-gray-400 py-8">
              No content available for this message.
            </div>
          )}

          {/* PRIORITY: If message has image attachments, show ONLY the image */}
          {!loading && !error && message.metadata?.attachments && message.metadata.attachments.some(att =>
            att.id && (att.mimeType?.startsWith('image/') || att.name?.match(/\.(jpg|jpeg|png|gif|webp)$/i))
          ) && (
            <div className="flex items-center justify-center h-full">
              {message.metadata.attachments.map((attachment, idx) => {
                // Only render image attachments
                if (attachment.id && (attachment.mimeType?.startsWith('image/') || attachment.name?.match(/\.(jpg|jpeg|png|gif|webp)$/i))) {
                  const imageUrl = `/api/library/media/${attachment.id}`;
                  return (
                    <div key={idx} className="flex flex-col items-center gap-4 max-w-full max-h-full">
                      <a
                        href={imageUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="block cursor-pointer hover:opacity-90 transition-opacity"
                        title="Click to open image in new tab"
                      >
                        <img
                          src={imageUrl}
                          alt={attachment.name || 'Image'}
                          className="max-w-full max-h-[70vh] object-contain rounded-lg shadow-2xl"
                          style={{ width: 'auto', height: 'auto' }}
                        />
                      </a>
                      {attachment.name && (
                        <div className="text-sm text-gray-400 text-center">
                          {attachment.name}
                        </div>
                      )}
                    </div>
                  );
                }
                return null;
              })}
            </div>
          )}

          {/* Regular content (only shown if NO image attachments) */}
          {!loading && !error && chunks.length > 0 && !(message.metadata?.attachments && message.metadata.attachments.some(att =>
            att.id && (att.mimeType?.startsWith('image/') || att.name?.match(/\.(jpg|jpeg|png|gif|webp)$/i))
          )) && (
            <div className="message-content prose prose-invert max-w-none">

              <ReactMarkdown
                remarkPlugins={[
                  remarkGfm,
                  [remarkMath, { singleDollarTextMath: true }]
                ]}
                rehypePlugins={[
                  [rehypeKatex, {
                    strict: false,
                    trust: true,
                    output: 'html'
                  }]
                ]}
                components={{
                  // Custom styling for code blocks
                  code({ node, inline, className, children, ...props }) {
                    return inline ? (
                      <code className="bg-gray-800 px-1.5 py-0.5 rounded text-sm font-mono text-blue-300" {...props}>
                        {children}
                      </code>
                    ) : (
                      <pre className="bg-gray-800 p-4 rounded-lg overflow-x-auto my-4">
                        <code className={`${className} text-sm font-mono text-gray-200`} {...props}>
                          {children}
                        </code>
                      </pre>
                    );
                  },
                  // Custom styling for pre blocks
                  pre({ node, children, ...props }) {
                    return children;
                  },
                  // Custom styling for paragraphs
                  p({ node, children, ...props }) {
                    // Check if children contain block elements (like pre, table, div)
                    // If so, render as div to avoid invalid nesting
                    const hasBlockChild = node?.children?.some(child =>
                      child.type === 'element' && ['pre', 'table', 'div', 'blockquote'].includes(child.tagName)
                    );

                    return hasBlockChild ? (
                      <div className="text-gray-200 leading-relaxed mb-4" {...props}>
                        {children}
                      </div>
                    ) : (
                      <p className="text-gray-200 leading-relaxed mb-4" {...props}>
                        {children}
                      </p>
                    );
                  },
                  // Custom styling for headings
                  h1({ node, children, ...props }) {
                    return (
                      <h1 className="text-3xl font-bold text-white mt-8 mb-4 border-b border-gray-700 pb-2" {...props}>
                        {children}
                      </h1>
                    );
                  },
                  h2({ node, children, ...props }) {
                    return (
                      <h2 className="text-2xl font-bold text-white mt-6 mb-3" {...props}>
                        {children}
                      </h2>
                    );
                  },
                  h3({ node, children, ...props }) {
                    return (
                      <h3 className="text-xl font-semibold text-white mt-5 mb-2" {...props}>
                        {children}
                      </h3>
                    );
                  },
                  // Custom styling for lists
                  ul({ node, children, ...props }) {
                    return (
                      <ul className="list-disc list-inside text-gray-200 mb-4 space-y-1" {...props}>
                        {children}
                      </ul>
                    );
                  },
                  ol({ node, children, ...props }) {
                    return (
                      <ol className="list-decimal list-inside text-gray-200 mb-4 space-y-1" {...props}>
                        {children}
                      </ol>
                    );
                  },
                  li({ node, children, ...props }) {
                    return (
                      <li className="text-gray-200 ml-4" {...props}>
                        {children}
                      </li>
                    );
                  },
                  // Custom styling for blockquotes
                  blockquote({ node, children, ...props }) {
                    return (
                      <blockquote className="border-l-4 border-blue-500 pl-4 py-2 my-4 bg-gray-800/50 italic text-gray-300" {...props}>
                        {children}
                      </blockquote>
                    );
                  },
                  // Custom styling for links
                  a({ node, children, ...props }) {
                    return (
                      <a
                        className="text-blue-400 hover:text-blue-300 underline transition-colors"
                        target="_blank"
                        rel="noopener noreferrer"
                        {...props}
                      >
                        {children}
                      </a>
                    );
                  },
                  // Custom styling for images
                  img({ node, ...props }) {
                    return (
                      <img
                        className="max-w-full h-auto rounded-lg shadow-lg my-6 border border-gray-700"
                        {...props}
                      />
                    );
                  },
                  // Custom styling for tables
                  table({ node, children, ...props }) {
                    return (
                      <div className="overflow-x-auto my-4">
                        <table className="min-w-full border border-gray-700 rounded-lg" {...props}>
                          {children}
                        </table>
                      </div>
                    );
                  },
                  th({ node, children, ...props }) {
                    return (
                      <th className="bg-gray-800 text-white px-4 py-2 border border-gray-700 font-semibold" {...props}>
                        {children}
                      </th>
                    );
                  },
                  td({ node, children, ...props }) {
                    return (
                      <td className="bg-gray-900 text-gray-200 px-4 py-2 border border-gray-700" {...props}>
                        {children}
                      </td>
                    );
                  },
                  // Custom styling for horizontal rules
                  hr({ node, ...props }) {
                    return (
                      <hr className="border-gray-700 my-6" {...props} />
                    );
                  }
                }}
              >
                {getFullContent()}
              </ReactMarkdown>
            </div>
          )}
        </div>

        {/* Footer with stats */}
        <div className="bg-gray-800 border-t border-gray-700 p-3 rounded-b-lg">
          <div className="flex gap-4 text-xs text-gray-400">
            <span>{chunks.length} chunks</span>
            <span>{message.token_count} tokens</span>
            {message.timestamp && (
              <span className="font-mono">{formatTimestamp(message.timestamp)}</span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

MessageLightbox.propTypes = {
  message: PropTypes.object,
  messages: PropTypes.array,
  onNavigate: PropTypes.func,
  onClose: PropTypes.func.isRequired,
  onPipelineOpen: PropTypes.func,
  onAddToBook: PropTypes.func
};
