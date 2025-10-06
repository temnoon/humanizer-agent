import { useState } from 'react'
import PropTypes from 'prop-types'
import axios from 'axios'

/**
 * MadhyamakaPanel - Middle Path detection and transformation
 *
 * Exposes the Madhyamaka API (Nagarjuna's philosophy):
 * - Detect eternalism (reification)
 * - Detect nihilism (denial)
 * - Generate middle path alternatives
 * - Detect clinging to views
 */
function MadhyamakaPanel({ isOpen, onClose, currentDocument, onResultReady }) {
  const [mode, setMode] = useState('detect') // detect, transform
  const [loading, setLoading] = useState(false)
  const [detection, setDetection] = useState(null)
  const [alternatives, setAlternatives] = useState(null)
  const [error, setError] = useState(null)

  const API_BASE = 'http://localhost:8000'

  const handleDetectEternalism = async () => {
    if (!currentDocument?.content) {
      setError('No document content available')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const response = await axios.post(`${API_BASE}/api/madhyamaka/detect/eternalism`, {
        content: currentDocument.content
      })

      setDetection({ type: 'eternalism', data: response.data })
      setLoading(false)
    } catch (err) {
      setError(err.response?.data?.detail || 'Detection failed')
      setLoading(false)
    }
  }

  const handleDetectNihilism = async () => {
    if (!currentDocument?.content) {
      setError('No document content available')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const response = await axios.post(`${API_BASE}/api/madhyamaka/detect/nihilism`, {
        content: currentDocument.content
      })

      setDetection({ type: 'nihilism', data: response.data })
      setLoading(false)
    } catch (err) {
      setError(err.response?.data?.detail || 'Detection failed')
      setLoading(false)
    }
  }

  const handleDetectMiddlePath = async () => {
    if (!currentDocument?.content) {
      setError('No document content available')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const response = await axios.post(`${API_BASE}/api/madhyamaka/detect/middle-path-proximity`, {
        content: currentDocument.content
      })

      setDetection({ type: 'middle_path', data: response.data })
      setLoading(false)
    } catch (err) {
      setError(err.response?.data?.detail || 'Detection failed')
      setLoading(false)
    }
  }

  const handleGenerateAlternatives = async () => {
    if (!currentDocument?.content) {
      setError('No document content available')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const response = await axios.post(`${API_BASE}/api/madhyamaka/transform/middle-path-alternatives`, {
        content: currentDocument.content,
        num_alternatives: 5,
        user_stage: 2
      })

      setAlternatives(response.data)
      setLoading(false)
    } catch (err) {
      setError(err.response?.data?.detail || 'Transformation failed')
      setLoading(false)
    }
  }

  const viewAlternative = (alt) => {
    if (onResultReady) {
      onResultReady({
        content: alt.text,
        type: 'markdown',
        metadata: {
          transformationType: 'middle_path',
          originalType: alt.type
        }
      })
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-y-0 right-0 w-96 bg-gray-900 border-l border-gray-800 shadow-xl z-50 flex flex-col overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-800">
        <div className="flex items-center space-x-2">
          <span className="text-2xl">☯️</span>
          <h2 className="text-lg font-structural font-semibold text-white">Middle Path</h2>
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

      {/* Mode Selector */}
      <div className="flex border-b border-gray-800">
        <button
          onClick={() => setMode('detect')}
          className={`flex-1 px-4 py-3 text-sm font-medium transition-colors ${
            mode === 'detect'
              ? 'text-white border-b-2 border-realm-symbolic bg-gray-800'
              : 'text-gray-400 hover:text-white hover:bg-gray-800'
          }`}
        >
          Detect
        </button>
        <button
          onClick={() => setMode('transform')}
          className={`flex-1 px-4 py-3 text-sm font-medium transition-colors ${
            mode === 'transform'
              ? 'text-white border-b-2 border-realm-symbolic bg-gray-800'
              : 'text-gray-400 hover:text-white hover:bg-gray-800'
          }`}
        >
          Transform
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* Detection Mode */}
        {mode === 'detect' && (
          <>
            <div className="space-y-2">
              <button
                onClick={handleDetectEternalism}
                disabled={loading || !currentDocument?.content}
                className="w-full px-4 py-2 bg-red-900 hover:bg-red-800 disabled:bg-gray-700 text-white rounded-md text-sm font-medium transition-colors"
              >
                Detect Eternalism
              </button>
              <button
                onClick={handleDetectNihilism}
                disabled={loading || !currentDocument?.content}
                className="w-full px-4 py-2 bg-blue-900 hover:bg-blue-800 disabled:bg-gray-700 text-white rounded-md text-sm font-medium transition-colors"
              >
                Detect Nihilism
              </button>
              <button
                onClick={handleDetectMiddlePath}
                disabled={loading || !currentDocument?.content}
                className="w-full px-4 py-2 bg-green-900 hover:bg-green-800 disabled:bg-gray-700 text-white rounded-md text-sm font-medium transition-colors"
              >
                Check Middle Path Proximity
              </button>
            </div>

            {/* Detection Results */}
            {detection && (
              <div className="bg-gray-800 p-4 rounded-md space-y-3">
                <div className="text-sm font-medium text-white capitalize">
                  {detection.type.replace(/_/g, ' ')} Detection
                </div>

                {/* Eternalism Results */}
                {detection.type === 'eternalism' && (
                  <>
                    <div className={`text-lg font-bold ${
                      detection.data.eternalism_detected ? 'text-red-400' : 'text-green-400'
                    }`}>
                      {detection.data.eternalism_detected ? 'Detected' : 'Not Detected'}
                    </div>
                    <div className="text-sm text-gray-400">
                      Confidence: {(detection.data.confidence * 100).toFixed(0)}%
                    </div>
                    {detection.data.indicators && detection.data.indicators.length > 0 && (
                      <div className="space-y-2">
                        <div className="text-xs text-gray-500">Indicators:</div>
                        {detection.data.indicators.map((indicator, idx) => (
                          <div key={idx} className="text-xs bg-gray-900 p-2 rounded text-gray-300">
                            {indicator}
                          </div>
                        ))}
                      </div>
                    )}
                    {detection.data.middle_path_alternatives && (
                      <div className="space-y-2">
                        <div className="text-xs text-gray-500">Middle Path Alternatives:</div>
                        {detection.data.middle_path_alternatives.map((alt, idx) => (
                          <div key={idx} className="bg-gray-900 p-2 rounded text-xs">
                            <div className="text-green-400 font-medium">{alt.suggestion}</div>
                            <div className="text-gray-400 mt-1">{alt.reframed}</div>
                          </div>
                        ))}
                      </div>
                    )}
                  </>
                )}

                {/* Nihilism Results */}
                {detection.type === 'nihilism' && (
                  <>
                    <div className={`text-lg font-bold ${
                      detection.data.nihilism_detected ? 'text-blue-400' : 'text-green-400'
                    }`}>
                      {detection.data.nihilism_detected ? 'Detected' : 'Not Detected'}
                    </div>
                    <div className="text-sm text-gray-400">
                      Confidence: {(detection.data.confidence * 100).toFixed(0)}%
                    </div>
                    {detection.data.middle_path_alternatives && (
                      <div className="space-y-2">
                        <div className="text-xs text-gray-500">Corrective Guidance:</div>
                        {detection.data.middle_path_alternatives.map((alt, idx) => (
                          <div key={idx} className="bg-gray-900 p-2 rounded text-xs">
                            <div className="text-blue-400 font-medium">{alt.suggestion}</div>
                            <div className="text-gray-400 mt-1">{alt.reframed}</div>
                          </div>
                        ))}
                      </div>
                    )}
                  </>
                )}

                {/* Middle Path Results */}
                {detection.type === 'middle_path' && (
                  <>
                    <div className="text-lg font-bold text-green-400">
                      Score: {(detection.data.middle_path_score * 100).toFixed(0)}%
                    </div>
                    {detection.data.analysis && (
                      <div className="text-sm text-gray-400 whitespace-pre-wrap">
                        {detection.data.analysis}
                      </div>
                    )}
                    {detection.data.celebration && (
                      <div className="text-sm text-green-400 italic">
                        {detection.data.celebration}
                      </div>
                    )}
                  </>
                )}

                {/* Teaching Moment */}
                {detection.data.teaching_moment && (
                  <div className="bg-realm-subjective/20 p-3 rounded border border-realm-subjective">
                    <div className="text-xs text-realm-subjective-lighter font-medium mb-1">
                      Teaching: {detection.data.teaching_moment.principle?.replace(/_/g, ' ')}
                    </div>
                    <div className="text-xs text-gray-400">
                      {detection.data.teaching_moment.guidance}
                    </div>
                  </div>
                )}
              </div>
            )}
          </>
        )}

        {/* Transform Mode */}
        {mode === 'transform' && (
          <>
            <div>
              <button
                onClick={handleGenerateAlternatives}
                disabled={loading || !currentDocument?.content}
                className="w-full px-4 py-2 bg-realm-symbolic hover:bg-realm-symbolic-light disabled:bg-gray-700 text-white rounded-md text-sm font-medium transition-colors"
              >
                {loading ? 'Generating...' : 'Generate Middle Path Alternatives'}
              </button>
            </div>

            {/* Alternatives Results */}
            {alternatives && alternatives.middle_path_alternatives && (
              <div className="space-y-2">
                <div className="text-sm font-medium text-gray-400">
                  {alternatives.middle_path_alternatives.length} Alternatives
                </div>
                <div className="text-xs text-gray-500 mb-2">
                  Extreme detected: {alternatives.extreme_type || 'balanced'}
                </div>
                {alternatives.middle_path_alternatives.map((alt, idx) => (
                  <div
                    key={idx}
                    onClick={() => viewAlternative(alt)}
                    className="bg-gray-800 p-3 rounded-md cursor-pointer hover:bg-gray-750 transition-colors"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="text-xs px-2 py-1 rounded bg-green-900/30 text-green-400">
                        {alt.type}
                      </div>
                      {alt.middle_path_score && (
                        <div className="text-xs text-gray-500">
                          Score: {(alt.middle_path_score * 100).toFixed(0)}%
                        </div>
                      )}
                    </div>
                    <div className="text-sm text-gray-300 line-clamp-3">
                      {alt.text}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </>
        )}

        {/* Error */}
        {error && (
          <div className="bg-red-900/20 border border-red-500 p-3 rounded-md">
            <div className="text-sm text-red-400">{error}</div>
          </div>
        )}
      </div>
    </div>
  )
}

MadhyamakaPanel.propTypes = {
  isOpen: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
  currentDocument: PropTypes.shape({
    content: PropTypes.string
  }),
  onResultReady: PropTypes.func
}

export default MadhyamakaPanel
