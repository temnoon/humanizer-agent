import { useEffect } from 'react';

/**
 * useKeyboardShortcuts - Global keyboard shortcut hook
 *
 * Provides consistent keyboard navigation throughout the app.
 * Supports:
 * - Ctrl/Cmd+K: Focus search
 * - Escape: Close modals/clear search
 * - Arrow keys: Navigate lists/messages
 * - Ctrl/Cmd+N: New item (context-dependent)
 * - Ctrl/Cmd+S: Save (context-dependent)
 */
export function useKeyboardShortcuts({
  onSearch,
  onEscape,
  onArrowUp,
  onArrowDown,
  onArrowLeft,
  onArrowRight,
  onNew,
  onSave,
  enabled = true,
}) {
  useEffect(() => {
    if (!enabled) return;

    const handleKeyDown = (e) => {
      const isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0;
      const ctrlOrCmd = isMac ? e.metaKey : e.ctrlKey;

      // Ctrl/Cmd+K: Focus search
      if (ctrlOrCmd && e.key === 'k') {
        e.preventDefault();
        if (onSearch) {
          onSearch();
        }
      }

      // Escape: Close/Clear
      if (e.key === 'Escape') {
        if (onEscape) {
          onEscape();
        }
      }

      // Arrow keys (only if not in input/textarea)
      const isInputField = ['INPUT', 'TEXTAREA'].includes(document.activeElement.tagName);
      if (!isInputField) {
        if (e.key === 'ArrowUp' && onArrowUp) {
          e.preventDefault();
          onArrowUp();
        }
        if (e.key === 'ArrowDown' && onArrowDown) {
          e.preventDefault();
          onArrowDown();
        }
        if (e.key === 'ArrowLeft' && onArrowLeft) {
          e.preventDefault();
          onArrowLeft();
        }
        if (e.key === 'ArrowRight' && onArrowRight) {
          e.preventDefault();
          onArrowRight();
        }
      }

      // Ctrl/Cmd+N: New
      if (ctrlOrCmd && e.key === 'n' && onNew) {
        e.preventDefault();
        onNew();
      }

      // Ctrl/Cmd+S: Save
      if (ctrlOrCmd && e.key === 's' && onSave) {
        e.preventDefault();
        onSave();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onSearch, onEscape, onArrowUp, onArrowDown, onArrowLeft, onArrowRight, onNew, onSave, enabled]);
}

/**
 * useGlobalSearch - Global search shortcut (Ctrl/Cmd+K)
 *
 * Focuses the search input when user presses Ctrl/Cmd+K
 */
export function useGlobalSearch(searchInputRef) {
  useEffect(() => {
    const handleKeyDown = (e) => {
      const isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0;
      const ctrlOrCmd = isMac ? e.metaKey : e.ctrlKey;

      if (ctrlOrCmd && e.key === 'k') {
        e.preventDefault();
        if (searchInputRef?.current) {
          searchInputRef.current.focus();
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [searchInputRef]);
}
