/**
 * PhraseFlagger - Configurable phrase detection and flagging system
 *
 * Detects and highlights configurable patterns in text, including:
 * - LLM-generated slop phrases
 * - Hedge words and weak language
 * - Academic jargon
 * - Custom user-defined patterns
 */

export class PhraseFlagger {
  constructor() {
    this.patterns = this.loadPatterns()
    this.enabled = true
  }

  /**
   * Load default and custom patterns
   */
  loadPatterns() {
    // Get custom patterns from localStorage
    const customPatterns = JSON.parse(
      localStorage.getItem('phrase_flagger_patterns') || '[]'
    )

    // Default built-in patterns
    const defaultPatterns = [
      {
        id: 'llm-slop',
        name: 'LLM Slop',
        description: 'Common AI-generated filler phrases',
        pattern: /\b(delve|leverage|robust|holistic|synergy|paradigm shift|cutting-edge|state-of-the-art|in today's world|it's important to note|dive deep|navigating the landscape|it is worth noting|at the end of the day|moving forward|circle back|touch base|low-hanging fruit|game changer|double down|think outside the box)\b/gi,
        color: '#ef4444',
        bgColor: 'rgba(239, 68, 68, 0.2)',
        severity: 'high',
        enabled: true
      },
      {
        id: 'hedge-words',
        name: 'Hedge Words',
        description: 'Uncertain or qualifying language',
        pattern: /\b(perhaps|maybe|possibly|might|could|would|should|somewhat|relatively|fairly|quite|rather|slightly)\b/gi,
        color: '#f59e0b',
        bgColor: 'rgba(245, 158, 11, 0.2)',
        severity: 'medium',
        enabled: true
      },
      {
        id: 'passive-voice',
        name: 'Passive Voice',
        description: 'Passive voice constructions',
        pattern: /\b(was|were|been|being)\s+\w+(ed|en)\b/gi,
        color: '#8b5cf6',
        bgColor: 'rgba(139, 92, 246, 0.2)',
        severity: 'low',
        enabled: true
      },
      {
        id: 'academic-jargon',
        name: 'Academic Jargon',
        description: 'Overly formal or academic language',
        pattern: /\b(aforementioned|hereby|heretofore|pursuant|notwithstanding|vis-à-vis|ergo|ipso facto|inter alia|mutatis mutandis)\b/gi,
        color: '#a78bfa',
        bgColor: 'rgba(167, 139, 250, 0.2)',
        severity: 'low',
        enabled: true
      },
      {
        id: 'filler-words',
        name: 'Filler Words',
        description: 'Unnecessary filler words',
        pattern: /\b(basically|literally|actually|really|very|just|simply|essentially|fundamentally|ultimately)\b/gi,
        color: '#06b6d4',
        bgColor: 'rgba(6, 182, 212, 0.2)',
        severity: 'low',
        enabled: true
      },
      {
        id: 'intensifiers',
        name: 'Intensifiers',
        description: 'Overused intensifiers',
        pattern: /\b(absolutely|completely|totally|extremely|highly|incredibly|remarkably|exceptionally|extraordinarily)\b/gi,
        color: '#ec4899',
        bgColor: 'rgba(236, 72, 153, 0.2)',
        severity: 'low',
        enabled: true
      }
    ]

    return [...defaultPatterns, ...customPatterns]
  }

  /**
   * Save patterns to localStorage
   */
  savePatterns() {
    const customPatterns = this.patterns.filter(p => !p.builtin)
    localStorage.setItem(
      'phrase_flagger_patterns',
      JSON.stringify(customPatterns)
    )
  }

  /**
   * Add a custom pattern
   */
  addPattern(pattern) {
    this.patterns.push({
      id: `custom-${Date.now()}`,
      builtin: false,
      enabled: true,
      ...pattern
    })
    this.savePatterns()
  }

  /**
   * Remove a pattern
   */
  removePattern(id) {
    this.patterns = this.patterns.filter(p => p.id !== id)
    this.savePatterns()
  }

  /**
   * Toggle pattern on/off
   */
  togglePattern(id) {
    const pattern = this.patterns.find(p => p.id === id)
    if (pattern) {
      pattern.enabled = !pattern.enabled
      this.savePatterns()
    }
  }

  /**
   * Detect flagged phrases in text
   */
  detect(text) {
    if (!this.enabled || !text) return []

    const results = []
    const enabledPatterns = this.patterns.filter(p => p.enabled)

    enabledPatterns.forEach(pattern => {
      try {
        // Convert string pattern to RegExp if needed
        const regex = typeof pattern.pattern === 'string'
          ? new RegExp(pattern.pattern, 'gi')
          : pattern.pattern

        const matches = text.matchAll(regex)

        for (const match of matches) {
          results.push({
            text: match[0],
            index: match.index,
            patternId: pattern.id,
            patternName: pattern.name,
            description: pattern.description,
            color: pattern.color,
            bgColor: pattern.bgColor,
            severity: pattern.severity
          })
        }
      } catch (err) {
        console.error(`Error in pattern ${pattern.id}:`, err)
      }
    })

    // Sort by index
    return results.sort((a, b) => a.index - b.index)
  }

  /**
   * Get statistics about flagged phrases
   */
  getStats(text) {
    const flagged = this.detect(text)
    const stats = {}

    this.patterns.forEach(pattern => {
      const count = flagged.filter(f => f.patternId === pattern.id).length
      if (count > 0) {
        stats[pattern.id] = {
          name: pattern.name,
          count,
          severity: pattern.severity
        }
      }
    })

    return {
      total: flagged.length,
      byPattern: stats,
      severityCounts: {
        high: flagged.filter(f => f.severity === 'high').length,
        medium: flagged.filter(f => f.severity === 'medium').length,
        low: flagged.filter(f => f.severity === 'low').length
      }
    }
  }

  /**
   * Highlight flagged text in HTML
   */
  highlightText(text) {
    const flagged = this.detect(text)
    if (flagged.length === 0) return text

    let result = text
    const sorted = [...flagged].sort((a, b) => b.index - a.index)

    sorted.forEach(flag => {
      const before = result.substring(0, flag.index)
      const match = result.substring(flag.index, flag.index + flag.text.length)
      const after = result.substring(flag.index + flag.text.length)

      const style = `background-color: ${flag.bgColor}; color: ${flag.color}; padding: 0 4px; border-radius: 3px; cursor: help;`
      const title = `${flag.patternName}: ${flag.description}`

      result = `${before}<mark style="${style}" title="${title}" data-pattern="${flag.patternId}">${match}</mark>${after}`
    })

    return result
  }

  /**
   * Get pattern configuration
   */
  getPatterns() {
    return this.patterns
  }

  /**
   * Export configuration
   */
  exportConfig() {
    return {
      enabled: this.enabled,
      patterns: this.patterns
    }
  }

  /**
   * Import configuration
   */
  importConfig(config) {
    this.enabled = config.enabled ?? true
    this.patterns = config.patterns || []
    this.savePatterns()
  }
}

// Singleton instance
export const phraseFlagger = new PhraseFlagger()
