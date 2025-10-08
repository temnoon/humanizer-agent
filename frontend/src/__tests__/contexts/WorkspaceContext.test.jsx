import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { WorkspaceProvider, useWorkspace } from '../../contexts/WorkspaceContext';

describe('WorkspaceContext', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  describe('Provider initialization', () => {
    it('should throw error when useWorkspace is used outside provider', () => {
      // Suppress console.error for this test
      const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {});

      expect(() => {
        renderHook(() => useWorkspace());
      }).toThrow('useWorkspace must be used within a WorkspaceProvider');

      consoleError.mockRestore();
    });

    it('should initialize with default state', () => {
      const { result } = renderHook(() => useWorkspace(), {
        wrapper: WorkspaceProvider,
      });

      expect(result.current.currentTab).toBeNull();
      expect(result.current.tabs).toEqual([]);
      expect(result.current.activeTabIndex).toBe(-1);
      expect(result.current.interestList).toEqual([]);
      expect(result.current.preferences).toEqual({
        defaultLimit: 100,
        itemsPerPage: 100,
        showSystemMessages: false,
        theme: 'dark',
      });
    });

    it('should load preferences from localStorage', () => {
      const savedPrefs = {
        defaultLimit: 200,
        itemsPerPage: 50,
        showSystemMessages: true,
        theme: 'light',
      };
      localStorage.setItem('humanizer-preferences', JSON.stringify(savedPrefs));

      const { result } = renderHook(() => useWorkspace(), {
        wrapper: WorkspaceProvider,
      });

      expect(result.current.preferences).toEqual(savedPrefs);
    });

    it('should handle corrupted localStorage gracefully', () => {
      localStorage.setItem('humanizer-preferences', 'invalid json');

      const { result } = renderHook(() => useWorkspace(), {
        wrapper: WorkspaceProvider,
      });

      expect(result.current.preferences).toEqual({
        defaultLimit: 100,
        itemsPerPage: 100,
        showSystemMessages: false,
        theme: 'dark',
      });
    });
  });

  describe('Tab management', () => {
    it('should add a new tab', () => {
      const { result } = renderHook(() => useWorkspace(), {
        wrapper: WorkspaceProvider,
      });

      act(() => {
        result.current.addTab('conversation', 'Test Conversation', { id: 1 });
      });

      expect(result.current.tabs).toHaveLength(1);
      expect(result.current.tabs[0]).toMatchObject({
        type: 'conversation',
        title: 'Test Conversation',
        data: { id: 1 },
      });
      expect(result.current.activeTabIndex).toBe(0);
      expect(result.current.currentTab).toBe(result.current.tabs[0]);
    });

    it('should add multiple tabs', () => {
      const { result } = renderHook(() => useWorkspace(), {
        wrapper: WorkspaceProvider,
      });

      act(() => {
        result.current.addTab('conversation', 'Tab 1', { id: 1 });
        result.current.addTab('book', 'Tab 2', { id: 2 });
        result.current.addTab('image', 'Tab 3', { id: 3 });
      });

      expect(result.current.tabs).toHaveLength(3);
      expect(result.current.activeTabIndex).toBe(2); // Last tab is active
      expect(result.current.currentTab?.title).toBe('Tab 3');
    });

    it('should close a tab', () => {
      const { result } = renderHook(() => useWorkspace(), {
        wrapper: WorkspaceProvider,
      });

      act(() => {
        result.current.addTab('conversation', 'Tab 1', { id: 1 });
        result.current.addTab('book', 'Tab 2', { id: 2 });
        result.current.addTab('image', 'Tab 3', { id: 3 });
      });

      act(() => {
        result.current.closeTab(1); // Close middle tab
      });

      expect(result.current.tabs).toHaveLength(2);
      expect(result.current.tabs[0].title).toBe('Tab 1');
      expect(result.current.tabs[1].title).toBe('Tab 3');
      expect(result.current.activeTabIndex).toBe(1);
    });

    it('should handle closing the active tab', () => {
      const { result } = renderHook(() => useWorkspace(), {
        wrapper: WorkspaceProvider,
      });

      act(() => {
        result.current.addTab('conversation', 'Tab 1', { id: 1 });
        result.current.addTab('book', 'Tab 2', { id: 2 });
      });

      act(() => {
        result.current.closeTab(1); // Close active tab
      });

      expect(result.current.tabs).toHaveLength(1);
      expect(result.current.activeTabIndex).toBe(0);
      expect(result.current.currentTab?.title).toBe('Tab 1');
    });

    it('should handle closing the last tab', () => {
      const { result } = renderHook(() => useWorkspace(), {
        wrapper: WorkspaceProvider,
      });

      act(() => {
        result.current.addTab('conversation', 'Only Tab', { id: 1 });
      });

      act(() => {
        result.current.closeTab(0);
      });

      expect(result.current.tabs).toHaveLength(0);
      expect(result.current.activeTabIndex).toBe(-1);
      expect(result.current.currentTab).toBeNull();
    });

    it('should switch to a specific tab', () => {
      const { result } = renderHook(() => useWorkspace(), {
        wrapper: WorkspaceProvider,
      });

      act(() => {
        result.current.addTab('conversation', 'Tab 1', { id: 1 });
        result.current.addTab('book', 'Tab 2', { id: 2 });
        result.current.addTab('image', 'Tab 3', { id: 3 });
      });

      act(() => {
        result.current.switchToTab(0);
      });

      expect(result.current.activeTabIndex).toBe(0);
      expect(result.current.currentTab?.title).toBe('Tab 1');
    });

    it('should navigate to next tab (wrapping)', () => {
      const { result } = renderHook(() => useWorkspace(), {
        wrapper: WorkspaceProvider,
      });

      act(() => {
        result.current.addTab('conversation', 'Tab 1', { id: 1 });
        result.current.addTab('book', 'Tab 2', { id: 2 });
        result.current.addTab('image', 'Tab 3', { id: 3 });
      });

      // Currently on Tab 3 (index 2)
      act(() => {
        result.current.navigateToNextTab();
      });

      // Should wrap to Tab 1 (index 0)
      expect(result.current.activeTabIndex).toBe(0);
      expect(result.current.currentTab?.title).toBe('Tab 1');
    });

    it('should navigate to previous tab (wrapping)', () => {
      const { result } = renderHook(() => useWorkspace(), {
        wrapper: WorkspaceProvider,
      });

      act(() => {
        result.current.addTab('conversation', 'Tab 1', { id: 1 });
        result.current.addTab('book', 'Tab 2', { id: 2 });
        result.current.addTab('image', 'Tab 3', { id: 3 });
        result.current.switchToTab(0);
      });

      // Currently on Tab 1 (index 0)
      act(() => {
        result.current.navigateToPrevTab();
      });

      // Should wrap to Tab 3 (index 2)
      expect(result.current.activeTabIndex).toBe(2);
      expect(result.current.currentTab?.title).toBe('Tab 3');
    });
  });

  describe('Interest list management', () => {
    it('should add an item to interest list', () => {
      const { result } = renderHook(() => useWorkspace(), {
        wrapper: WorkspaceProvider,
      });

      const item = {
        type: 'conversation',
        id: 1,
        title: 'Interesting Conversation',
        data: { summary: 'Test' },
      };

      act(() => {
        result.current.addToInterest(item);
      });

      expect(result.current.interestList).toHaveLength(1);
      expect(result.current.interestList[0]).toMatchObject(item);
      expect(result.current.interestList[0]).toHaveProperty('timestamp');
    });

    it('should not add duplicate items', () => {
      const { result } = renderHook(() => useWorkspace(), {
        wrapper: WorkspaceProvider,
      });

      const item = {
        type: 'conversation',
        id: 1,
        title: 'Interesting Conversation',
      };

      act(() => {
        result.current.addToInterest(item);
        result.current.addToInterest(item); // Try to add again
      });

      expect(result.current.interestList).toHaveLength(1);
    });

    it('should remove an item from interest list', () => {
      const { result } = renderHook(() => useWorkspace(), {
        wrapper: WorkspaceProvider,
      });

      const item1 = { type: 'conversation', id: 1, title: 'Item 1' };
      const item2 = { type: 'book', id: 2, title: 'Item 2' };

      act(() => {
        result.current.addToInterest(item1);
        result.current.addToInterest(item2);
      });

      act(() => {
        result.current.removeFromInterest(1);
      });

      expect(result.current.interestList).toHaveLength(1);
      expect(result.current.interestList[0].id).toBe(2);
    });

    it('should clear all items from interest list', () => {
      const { result } = renderHook(() => useWorkspace(), {
        wrapper: WorkspaceProvider,
      });

      act(() => {
        result.current.addToInterest({ type: 'conversation', id: 1, title: 'Item 1' });
        result.current.addToInterest({ type: 'book', id: 2, title: 'Item 2' });
        result.current.addToInterest({ type: 'image', id: 3, title: 'Item 3' });
      });

      act(() => {
        result.current.clearInterestList();
      });

      expect(result.current.interestList).toHaveLength(0);
    });

    it('should navigate to an interest item by creating a tab', () => {
      const { result } = renderHook(() => useWorkspace(), {
        wrapper: WorkspaceProvider,
      });

      const item = {
        type: 'conversation',
        id: 1,
        title: 'Interesting Conversation',
        data: { conversationId: 1 },
      };

      act(() => {
        result.current.addToInterest(item);
        result.current.navigateToInterest(item);
      });

      expect(result.current.tabs).toHaveLength(1);
      expect(result.current.currentTab).toMatchObject({
        type: 'conversation',
        title: 'Interesting Conversation',
        data: { conversationId: 1 },
      });
    });
  });

  describe('Preferences management', () => {
    it('should update preferences', () => {
      const { result } = renderHook(() => useWorkspace(), {
        wrapper: WorkspaceProvider,
      });

      act(() => {
        result.current.updatePreferences({ itemsPerPage: 200 });
      });

      expect(result.current.preferences.itemsPerPage).toBe(200);
      expect(result.current.preferences.defaultLimit).toBe(100); // Other values unchanged
    });

    it('should persist preferences to localStorage', () => {
      const { result } = renderHook(() => useWorkspace(), {
        wrapper: WorkspaceProvider,
      });

      act(() => {
        result.current.updatePreferences({
          itemsPerPage: 200,
          theme: 'light',
        });
      });

      const saved = JSON.parse(localStorage.getItem('humanizer-preferences'));
      expect(saved).toMatchObject({
        itemsPerPage: 200,
        theme: 'light',
        defaultLimit: 100,
        showSystemMessages: false,
      });
    });

    it('should handle localStorage errors gracefully', () => {
      const { result } = renderHook(() => useWorkspace(), {
        wrapper: WorkspaceProvider,
      });

      // Mock localStorage.setItem to throw
      const setItemSpy = vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {
        throw new Error('QuotaExceededError');
      });

      const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {});

      act(() => {
        result.current.updatePreferences({ itemsPerPage: 200 });
      });

      // Preferences should still update in memory
      expect(result.current.preferences.itemsPerPage).toBe(200);
      expect(consoleError).toHaveBeenCalled();

      setItemSpy.mockRestore();
      consoleError.mockRestore();
    });

    it('should merge new preferences with existing ones', () => {
      const { result } = renderHook(() => useWorkspace(), {
        wrapper: WorkspaceProvider,
      });

      act(() => {
        result.current.updatePreferences({ itemsPerPage: 200 });
        result.current.updatePreferences({ theme: 'light' });
      });

      expect(result.current.preferences).toEqual({
        defaultLimit: 100,
        itemsPerPage: 200,
        showSystemMessages: false,
        theme: 'light',
      });
    });
  });

  describe('Complex workflows', () => {
    it('should handle complete user journey: add tabs, manage interest list, switch tabs', () => {
      const { result } = renderHook(() => useWorkspace(), {
        wrapper: WorkspaceProvider,
      });

      // User opens a conversation
      act(() => {
        result.current.addTab('conversation', 'Conv 1', { id: 1 });
      });

      // User finds it interesting
      act(() => {
        result.current.addToInterest({
          type: 'conversation',
          id: 1,
          title: 'Conv 1',
        });
      });

      // User opens a book
      act(() => {
        result.current.addTab('book', 'Book 1', { id: 2 });
      });

      // User switches back to conversation
      act(() => {
        result.current.switchToTab(0);
      });

      expect(result.current.currentTab?.type).toBe('conversation');
      expect(result.current.interestList).toHaveLength(1);
      expect(result.current.tabs).toHaveLength(2);
    });

    it('should maintain state after closing non-active tabs', () => {
      const { result } = renderHook(() => useWorkspace(), {
        wrapper: WorkspaceProvider,
      });

      act(() => {
        result.current.addTab('conversation', 'Tab 1', { id: 1 });
        result.current.addTab('book', 'Tab 2', { id: 2 });
        result.current.addTab('image', 'Tab 3', { id: 3 });
        result.current.switchToTab(0);
      });

      // Close middle tab while first tab is active
      act(() => {
        result.current.closeTab(1);
      });

      expect(result.current.currentTab?.title).toBe('Tab 1');
      expect(result.current.activeTabIndex).toBe(0);
      expect(result.current.tabs).toHaveLength(2);
    });
  });
});
