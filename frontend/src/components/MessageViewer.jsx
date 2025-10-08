import { useState, useEffect } from 'react';
import axios from 'axios';
import PropTypes from 'prop-types';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import { useKeyboardShortcuts } from '../hooks/useKeyboardShortcuts';
import 'katex/dist/katex.min.css';

/**
 * MessageViewer Component
 *
 * NON-MODAL message viewer - displays in pane instead of overlay.
 * Replaces MessageLightbox for inline viewing.
 *
 * Features:
 * - Full content from all chunks
 * - Collapsible metadata section
 * - Proper timestamp formatting
 * - Keyboard navigation (arrow keys)
 * - No modal overlay - fits in layout system
 */
export default function MessageViewer({
  message,
  messages,
  onNavigate,
  onClose,
  onPipelineOpen,
  onAddToBook,
}) {
  const [chunks, setChunks] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showMetadata, setShowMetadata] = useState(false);

  useEffect(() => {
    if (message) {
      loadMessageContent();
    }
  }, [message]);

  const currentIndex = messages ? messages.findIndex((m) => m.id === message.id) : -1;
  const hasPrevious = currentIndex > 0;
  const hasNext = currentIndex >= 0 && currentIndex < messages.length - 1;

  const handlePrevious = () => {
    if (hasPrevious && onNavigate) {
      onNavigate(messages[currentIndex - 1]);
    }
  };

  const handleNext = () => {
    if (hasNext && onNavigate) {
      onNavigate(messages[currentIndex + 1]);
    }
  };

  // Keyboard shortcuts
  useKeyboardShortcuts({
    onArrowLeft: hasPrevious ? handlePrevious : null,
    onArrowRight: hasNext ? handleNext : null,
    onEscape: onClose,
    enabled: true,
  });

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
    if (value === null || value === undefined || value === '') {
      return null;
    }

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

    if (typeof value === 'object') {
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

    return (
      <div key={key} className="flex gap-2 text-sm mb-1">
        <span className="text-gray-400 font-medium min-w-[140px]">{key}:</span>
        <span className="text-gray-200">{String(value)}</span>
      </div>
    );
  };

  const preprocessLatex = (content) => {
    if (!content) return '';
    let processed = content;
    processed = processed.replace(/\\\[([\s\S]*?)\\\]/g, (match, equation) => `$$${equation}$$`);
    processed = processed.replace(/\\\(([\s\S]*?)\\\)/g, (match, equation) => `$${equation}$`);
    return processed;
  };

  const insertImages = (content) => {
    if (!content) return '';
    let processed = content;

    const attachmentMap = new Map();
    if (message.metadata?.attachments) {
      message.metadata.attachments.forEach((attachment) => {
        if (attachment.id) {
          attachmentMap.set(attachment.id, attachment);
          const idWithoutPrefix = attachment.id.replace(/^file-/, '');
          attachmentMap.set(idWithoutPrefix, attachment);
        }
      });
    }

    processed = processed.replace(/file-([a-zA-Z0-9]+)/g, (match, hash) => {
      const attachment = attachmentMap.get(match) || attachmentMap.get(hash);
      if (attachment && (attachment.mime_type?.startsWith('image/') || attachment.mimeType?.startsWith('image/'))) {
        const imageUrl = `/api/library/media/${attachment.id}`;
        return `![${attachment.name || 'Image'}](${imageUrl})`;
      }
      return match;
    });

    return processed;
  };

  const getFullContent = () => {
    if (chunks.length === 0) return '';
    const rawContent = chunks
      .sort((a, b) => a.chunk_sequence - b.chunk_sequence)
      .map((chunk) => chunk.content)
      .join('\n\n');
    let processed = insertImages(rawContent);
    processed = preprocessLatex(processed);
    return processed;
  };

  const getRoleIcon = (role) => {
    const icons = {
      user: '👤',
      assistant: '🤖',
      system: '⚙️',
      tool: '🔧',
    };
    return icons[role] || '💬';
  };

  if (!message) {
    return (
      <div className="h-full flex items-center justify-center bg-gray-900 text-gray-400">
        <p>No message selected</p>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col bg-gray-900">
      {/* Header */}
      <div className="bg-gray-800 border-b border-gray-700 p-4 flex items-center justify-between flex-shrink-0">
        {/* Previous arrow */}
        <button
          onClick={handlePrevious}
          disabled={!hasPrevious}
          className={`p-2 rounded transition-colors ${
            hasPrevious ? 'hover:bg-gray-700 text-white' : 'text-gray-600 cursor-not-allowed'
          }`}
          title="Previous message (←)"
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
        </button>

        {/* Title */}
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
            </p>
          </div>
        </div>

        {/* Controls */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowMetadata(!showMetadata)}
            className="px-3 py-1 bg-gray-700 hover:bg-gray-600 rounded text-sm transition-colors"
          >
            Metadata
          </button>
          {onPipelineOpen && (
            <button
              onClick={() => onPipelineOpen(message)}
              className="px-3 py-1 bg-blue-700 hover:bg-blue-600 rounded text-sm transition-colors"
            >
              Pipeline
            </button>
          )}
          {onAddToBook && (
            <button
              onClick={() => onAddToBook(message, chunks)}
              className="px-3 py-1 bg-green-700 hover:bg-green-600 rounded text-sm transition-colors"
            >
              📖
            </button>
          )}
          {onClose && (
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-700 rounded transition-colors"
              title="Close (Esc)"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          )}
          <button
            onClick={handleNext}
            disabled={!hasNext}
            className={`p-2 rounded transition-colors ${
              hasNext ? 'hover:bg-gray-700 text-white' : 'text-gray-600 cursor-not-allowed'
            }`}
            title="Next message (→)"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </button>
        </div>
      </div>

      {/* Metadata */}
      {showMetadata && (
        <div className="bg-gray-850 border-b border-gray-700 p-4 max-h-60 overflow-y-auto flex-shrink-0">
          <h3 className="text-sm font-semibold text-gray-300 mb-3">Message Metadata</h3>
          <div className="space-y-1">
            {renderMetadataField('message_id', message.id)}
            {renderMetadataField('sequence_number', message.sequence_number)}
            {renderMetadataField('role', message.role)}
            {renderMetadataField('message_type', message.message_type)}
            {renderMetadataField('timestamp', message.timestamp)}
            {message.metadata &&
              Object.entries(message.metadata).map(([key, value]) => renderMetadataField(key, value))}
          </div>
        </div>
      )}

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-8">
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

        {!loading && !error && chunks.length > 0 && (
          <div className="message-content prose prose-invert max-w-none">
            <ReactMarkdown
              remarkPlugins={[remarkGfm, [remarkMath, { singleDollarTextMath: true }]]}
              rehypePlugins={[[rehypeKatex, { strict: false, trust: true, output: 'html' }]]}
            >
              {getFullContent()}
            </ReactMarkdown>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="bg-gray-800 border-t border-gray-700 p-3 flex-shrink-0">
        <div className="flex gap-4 text-xs text-gray-400">
          <span>{chunks.length} chunks</span>
          <span>{message.token_count} tokens</span>
          {message.timestamp && <span className="font-mono">{formatTimestamp(message.timestamp)}</span>}
        </div>
      </div>
    </div>
  );
}

MessageViewer.propTypes = {
  message: PropTypes.object,
  messages: PropTypes.array,
  onNavigate: PropTypes.func,
  onClose: PropTypes.func,
  onPipelineOpen: PropTypes.func,
  onAddToBook: PropTypes.func,
};
