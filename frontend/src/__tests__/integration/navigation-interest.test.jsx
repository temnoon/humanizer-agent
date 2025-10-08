import { describe, it, expect, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { WorkspaceProvider, useWorkspace } from '../../contexts/WorkspaceContext';

describe('Navigation and Interest List Integration', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  describe('Interest List Navigation Flow', () => {
    it('should add item to interest list and navigate to it', () => {
      const { result } = renderHook(() => useWorkspace(), {
        wrapper: WorkspaceProvider,
      });

      // 1. Add item to interest list
      const item = {
        type: 'conversation',
        id: 1,
        title: 'Interesting Conversation',
        data: { conversationId: 1 },
      };

      act(() => {
        result.current.addToInterest(item);
      });

      expect(result.current.interestList).toHaveLength(1);
      expect(result.current.interestList[0]).toMatchObject(item);

      // 2. Navigate to the item (creates a tab)
      act(() => {
        result.current.navigateToInterest(item);
      });

      expect(result.current.tabs).toHaveLength(1);
      expect(result.current.currentTab).toMatchObject({
        type: 'conversation',
        title: 'Interesting Conversation',
      });
    });

    it('should support full exploration flow: browse → interest → navigate → explore more', () => {
      const { result } = renderHook(() => useWorkspace(), {
        wrapper: WorkspaceProvider,
      });

      // 1. User browses images and finds interesting one
      const imageItem = {
        type: 'image',
        id: 1,
        title: 'Cool Image',
      };

      act(() => {
        result.current.addToInterest(imageItem);
      });

      expect(result.current.interestList).toHaveLength(1);

      // 2. User opens the image conversation
      const convItem = {
        type: 'conversation',
        id: 2,
        title: 'Image Conversation',
      };

      act(() => {
        result.current.addTab('conversation', convItem.title, { id: convItem.id });
        result.current.addToInterest(convItem);
      });

      expect(result.current.interestList).toHaveLength(2);
      expect(result.current.tabs).toHaveLength(1);

      // 3. User finds related transformation
      const transformItem = {
        type: 'transformation',
        id: 3,
        title: 'Related Transformation',
      };

      act(() => {
        result.current.addToInterest(transformItem);
      });

      expect(result.current.interestList).toHaveLength(3);

      // 4. User navigates back through interest list
      act(() => {
        result.current.navigateToInterest(result.current.interestList[0]);
      });

      expect(result.current.tabs).toHaveLength(2);
      expect(result.current.currentTab?.type).toBe('image');
    });

    it('should handle removing items from interest list while navigating', () => {
      const { result } = renderHook(() => useWorkspace(), {
        wrapper: WorkspaceProvider,
      });

      // Add multiple items
      act(() => {
        result.current.addToInterest({ type: 'conversation', id: 1, title: 'Conv 1' });
        result.current.addToInterest({ type: 'conversation', id: 2, title: 'Conv 2' });
        result.current.addToInterest({ type: 'conversation', id: 3, title: 'Conv 3' });
      });

      expect(result.current.interestList).toHaveLength(3);

      // Navigate to second item
      act(() => {
        result.current.navigateToInterest(result.current.interestList[1]);
      });

      expect(result.current.tabs).toHaveLength(1);

      // Remove first item
      act(() => {
        result.current.removeFromInterest(1);
      });

      expect(result.current.interestList).toHaveLength(2);
      expect(result.current.tabs).toHaveLength(1); // Tab should still exist

      // Navigate to third item (now second in list)
      act(() => {
        result.current.navigateToInterest(result.current.interestList[1]);
      });

      expect(result.current.tabs).toHaveLength(2);
    });

    it('should prevent duplicate items in interest list', () => {
      const { result } = renderHook(() => useWorkspace(), {
        wrapper: WorkspaceProvider,
      });

      const item = {
        type: 'conversation',
        id: 1,
        title: 'Same Conversation',
      };

      // Add same item multiple times
      act(() => {
        result.current.addToInterest(item);
        result.current.addToInterest(item);
        result.current.addToInterest(item);
      });

      // Should only have one item
      expect(result.current.interestList).toHaveLength(1);
    });

    it('should clear interest list without affecting tabs', () => {
      const { result } = renderHook(() => useWorkspace(), {
        wrapper: WorkspaceProvider,
      });

      // Add items and create tabs
      act(() => {
        result.current.addToInterest({ type: 'conversation', id: 1, title: 'Conv 1' });
        result.current.addTab('conversation', 'Conv 1', { id: 1 });
        result.current.addToInterest({ type: 'conversation', id: 2, title: 'Conv 2' });
      });

      expect(result.current.interestList).toHaveLength(2);
      expect(result.current.tabs).toHaveLength(1);

      // Clear interest list
      act(() => {
        result.current.clearInterestList();
      });

      expect(result.current.interestList).toHaveLength(0);
      expect(result.current.tabs).toHaveLength(1); // Tabs should remain
    });
  });

  describe('Tab and Interest List Coordination', () => {
    it('should maintain independent state for tabs and interest list', () => {
      const { result } = renderHook(() => useWorkspace(), {
        wrapper: WorkspaceProvider,
      });

      // Add items to interest list
      act(() => {
        result.current.addToInterest({ type: 'conversation', id: 1, title: 'Conv 1' });
        result.current.addToInterest({ type: 'conversation', id: 2, title: 'Conv 2' });
      });

      // Create tabs independently
      act(() => {
        result.current.addTab('book', 'Book 1', { id: 3 });
        result.current.addTab('image', 'Image 1', { id: 4 });
      });

      expect(result.current.interestList).toHaveLength(2);
      expect(result.current.tabs).toHaveLength(2);

      // Close a tab
      act(() => {
        result.current.closeTab(0);
      });

      expect(result.current.tabs).toHaveLength(1);
      expect(result.current.interestList).toHaveLength(2); // Interest list unchanged

      // Remove from interest list
      act(() => {
        result.current.removeFromInterest(1);
      });

      expect(result.current.interestList).toHaveLength(1);
      expect(result.current.tabs).toHaveLength(1); // Tabs unchanged
    });

    it('should support navigating to interest item multiple times', () => {
      const { result } = renderHook(() => useWorkspace(), {
        wrapper: WorkspaceProvider,
      });

      const item = {
        type: 'conversation',
        id: 1,
        title: 'Conv 1',
      };

      act(() => {
        result.current.addToInterest(item);
      });

      // Navigate to it multiple times
      act(() => {
        result.current.navigateToInterest(item);
        result.current.navigateToInterest(item);
        result.current.navigateToInterest(item);
      });

      // Should create 3 tabs (even though it's the same item)
      expect(result.current.tabs).toHaveLength(3);
      expect(result.current.interestList).toHaveLength(1); // Still only one interest item
    });
  });

  describe('Complex Navigation Scenarios', () => {
    it('should handle circular navigation through interest list', () => {
      const { result } = renderHook(() => useWorkspace(), {
        wrapper: WorkspaceProvider,
      });

      // Add items in a "circular" pattern
      const items = [
        { type: 'conversation', id: 1, title: 'Conv 1' },
        { type: 'image', id: 2, title: 'Image 1' },
        { type: 'book', id: 3, title: 'Book 1' },
      ];

      act(() => {
        items.forEach(item => result.current.addToInterest(item));
      });

      // Navigate through all items
      items.forEach((item, index) => {
        act(() => {
          result.current.navigateToInterest(result.current.interestList[index]);
        });
      });

      expect(result.current.tabs).toHaveLength(3);

      // Navigate back to first item
      act(() => {
        result.current.navigateToInterest(result.current.interestList[0]);
      });

      expect(result.current.tabs).toHaveLength(4);
      expect(result.current.currentTab?.title).toBe('Conv 1');
    });

    it('should maintain interest list order over time', () => {
      const { result } = renderHook(() => useWorkspace(), {
        wrapper: WorkspaceProvider,
      });

      // Add items one by one
      const items = [
        { type: 'conversation', id: 1, title: 'First' },
        { type: 'conversation', id: 2, title: 'Second' },
        { type: 'conversation', id: 3, title: 'Third' },
      ];

      items.forEach(item => {
        act(() => {
          result.current.addToInterest(item);
        });
      });

      // Verify order
      expect(result.current.interestList[0].title).toBe('First');
      expect(result.current.interestList[1].title).toBe('Second');
      expect(result.current.interestList[2].title).toBe('Third');

      // Remove middle item
      act(() => {
        result.current.removeFromInterest(2);
      });

      // Verify order maintained
      expect(result.current.interestList[0].title).toBe('First');
      expect(result.current.interestList[1].title).toBe('Third');
    });
  });
});
