/**
 * ArtifactBrowser Component
 *
 * Browse and manage saved semantic artifacts.
 * Shows list of artifacts with filters, search, and detail view.
 */

import React, { useState, useEffect } from 'react';
import { useArtifacts } from '../hooks/useArtifacts';

const ArtifactBrowser = ({ onArtifactSelect }) => {
  const {
    artifacts,
    loading,
    error,
    total,
    listArtifacts,
    searchArtifacts,
    getArtifact,
    deleteArtifact,
    clearError
  } = useArtifacts();

  const [searchQuery, setSearchQuery] = useState('');
  const [filterType, setFilterType] = useState('');
  const [filterOperation, setFilterOperation] = useState('');

  // Load artifacts on mount
  useEffect(() => {
    listArtifacts();
  }, [listArtifacts]);

  // Handle search
  const handleSearch = async (e) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      await searchArtifacts(searchQuery, {
        artifactType: filterType || null
      });
    } else {
      await listArtifacts({
        artifactType: filterType || null,
        operation: filterOperation || null
      });
    }
  };

  // Handle filter change
  const handleFilterChange = async () => {
    if (searchQuery.trim()) {
      await searchArtifacts(searchQuery, {
        artifactType: filterType || null
      });
    } else {
      await listArtifacts({
        artifactType: filterType || null,
        operation: filterOperation || null
      });
    }
  };

  // View artifact details - fetch full artifact and open in main pane
  const handleViewArtifact = async (artifact) => {
    const fullArtifact = await getArtifact(artifact.id);
    if (fullArtifact && onArtifactSelect) {
      onArtifactSelect(fullArtifact);
    }
  };

  // Delete artifact
  const handleDelete = async (artifactId, e) => {
    e.stopPropagation();
    if (window.confirm('Delete this artifact?')) {
      await deleteArtifact(artifactId);
    }
  };

  // Format date
  const formatDate = (dateString) => {
    if (!dateString) return 'Unknown';
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  // Get artifact type badge color
  const getTypeBadgeClass = (type) => {
    const colors = {
      report: 'badge-primary',
      extraction: 'badge-secondary',
      transformation: 'badge-accent',
      cluster_summary: 'badge-info',
      synthesis: 'badge-success',
      comparison: 'badge-warning'
    };
    return colors[type] || 'badge-neutral';
  };

  return (
    <div className="flex flex-col h-full bg-base-200">
      {/* Header */}
      <div className="p-4 bg-base-100 border-b border-base-300">
        <h2 className="text-xl font-bold mb-3">Artifacts</h2>

        {/* Search */}
        <form onSubmit={handleSearch} className="mb-3">
          <div className="join w-full">
            <input
              type="text"
              placeholder="Search artifacts..."
              className="input input-sm input-bordered join-item flex-1"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
            <button type="submit" className="btn btn-sm btn-primary join-item">
              Search
            </button>
          </div>
        </form>

        {/* Filters */}
        <div className="space-y-2">
          <select
            className="select select-sm select-bordered w-full"
            style={{ backgroundColor: '#1f2937', color: '#f9fafb' }}
            value={filterType}
            onChange={(e) => {
              setFilterType(e.target.value);
              setTimeout(handleFilterChange, 0);
            }}
          >
            <option value="">All Types</option>
            <option value="report">Report</option>
            <option value="extraction">Extraction</option>
            <option value="transformation">Transformation</option>
            <option value="cluster_summary">Cluster Summary</option>
            <option value="synthesis">Synthesis</option>
            <option value="comparison">Comparison</option>
          </select>

          <select
            className="select select-sm select-bordered w-full"
            style={{ backgroundColor: '#1f2937', color: '#f9fafb' }}
            value={filterOperation}
            onChange={(e) => {
              setFilterOperation(e.target.value);
              setTimeout(handleFilterChange, 0);
            }}
          >
            <option value="">All Operations</option>
            <option value="personify_rewrite">Personify Rewrite</option>
            <option value="semantic_search">Semantic Search</option>
            <option value="cluster_embeddings">Cluster Embeddings</option>
            <option value="paragraph_extract">Paragraph Extract</option>
          </select>
        </div>

        {/* Stats */}
        <div className="text-sm text-base-content/70 mt-2">
          {total} artifact{total !== 1 ? 's' : ''}
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="alert alert-error m-4">
          <span>{error}</span>
          <button onClick={clearError} className="btn btn-sm btn-ghost">✕</button>
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="flex items-center justify-center p-8">
          <span className="loading loading-spinner loading-lg"></span>
        </div>
      )}

      {/* Artifacts List */}
      <div className="flex-1 overflow-y-auto p-4 space-y-2">
        {!loading && artifacts.length === 0 && (
          <div className="text-center text-base-content/50 py-8">
            No artifacts found
          </div>
        )}

        {artifacts.map((artifact) => (
          <div
            key={artifact.id}
            className="card bg-base-100 shadow-sm hover:shadow-md transition-shadow cursor-pointer"
            onClick={() => handleViewArtifact(artifact)}
          >
            <div className="card-body p-3">
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className={`badge badge-sm ${getTypeBadgeClass(artifact.artifact_type)}`}>
                      {artifact.artifact_type}
                    </span>
                    <span className="text-xs text-base-content/50">
                      {formatDate(artifact.created_at)}
                    </span>
                  </div>
                  <div className="text-sm font-semibold mb-1 truncate">
                    {artifact.operation}
                  </div>
                  <div className="text-xs text-base-content/70 line-clamp-2">
                    {artifact.content?.substring(0, 100)}...
                  </div>
                  {artifact.topics && artifact.topics.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-2">
                      {artifact.topics.slice(0, 3).map((topic, idx) => (
                        <span key={idx} className="badge badge-xs badge-outline">{topic}</span>
                      ))}
                      {artifact.topics.length > 3 && (
                        <span className="badge badge-xs badge-outline">+{artifact.topics.length - 3}</span>
                      )}
                    </div>
                  )}
                </div>
                <button
                  onClick={(e) => handleDelete(artifact.id, e)}
                  className="btn btn-ghost btn-xs text-error"
                  title="Delete"
                >
                  ✕
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ArtifactBrowser;
