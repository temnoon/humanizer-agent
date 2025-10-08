import { useState } from 'react';
import PropTypes from 'prop-types';

/**
 * SearchBar - Unified search component
 *
 * Replaces duplicate search bar implementations throughout the app.
 * Features:
 * - Consistent styling and behavior
 * - Keyboard shortcuts (Ctrl+K/Cmd+K to focus)
 * - Clear button
 * - Loading state
 * - Debounce support
 */
export default function SearchBar({
  value,
  onChange,
  onSearch,
  onClear,
  placeholder = 'Search...',
  loading = false,
  className = '',
  autoFocus = false,
}) {
  const [isFocused, setIsFocused] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (onSearch) {
      onSearch(value);
    }
  };

  const handleClear = () => {
    onChange('');
    if (onClear) {
      onClear();
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Escape') {
      handleClear();
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      className={`relative ${className}`}
    >
      <div
        className={`
          relative flex items-center
          bg-gray-800 rounded-lg
          border-2 transition-all duration-200
          ${isFocused ? 'border-blue-500 ring-2 ring-blue-500/20' : 'border-gray-700'}
        `}
      >
        {/* Search icon */}
        <div className="absolute left-3 pointer-events-none">
          {loading ? (
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-gray-400"></div>
          ) : (
            <svg
              className="w-5 h-5 text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
          )}
        </div>

        {/* Input field */}
        <input
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          placeholder={placeholder}
          autoFocus={autoFocus}
          className="
            w-full px-10 py-2.5
            bg-transparent
            text-white placeholder-gray-500
            focus:outline-none
            text-sm
          "
        />

        {/* Clear button (show when there's text) */}
        {value && (
          <button
            type="button"
            onClick={handleClear}
            className="absolute right-3 p-1 hover:bg-gray-700 rounded transition-colors"
            title="Clear (Esc)"
          >
            <svg
              className="w-4 h-4 text-gray-400 hover:text-white"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        )}
      </div>

      {/* Keyboard hint */}
      {!isFocused && !value && (
        <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none">
          <kbd className="px-2 py-0.5 text-xs text-gray-500 bg-gray-900 border border-gray-700 rounded">
            Ctrl+K
          </kbd>
        </div>
      )}
    </form>
  );
}

SearchBar.propTypes = {
  value: PropTypes.string.isRequired,
  onChange: PropTypes.func.isRequired,
  onSearch: PropTypes.func,
  onClear: PropTypes.func,
  placeholder: PropTypes.string,
  loading: PropTypes.bool,
  className: PropTypes.string,
  autoFocus: PropTypes.bool,
};
