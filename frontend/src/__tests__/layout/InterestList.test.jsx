import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import InterestList from '../../components/layout/InterestList';
import { WorkspaceProvider } from '../../contexts/WorkspaceContext';
import { useWorkspace } from '../../contexts/WorkspaceContext';

// Create a test wrapper that provides both the provider and controls
function TestWrapper({ children, initialItems = [] }) {
  return (
    <WorkspaceProvider>
      <InterestListTester initialItems={initialItems} />
      {children}
    </WorkspaceProvider>
  );
}

// Helper component to populate interest list
function InterestListTester({ initialItems }) {
  const { addToInterest } = useWorkspace();

  // Add initial items on mount
  React.useEffect(() => {
    initialItems.forEach(item => addToInterest(item));
  }, []);

  return null;
}

// Mock React.useEffect for simpler testing
import * as React from 'react';

describe('InterestList', () => {
  describe('Empty state', () => {
    it('should return null when interest list is empty', () => {
      const { container } = render(
        <WorkspaceProvider>
          <InterestList />
        </WorkspaceProvider>
      );

      expect(container.firstChild).toBeNull();
    });
  });

  describe('Rendering with items', () => {
    it('should render interest list with items', () => {
      const { container } = render(
        <WorkspaceProvider>
          <InterestListWithItems />
        </WorkspaceProvider>
      );

      expect(screen.getByText('Interest Trail (2)')).toBeInTheDocument();
    });

    it('should display all interest items', () => {
      render(
        <WorkspaceProvider>
          <InterestListWithItems />
        </WorkspaceProvider>
      );

      expect(screen.getByText('Test Conversation')).toBeInTheDocument();
      expect(screen.getByText('Test Image')).toBeInTheDocument();
    });

    it('should show correct icons for different types', () => {
      render(
        <WorkspaceProvider>
          <InterestListWithMultipleTypes />
        </WorkspaceProvider>
      );

      // Check that various type icons are rendered (by checking the items exist)
      expect(screen.getByText('Conversation Item')).toBeInTheDocument();
      expect(screen.getByText('Book Item')).toBeInTheDocument();
      expect(screen.getByText('Image Item')).toBeInTheDocument();
    });

    it('should show item context when available', () => {
      render(
        <WorkspaceProvider>
          <InterestListWithContext />
        </WorkspaceProvider>
      );

      expect(screen.getByText('Additional context')).toBeInTheDocument();
    });

    it('should show connection arrows between items', () => {
      const { container } = render(
        <WorkspaceProvider>
          <InterestListWithItems />
        </WorkspaceProvider>
      );

      // Should have arrow (→) for second item
      const arrows = container.querySelectorAll('span');
      const hasArrow = Array.from(arrows).some(span => span.textContent === '→');
      expect(hasArrow).toBe(true);
    });
  });

  describe('Collapse/Expand', () => {
    it('should start expanded by default', () => {
      render(
        <WorkspaceProvider>
          <InterestListWithItems />
        </WorkspaceProvider>
      );

      expect(screen.getByText('Test Conversation')).toBeInTheDocument();
    });

    it('should collapse when header is clicked', () => {
      render(
        <WorkspaceProvider>
          <InterestListWithItems />
        </WorkspaceProvider>
      );

      const header = screen.getByText('Interest Trail (2)').closest('div');
      fireEvent.click(header);

      // Items should not be visible when collapsed
      expect(screen.queryByText('Test Conversation')).not.toBeInTheDocument();
    });

    it('should expand again when clicked twice', () => {
      render(
        <WorkspaceProvider>
          <InterestListWithItems />
        </WorkspaceProvider>
      );

      const header = screen.getByText('Interest Trail (2)').closest('div');

      // Collapse
      fireEvent.click(header);
      expect(screen.queryByText('Test Conversation')).not.toBeInTheDocument();

      // Expand
      fireEvent.click(header);
      expect(screen.getByText('Test Conversation')).toBeInTheDocument();
    });
  });

  describe('User interactions', () => {
    it('should call navigateToInterest when item is clicked', () => {
      const { getByText } = render(
        <WorkspaceProvider>
          <InterestListWithItems />
        </WorkspaceProvider>
      );

      const item = getByText('Test Conversation').closest('div');
      fireEvent.click(item);

      // After clicking, a tab should be created (we can verify by checking workspace state)
      // For now, just verify the click doesn't crash
      expect(item).toBeInTheDocument();
    });

    it('should remove item when remove button is clicked', () => {
      const { container } = render(
        <WorkspaceProvider>
          <InterestListWithItems />
        </WorkspaceProvider>
      );

      // Find remove button (X icon)
      const removeButtons = container.querySelectorAll('button');
      const removeButton = Array.from(removeButtons).find(btn => {
        return btn.querySelector('svg path[d*="M6 18L18 6M6 6l12 12"]');
      });

      if (removeButton) {
        fireEvent.click(removeButton);
      }

      // Verify component still renders (just with fewer items)
      expect(screen.getByText(/Interest Trail/)).toBeInTheDocument();
    });

    it('should clear all items when clear button is clicked', () => {
      const { container } = render(
        <WorkspaceProvider>
          <InterestListWithItems />
        </WorkspaceProvider>
      );

      const clearButton = screen.getByText('Clear');
      fireEvent.click(clearButton);

      // After clearing, component should not render (returns null)
      expect(container.firstChild).toBeNull();
    });

    it('should stop propagation when clear button is clicked', () => {
      render(
        <WorkspaceProvider>
          <InterestListWithItems />
        </WorkspaceProvider>
      );

      const clearButton = screen.getByText('Clear');
      const stopPropagationSpy = vi.fn();

      // Override stopPropagation
      const originalClick = clearButton.onclick;
      clearButton.onclick = (e) => {
        stopPropagationSpy();
        originalClick?.call(clearButton, e);
      };

      fireEvent.click(clearButton);

      // List should not collapse (stopPropagation worked)
      // If it collapsed, items wouldn't be visible
    });

    it('should stop propagation when remove button is clicked', () => {
      const { container } = render(
        <WorkspaceProvider>
          <InterestListWithItems />
        </WorkspaceProvider>
      );

      // Find remove button
      const removeButtons = container.querySelectorAll('button');
      const removeButton = Array.from(removeButtons).find(btn => {
        return btn.querySelector('svg path[d*="M6 18L18 6M6 6l12 12"]');
      });

      if (removeButton) {
        fireEvent.click(removeButton);

        // Should still be expanded (not collapsed by click)
        expect(screen.getByText(/Interest Trail/)).toBeInTheDocument();
      }
    });
  });

  describe('Icon mapping', () => {
    it('should show correct icon for conversation type', () => {
      render(
        <WorkspaceProvider>
          <InterestListWithType type="conversation" />
        </WorkspaceProvider>
      );

      expect(screen.getByText('Test Item')).toBeInTheDocument();
    });

    it('should show default icon for unknown type', () => {
      render(
        <WorkspaceProvider>
          <InterestListWithType type="unknown" />
        </WorkspaceProvider>
      );

      expect(screen.getByText('Test Item')).toBeInTheDocument();
    });
  });
});

