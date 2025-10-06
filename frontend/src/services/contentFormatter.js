/**
 * Content Formatter
 *
 * Converts various content types (text, images, code) to markdown format.
 * Handles ChatGPT/Claude image asset pointers and converts them to displayable markdown.
 */

/**
 * Check if content is a JSON object (for image_asset_pointer detection)
 */
function isJsonObject(str) {
  if (typeof str !== 'string') return false;
  try {
    const parsed = JSON.parse(str);
    return typeof parsed === 'object' && parsed !== null;
  } catch {
    return false;
  }
}

/**
 * Convert image_asset_pointer JSON to markdown image syntax
 */
function convertImagePointerToMarkdown(content) {
  try {
    const parsed = JSON.parse(content);

    // Check if it's an image_asset_pointer
    if (parsed.content_type === 'image_asset_pointer' && parsed.asset_pointer) {
      const fileId = parsed.asset_pointer.replace('file-service://', '');
      const alt = `Image ${parsed.width}x${parsed.height}`;

      // Use our backend media endpoint to serve the image
      return `![${alt}](http://localhost:8000/api/library/media/${fileId})`;
    }

    // If it's JSON but not an image pointer, return formatted JSON
    return `\`\`\`json\n${JSON.stringify(parsed, null, 2)}\n\`\`\``;
  } catch {
    // If parsing fails, return content as-is
    return content;
  }
}

/**
 * Convert chunk content to markdown format
 * Handles text, images, code blocks, etc.
 */
export function chunkToMarkdown(chunk) {
  if (!chunk || !chunk.content) return '';

  const content = chunk.content;

  // Check if content is JSON (potential image or structured data)
  if (isJsonObject(content)) {
    return convertImagePointerToMarkdown(content);
  }

  // Otherwise return content as-is (already markdown or plain text)
  return content;
}

/**
 * Convert array of chunks to combined markdown content
 */
export function chunksToMarkdown(chunks) {
  if (!chunks || chunks.length === 0) return '';

  return chunks
    .sort((a, b) => a.chunk_sequence - b.chunk_sequence)
    .map(c => chunkToMarkdown(c))
    .join('\n\n');
}

/**
 * Extract file ID from various image formats
 */
export function extractFileId(imageRef) {
  if (!imageRef) return null;

  // Handle file-service:// URLs
  if (imageRef.startsWith('file-service://')) {
    return imageRef.replace('file-service://', '');
  }

  // Handle direct file IDs
  if (imageRef.startsWith('file-')) {
    return imageRef;
  }

  return imageRef;
}
