import { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import { useWorkspace } from '../contexts/WorkspaceContext';

/**
 * SettingsModal - Configure application preferences
 *
 * Allows users to configure:
 * - Items per page (50, 100, 200, 500, 1000, 2000)
 * - Default limits
 * - Show/hide system messages
 * - Theme preferences
 *
 * All settings persist to localStorage via WorkspaceContext
 */
export default function SettingsModal({ isOpen, onClose }) {
  const { preferences, updatePreferences } = useWorkspace();
  const [localPrefs, setLocalPrefs] = useState(preferences);

  useEffect(() => {
    setLocalPrefs(preferences);
  }, [preferences]);

  if (!isOpen) return null;

  const handleSave = () => {
    updatePreferences(localPrefs);
    onClose();
  };

  const handleReset = () => {
    const defaultPrefs = {
      defaultLimit: 100,
      itemsPerPage: 100,
      showSystemMessages: false,
      theme: 'dark',
    };
    setLocalPrefs(defaultPrefs);
  };

  const itemsPerPageOptions = [50, 100, 200, 500, 1000, 2000];

  return (
    <div
      className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4"
      onClick={onClose}
    >
      <div
        className="bg-gray-900 rounded-lg shadow-2xl max-w-2xl w-full max-h-[80vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="bg-gray-800 border-b border-gray-700 p-4 flex items-center justify-between sticky top-0 z-10">
          <h2 className="text-xl font-bold text-white">Settings</h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-700 rounded transition-colors"
            title="Close"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Display Settings */}
          <section>
            <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <span>📊</span>
              Display Settings
            </h3>

            {/* Items Per Page */}
            <div className="space-y-2">
              <label className="block text-sm font-medium text-gray-300">
                Items Per Page
                <span className="text-gray-500 ml-2 font-normal">
                  (affects image browser, conversation list, etc.)
                </span>
              </label>
              <select
                value={localPrefs.itemsPerPage}
                onChange={(e) =>
                  setLocalPrefs({ ...localPrefs, itemsPerPage: parseInt(e.target.value) })
                }
                className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded text-white focus:outline-none focus:border-blue-500"
              >
                {itemsPerPageOptions.map((option) => (
                  <option key={option} value={option}>
                    {option} items
                  </option>
                ))}
              </select>
              <p className="text-xs text-gray-500">
                Higher values may slow down page loading but reduce pagination clicks
              </p>
            </div>

            {/* Default Limit */}
            <div className="space-y-2 mt-4">
              <label className="block text-sm font-medium text-gray-300">
                Default API Limit
                <span className="text-gray-500 ml-2 font-normal">(for initial data fetches)</span>
              </label>
              <input
                type="number"
                min="10"
                max="5000"
                step="10"
                value={localPrefs.defaultLimit}
                onChange={(e) =>
                  setLocalPrefs({ ...localPrefs, defaultLimit: parseInt(e.target.value) || 100 })
                }
                className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded text-white focus:outline-none focus:border-blue-500"
              />
              <p className="text-xs text-gray-500">Recommended: 100-200</p>
            </div>
          </section>

          {/* Content Filtering */}
          <section>
            <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <span>🔍</span>
              Content Filtering
            </h3>

            {/* Show System Messages */}
            <div className="flex items-center justify-between p-3 bg-gray-800 rounded">
              <div>
                <label className="text-sm font-medium text-gray-300">Show System Messages</label>
                <p className="text-xs text-gray-500">
                  Display system-generated messages in conversation views
                </p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={localPrefs.showSystemMessages}
                  onChange={(e) =>
                    setLocalPrefs({ ...localPrefs, showSystemMessages: e.target.checked })
                  }
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
              </label>
            </div>
          </section>

          {/* Theme Settings */}
          <section>
            <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <span>🎨</span>
              Appearance
            </h3>

            {/* Theme */}
            <div className="space-y-2">
              <label className="block text-sm font-medium text-gray-300">Theme</label>
              <select
                value={localPrefs.theme}
                onChange={(e) => setLocalPrefs({ ...localPrefs, theme: e.target.value })}
                className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded text-white focus:outline-none focus:border-blue-500"
              >
                <option value="dark">Dark</option>
                <option value="light">Light (Coming Soon)</option>
                <option value="auto">Auto (Coming Soon)</option>
              </select>
            </div>
          </section>

          {/* Keyboard Shortcuts Reference */}
          <section>
            <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <span>⌨️</span>
              Keyboard Shortcuts
            </h3>
            <div className="bg-gray-800 rounded p-4 space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-300">Focus Search</span>
                <kbd className="px-2 py-1 bg-gray-700 border border-gray-600 rounded text-xs">
                  Ctrl+K / Cmd+K
                </kbd>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-300">Navigate Messages</span>
                <kbd className="px-2 py-1 bg-gray-700 border border-gray-600 rounded text-xs">
                  ← →
                </kbd>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-300">Close Modal/Clear</span>
                <kbd className="px-2 py-1 bg-gray-700 border border-gray-600 rounded text-xs">Esc</kbd>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-300">Save</span>
                <kbd className="px-2 py-1 bg-gray-700 border border-gray-600 rounded text-xs">
                  Ctrl+S / Cmd+S
                </kbd>
              </div>
            </div>
          </section>
        </div>

        {/* Footer */}
        <div className="bg-gray-800 border-t border-gray-700 p-4 flex items-center justify-between sticky bottom-0">
          <button
            onClick={handleReset}
            className="px-4 py-2 text-gray-400 hover:text-white hover:bg-gray-700 rounded transition-colors"
          >
            Reset to Defaults
          </button>
          <div className="flex gap-2">
            <button
              onClick={onClose}
              className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded text-white transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              className="px-4 py-2 bg-blue-700 hover:bg-blue-600 rounded text-white transition-colors"
            >
              Save Changes
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

SettingsModal.propTypes = {
  isOpen: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
};
