import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook } from '@testing-library/react';
import { useKeyboardShortcuts } from '../../hooks/useKeyboardShortcuts';

describe('useKeyboardShortcuts', () => {
  let mockCallbacks;

  beforeEach(() => {
    mockCallbacks = {
      onSearch: vi.fn(),
      onEscape: vi.fn(),
      onArrowUp: vi.fn(),
      onArrowDown: vi.fn(),
      onArrowLeft: vi.fn(),
      onArrowRight: vi.fn(),
      onNew: vi.fn(),
      onSave: vi.fn(),
    };
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  const pressKey = (key, options = {}) => {
    const event = new KeyboardEvent('keydown', {
      key,
      metaKey: options.metaKey || false,
      ctrlKey: options.ctrlKey || false,
      ...options,
    });
    window.dispatchEvent(event);
  };

  it('should call onSearch when Ctrl+K is pressed', () => {
    renderHook(() => useKeyboardShortcuts(mockCallbacks));

    pressKey('k', { ctrlKey: true });

    expect(mockCallbacks.onSearch).toHaveBeenCalled();
  });

  it('should call onEscape when Escape is pressed', () => {
    renderHook(() => useKeyboardShortcuts(mockCallbacks));

    pressKey('Escape');

    expect(mockCallbacks.onEscape).toHaveBeenCalled();
  });

  it('should call onArrowUp when ArrowUp is pressed', () => {
    renderHook(() => useKeyboardShortcuts(mockCallbacks));

    pressKey('ArrowUp');

    expect(mockCallbacks.onArrowUp).toHaveBeenCalled();
  });

  it('should call onArrowDown when ArrowDown is pressed', () => {
    renderHook(() => useKeyboardShortcuts(mockCallbacks));

    pressKey('ArrowDown');

    expect(mockCallbacks.onArrowDown).toHaveBeenCalled();
  });

  it('should call onArrowLeft when ArrowLeft is pressed', () => {
    renderHook(() => useKeyboardShortcuts(mockCallbacks));

    pressKey('ArrowLeft');

    expect(mockCallbacks.onArrowLeft).toHaveBeenCalled();
  });

  it('should call onArrowRight when ArrowRight is pressed', () => {
    renderHook(() => useKeyboardShortcuts(mockCallbacks));

    pressKey('ArrowRight');

    expect(mockCallbacks.onArrowRight).toHaveBeenCalled();
  });

  it('should call onNew when Ctrl+N is pressed', () => {
    renderHook(() => useKeyboardShortcuts(mockCallbacks));

    pressKey('n', { ctrlKey: true });

    expect(mockCallbacks.onNew).toHaveBeenCalled();
  });

  it('should call onSave when Ctrl+S is pressed', () => {
    renderHook(() => useKeyboardShortcuts(mockCallbacks));

    pressKey('s', { ctrlKey: true });

    expect(mockCallbacks.onSave).toHaveBeenCalled();
  });

  it('should not call arrow handlers when focused in input field', () => {
    renderHook(() => useKeyboardShortcuts(mockCallbacks));

    // Create and focus an input element
    const input = document.createElement('input');
    document.body.appendChild(input);
    input.focus();

    pressKey('ArrowUp');

    expect(mockCallbacks.onArrowUp).not.toHaveBeenCalled();

    // Cleanup
    document.body.removeChild(input);
  });

  it('should not call arrow handlers when focused in textarea', () => {
    renderHook(() => useKeyboardShortcuts(mockCallbacks));

    // Create and focus a textarea
    const textarea = document.createElement('textarea');
    document.body.appendChild(textarea);
    textarea.focus();

    pressKey('ArrowDown');

    expect(mockCallbacks.onArrowDown).not.toHaveBeenCalled();

    // Cleanup
    document.body.removeChild(textarea);
  });

  it('should not call handlers when enabled is false', () => {
    renderHook(() => useKeyboardShortcuts({ ...mockCallbacks, enabled: false }));

    pressKey('k', { ctrlKey: true });
    pressKey('Escape');
    pressKey('ArrowUp');

    expect(mockCallbacks.onSearch).not.toHaveBeenCalled();
    expect(mockCallbacks.onEscape).not.toHaveBeenCalled();
    expect(mockCallbacks.onArrowUp).not.toHaveBeenCalled();
  });

  it('should not call handlers that are not provided', () => {
    renderHook(() => useKeyboardShortcuts({
      onSearch: mockCallbacks.onSearch,
      // Other handlers not provided
    }));

    // Should not throw errors
    expect(() => {
      pressKey('Escape');
      pressKey('ArrowUp');
      pressKey('s', { ctrlKey: true });
    }).not.toThrow();

    expect(mockCallbacks.onSearch).not.toHaveBeenCalled();
  });

  it('should cleanup event listeners on unmount', () => {
    const { unmount } = renderHook(() => useKeyboardShortcuts(mockCallbacks));

    unmount();

    // After unmount, handlers should not be called
    pressKey('k', { ctrlKey: true });

    expect(mockCallbacks.onSearch).not.toHaveBeenCalled();
  });

  it('should update handlers when dependencies change', () => {
    const { rerender } = renderHook(
      ({ callbacks }) => useKeyboardShortcuts(callbacks),
      { initialProps: { callbacks: mockCallbacks } }
    );

    // Change callback
    const newOnSearch = vi.fn();
    rerender({ callbacks: { ...mockCallbacks, onSearch: newOnSearch } });

    pressKey('k', { ctrlKey: true });

    expect(newOnSearch).toHaveBeenCalled();
    expect(mockCallbacks.onSearch).not.toHaveBeenCalled();
  });

  it('should prevent default for Ctrl/Cmd+K', () => {
    renderHook(() => useKeyboardShortcuts(mockCallbacks));

    const event = new KeyboardEvent('keydown', {
      key: 'k',
      ctrlKey: true,
      bubbles: true,
      cancelable: true,
    });

    const preventDefaultSpy = vi.spyOn(event, 'preventDefault');
    window.dispatchEvent(event);

    expect(preventDefaultSpy).toHaveBeenCalled();
  });

  it('should prevent default for arrow keys when not in input', () => {
    renderHook(() => useKeyboardShortcuts(mockCallbacks));

    const event = new KeyboardEvent('keydown', {
      key: 'ArrowUp',
      bubbles: true,
      cancelable: true,
    });

    const preventDefaultSpy = vi.spyOn(event, 'preventDefault');
    window.dispatchEvent(event);

    expect(preventDefaultSpy).toHaveBeenCalled();
  });

  it('should prevent default for Ctrl/Cmd+N', () => {
    renderHook(() => useKeyboardShortcuts(mockCallbacks));

    const event = new KeyboardEvent('keydown', {
      key: 'n',
      ctrlKey: true,
      bubbles: true,
      cancelable: true,
    });

    const preventDefaultSpy = vi.spyOn(event, 'preventDefault');
    window.dispatchEvent(event);

    expect(preventDefaultSpy).toHaveBeenCalled();
  });

  it('should prevent default for Ctrl/Cmd+S', () => {
    renderHook(() => useKeyboardShortcuts(mockCallbacks));

    const event = new KeyboardEvent('keydown', {
      key: 's',
      ctrlKey: true,
      bubbles: true,
      cancelable: true,
    });

    const preventDefaultSpy = vi.spyOn(event, 'preventDefault');
    window.dispatchEvent(event);

    expect(preventDefaultSpy).toHaveBeenCalled();
  });
});
