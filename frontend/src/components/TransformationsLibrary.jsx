import { useState, useEffect } from 'react';
import axios from 'axios';
import PropTypes from 'prop-types';

/**
 * TransformationsLibrary Component
 *
 * Browse and manage locally generated transformations:
 * - View all completed transformation jobs
 * - Link back to source messages/collections
 * - Reapply transformations to new content
 * - Filter by type and status
 */
export default function TransformationsLibrary({ onSelect }) {
  const [transformations, setTransformations] = useState([]);
  const [selectedTransformation, setSelectedTransformation] = useState(null);
  const [transformationDetail, setTransformationDetail] = useState(null);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterStatus, setFilterStatus] = useState('');
  const [filterType, setFilterType] = useState('');
  const [error, setError] = useState(null);
  const [reapplyTarget, setReapplyTarget] = useState('');
  const [reapplying, setReapplying] = useState(false);

  // View modes: 'list', 'detail'
  const [viewMode, setViewMode] = useState('list');

  // Load transformations on mount
  useEffect(() => {
    loadTransformations();
  }, [filterStatus, filterType]);

  const loadTransformations = async (search = '') => {
    setLoading(true);
    setError(null);
    try {
      const params = { limit: 100 };
      if (search) params.search = search;
      if (filterStatus) params.status = filterStatus;
      if (filterType) params.job_type = filterType;

      const response = await axios.get('/api/library/transformations', { params });
      setTransformations(response.data);
    } catch (err) {
      setError('Failed to load transformations');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const loadTransformationDetail = async (transformationId) => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get(`/api/library/transformations/${transformationId}`);
      setTransformationDetail(response.data);
      setSelectedTransformation(transformationId);
      setViewMode('detail');
    } catch (err) {
      setError('Failed to load transformation details');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleReapply = async () => {
    if (!reapplyTarget || !selectedTransformation) return;

    setReapplying(true);
    setError(null);
    try {
      const response = await axios.post(
        `/api/library/transformations/${selectedTransformation}/reapply`,
        null,
        { params: { target_message_id: reapplyTarget } }
      );
      alert(`Transformation queued! Job ID: ${response.data.job_id}`);
      setReapplyTarget('');
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to reapply transformation');
      console.error(err);
    } finally {
      setReapplying(false);
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    loadTransformations(searchQuery);
  };

  const handleBackToList = () => {
    setViewMode('list');
    setSelectedTransformation(null);
    setTransformationDetail(null);
    setReapplyTarget('');
  };

  const getJobTypeIcon = (jobType) => {
    const icons = {
      persona_transform: '🎭',
      madhyamaka_detect: '☯️',
      madhyamaka_transform: '⚖️',
      perspectives: '🔍',
      contemplation: '🧘'
    };
    return icons[jobType] || '⚙️';
  };

  const getJobTypeLabel = (jobType) => {
    const labels = {
      persona_transform: 'Persona Transform',
      madhyamaka_detect: 'Madhyamaka Detection',
      madhyamaka_transform: 'Madhyamaka Transform',
      perspectives: 'Multi-Perspective',
      contemplation: 'Contemplation'
    };
    return labels[jobType] || jobType;
  };

  const getStatusBadge = (status) => {
    const badges = {
      completed: 'bg-green-600',
      failed: 'bg-red-600',
      processing: 'bg-blue-600',
      pending: 'bg-yellow-600',
      paused: 'bg-gray-600',
      cancelled: 'bg-gray-700'
    };
    return badges[status] || 'bg-gray-600';
  };

  const formatDate = (isoString) => {
    if (!isoString) return 'N/A';
    const date = new Date(isoString);
    return date.toLocaleString();
  };

  return (
    <div className="flex flex-col h-full bg-gray-900 text-white">
      {/* Header with Filters */}
      <div className="bg-gray-800 border-b border-gray-700 p-4 sticky top-0 z-10">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-xl font-bold">🔧 Transformations</h2>
          {viewMode === 'detail' && (
            <button
              onClick={handleBackToList}
              className="px-3 py-1 bg-gray-700 hover:bg-gray-600 rounded text-sm"
            >
              ← Back to List
            </button>
          )}
        </div>

        {viewMode === 'list' && (
          <>
            {/* Search */}
            <form onSubmit={handleSearch} className="mb-3">
              <input
                type="text"
                placeholder="Search transformations..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
              />
            </form>

            {/* Filters */}
            <div className="flex gap-2">
              <select
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value)}
                className="px-3 py-1 bg-gray-700 border border-gray-600 rounded text-sm"
              >
                <option value="">All Statuses</option>
                <option value="completed">Completed</option>
                <option value="failed">Failed</option>
                <option value="processing">Processing</option>
                <option value="pending">Pending</option>
              </select>

              <select
                value={filterType}
                onChange={(e) => setFilterType(e.target.value)}
                className="px-3 py-1 bg-gray-700 border border-gray-600 rounded text-sm"
              >
                <option value="">All Types</option>
                <option value="persona_transform">Persona Transform</option>
                <option value="madhyamaka_detect">Madhyamaka Detection</option>
                <option value="madhyamaka_transform">Madhyamaka Transform</option>
                <option value="perspectives">Multi-Perspective</option>
                <option value="contemplation">Contemplation</option>
              </select>
            </div>
          </>
        )}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4">
        {error && (
          <div className="bg-red-900 border border-red-700 text-red-200 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}

        {loading ? (
          <div className="text-center text-gray-400 py-8">Loading...</div>
        ) : viewMode === 'list' ? (
          /* LIST VIEW */
          <div className="space-y-3">
            {transformations.length === 0 ? (
              <div className="text-center text-gray-500 py-8">
                No transformations found.
              </div>
            ) : (
              transformations.map((trans) => (
                <div
                  key={trans.id}
                  onClick={() => loadTransformationDetail(trans.id)}
                  className="bg-gray-800 border border-gray-700 p-4 rounded hover:bg-gray-750 cursor-pointer"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-2xl">{getJobTypeIcon(trans.job_type)}</span>
                      <div>
                        <h3 className="font-bold">{trans.name}</h3>
                        <p className="text-sm text-gray-400">{getJobTypeLabel(trans.job_type)}</p>
                      </div>
                    </div>

                    <span className={`px-2 py-1 rounded text-xs font-bold ${getStatusBadge(trans.status)}`}>
                      {trans.status.toUpperCase()}
                    </span>
                  </div>

                  {trans.description && (
                    <p className="text-sm text-gray-400 mb-2">{trans.description}</p>
                  )}

                  <div className="flex gap-4 text-xs text-gray-500">
                    <span>📅 {formatDate(trans.created_at)}</span>
                    <span>📊 {trans.processed_items}/{trans.total_items} items</span>
                    <span>🪙 {trans.tokens_used.toLocaleString()} tokens</span>
                  </div>

                  {trans.source_collection_id && (
                    <div className="mt-2 text-xs text-blue-400">
                      🔗 Linked to collection
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        ) : (
          /* DETAIL VIEW */
          transformationDetail && (
            <div className="space-y-4">
              {/* Job Info */}
              <div className="bg-gray-800 border border-gray-700 p-4 rounded">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <span className="text-3xl">{getJobTypeIcon(transformationDetail.job.job_type)}</span>
                    <div>
                      <h2 className="text-xl font-bold">{transformationDetail.job.name}</h2>
                      <p className="text-sm text-gray-400">{getJobTypeLabel(transformationDetail.job.job_type)}</p>
                    </div>
                  </div>

                  <span className={`px-3 py-1 rounded font-bold ${getStatusBadge(transformationDetail.job.status)}`}>
                    {transformationDetail.job.status.toUpperCase()}
                  </span>
                </div>

                {transformationDetail.job.description && (
                  <p className="text-gray-300 mb-3">{transformationDetail.job.description}</p>
                )}

                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <span className="text-gray-400">Created:</span>
                    <span className="ml-2">{formatDate(transformationDetail.job.created_at)}</span>
                  </div>
                  <div>
                    <span className="text-gray-400">Completed:</span>
                    <span className="ml-2">{formatDate(transformationDetail.job.completed_at)}</span>
                  </div>
                  <div>
                    <span className="text-gray-400">Progress:</span>
                    <span className="ml-2">{transformationDetail.job.progress_percentage.toFixed(1)}%</span>
                  </div>
                  <div>
                    <span className="text-gray-400">Tokens:</span>
                    <span className="ml-2">{transformationDetail.job.tokens_used.toLocaleString()}</span>
                  </div>
                </div>

                {/* Configuration */}
                <div className="mt-3 p-3 bg-gray-900 rounded">
                  <h4 className="font-bold mb-2 text-sm">Configuration:</h4>
                  <pre className="text-xs text-gray-400 overflow-x-auto">
                    {JSON.stringify(transformationDetail.job.configuration, null, 2)}
                  </pre>
                </div>
              </div>

              {/* Source Links */}
              {(transformationDetail.source_message || transformationDetail.source_collection) && (
                <div className="bg-gray-800 border border-gray-700 p-4 rounded">
                  <h3 className="font-bold mb-3">🔗 Source Links</h3>

                  {transformationDetail.source_collection && (
                    <div className="mb-3 p-3 bg-gray-900 rounded">
                      <div className="flex items-center gap-2 mb-1">
                        <span>📚</span>
                        <span className="font-bold">{transformationDetail.source_collection.title}</span>
                      </div>
                      <p className="text-xs text-gray-400">
                        {transformationDetail.source_collection.message_count} messages •
                        {' '}{transformationDetail.source_collection.chunk_count} chunks
                      </p>
                    </div>
                  )}

                  {transformationDetail.source_message && (
                    <div className="p-3 bg-gray-900 rounded">
                      <div className="flex items-center gap-2 mb-1">
                        <span>💬</span>
                        <span className="font-bold">Message #{transformationDetail.source_message.sequence_number}</span>
                        <span className="text-xs text-gray-500">({transformationDetail.source_message.role})</span>
                      </div>
                      {transformationDetail.source_message.summary && (
                        <p className="text-sm text-gray-400 mt-2">{transformationDetail.source_message.summary}</p>
                      )}
                    </div>
                  )}
                </div>
              )}

              {/* Transformations Results */}
              {transformationDetail.transformations.length > 0 && (
                <div className="bg-gray-800 border border-gray-700 p-4 rounded">
                  <h3 className="font-bold mb-3">📝 Results ({transformationDetail.transformations.length})</h3>
                  <div className="space-y-2">
                    {transformationDetail.transformations.slice(0, 5).map((trans, idx) => (
                      <div key={trans.id} className="p-2 bg-gray-900 rounded text-sm">
                        <div className="flex justify-between items-center">
                          <span className="text-gray-400">Transformation {idx + 1}</span>
                          <span className={`px-2 py-0.5 rounded text-xs ${getStatusBadge(trans.status)}`}>
                            {trans.status}
                          </span>
                        </div>
                        {trans.result_chunk_id && (
                          <span className="text-xs text-green-400">✓ Result created</span>
                        )}
                      </div>
                    ))}
                    {transformationDetail.transformations.length > 5 && (
                      <p className="text-xs text-gray-500 text-center">
                        + {transformationDetail.transformations.length - 5} more
                      </p>
                    )}
                  </div>
                </div>
              )}

              {/* Lineage */}
              {transformationDetail.lineage.length > 0 && (
                <div className="bg-gray-800 border border-gray-700 p-4 rounded">
                  <h3 className="font-bold mb-3">🌳 Lineage</h3>
                  <div className="space-y-2">
                    {transformationDetail.lineage.map((lin) => (
                      <div key={lin.id} className="p-2 bg-gray-900 rounded text-sm">
                        <div className="flex items-center gap-2">
                          <span className="text-gray-400">Generation {lin.generation}</span>
                          <span className="text-xs text-blue-400">{lin.transformation_path.join(' → ')}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Reapply Section */}
              <div className="bg-gray-800 border border-gray-700 p-4 rounded">
                <h3 className="font-bold mb-3">🔄 Reapply Transformation</h3>
                <p className="text-sm text-gray-400 mb-3">
                  Apply this transformation to a different message. Enter the target message UUID:
                </p>
                <div className="flex gap-2">
                  <input
                    type="text"
                    placeholder="Message UUID"
                    value={reapplyTarget}
                    onChange={(e) => setReapplyTarget(e.target.value)}
                    className="flex-1 px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
                  />
                  <button
                    onClick={handleReapply}
                    disabled={!reapplyTarget || reapplying}
                    className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed rounded font-bold"
                  >
                    {reapplying ? 'Applying...' : 'Reapply'}
                  </button>
                </div>
              </div>
            </div>
          )
        )}
      </div>
    </div>
  );
}

TransformationsLibrary.propTypes = {
  onSelect: PropTypes.func
};
