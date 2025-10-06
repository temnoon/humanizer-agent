import { useState, useEffect } from 'react';
import axios from 'axios';
import PropTypes from 'prop-types';

/**
 * LibraryBrowser Component
 *
 * Hierarchical browser for imported archives:
 * - Collections (ChatGPT archives, Claude conversations, etc.)
 * - Messages within collections
 * - Chunks within messages
 * - Media files
 */
export default function LibraryBrowser({ onSelect }) {
  const [collections, setCollections] = useState([]);
  const [selectedCollection, setSelectedCollection] = useState(null);
  const [collectionHierarchy, setCollectionHierarchy] = useState(null);
  const [selectedMessage, setSelectedMessage] = useState(null);
  const [messageChunks, setMessageChunks] = useState([]);
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [error, setError] = useState(null);

  // View modes: 'list', 'hierarchy', 'message', 'chunk'
  const [viewMode, setViewMode] = useState('list');

  // Load library stats
  useEffect(() => {
    loadStats();
  }, []);

  // Load collections on mount
  useEffect(() => {
    loadCollections();
  }, []);

  const loadStats = async () => {
    try {
      const response = await axios.get('/api/library/stats');
      setStats(response.data);
    } catch (err) {
      console.error('Failed to load stats:', err);
    }
  };

  const loadCollections = async (search = '') => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get('/api/library/collections', {
        params: { search, limit: 100 }
      });
      setCollections(response.data);
    } catch (err) {
      setError('Failed to load collections');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const loadCollectionHierarchy = async (collectionId) => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get(`/api/library/collections/${collectionId}`, {
        params: { include_chunks: true }
      });
      setCollectionHierarchy(response.data);
      setSelectedCollection(collectionId);
      setViewMode('hierarchy');
    } catch (err) {
      setError('Failed to load collection details');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const loadMessageChunks = async (messageId) => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get(`/api/library/messages/${messageId}/chunks`);
      setMessageChunks(response.data);
      setSelectedMessage(messageId);
      setViewMode('message');
    } catch (err) {
      setError('Failed to load message chunks');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    loadCollections(searchQuery);
  };

  const handleBackToList = () => {
    setViewMode('list');
    setSelectedCollection(null);
    setCollectionHierarchy(null);
  };

  const handleBackToHierarchy = () => {
    setViewMode('hierarchy');
    setSelectedMessage(null);
    setMessageChunks([]);
  };

  const getPlatformIcon = (platform) => {
    const icons = {
      chatgpt: '🤖',
      claude: '🎭',
      humanizer: '✨',
      twitter: '🐦',
      facebook: '📘'
    };
    return icons[platform] || '📁';
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

  return (
    <div className="flex flex-col bg-gray-900 text-white">
      {/* Header with Stats */}
      <div className="bg-gray-800 border-b border-gray-700 p-4 sticky top-0 z-10">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-xl font-bold">📚 Library</h2>
          {stats && (
            <div className="flex gap-4 text-sm text-gray-400">
              <span>{stats.collections} collections</span>
              <span>{stats.messages} messages</span>
              <span>{stats.chunks} chunks</span>
              <span>{stats.embedding_coverage.toFixed(0)}% embedded</span>
            </div>
          )}
        </div>

        {/* Search Bar */}
        <form onSubmit={handleSearch} className="flex gap-2">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search collections, messages, content..."
            className="flex-1 px-3 py-2 bg-gray-700 border border-gray-600 rounded text-sm focus:border-blue-500 focus:outline-none"
          />
          <button
            type="submit"
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded text-sm font-medium transition-colors"
          >
            Search
          </button>
        </form>
      </div>

      {/* Content Area */}
      <div className="p-4">
        {error && (
          <div className="bg-red-900/50 border border-red-700 rounded p-3 mb-4 text-sm">
            {error}
          </div>
        )}

        {loading && (
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
          </div>
        )}

        {/* Collections List View */}
        {viewMode === 'list' && !loading && (
          <div className="space-y-2">
            {collections.length === 0 ? (
              <div className="text-center py-8 text-gray-400">
                No collections found. Import some archives to get started!
              </div>
            ) : (
              collections.map((collection) => (
                <div
                  key={collection.id}
                  onClick={() => {
                    if (onSelect) {
                      onSelect(collection);
                    } else {
                      loadCollectionHierarchy(collection.id);
                    }
                  }}
                  className="bg-gray-800 hover:bg-gray-750 border border-gray-700 rounded-lg p-4 cursor-pointer transition-colors"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-2xl">{getPlatformIcon(collection.source_platform)}</span>
                        <h3 className="font-medium text-white">{collection.title}</h3>
                        <span className="text-xs px-2 py-1 bg-gray-700 rounded">
                          {collection.source_platform}
                        </span>
                      </div>
                      {collection.description && (
                        <p className="text-sm text-gray-400 mb-2">{collection.description}</p>
                      )}
                      <div className="flex flex-wrap gap-3 text-xs text-gray-500">
                        <span>💬 {collection.message_count} messages</span>
                        <span>📝 {collection.chunk_count} chunks</span>
                        {collection.media_count > 0 && (
                          <span>🖼️ {collection.media_count} media</span>
                        )}
                        {collection.word_count > 0 && (
                          <span>📊 {collection.word_count.toLocaleString()} words</span>
                        )}
                        {collection.total_tokens > 0 && (
                          <span>🔤 {collection.total_tokens.toLocaleString()} tokens</span>
                        )}
                      </div>
                    </div>
                    <div className="text-xs text-gray-500">
                      {collection.original_date
                        ? new Date(collection.original_date).toLocaleDateString()
                        : new Date(collection.created_at).toLocaleDateString()
                      }
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {/* Collection Hierarchy View */}
        {viewMode === 'hierarchy' && collectionHierarchy && (
          <div className="space-y-4">
            {/* Back Button */}
            <button
              onClick={handleBackToList}
              className="text-sm text-blue-400 hover:text-blue-300 flex items-center gap-1"
            >
              ← Back to Collections
            </button>

            {/* Collection Info */}
            <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-2">
                <span className="text-3xl">{getPlatformIcon(collectionHierarchy.collection.source_platform)}</span>
                <h2 className="text-xl font-bold">{collectionHierarchy.collection.title}</h2>
              </div>
              <p className="text-sm text-gray-400 mb-3">{collectionHierarchy.collection.description}</p>
              <div className="flex flex-wrap gap-3 text-sm">
                <span className="text-gray-400">
                  💬 {collectionHierarchy.collection.message_count} messages
                </span>
                <span className="text-gray-400">
                  📝 {collectionHierarchy.collection.chunk_count} chunks
                </span>
                <span className="text-gray-400">
                  🖼️ {collectionHierarchy.collection.media_count} media
                </span>
                {collectionHierarchy.collection.word_count > 0 && (
                  <span className="text-gray-400">
                    📊 {collectionHierarchy.collection.word_count.toLocaleString()} words
                  </span>
                )}
                {collectionHierarchy.collection.total_tokens > 0 && (
                  <span className="text-gray-400">
                    🔤 {collectionHierarchy.collection.total_tokens.toLocaleString()} tokens
                  </span>
                )}
              </div>
            </div>

            {/* Messages List */}
            <div>
              <h3 className="text-lg font-medium mb-3">Messages</h3>
              <div className="space-y-2">
                {collectionHierarchy.messages.map((message) => (
                  <div
                    key={message.id}
                    onClick={() => loadMessageChunks(message.id)}
                    className="bg-gray-800 hover:bg-gray-750 border border-gray-700 rounded-lg p-3 cursor-pointer transition-colors"
                  >
                    <div className="flex items-start gap-3">
                      <span className="text-xl">{getRoleIcon(message.role)}</span>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-xs font-medium text-gray-400">
                            #{message.sequence_number}
                          </span>
                          <span className="text-xs px-2 py-1 bg-gray-700 rounded">
                            {message.role}
                          </span>
                          {message.message_type && (
                            <span className="text-xs px-2 py-1 bg-blue-900/50 rounded">
                              {message.message_type}
                            </span>
                          )}
                        </div>
                        {message.summary && (
                          <p className="text-sm text-gray-300 truncate">{message.summary}</p>
                        )}
                        <div className="flex gap-3 mt-2 text-xs text-gray-500">
                          <span>📝 {message.chunk_count} chunks</span>
                          <span>🔤 {message.token_count} tokens</span>
                          {message.media_count > 0 && (
                            <span>🖼️ {message.media_count} media</span>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Message Chunks View */}
        {viewMode === 'message' && messageChunks.length > 0 && (
          <div className="space-y-4">
            {/* Back Button */}
            <button
              onClick={handleBackToHierarchy}
              className="text-sm text-blue-400 hover:text-blue-300 flex items-center gap-1"
            >
              ← Back to Messages
            </button>

            {/* Chunks */}
            <div className="space-y-3">
              {messageChunks.map((chunk) => (
                <div
                  key={chunk.id}
                  className={`bg-gray-800 border rounded-lg p-4 ${
                    chunk.is_summary ? 'border-blue-600' : 'border-gray-700'
                  }`}
                >
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-xs px-2 py-1 bg-gray-700 rounded">
                      {chunk.chunk_level}
                    </span>
                    <span className="text-xs text-gray-500">
                      Sequence: {chunk.chunk_sequence}
                    </span>
                    {chunk.is_summary && (
                      <span className="text-xs px-2 py-1 bg-blue-600 rounded">Summary</span>
                    )}
                    {chunk.has_embedding && (
                      <span className="text-xs px-2 py-1 bg-green-900/50 text-green-400 rounded">
                        ✓ Embedded
                      </span>
                    )}
                    {chunk.token_count && (
                      <span className="text-xs text-gray-500">
                        {chunk.token_count} tokens
                      </span>
                    )}
                  </div>
                  <div className="text-sm text-gray-300 whitespace-pre-wrap font-mono">
                    {chunk.content}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

LibraryBrowser.propTypes = {
  onSelect: PropTypes.func
};
