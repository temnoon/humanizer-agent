import { useState, useMemo } from 'react'
import axios from 'axios'
import './App.css'
import { checkTokenLimit, getWordCount, formatNumber } from './utils/tokenEstimator'
import NarrativeAnalyzer from './components/NarrativeAnalyzer'

function App() {
  const [activeTab, setActiveTab] = useState('transform') // 'transform' or 'narrative'
  const [content, setContent] = useState('')
  const [persona, setPersona] = useState('')
  const [namespace, setNamespace] = useState('')
  const [style, setStyle] = useState('casual')
  const [depth, setDepth] = useState(0.5)
  const [preserveStructure, setPreserveStructure] = useState(true)
  
  const [transformationId, setTransformationId] = useState(null)
  const [status, setStatus] = useState(null)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [userTier] = useState('free') // Could be made dynamic later

  const styles = [
    'formal',
    'casual',
    'academic',
    'creative',
    'technical',
    'journalistic'
  ]

  // Real-time token validation
  const tokenInfo = useMemo(() => {
    if (!content) {
      return { tokenCount: 0, wordCount: 0, isWithinLimit: true, message: '', percentUsed: 0 }
    }
    const tokenCheck = checkTokenLimit(content, userTier)
    const wordCount = getWordCount(content)
    return {
      ...tokenCheck,
      wordCount
    }
  }, [content, userTier])

  const handleTransform = async () => {
    if (!content || !persona || !namespace) {
      setError('Please fill in all required fields')
      return
    }

    // Check token limit before making API call
    if (!tokenInfo.isWithinLimit) {
      setError(`Content too long: ${tokenInfo.message}. Please shorten your text or upgrade to a premium account.`)
      return
    }

    setLoading(true)
    setError(null)
    setResult(null)

    try {
      // Start transformation
      const response = await axios.post('/api/transform', {
        content,
        persona,
        namespace,
        style,
        depth,
        preserve_structure: preserveStructure,
        user_tier: 'free' // Default to free tier
      })

      const id = response.data.id
      setTransformationId(id)

      // Poll for status
      const pollInterval = setInterval(async () => {
        try {
          const statusResponse = await axios.get(`/api/transform/${id}`)
          setStatus(statusResponse.data)

          if (statusResponse.data.status === 'completed') {
            clearInterval(pollInterval)
            // Fetch final result
            const resultResponse = await axios.get(`/api/transform/${id}/result`)
            setResult(resultResponse.data)
            setLoading(false)
          } else if (statusResponse.data.status === 'failed') {
            clearInterval(pollInterval)
            setError(statusResponse.data.error || 'Transformation failed')
            setLoading(false)
          }
        } catch (err) {
          clearInterval(pollInterval)
          setError('Failed to check status')
          setLoading(false)
        }
      }, 2000)

      // Timeout after 5 minutes
      setTimeout(() => {
        clearInterval(pollInterval)
        if (loading) {
          setError('Transformation timed out')
          setLoading(false)
        }
      }, 300000)

    } catch (err) {
      // Handle different error response formats
      let errorMessage = 'Failed to start transformation'
      
      if (err.response?.data?.detail) {
        if (typeof err.response.data.detail === 'string') {
          errorMessage = err.response.data.detail
        } else if (typeof err.response.data.detail === 'object') {
          // Handle detailed error object from token limit check
          if (err.response.data.detail.error && err.response.data.detail.message) {
            errorMessage = `${err.response.data.detail.error}: ${err.response.data.detail.message}`
            if (err.response.data.detail.token_count && err.response.data.detail.token_limit) {
              errorMessage += ` (${err.response.data.detail.token_count.toLocaleString()}/${err.response.data.detail.token_limit.toLocaleString()} tokens)`
            }
          } else {
            errorMessage = JSON.stringify(err.response.data.detail)
          }
        }
      }
      
      setError(errorMessage)
      setLoading(false)
    }
  }

  const handleReset = () => {
    setContent('')
    setPersona('')
    setNamespace('')
    setStyle('casual')
    setDepth(0.5)
    setPreserveStructure(true)
    setTransformationId(null)
    setStatus(null)
    setResult(null)
    setError(null)
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white p-8">
      <div className="max-w-6xl mx-auto">
        <header className="mb-8">
          <h1 className="text-4xl font-bold mb-2">🎭 Humanizer Agent</h1>
          <p className="text-gray-400">AI-powered narrative transformation using Claude Agent SDK</p>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Input Section */}
          <div className="space-y-6">
            <div className="bg-gray-800 p-6 rounded-lg">
              <h2 className="text-2xl font-semibold mb-4">Input</h2>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2">
                    Content *
                  </label>
                  <textarea
                    className={`w-full h-48 px-3 py-2 bg-gray-700 border rounded-md focus:outline-none focus:ring-2 ${
                      !tokenInfo.isWithinLimit && content 
                        ? 'border-red-500 focus:ring-red-500' 
                        : 'border-gray-600 focus:ring-blue-500'
                    }`}
                    placeholder="Enter the text you want to transform..."
                    value={content}
                    onChange={(e) => setContent(e.target.value)}
                    disabled={loading}
                  />
                  
                  {/* Token counter */}
                  {content && (
                    <div className="mt-2 text-sm space-y-1">
                      <div className="flex justify-between items-center">
                        <span className="text-gray-400">
                          {formatNumber(tokenInfo.wordCount)} words • {formatNumber(tokenInfo.tokenCount)} tokens (estimated)
                        </span>
                        <span className={`font-medium ${
                          tokenInfo.isWithinLimit ? 'text-green-400' : 'text-red-400'
                        }`}>
                          {tokenInfo.percentUsed.toFixed(1)}% of {userTier} limit
                        </span>
                      </div>
                      
                      {/* Progress bar */}
                      <div className="w-full bg-gray-700 rounded-full h-2">
                        <div
                          className={`h-2 rounded-full transition-all duration-300 ${
                            tokenInfo.percentUsed > 100 ? 'bg-red-500' :
                            tokenInfo.percentUsed > 80 ? 'bg-yellow-500' :
                            'bg-green-500'
                          }`}
                          style={{ width: `${Math.min(tokenInfo.percentUsed, 100)}%` }}
                        />
                      </div>
                      
                      {/* Warning message */}
                      {!tokenInfo.isWithinLimit && (
                        <div className="text-red-400 text-xs">
                          ⚠️ {tokenInfo.message}
                        </div>
                      )}
                    </div>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">
                    Persona * 
                    <span className="text-gray-400 text-xs ml-2">
                      (e.g., "Scholar", "Poet", "Scientist")
                    </span>
                  </label>
                  <input
                    type="text"
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Target persona/voice"
                    value={persona}
                    onChange={(e) => setPersona(e.target.value)}
                    disabled={loading}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">
                    Namespace *
                    <span className="text-gray-400 text-xs ml-2">
                      (e.g., "quantum-physics", "mythology", "business")
                    </span>
                  </label>
                  <input
                    type="text"
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Conceptual framework/domain"
                    value={namespace}
                    onChange={(e) => setNamespace(e.target.value)}
                    disabled={loading}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">
                    Style
                  </label>
                  <select
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    value={style}
                    onChange={(e) => setStyle(e.target.value)}
                    disabled={loading}
                  >
                    {styles.map(s => (
                      <option key={s} value={s}>{s}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">
                    Depth: {depth.toFixed(2)}
                    <span className="text-gray-400 text-xs ml-2">
                      (0=minimal, 1=deep)
                    </span>
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.1"
                    className="w-full"
                    value={depth}
                    onChange={(e) => setDepth(parseFloat(e.target.value))}
                    disabled={loading}
                  />
                </div>

                <div>
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      className="mr-2"
                      checked={preserveStructure}
                      onChange={(e) => setPreserveStructure(e.target.checked)}
                      disabled={loading}
                    />
                    <span className="text-sm">Preserve original structure</span>
                  </label>
                </div>
              </div>

              <div className="mt-6 flex gap-3">
                <button
                  onClick={handleTransform}
                  disabled={loading || !content || !persona || !namespace || !tokenInfo.isWithinLimit}
                  className={`flex-1 px-4 py-2 rounded-md font-medium transition-colors ${
                    !tokenInfo.isWithinLimit && content
                      ? 'bg-red-600 hover:bg-red-700 disabled:bg-red-600 disabled:cursor-not-allowed'
                      : 'bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed'
                  }`}
                  title={!tokenInfo.isWithinLimit && content ? 'Content exceeds token limit' : ''}
                >
                  {loading ? 'Transforming...' : 
                   !tokenInfo.isWithinLimit && content ? '⚠️ Content Too Long' :
                   '🚀 Transform'}
                </button>
                <button
                  onClick={handleReset}
                  disabled={loading}
                  className="px-4 py-2 bg-gray-600 hover:bg-gray-700 disabled:bg-gray-700 disabled:cursor-not-allowed rounded-md font-medium transition-colors"
                >
                  Reset
                </button>
              </div>
            </div>
          </div>

          {/* Output Section */}
          <div className="space-y-6">
            {/* Status */}
            {status && (
              <div className="bg-gray-800 p-6 rounded-lg">
                <h2 className="text-2xl font-semibold mb-4">Status</h2>
                <div className="space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="text-gray-400">Status:</span>
                    <span className={`font-medium ${
                      status.status === 'completed' ? 'text-green-400' :
                      status.status === 'failed' ? 'text-red-400' :
                      'text-yellow-400'
                    }`}>
                      {status.status}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-gray-400">Progress:</span>
                    <span className="font-medium">{(status.progress * 100).toFixed(0)}%</span>
                  </div>
                  <div className="w-full bg-gray-700 rounded-full h-2">
                    <div
                      className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${status.progress * 100}%` }}
                    />
                  </div>
                </div>
              </div>
            )}

            {/* Error */}
            {error && (
              <div className="bg-red-900/20 border border-red-500 p-6 rounded-lg">
                <h3 className="text-red-400 font-semibold mb-2">Error</h3>
                <p className="text-sm">{typeof error === 'string' ? error : JSON.stringify(error)}</p>
              </div>
            )}

            {/* Result */}
            {result && (
              <div className="bg-gray-800 p-6 rounded-lg">
                <h2 className="text-2xl font-semibold mb-4">✨ Transformed</h2>
                <div className="bg-gray-700 p-4 rounded-md max-h-96 overflow-y-auto">
                  <pre className="whitespace-pre-wrap text-sm">
                    {result.transformed_content}
                  </pre>
                </div>
                <div className="mt-4 text-xs text-gray-400 space-y-1">
                  <div>Persona: {result.persona}</div>
                  <div>Namespace: {result.namespace}</div>
                  <div>Style: {result.style}</div>
                </div>
              </div>
            )}

            {/* Placeholder */}
            {!status && !error && !result && (
              <div className="bg-gray-800 p-6 rounded-lg text-center text-gray-500">
                <div className="text-6xl mb-4">🎭</div>
                <p>Enter your content and transformation parameters to begin</p>
              </div>
            )}
          </div>
        </div>
      </div>
        </>
        )}
    </div>
  )
}

export default App
