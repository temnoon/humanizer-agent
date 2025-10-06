import { useState } from 'react'
import PropTypes from 'prop-types'
import axios from 'axios'
import ArchiveImporter from '../ArchiveImporter'

/**
 * ArchivePanel - Archive analysis and belief pattern detection
 *
 * Exposes archive analysis features:
 * - Belief pattern detection
 * - Emotional analysis
 * - Framework suggestions
 */
function ArchivePanel({ isOpen, onClose, currentDocument }) {
  const [activeTab, setActiveTab] = useState('import')  // 'import' or 'analyze'
  const [loading, setLoading] = useState(false)
  const [analysis, setAnalysis] = useState(null)
  const [error, setError] = useState(null)

  const API_BASE = 'http://localhost:8000'

  const handleAnalyzeArchive = async () => {
    if (!currentDocument?.content) {
      setError('No document content available')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const response = await axios.post(`${API_BASE}/api/philosophical/archive/analyze`, {
        content: currentDocument.content
      })

      setAnalysis(response.data)
      setLoading(false)
    } catch (err) {
      setError(err.response?.data?.detail || 'Analysis failed')
      setLoading(false)
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-y-0 right-0 w-96 bg-gray-900 border-l border-gray-800 shadow-xl z-50 flex flex-col overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-800">
        <div className="flex items-center space-x-2">
          <span className="text-2xl">🗄️</span>
          <h2 className="text-lg font-structural font-semibold text-white">Archive</h2>
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

      {/* Tabs */}
      <div className="flex border-b border-gray-800">
        <button
          onClick={() => setActiveTab('import')}
          className={`flex-1 px-4 py-3 text-sm font-medium transition-colors ${
            activeTab === 'import'
              ? 'text-blue-400 border-b-2 border-blue-400'
              : 'text-gray-400 hover:text-gray-300'
          }`}
        >
          Import Archive
        </button>
        <button
          onClick={() => setActiveTab('analyze')}
          className={`flex-1 px-4 py-3 text-sm font-medium transition-colors ${
            activeTab === 'analyze'
              ? 'text-blue-400 border-b-2 border-blue-400'
              : 'text-gray-400 hover:text-gray-300'
          }`}
        >
          Analyze Document
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {activeTab === 'import' ? (
          <ArchiveImporter />
        ) : (
          <>
            <div className="text-sm text-gray-400">
              Analyze your written archives to detect belief patterns, emotional states, and framework evolution over time.
            </div>

            <button
              onClick={handleAnalyzeArchive}
              disabled={loading || !currentDocument?.content}
              className="w-full px-4 py-2 bg-realm-corporeal hover:bg-realm-corporeal-light disabled:bg-gray-700 text-white rounded-md text-sm font-medium transition-colors"
            >
              {loading ? 'Analyzing...' : 'Analyze Document'}
            </button>

            {/* Analysis Results */}
            {analysis && (
          <div className="space-y-3">
            {/* Belief Patterns */}
            {analysis.belief_patterns && analysis.belief_patterns.length > 0 && (
              <div className="bg-gray-800 p-3 rounded-md">
                <div className="text-sm font-medium text-gray-300 mb-2">Belief Patterns</div>
                <div className="space-y-2">
                  {analysis.belief_patterns.map((pattern, idx) => (
                    <div key={idx} className="bg-gray-900 p-2 rounded text-xs">
                      <div className="text-realm-corporeal-light font-medium">{pattern.pattern}</div>
                      <div className="text-gray-400 mt-1">{pattern.description}</div>
                      {pattern.confidence && (
                        <div className="text-gray-500 mt-1">
                          Confidence: {(pattern.confidence * 100).toFixed(0)}%
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Emotional State */}
            {analysis.emotional_state && (
              <div className="bg-gray-800 p-3 rounded-md">
                <div className="text-sm font-medium text-gray-300 mb-2">Emotional State</div>
                <div className="text-sm text-gray-400">
                  {typeof analysis.emotional_state === 'string'
                    ? analysis.emotional_state
                    : JSON.stringify(analysis.emotional_state, null, 2)}
                </div>
              </div>
            )}

            {/* Framework Suggestions */}
            {analysis.framework_suggestions && analysis.framework_suggestions.length > 0 && (
              <div className="bg-gray-800 p-3 rounded-md">
                <div className="text-sm font-medium text-gray-300 mb-2">Framework Suggestions</div>
                <div className="space-y-2">
                  {analysis.framework_suggestions.map((suggestion, idx) => (
                    <div key={idx} className="bg-gray-900 p-2 rounded text-xs">
                      <div className="text-realm-symbolic-light font-medium">
                        {suggestion.persona} / {suggestion.namespace}
                      </div>
                      <div className="text-gray-400 mt-1">{suggestion.reason}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Awakening Moments */}
            {analysis.awakening_moments && analysis.awakening_moments.length > 0 && (
              <div className="bg-gray-800 p-3 rounded-md">
                <div className="text-sm font-medium text-gray-300 mb-2">Awakening Moments</div>
                <div className="space-y-2">
                  {analysis.awakening_moments.map((moment, idx) => (
                    <div key={idx} className="bg-gray-900 p-2 rounded text-xs text-gray-400">
                      {moment}
                    </div>
                  ))}
                </div>
              </div>
            )}
              </div>
            )}

            {/* Error */}
            {error && (
              <div className="bg-red-900/20 border border-red-500 p-3 rounded-md">
                <div className="text-sm text-red-400">{error}</div>
              </div>
            )}

            {/* Coming Soon */}
            <div className="bg-gray-800 p-4 rounded-md border border-gray-700">
              <div className="text-sm font-medium text-gray-400 mb-2">Coming Soon</div>
              <ul className="text-xs text-gray-500 space-y-1">
                <li>• Timeline visualization of belief evolution</li>
                <li>• Network graph of connected concepts</li>
                <li>• Multi-document pattern detection</li>
                <li>• Emotional journey mapping</li>
              </ul>
            </div>
          </>
        )}
      </div>
    </div>
  )
}

ArchivePanel.propTypes = {
  isOpen: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
  currentDocument: PropTypes.shape({
    content: PropTypes.string
  })
}

export default ArchivePanel
