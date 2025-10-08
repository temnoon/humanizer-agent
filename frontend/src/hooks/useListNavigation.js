import { useState, useEffect, useCallback } from 'react';

/**
 * useListNavigation - Unified keyboard and UI navigation for lists
 *
 * Provides:
 * - Keyboard navigation (ArrowUp, ArrowDown, Enter, Escape)
 * - Current index tracking
 * - Prev/Next navigation functions
 * - Selection handling
 *
 * Usage:
 * const { currentIndex, handlePrev, handleNext, handleSelect, handleKeyDown } = useListNavigation({
 *   items: messages,
 *   onSelect: (item) => openMessage(item),
 *   loop: false, // Whether to loop from end to start
 *   enabled: true
 * });
 */
export function useListNavigation({ items = [], onSelect, loop = false, enabled = true }) {
  const [currentIndex, setCurrentIndex] = useState(0);

  // Reset index when items change
  useEffect(() => {
    if (items.length === 0) {
      setCurrentIndex(0);
    } else if (currentIndex >= items.length) {
      setCurrentIndex(Math.max(0, items.length - 1));
    }
  }, [items, currentIndex]);

  const handlePrev = useCallback(() => {
    setCurrentIndex(prev => {
      if (prev === 0) {
        return loop ? items.length - 1 : 0;
      }
      return prev - 1;
    });
  }, [loop, items.length]);

  const handleNext = useCallback(() => {
    setCurrentIndex(prev => {
      if (prev === items.length - 1) {
        return loop ? 0 : items.length - 1;
      }
      return prev + 1;
    });
  }, [loop, items.length]);

  const handleSelect = useCallback((index) => {
    if (index >= 0 && index < items.length) {
      setCurrentIndex(index);
      if (onSelect) {
        onSelect(items[index], index);
      }
    }
  }, [items, onSelect]);

  const handleKeyDown = useCallback((e) => {
    if (!enabled || items.length === 0) return;

    switch (e.key) {
      case 'ArrowUp':
      case 'ArrowLeft':
        e.preventDefault();
        handlePrev();
        break;
      case 'ArrowDown':
      case 'ArrowRight':
        e.preventDefault();
        handleNext();
        break;
      case 'Enter':
        e.preventDefault();
        if (onSelect && items[currentIndex]) {
          onSelect(items[currentIndex], currentIndex);
        }
        break;
      case 'Escape':
        e.preventDefault();
        // Let parent handle escape (close modal, etc.)
        break;
      default:
        break;
    }
  }, [enabled, items, currentIndex, handlePrev, handleNext, onSelect]);

  // Attach keyboard listener
  useEffect(() => {
    if (!enabled) return;

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [enabled, handleKeyDown]);

  return {
    currentIndex,
    setCurrentIndex,
    handlePrev,
    handleNext,
    handleSelect,
    handleKeyDown,
    hasPrev: currentIndex > 0,
    hasNext: currentIndex < items.length - 1,
    currentItem: items[currentIndex]
  };
}
