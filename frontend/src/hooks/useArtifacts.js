/**
 * useArtifacts Hook
 *
 * React hook for interacting with the artifacts API.
 * Provides methods for listing, searching, creating, and managing artifacts.
 */

import { useState, useEffect, useCallback } from 'react';

const API_BASE = 'http://localhost:8000';

export const useArtifacts = () => {
  const [artifacts, setArtifacts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [total, setTotal] = useState(0);

  /**
   * List artifacts with optional filters
   */
  const listArtifacts = useCallback(async (options = {}) => {
    const {
      artifactType = null,
      operation = null,
      limit = 50,
      offset = 0
    } = options;

    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams({ limit, offset });
      if (artifactType) params.append('artifact_type', artifactType);
      if (operation) params.append('operation', operation);

      const response = await fetch(`${API_BASE}/api/artifacts?${params}`);

      if (!response.ok) {
        throw new Error(`Failed to list artifacts: ${response.statusText}`);
      }

      const data = await response.json();
      setArtifacts(data.artifacts || []);
      setTotal(data.total || 0);

      return data;
    } catch (err) {
      setError(err.message);
      console.error('List artifacts error:', err);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Search artifacts semantically
   */
  const searchArtifacts = useCallback(async (query, options = {}) => {
    const {
      artifactType = null,
      limit = 20
    } = options;

    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams({ query, limit });
      if (artifactType) params.append('artifact_type', artifactType);

      const response = await fetch(`${API_BASE}/api/artifacts/search?${params}`);

      if (!response.ok) {
        throw new Error(`Failed to search artifacts: ${response.statusText}`);
      }

      const data = await response.json();
      setArtifacts(data.artifacts || []);
      setTotal(data.total || 0);

      return data;
    } catch (err) {
      setError(err.message);
      console.error('Search artifacts error:', err);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Get a single artifact by ID
   */
  const getArtifact = useCallback(async (artifactId) => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE}/api/artifacts/${artifactId}`);

      if (!response.ok) {
        throw new Error(`Failed to get artifact: ${response.statusText}`);
      }

      const data = await response.json();
      return data;
    } catch (err) {
      setError(err.message);
      console.error('Get artifact error:', err);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Create a new artifact
   */
  const createArtifact = useCallback(async (artifactData) => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE}/api/artifacts/save`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(artifactData),
      });

      if (!response.ok) {
        throw new Error(`Failed to create artifact: ${response.statusText}`);
      }

      const data = await response.json();

      // Refresh the artifacts list
      await listArtifacts();

      return data;
    } catch (err) {
      setError(err.message);
      console.error('Create artifact error:', err);
      return null;
    } finally {
      setLoading(false);
    }
  }, [listArtifacts]);

  /**
   * Update an existing artifact
   */
  const updateArtifact = useCallback(async (artifactId, updates) => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE}/api/artifacts/${artifactId}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(updates),
      });

      if (!response.ok) {
        throw new Error(`Failed to update artifact: ${response.statusText}`);
      }

      const data = await response.json();

      // Update the artifact in the list
      setArtifacts(prev =>
        prev.map(a => a.id === artifactId ? data : a)
      );

      return data;
    } catch (err) {
      setError(err.message);
      console.error('Update artifact error:', err);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Delete an artifact
   */
  const deleteArtifact = useCallback(async (artifactId) => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE}/api/artifacts/${artifactId}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error(`Failed to delete artifact: ${response.statusText}`);
      }

      // Remove from the list
      setArtifacts(prev => prev.filter(a => a.id !== artifactId));
      setTotal(prev => prev - 1);

      return true;
    } catch (err) {
      setError(err.message);
      console.error('Delete artifact error:', err);
      return false;
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Get artifact lineage (ancestry and descendants)
   */
  const getLineage = useCallback(async (artifactId) => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE}/api/artifacts/${artifactId}/lineage`);

      if (!response.ok) {
        throw new Error(`Failed to get lineage: ${response.statusText}`);
      }

      const data = await response.json();
      return data;
    } catch (err) {
      setError(err.message);
      console.error('Get lineage error:', err);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    // State
    artifacts,
    loading,
    error,
    total,

    // Methods
    listArtifacts,
    searchArtifacts,
    getArtifact,
    createArtifact,
    updateArtifact,
    deleteArtifact,
    getLineage,

    // Utils
    clearError: () => setError(null),
  };
};

export default useArtifacts;
