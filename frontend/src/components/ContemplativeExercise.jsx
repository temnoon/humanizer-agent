import { useState, useEffect } from 'react'
import PropTypes from 'prop-types'

/**
 * Contemplative Exercise Component
 *
 * Supports contemplative practices: word dissolution, Socratic dialogue, witness prompts.
 * Helps users shift from intellectual understanding to direct experiential realization.
 */
function ContemplativeExercise({ exercise }) {
  const [dissolutionProgress, setDissolutionProgress] = useState(0)
  const [isDissolving, setIsDissolving] = useState(false)

  // Word dissolution animation
  useEffect(() => {
    if (isDissolving && exercise.word_dissolution) {
      const word = exercise.word_dissolution.word
      const interval = setInterval(() => {
        setDissolutionProgress((prev) => {
          if (prev >= word.length) {
            clearInterval(interval)
            setIsDissolving(false)
            return prev
          }
          return prev + 1
        })
      }, 500) // Dissolve one character every 500ms

      return () => clearInterval(interval)
    }
  }, [isDissolving, exercise.word_dissolution])

  const startDissolution = () => {
    setDissolutionProgress(0)
    setIsDissolving(true)
  }

  const resetDissolution = () => {
    setDissolutionProgress(0)
    setIsDissolving(false)
  }

  // Word Dissolution Exercise
  if (exercise.word_dissolution) {
    const { word, emotional_weight, belief_associations, dissolution_guidance } = exercise.word_dissolution
    const remainingWord = word.slice(0, word.length - dissolutionProgress)

    return (
      <div className="bg-realm-subjective border border-realm-subjective-light p-8 rounded-lg space-y-6">
        <div className="text-center">
          <h3 className="text-3xl font-contemplative font-semibold text-white mb-2">
            Word Dissolution
          </h3>
          <p className="text-sm text-gray-400">
            Feel the weight of language, then watch it dissolve into silence
          </p>
        </div>

        {/* The Word */}
        <div className="text-center py-8">
          <div className="text-6xl font-contemplative text-white mb-4 min-h-[100px] flex items-center justify-center">
            {dissolutionProgress === word.length ? (
              <span className="text-4xl text-realm-subjective-lighter italic">
                ... silence ...
              </span>
            ) : (
              <span className={`transition-all duration-500 ${isDissolving ? 'opacity-50' : 'opacity-100'}`}>
                {remainingWord || word}
              </span>
            )}
          </div>

          {/* Controls */}
          <div className="flex gap-3 justify-center">
            {!isDissolving && dissolutionProgress === 0 && (
              <button
                onClick={startDissolution}
                className="px-6 py-2 bg-realm-subjective-light hover:bg-realm-subjective-lighter text-white rounded-md font-structural transition-colors"
              >
                Begin Dissolution
              </button>
            )}
            {dissolutionProgress > 0 && (
              <button
                onClick={resetDissolution}
                className="px-6 py-2 bg-realm-symbolic hover:bg-realm-symbolic-light text-white rounded-md font-structural transition-colors"
              >
                Reset
              </button>
            )}
          </div>
        </div>

        {/* Guidance */}
        <div className="space-y-4">
          {emotional_weight && dissolutionProgress === 0 && (
            <div className="bg-realm-subjective-light p-4 rounded-md">
              <h4 className="text-base font-structural font-semibold text-white mb-2">
                Step 1: Feel the Weight
              </h4>
              <p className="text-sm text-gray-300 font-contemplative">
                {emotional_weight}
              </p>
            </div>
          )}

          {belief_associations && belief_associations.length > 0 && dissolutionProgress === 0 && (
            <div className="bg-realm-subjective-light p-4 rounded-md">
              <h4 className="text-base font-structural font-semibold text-white mb-2">
                Belief Associations
              </h4>
              <ul className="text-sm text-gray-300 font-contemplative space-y-1">
                {belief_associations.map((association, i) => (
                  <li key={i} className="italic">• {association}</li>
                ))}
              </ul>
            </div>
          )}

          <div className="bg-realm-subjective-light p-4 rounded-md">
            <h4 className="text-base font-structural font-semibold text-white mb-2">
              Dissolution Guidance
            </h4>
            <p className="text-sm text-gray-300 font-contemplative whitespace-pre-line leading-relaxed">
              {dissolution_guidance}
            </p>
          </div>
        </div>

        {/* Philosophical Context */}
        {exercise.philosophical_context && (
          <div className="border-t border-realm-subjective-light pt-4">
            <p className="text-xs text-gray-400 italic text-center">
              💡 {exercise.philosophical_context}
            </p>
          </div>
        )}
      </div>
    )
  }

  // Socratic Dialogue Exercise
  if (exercise.socratic_dialogue) {
    const { initial_statement, questions, philosophical_goal } = exercise.socratic_dialogue

    return (
      <div className="bg-realm-symbolic-dark border border-realm-symbolic p-8 rounded-lg space-y-6">
        <div className="text-center">
          <h3 className="text-3xl font-contemplative font-semibold text-white mb-2">
            Socratic Dialogue
          </h3>
          <p className="text-sm text-gray-400">
            Questions that reveal the constructed nature of belief
          </p>
        </div>

        {/* Initial Statement */}
        <div className="bg-realm-symbolic-light p-4 rounded-md">
          <h4 className="text-sm font-structural font-semibold text-white uppercase mb-2">
            Statement to Examine
          </h4>
          <p className="text-sm text-gray-200 font-contemplative italic">
            "{initial_statement}"
          </p>
        </div>

        {/* Questions */}
        <div className="space-y-3">
          <h4 className="text-base font-structural font-semibold text-white">
            Contemplative Questions
          </h4>
          {questions.map((q, index) => (
            <div
              key={index}
              className="bg-realm-symbolic-light p-4 rounded-md border-l-4"
              style={{ borderLeftColor: `rgba(139, 92, 246, ${1 - q.depth_level * 0.15})` }}
            >
              <p className="text-sm text-white font-contemplative mb-2">
                {q.question}
              </p>
              <div className="flex items-center gap-2 text-xs text-gray-400">
                <span>Intent: {q.intent}</span>
                <span>•</span>
                <span>Depth: {q.depth_level}/5</span>
              </div>
            </div>
          ))}
        </div>

        {/* Philosophical Goal */}
        <div className="bg-realm-subjective p-4 rounded-md">
          <p className="text-sm text-gray-300 font-contemplative italic">
            🎯 {philosophical_goal}
          </p>
        </div>

        {/* Guidance */}
        {exercise.philosophical_context && (
          <div className="border-t border-realm-symbolic pt-4">
            <p className="text-xs text-gray-400 italic">
              💡 {exercise.philosophical_context}
            </p>
          </div>
        )}

        {exercise.next_step && (
          <div className="text-center">
            <p className="text-sm text-gray-300 font-structural">
              → {exercise.next_step}
            </p>
          </div>
        )}
      </div>
    )
  }

  // Witness Prompt Exercise
  if (exercise.witness_prompt) {
    const { prompt, context } = exercise.witness_prompt

    return (
      <div className="bg-realm-subjective border border-realm-subjective-light p-8 rounded-lg space-y-6">
        <div className="text-center">
          <h3 className="text-3xl font-contemplative font-semibold text-white mb-2">
            Witness
          </h3>
          <p className="text-sm text-gray-400">
            Return to awareness before language
          </p>
        </div>

        {/* The Prompt */}
        <div className="text-center py-12">
          <p className="text-2xl font-contemplative text-white leading-relaxed italic">
            {prompt}
          </p>
        </div>

        {/* Context */}
        {context && (
          <div className="text-center">
            <p className="text-sm text-gray-400">
              {context}
            </p>
          </div>
        )}

        {/* Philosophical Context */}
        {exercise.philosophical_context && (
          <div className="bg-realm-subjective-light p-4 rounded-md">
            <p className="text-sm text-gray-300 font-contemplative italic">
              💡 {exercise.philosophical_context}
            </p>
          </div>
        )}

        {/* Guidance */}
        <div className="text-center space-y-2">
          <p className="text-xs text-gray-300 font-structural">
            Take three breaths. Return to presence.
          </p>
          {exercise.next_step && (
            <p className="text-xs text-gray-400">
              {exercise.next_step}
            </p>
          )}
        </div>
      </div>
    )
  }

  return null
}

ContemplativeExercise.propTypes = {
  exercise: PropTypes.shape({
    exercise_type: PropTypes.string.isRequired,
    word_dissolution: PropTypes.shape({
      word: PropTypes.string.isRequired,
      emotional_weight: PropTypes.string,
      belief_associations: PropTypes.arrayOf(PropTypes.string),
      dissolution_guidance: PropTypes.string.isRequired,
    }),
    socratic_dialogue: PropTypes.shape({
      initial_statement: PropTypes.string.isRequired,
      questions: PropTypes.arrayOf(
        PropTypes.shape({
          question: PropTypes.string.isRequired,
          intent: PropTypes.string.isRequired,
          depth_level: PropTypes.number.isRequired,
        })
      ).isRequired,
      philosophical_goal: PropTypes.string.isRequired,
    }),
    witness_prompt: PropTypes.shape({
      prompt: PropTypes.string.isRequired,
      context: PropTypes.string,
    }),
    philosophical_context: PropTypes.string,
    next_step: PropTypes.string,
  }).isRequired,
}

export default ContemplativeExercise
