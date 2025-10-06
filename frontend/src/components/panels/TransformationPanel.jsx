import { useState, useMemo } from 'react'
import PropTypes from 'prop-types'
import axios from 'axios'
import { checkTokenLimit, getWordCount, formatNumber } from '../../utils/tokenEstimator'

/**
 * TransformationPanel - Text transformation interface
 *
 * Exposes the transformation API:
 * - PERSONA/NAMESPACE/STYLE transformations
 * - Real-time token validation
 * - Progress tracking
 * - Result viewing
 */
function TransformationPanel({ isOpen, onClose, currentDocument, onResultReady }) {
  const [persona, setPersona] = useState('')
  const [namespace, setNamespace] = useState('')
  const [style, setStyle] = useState('casual')
  const [depth, setDepth] = useState(0.5)
  const [preserveStructure, setPreserveStructure] = useState(true)
  const [transforming, setTransforming] = useState(false)
  const [progress, setProgress] = useState(0)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  const API_BASE = 'http://localhost:8000'

  const styles = ['formal', 'casual', 'academic', 'creative', 'technical', 'journalistic']

  // Token validation
  const tokenInfo = useMemo(() => {
    const content = currentDocument?.content || ''
    if (!content) return { tokenCount: 0, wordCount: 0, isWithinLimit: true, percentUsed: 0 }

    const tokenCheck = checkTokenLimit(content, 'free')
    const wordCount = getWordCount(content)
    return { ...tokenCheck, wordCount }
  }, [currentDocument])

  const handleTransform = async () => {
    if (!currentDocument?.content || !persona || !namespace) {
      setError('Please provide content, persona, and namespace')
      return
    }

    if (!tokenInfo.isWithinLimit) {
      setError(`Content too long: ${tokenInfo.message}`)
      return
    }

    setTransforming(true)
    setError(null)
    setResult(null)
    setProgress(0)

    try {
      // Start transformation
      const response = await axios.post(`${API_BASE}/api/transform`, {
        content: currentDocument.content,
        persona,
        namespace,
        style,
        depth,
        preserve_structure: preserveStructure,
        user_tier: 'free'
      })

      const id = response.data.id

      // Poll for status
      const pollInterval = setInterval(async () => {
        try {
          const statusResponse = await axios.get(`${API_BASE}/api/transform/${id}`)
          setProgress(statusResponse.data.progress)

          if (statusResponse.data.status === 'completed') {
            clearInterval(pollInterval)
            const resultResponse = await axios.get(`${API_BASE}/api/transform/${id}/result`)
            setResult(resultResponse.data)
            setTransforming(false)

            // Notify parent of result
            if (onResultReady) {
              onResultReady({
                content: resultResponse.data.transformed_content,
                type: currentDocument.type,
                metadata: {
                  persona,
                  namespace,
                  style,
                  originalId: currentDocument.id
                }
              })
            }
          } else if (statusResponse.data.status === 'failed') {
            clearInterval(pollInterval)
            setError(statusResponse.data.error || 'Transformation failed')
            setTransforming(false)
          }
        } catch (err) {
          clearInterval(pollInterval)
          setError('Failed to check status')
          setTransforming(false)
        }
      }, 2000)

      setTimeout(() => {
        clearInterval(pollInterval)
        if (transforming) {
          setError('Transformation timed out')
          setTransforming(false)
        }
      }, 300000)

    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to start transformation')
      setTransforming(false)
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-y-0 right-0 w-96 bg-gray-900 border-l border-gray-800 shadow-xl z-50 flex flex-col overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-800">
        <div className="flex items-center space-x-2">
          <span className="text-2xl">🎭</span>
          <h2 className="text-lg font-structural font-semibold text-white">Transform</h2>
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
        {/* Document Info */}
        {currentDocument && (
          <div className="bg-gray-800 p-3 rounded-md">
            <div className="text-xs text-gray-400 mb-1">Current Document</div>
            <div className="text-sm text-white truncate">
              {currentDocument.content?.substring(0, 80)}...
            </div>
            <div className="flex items-center justify-between mt-2 text-xs text-gray-400">
              <span>{formatNumber(tokenInfo.wordCount)} words</span>
              <span className={tokenInfo.isWithinLimit ? 'text-green-400' : 'text-red-400'}>
                {formatNumber(tokenInfo.tokenCount)} tokens
              </span>
            </div>
          </div>
        )}

        {/* Transformation Parameters */}
        <div className="space-y-3">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Persona *
            </label>
            <input
              type="text"
              placeholder="e.g., Scholar, Poet, Scientist"
              value={persona}
              onChange={(e) => setPersona(e.target.value)}
              disabled={transforming}
              className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-md text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-realm-symbolic"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Namespace *
            </label>
            <input
              type="text"
              placeholder="e.g., quantum-physics, mythology"
              value={namespace}
              onChange={(e) => setNamespace(e.target.value)}
              disabled={transforming}
              className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-md text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-realm-symbolic"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Style
            </label>
            <select
              value={style}
              onChange={(e) => setStyle(e.target.value)}
              disabled={transforming}
              className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-realm-symbolic"
            >
              {styles.map(s => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Depth: {depth.toFixed(2)}
            </label>
            <input
              type="range"
              min="0"
              max="1"
              step="0.1"
              value={depth}
              onChange={(e) => setDepth(parseFloat(e.target.value))}
              disabled={transforming}
              className="w-full"
            />
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>Minimal</span>
              <span>Deep</span>
            </div>
          </div>

          <div>
            <label className="flex items-center text-sm text-gray-300">
              <input
                type="checkbox"
                checked={preserveStructure}
                onChange={(e) => setPreserveStructure(e.target.checked)}
                disabled={transforming}
                className="mr-2"
              />
              Preserve structure
            </label>
          </div>
        </div>

        {/* Progress */}
        {transforming && (
          <div className="bg-gray-800 p-3 rounded-md">
            <div className="text-sm text-gray-300 mb-2">Transforming...</div>
            <div className="w-full bg-gray-700 rounded-full h-2">
              <div
                className="bg-realm-symbolic h-2 rounded-full transition-all duration-300"
                style={{ width: `${progress * 100}%` }}
              />
            </div>
            <div className="text-xs text-gray-500 mt-1 text-right">
              {(progress * 100).toFixed(0)}%
            </div>
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="bg-red-900/20 border border-red-500 p-3 rounded-md">
            <div className="text-sm text-red-400">{error}</div>
          </div>
        )}

        {/* Result Preview */}
        {result && (
          <div className="bg-gray-800 p-3 rounded-md">
            <div className="text-sm font-medium text-green-400 mb-2">✓ Complete</div>
            <div className="text-xs text-gray-400 mb-2">
              {result.transformed_content.length} characters
            </div>
            <button
              onClick={() => onResultReady && onResultReady({
                content: result.transformed_content,
                type: currentDocument.type,
                metadata: { persona, namespace, style }
              })}
              className="w-full px-3 py-2 bg-realm-corporeal hover:bg-realm-corporeal-light text-white rounded-md text-sm transition-colors"
            >
              View Result
            </button>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-gray-800">
        <button
          onClick={handleTransform}
          disabled={transforming || !currentDocument?.content || !persona || !namespace || !tokenInfo.isWithinLimit}
          className="w-full px-4 py-2 bg-realm-symbolic hover:bg-realm-symbolic-light disabled:bg-gray-700 disabled:cursor-not-allowed text-white rounded-md font-medium transition-colors"
        >
          {transforming ? 'Transforming...' : '🚀 Transform'}
        </button>
      </div>
    </div>
  )
}

TransformationPanel.propTypes = {
  isOpen: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
  currentDocument: PropTypes.shape({
    id: PropTypes.string,
    content: PropTypes.string,
    type: PropTypes.string
  }),
  onResultReady: PropTypes.func
}

export default TransformationPanel
