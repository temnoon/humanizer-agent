import { useState, useEffect } from 'react'
import PropTypes from 'prop-types'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import axios from 'axios'

/**
 * ResultsModal - Display transformation job results
 *
 * Shows results based on job type:
 * - persona_transform: Transformed text chunks
 * - madhyamaka_detect: Detection analysis (eternalism/nihilism scores)
 * - madhyamaka_transform: Middle path alternatives
 * - perspectives: Multiple perspectives
 */
function ResultsModal({ job, onClose }) {
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const API_BASE = 'http://localhost:8000'

  useEffect(() => {
    if (job) {
      loadResults()
    }
  }, [job])

  const loadResults = async () => {
    setLoading(true)
    setError(null)

    try {
      const response = await axios.get(`${API_BASE}/api/pipeline/jobs/${job.id}/results`)
      setResults(response.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load results')
      console.error('Failed to load results:', err)
    } finally {
      setLoading(false)
    }
  }

  const renderPersonaTransform = (results) => {
    return (
      <div className="space-y-6">
        {results.map((result, idx) => (
          <div key={idx} className="bg-gray-800 rounded-lg p-6 border border-gray-700">
            <div className="text-xs text-gray-400 mb-4 flex justify-between items-center pb-3 border-b border-gray-700">
              <span className="font-semibold">Transformation Result #{idx + 1}</span>
              <span className="text-gray-500">{result.tokens_used} tokens • {result.processing_time_ms}ms</span>
            </div>
            <div className="prose prose-invert prose-lg max-w-none
                          prose-headings:font-bold prose-headings:tracking-tight
                          prose-h1:text-3xl prose-h1:mb-4 prose-h1:mt-6
                          prose-h2:text-2xl prose-h2:mb-3 prose-h2:mt-5
                          prose-h3:text-xl prose-h3:mb-2 prose-h3:mt-4
                          prose-p:mb-4 prose-p:leading-relaxed
                          prose-ul:my-4 prose-ul:space-y-2
                          prose-ol:my-4 prose-ol:space-y-2
                          prose-li:my-1
                          prose-blockquote:border-l-4 prose-blockquote:border-blue-500 prose-blockquote:pl-4 prose-blockquote:italic
                          prose-code:bg-gray-900 prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded prose-code:text-sm
                          prose-pre:bg-gray-900 prose-pre:border prose-pre:border-gray-700">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  // Ensure paragraphs have proper spacing
                  p: ({children}) => <p className="mb-4 leading-relaxed">{children}</p>,
                  // Style headings
                  h1: ({children}) => <h1 className="text-3xl font-bold mb-4 mt-6 text-white">{children}</h1>,
                  h2: ({children}) => <h2 className="text-2xl font-bold mb-3 mt-5 text-white">{children}</h2>,
                  h3: ({children}) => <h3 className="text-xl font-semibold mb-2 mt-4 text-gray-100">{children}</h3>,
                  // Style lists
                  ul: ({children}) => <ul className="my-4 space-y-2 list-disc pl-6">{children}</ul>,
                  ol: ({children}) => <ol className="my-4 space-y-2 list-decimal pl-6">{children}</ol>,
                  // Style code blocks
                  code: ({inline, children}) =>
                    inline
                      ? <code className="bg-gray-900 px-1.5 py-0.5 rounded text-sm text-blue-300">{children}</code>
                      : <code className="block bg-gray-900 p-3 rounded border border-gray-700 text-sm">{children}</code>
                }}
              >
                {result.content}
              </ReactMarkdown>
            </div>
          </div>
        ))}
      </div>
    )
  }

  const renderMadhyamakaDetect = (results) => {
    return (
      <div className="space-y-4">
        {results.map((result, idx) => {
          const metadata = result.metadata || {}
          const detection = metadata.detection_result || {}

          return (
            <div key={idx} className="bg-gray-800 rounded-lg p-4 border border-gray-700">
              <h3 className="text-lg font-semibold text-white mb-4">Analysis #{idx + 1}</h3>

              {detection.eternalism && (
                <div className="mb-4">
                  <h4 className="text-sm font-medium text-orange-400 mb-2">Eternalism Detection</h4>
                  <div className="bg-gray-900 rounded p-3 space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-400">Confidence:</span>
                      <span className="text-white font-mono">
                        {detection.eternalism.confidence?.toFixed(4) || 'N/A'}
                      </span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-400">Detected:</span>
                      <span className={`font-semibold ${detection.eternalism.eternalism_detected ? 'text-red-400' : 'text-green-400'}`}>
                        {detection.eternalism.eternalism_detected ? 'Yes' : 'No'}
                      </span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-400">Severity:</span>
                      <span className="text-gray-300">{detection.eternalism.severity || 'N/A'}</span>
                    </div>
                    {detection.eternalism.indicators && detection.eternalism.indicators.length > 0 && (
                      <div>
                        <span className="text-xs text-gray-500">Indicators:</span>
                        <ul className="list-disc list-inside text-xs text-gray-300 mt-1">
                          {detection.eternalism.indicators.map((p, i) => (
                            <li key={i}>
                              {typeof p === 'string' ? p : `${p.type || 'indicator'}: ${p.phrases?.join(', ') || p.evidence?.join(', ') || ''}`}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {detection.nihilism && (
                <div className="mb-4">
                  <h4 className="text-sm font-medium text-blue-400 mb-2">Nihilism Detection</h4>
                  <div className="bg-gray-900 rounded p-3 space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-400">Confidence:</span>
                      <span className="text-white font-mono">
                        {detection.nihilism.confidence?.toFixed(4) || 'N/A'}
                      </span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-400">Detected:</span>
                      <span className={`font-semibold ${detection.nihilism.nihilism_detected ? 'text-red-400' : 'text-green-400'}`}>
                        {detection.nihilism.nihilism_detected ? 'Yes' : 'No'}
                      </span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-400">Severity:</span>
                      <span className="text-gray-300">{detection.nihilism.severity || 'N/A'}</span>
                    </div>
                    {detection.nihilism.indicators && detection.nihilism.indicators.length > 0 && (
                      <div>
                        <span className="text-xs text-gray-500">Indicators:</span>
                        <ul className="list-disc list-inside text-xs text-gray-300 mt-1">
                          {detection.nihilism.indicators.map((p, i) => (
                            <li key={i}>
                              {typeof p === 'string' ? p : `${p.type || 'indicator'}: ${p.phrases?.join(', ') || p.evidence?.join(', ') || ''}`}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {detection.middle_path && (
                <div>
                  <h4 className="text-sm font-medium text-green-400 mb-2">Middle Path Proximity</h4>
                  <div className="bg-gray-900 rounded p-3 space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-400">Score:</span>
                      <span className="text-white font-mono">
                        {detection.middle_path.middle_path_score?.toFixed(4) || 'N/A'}
                      </span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-400">Proximity:</span>
                      <span className="text-gray-300">{detection.middle_path.proximity || 'N/A'}</span>
                    </div>
                    {detection.middle_path.indicators?.positive && detection.middle_path.indicators.positive.length > 0 && (
                      <div>
                        <span className="text-xs text-gray-500">Positive Indicators:</span>
                        <ul className="list-disc list-inside text-xs text-gray-300 mt-1">
                          {detection.middle_path.indicators.positive.map((ind, i) => (
                            <li key={i}>{ind.type}: {ind.evidence?.join(', ')}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {detection.error && (
                <div className="text-sm text-yellow-400 bg-yellow-900/20 rounded p-3">
                  Error: {detection.error}
                </div>
              )}
            </div>
          )
        })}
      </div>
    )
  }

  const renderMadhyamakaTransform = (results) => {
    return (
      <div className="space-y-6">
        {results.map((result, idx) => (
          <div key={idx} className="bg-gray-800 rounded-lg p-6 border border-gray-700">
            <div className="text-xs text-gray-400 mb-4 flex justify-between items-center pb-3 border-b border-gray-700">
              <span className="font-semibold">Middle Path Transformation #{idx + 1}</span>
              <span className="text-gray-500">{result.tokens_used || 0} tokens • {result.processing_time_ms || 0}ms</span>
            </div>
            <div className="prose prose-invert prose-lg max-w-none
                          prose-headings:font-bold prose-headings:tracking-tight
                          prose-h1:text-3xl prose-h1:mb-4 prose-h1:mt-6
                          prose-h2:text-2xl prose-h2:mb-3 prose-h2:mt-5
                          prose-h3:text-xl prose-h3:mb-2 prose-h3:mt-4
                          prose-p:mb-4 prose-p:leading-relaxed
                          prose-ul:my-4 prose-ul:space-y-2
                          prose-ol:my-4 prose-ol:space-y-2
                          prose-li:my-1
                          prose-blockquote:border-l-4 prose-blockquote:border-blue-500 prose-blockquote:pl-4 prose-blockquote:italic
                          prose-code:bg-gray-900 prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded prose-code:text-sm
                          prose-pre:bg-gray-900 prose-pre:border prose-pre:border-gray-700
                          prose-strong:text-green-400">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  // Ensure paragraphs have proper spacing
                  p: ({children}) => <p className="mb-4 leading-relaxed">{children}</p>,
                  // Style headings - H2 for alternatives with green left border
                  h1: ({children}) => <h1 className="text-3xl font-bold mb-4 mt-6 text-white">{children}</h1>,
                  h2: ({children}) => (
                    <h2 className="text-2xl font-bold mb-3 mt-6 pt-4 text-white border-l-4 border-green-500 pl-4 bg-gray-900/50 py-2 rounded-r">
                      {children}
                    </h2>
                  ),
                  h3: ({children}) => <h3 className="text-xl font-semibold mb-2 mt-4 text-gray-100">{children}</h3>,
                  // Style lists
                  ul: ({children}) => <ul className="my-4 space-y-2 list-disc pl-6">{children}</ul>,
                  ol: ({children}) => <ol className="my-4 space-y-2 list-decimal pl-6">{children}</ol>,
                  // Style code blocks
                  code: ({inline, children}) =>
                    inline
                      ? <code className="bg-gray-900 px-1.5 py-0.5 rounded text-sm text-blue-300">{children}</code>
                      : <code className="block bg-gray-900 p-3 rounded border border-gray-700 text-sm">{children}</code>,
                  // Style bold text (for "Improvements:", "Type:", etc.) in green
                  strong: ({children}) => <strong className="text-green-400 font-semibold">{children}</strong>,
                  // Style em (for notes) in italic gray
                  em: ({children}) => <em className="text-gray-400 italic">{children}</em>,
                  // Style horizontal rules
                  hr: () => <hr className="my-6 border-gray-700" />
                }}
              >
                {result.content}
              </ReactMarkdown>
            </div>
          </div>
        ))}
      </div>
    )
  }

  const renderPerspectives = (results) => {
    return (
      <div className="space-y-6">
        {results.map((result, idx) => {
          const metadata = result.metadata || {}
          const numPerspectives = metadata.num_perspectives || 3
          const perspectiveTypes = metadata.perspective_types || []

          return (
            <div key={idx} className="bg-gray-800 rounded-lg p-6 border border-gray-700">
              <div className="text-xs text-gray-400 mb-4 flex justify-between items-center pb-3 border-b border-gray-700">
                <div>
                  <span className="font-semibold">Multi-Perspective Analysis #{idx + 1}</span>
                  <span className="ml-3 text-gray-500">{numPerspectives} perspectives</span>
                </div>
                <span className="text-gray-500">{result.tokens_used} tokens • {result.processing_time_ms}ms</span>
              </div>
              <div className="prose prose-invert prose-lg max-w-none
                            prose-headings:font-bold prose-headings:tracking-tight
                            prose-h1:text-3xl prose-h1:mb-4 prose-h1:mt-6
                            prose-h2:text-2xl prose-h2:mb-3 prose-h2:mt-5 prose-h2:border-l-4 prose-h2:border-blue-500 prose-h2:pl-4
                            prose-h3:text-xl prose-h3:mb-2 prose-h3:mt-4
                            prose-p:mb-4 prose-p:leading-relaxed
                            prose-ul:my-4 prose-ul:space-y-2
                            prose-ol:my-4 prose-ol:space-y-2
                            prose-li:my-1
                            prose-blockquote:border-l-4 prose-blockquote:border-blue-500 prose-blockquote:pl-4 prose-blockquote:italic
                            prose-code:bg-gray-900 prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded prose-code:text-sm
                            prose-pre:bg-gray-900 prose-pre:border prose-pre:border-gray-700">
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  components={{
                    // Ensure paragraphs have proper spacing
                    p: ({children}) => <p className="mb-4 leading-relaxed">{children}</p>,
                    // Style headings - H2 for perspectives with blue left border
                    h1: ({children}) => <h1 className="text-3xl font-bold mb-4 mt-6 text-white">{children}</h1>,
                    h2: ({children}) => (
                      <h2 className="text-2xl font-bold mb-3 mt-6 pt-4 text-white border-l-4 border-blue-500 pl-4 bg-gray-900/50 py-2 rounded-r">
                        {children}
                      </h2>
                    ),
                    h3: ({children}) => <h3 className="text-xl font-semibold mb-2 mt-4 text-gray-100">{children}</h3>,
                    // Style lists
                    ul: ({children}) => <ul className="my-4 space-y-2 list-disc pl-6">{children}</ul>,
                    ol: ({children}) => <ol className="my-4 space-y-2 list-decimal pl-6">{children}</ol>,
                    // Style code blocks
                    code: ({inline, children}) =>
                      inline
                        ? <code className="bg-gray-900 px-1.5 py-0.5 rounded text-sm text-blue-300">{children}</code>
                        : <code className="block bg-gray-900 p-3 rounded border border-gray-700 text-sm">{children}</code>
                  }}
                >
                  {result.content}
                </ReactMarkdown>
              </div>
            </div>
          )
        })}
      </div>
    )
  }

  const renderResults = () => {
    if (!results || !results.results || results.results.length === 0) {
      return (
        <div className="text-center text-gray-400 py-8">
          No results found for this job.
        </div>
      )
    }

    switch (results.job_type) {
      case 'persona_transform':
        return renderPersonaTransform(results.results)
      case 'madhyamaka_detect':
        return renderMadhyamakaDetect(results.results)
      case 'madhyamaka_transform':
        return renderMadhyamakaTransform(results.results)
      case 'perspectives':
        return renderPerspectives(results.results)
      default:
        return (
          <div className="text-yellow-400">
            Unsupported job type: {results.job_type}
          </div>
        )
    }
  }

  if (!job) return null

  return (
    <div
      className="fixed inset-0 bg-black bg-opacity-80 z-50 flex items-center justify-center p-4"
      onClick={onClose}
    >
      <div
        className="bg-gray-900 rounded-lg shadow-2xl max-w-4xl w-full max-h-[90vh] flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="bg-gray-800 border-b border-gray-700 p-4 flex items-center justify-between rounded-t-lg">
          <div>
            <h2 className="text-lg font-bold text-white">
              {results?.job_name || job.name}
            </h2>
            <p className="text-sm text-gray-400">
              {results?.job_type || job.job_type}
              {results && ` • ${results.results?.length || 0} result(s)`}
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-700 rounded transition-colors text-gray-400 hover:text-white"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {loading && (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
              <span className="ml-3 text-gray-400">Loading results...</span>
            </div>
          )}

          {error && (
            <div className="bg-red-900/20 border border-red-500 rounded p-4 text-red-400">
              {error}
            </div>
          )}

          {!loading && !error && renderResults()}
        </div>

        {/* Footer */}
        <div className="bg-gray-800 border-t border-gray-700 p-4 rounded-b-lg">
          <button
            onClick={onClose}
            className="w-full px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-md transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  )
}

ResultsModal.propTypes = {
  job: PropTypes.shape({
    id: PropTypes.string.isRequired,
    name: PropTypes.string,
    job_type: PropTypes.string
  }),
  onClose: PropTypes.func.isRequired
}

export default ResultsModal
