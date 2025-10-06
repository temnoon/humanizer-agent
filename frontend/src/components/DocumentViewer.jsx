import { useState, useEffect, useMemo } from 'react'
import PropTypes from 'prop-types'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import remarkMath from 'remark-math'
import rehypeKatex from 'rehype-katex'
import 'katex/dist/katex.min.css'

/**
 * DocumentViewer - Advanced document rendering with phrase flagging
 *
 * Features:
 * - Markdown rendering with GFM (tables, task lists, etc.)
 * - LaTeX/Math support via KaTeX
 * - Code syntax highlighting
 * - Phrase flagging and highlighting
 * - Editable/read-only modes
 * - Export options
 */
function DocumentViewer({
  document,
  onDocumentChange,
  onCompare,
  selectedMessage,
  className = '',
  splitMode = false,
  readOnly = false
}) {
  const [editMode, setEditMode] = useState(false)
  const [content, setContent] = useState(document?.content || '')
  const [showFlagged, setShowFlagged] = useState(true)
  const [flaggedPhrases, setFlaggedPhrases] = useState([])

  useEffect(() => {
    setContent(document?.content || '')
  }, [document])

  // Phrase flagging patterns (configurable)
  const flagPatterns = useMemo(() => [
    {
      id: 'llm-slop',
      pattern: /\b(delve|leverage|robust|holistic|synergy|paradigm shift|cutting-edge|state-of-the-art|in today's world|it's important to note|dive deep)\b/gi,
      label: 'LLM Slop',
      color: 'text-red-400',
      bgColor: 'bg-red-900/30'
    },
    {
      id: 'hedge-words',
      pattern: /\b(perhaps|maybe|possibly|might|could|would|should)\b/gi,
      label: 'Hedge Words',
      color: 'text-yellow-400',
      bgColor: 'bg-yellow-900/30'
    },
    {
      id: 'academic-jargon',
      pattern: /\b(aforementioned|hereby|heretofore|pursuant|notwithstanding|vis-à-vis)\b/gi,
      label: 'Academic Jargon',
      color: 'text-purple-400',
      bgColor: 'bg-purple-900/30'
    }
  ], [])

  // Detect flagged phrases
  useEffect(() => {
    const detected = []
    flagPatterns.forEach(pattern => {
      const matches = content.matchAll(pattern.pattern)
      for (const match of matches) {
        detected.push({
          text: match[0],
          index: match.index,
          patternId: pattern.id,
          label: pattern.label,
          color: pattern.color,
          bgColor: pattern.bgColor
        })
      }
    })
    setFlaggedPhrases(detected)
  }, [content, flagPatterns])

  const handleContentChange = (newContent) => {
    setContent(newContent)
    if (onDocumentChange) {
      onDocumentChange({
        ...document,
        content: newContent
      })
    }
  }

  const handleSave = () => {
    if (onDocumentChange) {
      onDocumentChange({
        ...document,
        content
      })
    }
    setEditMode(false)
  }

  const highlightFlaggedText = (text) => {
    if (!showFlagged || flaggedPhrases.length === 0) {
      return text
    }

    let highlighted = text
    const sortedPhrases = [...flaggedPhrases].sort((a, b) => b.index - a.index)

    sortedPhrases.forEach(phrase => {
      const before = highlighted.substring(0, phrase.index)
      const match = highlighted.substring(phrase.index, phrase.index + phrase.text.length)
      const after = highlighted.substring(phrase.index + phrase.text.length)

      highlighted = `${before}<mark class="${phrase.bgColor} ${phrase.color} px-1 rounded" title="${phrase.label}">${match}</mark>${after}`
    })

    return highlighted
  }

  const renderContent = () => {
    if (editMode && !readOnly) {
      return (
        <textarea
          value={content}
          onChange={(e) => handleContentChange(e.target.value)}
          className="w-full h-full p-6 bg-gray-900 text-gray-100 font-grounded text-sm resize-none focus:outline-none"
          spellCheck={false}
        />
      )
    }

    const type = document?.type || 'markdown'
    const language = document?.language || 'markdown'

    if (type === 'code') {
      return (
        <SyntaxHighlighter
          language={language}
          style={vscDarkPlus}
          customStyle={{
            margin: 0,
            padding: '1.5rem',
            background: 'transparent',
            fontSize: '0.9rem',
            lineHeight: '1.6'
          }}
          showLineNumbers={true}
        >
          {content}
        </SyntaxHighlighter>
      )
    }

    if (type === 'markdown' || type === 'latex') {
      return (
        <div className="prose prose-invert prose-lg max-w-none p-6">
          <ReactMarkdown
            remarkPlugins={[remarkGfm, remarkMath]}
            rehypePlugins={[rehypeKatex]}
            components={{
              code({ node, inline, className, children, ...props }) {
                const match = /language-(\w+)/.exec(className || '')
                return !inline && match ? (
                  <SyntaxHighlighter
                    language={match[1]}
                    style={vscDarkPlus}
                    PreTag="div"
                    {...props}
                  >
                    {String(children).replace(/\n$/, '')}
                  </SyntaxHighlighter>
                ) : (
                  <code className={className} {...props}>
                    {children}
                  </code>
                )
              }
            }}
          >
            {content}
          </ReactMarkdown>
        </div>
      )
    }

    // Plain text
    return (
      <div
        className="p-6 text-gray-100 font-grounded whitespace-pre-wrap"
        dangerouslySetInnerHTML={{ __html: highlightFlaggedText(content) }}
      />
    )
  }

  return (
    <div className={`flex flex-col h-full bg-gray-950 ${className}`}>
      {/* Toolbar */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-gray-800 bg-gray-900">
        <div className="flex items-center space-x-2">
          {/* Document Type Badge */}
          <span className="px-2 py-1 text-xs font-medium rounded bg-realm-corporeal/20 text-realm-corporeal">
            {document?.type || 'text'}
          </span>

          {/* Flagged Phrases Indicator */}
          {flaggedPhrases.length > 0 && (
            <button
              onClick={() => setShowFlagged(!showFlagged)}
              className={`px-2 py-1 text-xs font-medium rounded transition-colors ${
                showFlagged
                  ? 'bg-red-900/40 text-red-400'
                  : 'bg-gray-700 text-gray-400'
              }`}
            >
              {flaggedPhrases.length} flagged
            </button>
          )}
        </div>

        <div className="flex items-center space-x-2">
          {/* Edit/Save Toggle */}
          {!readOnly && (
            <button
              onClick={() => editMode ? handleSave() : setEditMode(true)}
              className="px-3 py-1 text-sm font-medium rounded bg-realm-symbolic hover:bg-realm-symbolic-light text-white transition-colors"
            >
              {editMode ? 'Save' : 'Edit'}
            </button>
          )}

          {/* Compare */}
          {onCompare && !splitMode && (
            <button
              onClick={() => onCompare(document)}
              className="px-3 py-1 text-sm font-medium rounded bg-gray-700 hover:bg-gray-600 text-white transition-colors"
              title="Compare with another document"
            >
              Compare
            </button>
          )}

          {/* Export */}
          <div className="relative group">
            <button className="px-3 py-1 text-sm font-medium rounded bg-gray-700 hover:bg-gray-600 text-white transition-colors">
              Export
            </button>
            <div className="absolute right-0 mt-1 w-32 bg-gray-800 border border-gray-700 rounded-md shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-10">
              <button className="w-full px-3 py-2 text-left text-sm text-gray-300 hover:bg-gray-700">
                Markdown
              </button>
              <button className="w-full px-3 py-2 text-left text-sm text-gray-300 hover:bg-gray-700">
                PDF
              </button>
              <button className="w-full px-3 py-2 text-left text-sm text-gray-300 hover:bg-gray-700">
                HTML
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Content Area */}
      <div className="flex-1 overflow-y-auto">
        {content ? renderContent() : (
          <div className="flex items-center justify-center h-full text-gray-500">
            <div className="text-center">
              <div className="text-6xl mb-4">📄</div>
              <p>No document selected</p>
            </div>
          </div>
        )}
      </div>

      {/* Flagged Phrases Legend */}
      {showFlagged && flaggedPhrases.length > 0 && (
        <div className="border-t border-gray-800 bg-gray-900 p-3">
          <div className="text-xs text-gray-400 mb-2">Flagged Patterns:</div>
          <div className="flex flex-wrap gap-2">
            {flagPatterns.map(pattern => {
              const count = flaggedPhrases.filter(p => p.patternId === pattern.id).length
              if (count === 0) return null
              return (
                <span
                  key={pattern.id}
                  className={`px-2 py-1 text-xs rounded ${pattern.bgColor} ${pattern.color}`}
                >
                  {pattern.label}: {count}
                </span>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}

DocumentViewer.propTypes = {
  document: PropTypes.shape({
    content: PropTypes.string,
    type: PropTypes.oneOf(['markdown', 'code', 'latex', 'text']),
    language: PropTypes.string,
    metadata: PropTypes.object
  }),
  onDocumentChange: PropTypes.func,
  onCompare: PropTypes.func,
  selectedMessage: PropTypes.object,
  className: PropTypes.string,
  splitMode: PropTypes.bool,
  readOnly: PropTypes.bool
}

export default DocumentViewer
