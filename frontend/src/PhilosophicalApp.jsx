import { useState, useMemo, useEffect } from 'react'
import axios from 'axios'
import './App.css'
import { checkTokenLimit, getWordCount, formatNumber } from './utils/tokenEstimator'
import MultiPerspectiveView from './components/MultiPerspectiveView'
import ContemplativeExercise from './components/ContemplativeExercise'
import SessionSidebar from './components/SessionSidebar'

/**
 * Humanizer - Language as a Sense
 *
 * Philosophical application for witnessing the constructed nature of meaning.
 * Supports multi-perspective transformations and contemplative practices.
 */
function PhilosophicalApp() {
  // Mode selection
  const [mode, setMode] = useState('transform') // 'transform', 'perspectives', 'contemplate'

  // Session state
  const [currentSession, setCurrentSession] = useState(null)
  const [sidebarVisible, setSidebarVisible] = useState(false)

  // Transformation state
  const [content, setContent] = useState('')
  const [persona, setPersona] = useState('')
  const [namespace, setNamespace] = useState('')
  const [style, setStyle] = useState('casual')
  const [depth, setDepth] = useState(0.5)
  const [preserveStructure, setPreserveStructure] = useState(true)

  // Results state
  const [transformationId, setTransformationId] = useState(null)
  const [status, setStatus] = useState(null)
  const [result, setResult] = useState(null)
  const [perspectives, setPerspectives] = useState(null)
  const [contemplativeExercise, setContemplativeExercise] = useState(null)

  // UI state
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [userTier] = useState('free')

  // Initialize or load session
  useEffect(() => {
    const loadCurrentSession = async () => {
      const savedSessionId = localStorage.getItem('current_session_id')
      if (savedSessionId) {
        try {
          const response = await axios.get(`http://localhost:8000/api/sessions/${savedSessionId}`)
          setCurrentSession(response.data)
        } catch (err) {
          console.error('Failed to load saved session:', err)
          localStorage.removeItem('current_session_id')
        }
      }
    }

    loadCurrentSession()
  }, [])

  const styles = ['formal', 'casual', 'academic', 'creative', 'technical', 'journalistic']

  // Real-time token validation
  const tokenInfo = useMemo(() => {
    if (!content) {
      return { tokenCount: 0, wordCount: 0, isWithinLimit: true, message: '', percentUsed: 0 }
    }
    const tokenCheck = checkTokenLimit(content, userTier)
    const wordCount = getWordCount(content)
    return { ...tokenCheck, wordCount }
  }, [content, userTier])

  // Single transformation
  const handleTransform = async () => {
    if (!content || !persona || !namespace) {
      setError('Please fill in all required fields')
      return
    }

    if (!tokenInfo.isWithinLimit) {
      setError(`Content too long: ${tokenInfo.message}`)
      return
    }

    // Ensure we have a session
    let sessionId = currentSession?.id
    if (!sessionId) {
      sessionId = await handleCreateSessionForTransformation()
      if (!sessionId) {
        setError('Failed to create session')
        setLoading(false)
        return
      }
    }

    const userId = localStorage.getItem('humanizer_user_id')

    setLoading(true)
    setError(null)
    setResult(null)
    setPerspectives(null)

    try {
      const response = await axios.post('/api/transform', {
        content,
        persona,
        namespace,
        style,
        depth,
        preserve_structure: preserveStructure,
        user_tier: userTier,
        session_id: sessionId,
        user_id: userId
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
            const resultResponse = await axios.get(`/api/transform/${id}/result`)
            setResult(resultResponse.data)

            // Refresh session to update transformation count
            if (currentSession) {
              const sessionResponse = await axios.get(`http://localhost:8000/api/sessions/${currentSession.id}`)
              setCurrentSession(sessionResponse.data)
            }

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

      setTimeout(() => clearInterval(pollInterval), 300000)

    } catch (err) {
      const errorDetail = err.response?.data?.detail
      // Handle validation errors (arrays of error objects)
      if (Array.isArray(errorDetail)) {
        setError(errorDetail.map(e => e.msg).join(', '))
      } else if (typeof errorDetail === 'string') {
        setError(errorDetail)
      } else {
        setError('Failed to start transformation')
      }
      setLoading(false)
    }
  }

  // Multi-perspective transformation
  const handleGeneratePerspectives = async () => {
    if (!content || !persona || !namespace) {
      setError('Please fill in all required fields')
      return
    }

    if (!tokenInfo.isWithinLimit) {
      setError(`Content too long: ${tokenInfo.message}`)
      return
    }

    // Ensure we have a session
    let sessionId = currentSession?.id
    if (!sessionId) {
      sessionId = await handleCreateSessionForTransformation()
      if (!sessionId) {
        setError('Failed to create session')
        setLoading(false)
        return
      }
    }

    const userId = localStorage.getItem('humanizer_user_id')

    setLoading(true)
    setError(null)
    setResult(null)
    setPerspectives(null)

    try {
      const response = await axios.post('/api/philosophical/perspectives', {
        content,
        persona,
        namespace,
        style,
        depth,
        preserve_structure: preserveStructure,
        user_tier: userTier,
        session_id: sessionId,
        user_id: userId
      })

      setPerspectives(response.data)

      // Refresh session to update transformation count
      if (currentSession) {
        const sessionResponse = await axios.get(`http://localhost:8000/api/sessions/${currentSession.id}`)
        setCurrentSession(sessionResponse.data)
      }

      setLoading(false)
    } catch (err) {
      const errorDetail = err.response?.data?.detail
      // Handle validation errors (arrays of error objects)
      if (Array.isArray(errorDetail)) {
        setError(errorDetail.map(e => e.msg).join(', '))
      } else if (typeof errorDetail === 'string') {
        setError(errorDetail)
      } else {
        setError('Failed to generate perspectives')
      }
      setLoading(false)
    }
  }

  // Contemplative exercise
  const handleGenerateExercise = async (exerciseType) => {
    if (!content) {
      setError('Please enter some text first')
      return
    }

    setLoading(true)
    setError(null)
    setContemplativeExercise(null)

    try {
      const response = await axios.post('/api/philosophical/contemplate', {
        exercise_type: exerciseType,
        content: content,
        user_stage: 2 // Could be made dynamic based on user history
      })

      setContemplativeExercise(response.data)
      setMode('contemplate')
      setLoading(false)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to generate exercise')
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
    setPerspectives(null)
    setContemplativeExercise(null)
    setError(null)
    setMode('transform')
  }

  // Session management handlers
  const handleSessionSelect = async (session) => {
    setCurrentSession(session)
    localStorage.setItem('current_session_id', session.id)

    // Load session transformations if any
    try {
      const response = await axios.get(`http://localhost:8000/api/sessions/${session.id}/transformations`)
      const transformations = response.data

      // Optionally load the most recent transformation
      if (transformations.length > 0) {
        const latest = transformations[transformations.length - 1]
        setContent(latest.source_text)
        setPersona(latest.persona)
        setNamespace(latest.namespace)
        setStyle(latest.style)
      }
    } catch (err) {
      console.error('Failed to load session transformations:', err)
    }
  }

  const handleNewSession = async (session) => {
    setCurrentSession(session)
    localStorage.setItem('current_session_id', session.id)
    handleReset()
  }

  const handleCreateSessionForTransformation = async () => {
    if (!content) return

    const userId = localStorage.getItem('humanizer_user_id')
    if (!userId) {
      setError('User not initialized')
      return
    }

    try {
      // Create a new session with auto-generated title
      const title = `${persona || 'Transformation'} - ${new Date().toLocaleDateString()}`
      const response = await axios.post('http://localhost:8000/api/sessions', {
        title,
        user_id: userId
      })

      const newSession = response.data
      setCurrentSession(newSession)
      localStorage.setItem('current_session_id', newSession.id)

      return newSession.id
    } catch (err) {
      console.error('Failed to create session:', err)
      return null
    }
  }

  return (
    <div className="min-h-screen bg-realm-subjective-dark text-white">
      {/* Session Sidebar */}
      <SessionSidebar
        currentSessionId={currentSession?.id}
        onSessionSelect={handleSessionSelect}
        onNewSession={handleNewSession}
        isVisible={sidebarVisible}
        onToggleVisibility={() => setSidebarVisible(!sidebarVisible)}
      />

      {/* Header */}
      <header className="bg-realm-subjective border-b border-realm-subjective-light">
        <div className="max-w-7xl mx-auto px-8 py-6">
          <h1 className="text-4xl font-contemplative font-bold mb-2 text-white">
            Humanizer
          </h1>
          <p className="text-gray-300 font-structural">
            Language as a Sense — Realizing Our Subjective Ontological Nature
          </p>

          {/* Mode Tabs */}
          <div className="mt-4 flex gap-2">
            <button
              onClick={() => setMode('transform')}
              className={`px-4 py-2 rounded-md font-structural transition-colors ${
                mode === 'transform'
                  ? 'bg-realm-symbolic text-white'
                  : 'bg-realm-subjective-light text-gray-400 hover:text-white'
              }`}
            >
              Transform
            </button>
            <button
              onClick={() => setMode('perspectives')}
              className={`px-4 py-2 rounded-md font-structural transition-colors ${
                mode === 'perspectives'
                  ? 'bg-realm-symbolic text-white'
                  : 'bg-realm-subjective-light text-gray-400 hover:text-white'
              }`}
            >
              Multi-Perspective
            </button>
            <button
              onClick={() => setMode('contemplate')}
              className={`px-4 py-2 rounded-md font-structural transition-colors ${
                mode === 'contemplate'
                  ? 'bg-realm-subjective-lighter text-white'
                  : 'bg-realm-subjective-light text-gray-400 hover:text-white'
              }`}
            >
              Contemplate
            </button>
          </div>

          {/* Session Indicator */}
          {currentSession && (
            <div className="mt-4 text-sm text-gray-400">
              <span className="font-structural">Current Session:</span>{' '}
              <span className="text-white font-semibold">{currentSession.title}</span>
              <span className="mx-2">•</span>
              <span>{currentSession.transformation_count} transformation{currentSession.transformation_count !== 1 ? 's' : ''}</span>
            </div>
          )}
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Input Section (Corporeal Realm) */}
          <div className="space-y-6">
            <div className="bg-realm-corporeal-dark border border-realm-corporeal p-6 rounded-lg">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-2xl font-structural font-semibold text-white">Input</h2>
                <span className="text-xs text-realm-corporeal-light uppercase tracking-wide">
                  Corporeal Realm
                </span>
              </div>

              <div className="space-y-4">
                {/* Content */}
                <div>
                  <label className="block text-sm font-structural font-medium mb-2 text-gray-300">
                    Source Text *
                  </label>
                  <textarea
                    className={`w-full h-48 px-3 py-2 bg-gray-900 border rounded-md focus:outline-none focus:ring-2 font-grounded ${
                      !tokenInfo.isWithinLimit && content
                        ? 'border-red-500 focus:ring-red-500'
                        : 'border-realm-corporeal focus:ring-realm-corporeal'
                    }`}
                    placeholder="Enter the text before meaning is constructed..."
                    value={content}
                    onChange={(e) => setContent(e.target.value)}
                    disabled={loading}
                  />

                  {/* Token counter */}
                  {content && (
                    <div className="mt-2 text-sm space-y-1">
                      <div className="flex justify-between items-center">
                        <span className="text-gray-400 font-structural">
                          {formatNumber(tokenInfo.wordCount)} words • {formatNumber(tokenInfo.tokenCount)} tokens
                        </span>
                        <span className={`font-medium ${
                          tokenInfo.isWithinLimit ? 'text-realm-corporeal-light' : 'text-red-400'
                        }`}>
                          {tokenInfo.percentUsed.toFixed(1)}%
                        </span>
                      </div>

                      <div className="w-full bg-gray-800 rounded-full h-2">
                        <div
                          className={`h-2 rounded-full transition-all duration-300 ${
                            tokenInfo.percentUsed > 100 ? 'bg-red-500' :
                            tokenInfo.percentUsed > 80 ? 'bg-yellow-500' :
                            'bg-realm-corporeal'
                          }`}
                          style={{ width: `${Math.min(tokenInfo.percentUsed, 100)}%` }}
                        />
                      </div>

                      {!tokenInfo.isWithinLimit && (
                        <div className="text-red-400 text-xs">
                          ⚠️ {tokenInfo.message}
                        </div>
                      )}
                    </div>
                  )}
                </div>

                {/* Belief Framework Parameters */}
                <div className="border-t border-realm-corporeal pt-4">
                  <h3 className="text-base font-structural font-semibold text-white mb-3 uppercase tracking-wide">
                    Belief Framework (Symbolic Realm)
                  </h3>

                  <div className="space-y-3">
                    <div>
                      <label className="block text-xs font-structural font-medium mb-1 text-gray-400">
                        PERSONA *
                        <span className="text-xs ml-2 font-normal italic">
                          (Voice/conscious position)
                        </span>
                      </label>
                      <input
                        type="text"
                        className="w-full px-3 py-2 bg-gray-900 border border-realm-symbolic-dark rounded-md focus:outline-none focus:ring-2 focus:ring-realm-symbolic font-structural text-sm"
                        placeholder="e.g., Scholar, Poet, Scientist"
                        value={persona}
                        onChange={(e) => setPersona(e.target.value)}
                        disabled={loading}
                      />
                    </div>

                    <div>
                      <label className="block text-xs font-structural font-medium mb-1 text-gray-400">
                        NAMESPACE *
                        <span className="text-xs ml-2 font-normal italic">
                          (Conceptual domain)
                        </span>
                      </label>
                      <input
                        type="text"
                        className="w-full px-3 py-2 bg-gray-900 border border-realm-symbolic-dark rounded-md focus:outline-none focus:ring-2 focus:ring-realm-symbolic font-structural text-sm"
                        placeholder="e.g., quantum-physics, mythology"
                        value={namespace}
                        onChange={(e) => setNamespace(e.target.value)}
                        disabled={loading}
                      />
                    </div>

                    <div>
                      <label className="block text-xs font-structural font-medium mb-1 text-gray-400">
                        STYLE
                      </label>
                      <select
                        className="w-full px-3 py-2 bg-gray-900 border border-realm-symbolic-dark rounded-md focus:outline-none focus:ring-2 focus:ring-realm-symbolic font-structural text-sm"
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
                      <label className="block text-xs font-structural font-medium mb-1 text-gray-400">
                        Depth: {depth.toFixed(2)}
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
                        <span className="text-xs font-structural text-gray-400">Preserve structure</span>
                      </label>
                    </div>
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="mt-6 space-y-2">
                {mode === 'transform' && (
                  <button
                    onClick={handleTransform}
                    disabled={loading || !content || !persona || !namespace || !tokenInfo.isWithinLimit}
                    className="w-full px-4 py-3 bg-realm-symbolic hover:bg-realm-symbolic-light disabled:bg-gray-700 disabled:cursor-not-allowed rounded-md font-structural font-medium transition-colors"
                  >
                    {loading ? 'Transforming...' : 'Transform Perspective'}
                  </button>
                )}

                {mode === 'perspectives' && (
                  <button
                    onClick={handleGeneratePerspectives}
                    disabled={loading || !content || !persona || !namespace || !tokenInfo.isWithinLimit}
                    className="w-full px-4 py-3 bg-realm-symbolic hover:bg-realm-symbolic-light disabled:bg-gray-700 disabled:cursor-not-allowed rounded-md font-structural font-medium transition-colors"
                  >
                    {loading ? 'Generating...' : 'Generate Multiple Perspectives'}
                  </button>
                )}

                {mode === 'contemplate' && (
                  <div className="space-y-2">
                    <button
                      onClick={() => handleGenerateExercise('word_dissolution')}
                      disabled={loading || !content}
                      className="w-full px-4 py-3 bg-realm-subjective-lighter hover:bg-realm-subjective-light disabled:bg-gray-700 disabled:cursor-not-allowed rounded-md font-structural font-medium transition-colors"
                    >
                      {loading ? 'Generating...' : 'Word Dissolution'}
                    </button>
                    <button
                      onClick={() => handleGenerateExercise('socratic_dialogue')}
                      disabled={loading || !content}
                      className="w-full px-4 py-3 bg-realm-symbolic hover:bg-realm-symbolic-light disabled:bg-gray-700 disabled:cursor-not-allowed rounded-md font-structural font-medium transition-colors"
                    >
                      {loading ? 'Generating...' : 'Socratic Dialogue'}
                    </button>
                    <button
                      onClick={() => handleGenerateExercise('witness')}
                      disabled={loading || !content}
                      className="w-full px-4 py-3 bg-realm-subjective hover:bg-realm-subjective-light disabled:bg-gray-700 disabled:cursor-not-allowed rounded-md font-structural font-medium transition-colors"
                    >
                      {loading ? 'Generating...' : 'Witness Prompt'}
                    </button>
                  </div>
                )}

                <button
                  onClick={handleReset}
                  disabled={loading}
                  className="w-full px-4 py-2 bg-gray-700 hover:bg-gray-600 disabled:bg-gray-800 disabled:cursor-not-allowed rounded-md font-structural transition-colors"
                >
                  Reset
                </button>
              </div>
            </div>
          </div>

          {/* Output Section */}
          <div className="space-y-6">
            {/* Error */}
            {error && (
              <div className="bg-red-900/20 border border-red-500 p-6 rounded-lg">
                <h3 className="text-red-400 font-structural font-semibold mb-2">Error</h3>
                <p className="text-sm">{error}</p>
              </div>
            )}

            {/* Single Result (Symbolic Realm) */}
            {result && mode === 'transform' && (
              <div className="bg-realm-symbolic-dark border border-realm-symbolic p-6 rounded-lg">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-2xl font-structural font-semibold text-white">Transformed</h2>
                  <span className="text-xs text-gray-400 uppercase tracking-wide">
                    Symbolic Realm
                  </span>
                </div>
                <div className="bg-gray-900 p-4 rounded-md max-h-96 overflow-y-auto">
                  <pre className="whitespace-pre-wrap text-sm font-contemplative text-gray-200">
                    {result.transformed_content}
                  </pre>
                </div>
                <div className="mt-4 text-xs text-gray-400 space-y-1 font-structural">
                  <div>Framework: {result.persona} / {result.namespace} / {result.style}</div>
                </div>
                <div className="mt-4 pt-4 border-t border-realm-symbolic text-xs text-gray-400 italic">
                  💡 This is one perspective. The same content can be constructed differently through other belief frameworks.
                </div>
              </div>
            )}

            {/* Multi-Perspective View */}
            {perspectives && mode === 'perspectives' && (
              <MultiPerspectiveView
                sourceText={perspectives.source_text}
                perspectives={perspectives.perspectives}
                philosophicalNote={perspectives.philosophical_note}
              />
            )}

            {/* Contemplative Exercise */}
            {contemplativeExercise && mode === 'contemplate' && (
              <ContemplativeExercise exercise={contemplativeExercise} />
            )}

            {/* Status */}
            {status && loading && (
              <div className="bg-gray-800 p-6 rounded-lg">
                <h3 className="text-lg font-structural font-semibold mb-4">Processing...</h3>
                <div className="w-full bg-gray-700 rounded-full h-2">
                  <div
                    className="bg-realm-symbolic h-2 rounded-full transition-all duration-300"
                    style={{ width: `${status.progress * 100}%` }}
                  />
                </div>
                <p className="text-sm text-gray-400 mt-2">{(status.progress * 100).toFixed(0)}%</p>
              </div>
            )}

            {/* Placeholder */}
            {!status && !error && !result && !perspectives && !contemplativeExercise && (
              <div className="bg-realm-subjective border border-realm-subjective-light p-8 rounded-lg text-center">
                <div className="text-6xl mb-4">✨</div>
                <p className="text-white font-contemplative text-xl mb-2">
                  Witness Language as a Sense
                </p>
                <p className="text-sm text-gray-400 font-structural">
                  Enter text and choose a mode to begin
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Philosophical Footer */}
        <div className="mt-8 pt-8 border-t border-realm-subjective-light">
          <div className="text-center space-y-2">
            <p className="text-sm text-gray-300 font-contemplative italic">
              "Language is not objective reality—it's a sense through which consciousness constructs meaning."
            </p>
            <p className="text-xs text-gray-500 font-structural">
              Three Realms: Corporeal (physical) • Symbolic (constructed) • Subjective (conscious)
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default PhilosophicalApp