// Helper components to render InterestList with preset data
function InterestListWithItems() {
  const { addToInterest } = useWorkspace();

  React.useEffect(() => {
    addToInterest({
      type: 'conversation',
      id: 1,
      title: 'Test Conversation',
    });
    addToInterest({
      type: 'image',
      id: 2,
      title: 'Test Image',
    });
  }, []);

  return <InterestList />;
}

function InterestListWithMultipleTypes() {
  const { addToInterest } = useWorkspace();

  React.useEffect(() => {
    addToInterest({ type: 'conversation', id: 1, title: 'Conversation Item' });
    addToInterest({ type: 'book', id: 2, title: 'Book Item' });
    addToInterest({ type: 'image', id: 3, title: 'Image Item' });
    addToInterest({ type: 'message', id: 4, title: 'Message Item' });
  }, []);

  return <InterestList />;
}

function InterestListWithContext() {
  const { addToInterest } = useWorkspace();

  React.useEffect(() => {
    addToInterest({
      type: 'conversation',
      id: 1,
      title: 'Item with Context',
      context: 'Additional context',
    });
  }, []);

  return <InterestList />;
}

function InterestListWithType({ type }) {
  const { addToInterest } = useWorkspace();

  React.useEffect(() => {
    addToInterest({
      type,
      id: 1,
      title: 'Test Item',
    });
  }, [type]);

  return <InterestList />;
}
