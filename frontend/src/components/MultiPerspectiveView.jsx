import { useState } from 'react'
import PropTypes from 'prop-types'

/**
 * Multi-Perspective View Component
 *
 * Displays multiple transformations simultaneously to reveal
 * how meaning is constructed by different belief frameworks.
 */
function MultiPerspectiveView({ sourceText, perspectives, philosophicalNote }) {
  const [expandedIndex, setExpandedIndex] = useState(null)

  const toggleExpanded = (index) => {
    setExpandedIndex(expandedIndex === index ? null : index)
  }

  return (
    <div className="space-y-6">
      {/* Source Text (Corporeal Realm) */}
      <div className="bg-realm-corporeal-dark border border-realm-corporeal p-6 rounded-lg">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-xl font-structural font-semibold text-white">
            Source Text
          </h3>
          <span className="text-xs text-realm-corporeal-light uppercase tracking-wide">
            Corporeal Realm
          </span>
        </div>
        <p className="text-sm text-gray-300 font-grounded leading-relaxed whitespace-pre-wrap">
          {sourceText}
        </p>
        <p className="text-xs text-realm-corporeal-light mt-3 italic">
          Raw text before consciousness constructs meaning
        </p>
      </div>

      {/* Philosophical Note */}
      {philosophicalNote && (
        <div className="bg-realm-subjective border border-realm-subjective-light p-4 rounded-lg">
          <p className="text-sm text-gray-300 font-contemplative italic leading-relaxed">
            💡 {philosophicalNote}
          </p>
        </div>
      )}

      {/* Perspectives (Symbolic Realm) */}
      <div className="space-y-4">
        <h3 className="text-2xl font-structural font-semibold text-white">
          Belief Framework Perspectives
        </h3>

        <div className="grid grid-cols-1 gap-4">
          {perspectives.map((perspective, index) => (
            <div
              key={index}
              className="bg-realm-symbolic-dark border border-realm-symbolic rounded-lg overflow-hidden transition-all duration-300"
            >
              {/* Framework Header */}
              <button
                onClick={() => toggleExpanded(index)}
                className="w-full px-6 py-4 bg-realm-symbolic hover:bg-realm-symbolic-light transition-colors text-left flex items-center justify-between"
              >
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="font-structural font-semibold text-white">
                      Perspective {index + 1}
                    </span>
                    <span className="text-xs text-gray-400 uppercase tracking-wide">
                      Symbolic Realm
                    </span>
                  </div>
                  <div className="text-sm text-gray-300 mt-1 font-structural">
                    {perspective.belief_framework.persona} / {perspective.belief_framework.namespace} / {perspective.belief_framework.style}
                  </div>
                </div>
                <svg
                  className={`w-5 h-5 text-white transition-transform ${expandedIndex === index ? 'rotate-180' : ''}`}
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>

              {/* Expanded Content */}
              {expandedIndex === index && (
                <div className="px-6 py-4 bg-realm-symbolic-dark border-t border-realm-symbolic">
                  {/* Transformed Content */}
                  <div className="mb-4">
                    <div className="bg-gray-900 p-4 rounded-md">
                      <p className="text-sm text-gray-200 font-contemplative leading-relaxed whitespace-pre-wrap">
                        {perspective.transformed_content}
                      </p>
                    </div>
                  </div>

                  {/* Framework Details */}
                  <div className="space-y-3">
                    {perspective.belief_framework.description && (
                      <div>
                        <h4 className="text-sm font-structural font-semibold text-white uppercase mb-1">
                          Framework Description
                        </h4>
                        <p className="text-sm text-gray-300">
                          {perspective.belief_framework.description}
                        </p>
                      </div>
                    )}

                    {perspective.belief_framework.philosophical_context && (
                      <div>
                        <h4 className="text-sm font-structural font-semibold text-white uppercase mb-1">
                          What This Emphasizes
                        </h4>
                        <p className="text-sm text-gray-300">
                          {perspective.belief_framework.philosophical_context}
                        </p>
                      </div>
                    )}

                    {perspective.emotional_profile && (
                      <div>
                        <h4 className="text-sm font-structural font-semibold text-white uppercase mb-1">
                          Emotional Profile
                        </h4>
                        <p className="text-sm text-gray-300">
                          {perspective.emotional_profile}
                        </p>
                      </div>
                    )}

                    {perspective.emphasis && (
                      <div>
                        <h4 className="text-sm font-structural font-semibold text-white uppercase mb-1">
                          Framework Emphasis
                        </h4>
                        <p className="text-sm text-gray-300">
                          {perspective.emphasis}
                        </p>
                      </div>
                    )}
                  </div>

                  {/* Awareness Prompt */}
                  <div className="mt-4 pt-4 border-t border-realm-symbolic">
                    <p className="text-xs text-gray-300 italic">
                      🌟 Notice: How does this perspective make you <em>feel</em> differently?
                      That shift reveals the Emotional Belief Loop at work.
                    </p>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Witness Prompt */}
      <div className="bg-realm-subjective border border-realm-subjective-light p-6 rounded-lg text-center">
        <p className="text-white font-contemplative text-lg italic mb-2">
          "Each perspective is a lens. You are the witness."
        </p>
        <p className="text-xs text-gray-400">
          Return to awareness—the subjective realm where all meaning arises.
        </p>
      </div>
    </div>
  )
}

MultiPerspectiveView.propTypes = {
  sourceText: PropTypes.string.isRequired,
  perspectives: PropTypes.arrayOf(
    PropTypes.shape({
      belief_framework: PropTypes.shape({
        persona: PropTypes.string.isRequired,
        namespace: PropTypes.string.isRequired,
        style: PropTypes.string.isRequired,
        description: PropTypes.string,
        philosophical_context: PropTypes.string,
      }).isRequired,
      transformed_content: PropTypes.string.isRequired,
      emotional_profile: PropTypes.string,
      emphasis: PropTypes.string,
    })
  ).isRequired,
  philosophicalNote: PropTypes.string,
}

export default MultiPerspectiveView
