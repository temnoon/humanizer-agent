/**
 * Frontend token estimation utility
 * Provides rough token count estimates without requiring a full tokenizer
 */

// Token limits by tier
export const TOKEN_LIMITS = {
  free: 4000,
  premium: 32000,
  enterprise: 100000
}

/**
 * Estimate token count based on text characteristics
 * This is a rough approximation based on common patterns:
 * - 1 token ≈ 4 characters for English text
 * - 1 token ≈ 0.75 words for typical English
 * - Punctuation and special characters affect the ratio
 */
export function estimateTokenCount(text) {
  if (!text || typeof text !== 'string') {
    return 0
  }

  // Remove extra whitespace and normalize
  const normalizedText = text.trim().replace(/\s+/g, ' ')
  
  // Character-based estimation (more conservative)
  const charCount = normalizedText.length
  const tokensByChars = Math.ceil(charCount / 4)
  
  // Word-based estimation
  const words = normalizedText.split(/\s+/).filter(word => word.length > 0)
  const tokensByWords = Math.ceil(words.length / 0.75)
  
  // Use the higher estimate to be conservative
  const estimatedTokens = Math.max(tokensByChars, tokensByWords)
  
  // Add some buffer for safety (10%)
  return Math.ceil(estimatedTokens * 1.1)
}

/**
 * Check if text exceeds token limit for given tier
 */
export function checkTokenLimit(text, tier = 'free') {
  const estimatedTokens = estimateTokenCount(text)
  const limit = TOKEN_LIMITS[tier] || TOKEN_LIMITS.free
  
  return {
    tokenCount: estimatedTokens,
    limit: limit,
    isWithinLimit: estimatedTokens <= limit,
    percentUsed: (estimatedTokens / limit) * 100,
    message: estimatedTokens <= limit 
      ? `Within ${tier} limit (${estimatedTokens.toLocaleString()}/${limit.toLocaleString()} tokens)`
      : `Exceeds ${tier} limit (${estimatedTokens.toLocaleString()}/${limit.toLocaleString()} tokens)`
  }
}

/**
 * Get word count estimate from text
 */
export function getWordCount(text) {
  if (!text || typeof text !== 'string') {
    return 0
  }
  
  const words = text.trim().split(/\s+/).filter(word => word.length > 0)
  return words.length
}

/**
 * Format large numbers with commas
 */
export function formatNumber(num) {
  return num.toLocaleString()
}