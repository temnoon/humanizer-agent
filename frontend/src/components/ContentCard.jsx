import PropTypes from 'prop-types';

/**
 * ContentCard Component
 *
 * Displays a single piece of content in a book section.
 * Shows source type (chunk or transformation) with metadata.
 * Phase 1: Read-only display
 * Phase 2: Will add editing, deletion, reordering
 */
export default function ContentCard({ contentLink, sequenceNumber }) {
  // Determine content source and type
  const isChunk = !!contentLink.chunk_id;
  const isTransformation = !!contentLink.transformation_job_id;

  // Get the actual content text
  const contentText = contentLink.chunk_content || contentLink.job_content || '';

  // Get source metadata
  const sourceType = isChunk ? '💬 Conversation' : isTransformation ? '🔄 Transformation' : '❓ Unknown';
  const sourceColor = isChunk ? 'bg-blue-900 text-blue-200' : isTransformation ? 'bg-purple-900 text-purple-200' : 'bg-gray-700 text-gray-300';

  // Get specific metadata
  const getMetadataText = () => {
    if (isChunk) {
      return 'From conversation chunk';
    }
    if (isTransformation && contentLink.job_metadata) {
      const jobType = contentLink.job_metadata.job_type || 'unknown';
      return `${jobType.replace('_', ' ')} transformation`;
    }
    return 'Unknown source';
  };

  // Truncate long content for display
  const truncateContent = (text, maxLength = 200) => {
    if (!text || text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
  };

  return (
    <div className="border border-gray-700 rounded-lg overflow-hidden bg-gray-800 mb-3">
      {/* Header with source type and metadata */}
      <div className="flex items-center justify-between px-4 py-2 bg-gray-850 border-b border-gray-700">
        <div className="flex items-center gap-2">
          <span className={`px-2 py-1 rounded text-xs font-semibold ${sourceColor}`}>
            {sourceType}
          </span>
          <span className="text-xs text-gray-400">{getMetadataText()}</span>
        </div>
        <div className="flex items-center gap-2">
          {sequenceNumber !== undefined && (
            <span className="text-xs text-gray-500">#{sequenceNumber + 1}</span>
          )}
        </div>
      </div>

      {/* Content preview */}
      <div className="px-4 py-3">
        <div className="text-sm text-gray-300 whitespace-pre-wrap font-mono">
          {truncateContent(contentText)}
        </div>

        {contentText.length > 200 && (
          <div className="mt-2 text-xs text-gray-500 italic">
            ({contentText.length} characters total)
          </div>
        )}

        {/* Notes if present */}
        {contentLink.notes && (
          <div className="mt-3 pt-3 border-t border-gray-700">
            <div className="text-xs text-gray-500 mb-1">Notes:</div>
            <div className="text-sm text-gray-400 italic">{contentLink.notes}</div>
          </div>
        )}
      </div>

      {/* Phase 2 will add: Edit, Delete, Reorder buttons */}
    </div>
  );
}

ContentCard.propTypes = {
  contentLink: PropTypes.shape({
    id: PropTypes.string.isRequired,
    chunk_id: PropTypes.string,
    transformation_job_id: PropTypes.string,
    chunk_content: PropTypes.string,
    job_content: PropTypes.string,
    chunk_metadata: PropTypes.object,
    job_metadata: PropTypes.object,
    notes: PropTypes.string,
    sequence_number: PropTypes.number,
  }).isRequired,
  sequenceNumber: PropTypes.number,
};
