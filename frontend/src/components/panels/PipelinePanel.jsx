import { useState, useEffect } from 'react'
import PropTypes from 'prop-types'
import axios from 'axios'
import ResultsModal from './ResultsModal'

/**
 * PipelinePanel - Transformation Pipeline Operations
 *
 * Creates and manages transformation jobs on messages/chunks:
 * - persona_transform: Transform with PERSONA/NAMESPACE/STYLE
 * - madhyamaka_detect: Detect extreme views (eternalism/nihilism)
 * - madhyamaka_transform: Transform toward middle path
 * - perspectives: Generate multiple perspectives
 *
 * Tracks job progress and displays results.
 */
function PipelinePanel({ isOpen, onClose, currentMessage }) {
  const [jobType, setJobType] = useState('persona_transform')
  const [config, setConfig] = useState({
    persona: '',
    namespace: '',
    style: 'casual',
    depth: 0.5,
    user_stage: 3
  })
  const [jobs, setJobs] = useState([])
  const [activeJob, setActiveJob] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [resultsJob, setResultsJob] = useState(null)

  const API_BASE = 'http://localhost:8000'

  const jobTypes = [
    { value: 'persona_transform', label: '🎭 Persona Transform', requiresConfig: true },
    { value: 'madhyamaka_detect', label: '🔍 Madhyamaka Detect', requiresConfig: false },
    { value: 'madhyamaka_transform', label: '☸️ Middle Path Transform', requiresConfig: false },
    { value: 'perspectives', label: '🔮 Multi-Perspective', requiresConfig: false }
  ]

  const styles = ['formal', 'casual', 'academic', 'creative', 'technical', 'journalistic']

  // Load active jobs on mount
  useEffect(() => {
    if (isOpen) {
      loadJobs()
    }
  }, [isOpen])

  // Poll active job status
  useEffect(() => {
    if (!activeJob) return

    const pollInterval = setInterval(async () => {
      try {
        const response = await axios.get(`${API_BASE}/api/pipeline/jobs/${activeJob.id}`)
        const updatedJob = response.data

        setActiveJob(updatedJob)

        // Update in jobs list
        setJobs(prev => prev.map(j => j.id === updatedJob.id ? updatedJob : j))

        // Stop polling if complete or failed
        if (updatedJob.status === 'completed' || updatedJob.status === 'failed') {
          clearInterval(pollInterval)
        }
      } catch (err) {
        console.error('Failed to poll job status:', err)
        clearInterval(pollInterval)
      }
    }, 2000)

    return () => clearInterval(pollInterval)
  }, [activeJob?.id])

  const loadJobs = async () => {
    try {
      const response = await axios.get(`${API_BASE}/api/pipeline/jobs`, {
        params: { page: 1, page_size: 10 }
      })
      setJobs(response.data.jobs || [])
    } catch (err) {
      console.error('Failed to load jobs:', err)
    }
  }

  const handleStartJob = async () => {
    if (!currentMessage) {
      setError('No message selected')
      return
    }

    // Validate configuration for persona_transform
    if (jobType === 'persona_transform' && (!config.persona || !config.namespace)) {
      setError('Persona and namespace are required for transformation')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const requestBody = {
        name: `${jobType} on message ${currentMessage.id.substring(0, 8)}`,
        job_type: jobType,
        source_message_ids: [currentMessage.id],
        configuration: jobType === 'persona_transform' ? {
          persona: config.persona,
          namespace: config.namespace,
          style: config.style,
          depth: config.depth,
          preserve_structure: true
        } : jobType === 'madhyamaka_transform' ? {
          user_stage: config.user_stage
        } : {
          // Default config for other job types
        }
      }

      const response = await axios.post(`${API_BASE}/api/pipeline/jobs`, requestBody)

      const newJob = {
        id: response.data.id,
        name: response.data.name,
        job_type: response.data.job_type,
        status: response.data.status,
        total_items: response.data.total_items,
        created_at: response.data.created_at
      }

      setJobs(prev => [newJob, ...prev])
      setActiveJob(newJob)
      setLoading(false)

    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to start job')
      setLoading(false)
    }
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'pending': return 'text-gray-400'
      case 'running': return 'text-blue-400'
      case 'completed': return 'text-green-400'
      case 'failed': return 'text-red-400'
      default: return 'text-gray-400'
    }
  }

  const getStatusIcon = (status) => {
    switch (status) {
      case 'pending': return '⏳'
      case 'running': return '🔄'
      case 'completed': return '✓'
      case 'failed': return '✗'
      default: return '○'
    }
  }

  const requiresConfig = jobTypes.find(jt => jt.value === jobType)?.requiresConfig

  if (!isOpen) return null

  return (
    <div className="fixed inset-y-0 right-0 w-96 bg-gray-900 border-l border-gray-800 shadow-xl z-50 flex flex-col overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-800">
        <div className="flex items-center space-x-2">
          <span className="text-2xl">⚙️</span>
          <h2 className="text-lg font-structural font-semibold text-white">Pipeline</h2>
        </div>
        <button
          onClick={onClose}
          className="p-2 hover:bg-gray-800 rounded-md transition-colors text-gray-400 hover:text-white"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* Current Message Info */}
        {currentMessage && (
          <div className="bg-gray-800 p-3 rounded-md">
            <div className="text-xs text-gray-400 mb-1">Source Message</div>
            <div className="text-sm text-white">
              Message #{currentMessage.index || '?'}
            </div>
            <div className="text-xs text-gray-500 mt-1">
              {currentMessage.chunk_count || 1} chunk(s)
            </div>
          </div>
        )}

        {/* Job Type Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Operation
          </label>
          <select
            value={jobType}
            onChange={(e) => setJobType(e.target.value)}
            disabled={loading}
            className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-realm-symbolic"
          >
            {jobTypes.map(jt => (
              <option key={jt.value} value={jt.value}>{jt.label}</option>
            ))}
          </select>
        </div>

        {/* Configuration (for persona_transform) */}
        {requiresConfig && (
          <div className="space-y-3 bg-gray-800 p-3 rounded-md">
            <div className="text-xs text-gray-400 mb-2">Configuration</div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">
                Persona *
              </label>
              <input
                type="text"
                placeholder="e.g., Scholar, Poet"
                value={config.persona}
                onChange={(e) => setConfig({...config, persona: e.target.value})}
                disabled={loading}
                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white text-sm placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-realm-symbolic"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">
                Namespace *
              </label>
              <input
                type="text"
                placeholder="e.g., quantum-physics"
                value={config.namespace}
                onChange={(e) => setConfig({...config, namespace: e.target.value})}
                disabled={loading}
                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white text-sm placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-realm-symbolic"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">
                Style
              </label>
              <select
                value={config.style}
                onChange={(e) => setConfig({...config, style: e.target.value})}
                disabled={loading}
                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white text-sm focus:outline-none focus:ring-2 focus:ring-realm-symbolic"
              >
                {styles.map(s => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">
                Depth: {config.depth.toFixed(1)}
              </label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={config.depth}
                onChange={(e) => setConfig({...config, depth: parseFloat(e.target.value)})}
                disabled={loading}
                className="w-full"
              />
            </div>
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="bg-red-900/20 border border-red-500 p-3 rounded-md">
            <div className="text-sm text-red-400">{error}</div>
          </div>
        )}

        {/* Active Job Status */}
        {activeJob && (
          <div className="bg-gray-800 p-3 rounded-md border-l-4 border-blue-500">
            <div className="flex items-center justify-between mb-2">
              <div className="text-sm font-medium text-white">Active Job</div>
              <div className={`text-sm ${getStatusColor(activeJob.status)}`}>
                {getStatusIcon(activeJob.status)} {activeJob.status}
              </div>
            </div>
            <div className="text-xs text-gray-400 mb-2">{activeJob.name}</div>

            {activeJob.status === 'running' && activeJob.progress && (
              <div className="mt-2">
                <div className="w-full bg-gray-700 rounded-full h-2">
                  <div
                    className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                    style={{
                      width: `${activeJob.progress.progress_percentage || 0}%`
                    }}
                  />
                </div>
                <div className="text-xs text-gray-500 mt-1 text-right">
                  {activeJob.progress.processed_items || 0} / {activeJob.progress.total_items || 0}
                </div>
              </div>
            )}

            {activeJob.status === 'completed' && (
              <div className="mt-2">
                <button
                  className="w-full px-3 py-1.5 bg-green-600 hover:bg-green-700 text-white text-sm rounded-md transition-colors"
                  onClick={() => setResultsJob(activeJob)}
                >
                  View Results
                </button>
              </div>
            )}
          </div>
        )}

        {/* Recent Jobs */}
        <div>
          <div className="text-xs text-gray-400 mb-2">Recent Jobs</div>
          <div className="space-y-2">
            {jobs.length === 0 && (
              <div className="text-xs text-gray-500 text-center py-4">
                No jobs yet
              </div>
            )}
            {jobs.slice(0, 5).map(job => (
              <div
                key={job.id}
                onClick={() => setActiveJob(job)}
                className={`bg-gray-800 p-2 rounded-md text-xs cursor-pointer hover:bg-gray-750 transition-colors ${
                  activeJob?.id === job.id ? 'ring-2 ring-realm-symbolic' : ''
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="text-white truncate flex-1">{job.name}</div>
                  <div className={`ml-2 ${getStatusColor(job.status)}`}>
                    {getStatusIcon(job.status)}
                  </div>
                </div>
                <div className="text-gray-500 mt-1">
                  {new Date(job.created_at).toLocaleTimeString()}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-gray-800">
        <button
          onClick={handleStartJob}
          disabled={loading || !currentMessage || (requiresConfig && (!config.persona || !config.namespace))}
          className="w-full px-4 py-2 bg-realm-symbolic hover:bg-realm-symbolic-light disabled:bg-gray-700 disabled:cursor-not-allowed text-white rounded-md font-medium transition-colors"
        >
          {loading ? 'Starting...' : '🚀 Start Job'}
        </button>
      </div>

      {/* Results Modal */}
      {resultsJob && (
        <ResultsModal
          job={resultsJob}
          onClose={() => setResultsJob(null)}
        />
      )}
    </div>
  )
}

PipelinePanel.propTypes = {
  isOpen: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
  currentMessage: PropTypes.shape({
    id: PropTypes.string,
    index: PropTypes.number,
    chunk_count: PropTypes.number
  })
}

export default PipelinePanel
