import { useState } from 'react';
import { useWorkspace } from '../../contexts/WorkspaceContext';

/**
 * InterestList - Hierarchical breadcrumb of user's browse path
 *
 * Tracks the user's exploration path through the workspace:
 * Example flow:
 * 1. User browses images → finds interesting image
 * 2. Clicks to see conversation → adds image to interest list
 * 3. Reads conversation → finds interesting phrase
 * 4. Searches for phrase → adds conversation to interest list
 * 5. Finds related transformations → adds search results
 *
 * The interest list becomes a "trail of breadcrumbs" showing
 * how the user got from point A to point B.
 */
export default function InterestList() {
  const { interestList, removeFromInterest, navigateToInterest, clearInterestList } = useWorkspace();
  const [isCollapsed, setIsCollapsed] = useState(false);

  const getIcon = (type) => {
    const icons = {
      image: '🖼️',
      conversation: '💬',
      message: '📝',
      book: '📖',
      transformation: '🎭',
      search: '🔍',
      collection: '📚'
    };
    return icons[type] || '📌';
  };

  if (interestList.length === 0) {
    return null; // Don't show if empty
  }

  return (
    <div className="bg-gray-800 border-b border-gray-700">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2 cursor-pointer hover:bg-gray-750" onClick={() => setIsCollapsed(!isCollapsed)}>
        <div className="flex items-center gap-2">
          <svg
            className={`w-4 h-4 text-gray-400 transition-transform ${isCollapsed ? '' : 'rotate-90'}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
          <span className="text-sm font-medium text-gray-300">
            Interest Trail ({interestList.length})
          </span>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={(e) => {
              e.stopPropagation();
              clearInterestList();
            }}
            className="text-xs text-gray-500 hover:text-gray-300 px-2 py-1 rounded hover:bg-gray-700 transition-colors"
            title="Clear all"
          >
            Clear
          </button>
        </div>
      </div>

      {/* Interest Items */}
      {!isCollapsed && (
        <div className="px-4 pb-3 space-y-1">
          {interestList.map((item, index) => (
            <div
              key={item.id}
              className="flex items-center gap-2 group"
            >
              {/* Connection line (for all but first item) */}
              {index > 0 && (
                <div className="flex items-center text-gray-600 text-xs">
                  <span>→</span>
                </div>
              )}

              {/* Item card */}
              <div
                onClick={() => navigateToInterest(item)}
                className="flex-1 flex items-center gap-2 px-3 py-2 bg-gray-750 rounded hover:bg-gray-700 cursor-pointer transition-colors"
              >
                <span className="text-lg">{getIcon(item.type)}</span>
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium text-white truncate">
                    {item.title}
                  </div>
                  {item.context && (
                    <div className="text-xs text-gray-400 truncate">
                      {item.context}
                    </div>
                  )}
                </div>

                {/* Remove button (appears on hover) */}
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    removeFromInterest(item.id);
                  }}
                  className="opacity-0 group-hover:opacity-100 text-gray-500 hover:text-white transition-opacity"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
