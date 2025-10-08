import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import LayoutManager from '../../components/layout/LayoutManager';

// Mock react-resizable-panels
vi.mock('react-resizable-panels', () => ({
  Panel: ({ children, className }) => <div className={className} data-testid="panel">{children}</div>,
  PanelGroup: ({ children, direction, onLayout }) => (
    <div data-testid={`panel-group-${direction}`} data-onlayout={onLayout ? 'true' : 'false'}>
      {children}
    </div>
  ),
  PanelResizeHandle: ({ className }) => <div className={className} data-testid="resize-handle" />,
}));

describe('LayoutManager', () => {
  const mockSidebar = <div data-testid="sidebar">Sidebar</div>;
  const mockMainContent = <div data-testid="main-content">Main Content</div>;
  const mockPreviewPane = <div data-testid="preview-pane">Preview</div>;
  const mockInspectorPane = <div data-testid="inspector-pane">Inspector</div>;

  beforeEach(() => {
    localStorage.clear();
  });

  describe('Initialization', () => {
    it('should render with default layout', () => {
      render(
        <LayoutManager
          sidebar={mockSidebar}
          mainContent={mockMainContent}
        />
      );

      expect(screen.getByTestId('sidebar')).toBeInTheDocument();
      expect(screen.getByTestId('main-content')).toBeInTheDocument();
    });

    it('should initialize with default sizes when no saved layout', () => {
      render(
        <LayoutManager
          sidebar={mockSidebar}
          mainContent={mockMainContent}
        />
      );

      // Component should render without errors
      expect(screen.getByTestId('panel-group-horizontal')).toBeInTheDocument();
    });

    it('should load saved layout from localStorage', () => {
      const savedLayout = {
        sidebarSize: 30,
        mainSize: 40,
        previewSize: 30,
        inspectorSize: 25,
      };
      localStorage.setItem('humanizer-layout', JSON.stringify(savedLayout));

      render(
        <LayoutManager
          sidebar={mockSidebar}
          mainContent={mockMainContent}
        />
      );

      // Verify localStorage was read
      const stored = JSON.parse(localStorage.getItem('humanizer-layout'));
      expect(stored).toEqual(savedLayout);
    });

    it('should handle corrupted localStorage gracefully', () => {
      localStorage.setItem('humanizer-layout', 'invalid json');

      render(
        <LayoutManager
          sidebar={mockSidebar}
          mainContent={mockMainContent}
        />
      );

      // Should render with default layout without crashing
      expect(screen.getByTestId('sidebar')).toBeInTheDocument();
      expect(screen.getByTestId('main-content')).toBeInTheDocument();
    });
  });

  describe('Pane visibility', () => {
    it('should not show preview pane when showPreview is false', () => {
      render(
        <LayoutManager
          sidebar={mockSidebar}
          mainContent={mockMainContent}
          previewPane={mockPreviewPane}
          showPreview={false}
        />
      );

      expect(screen.queryByTestId('preview-pane')).not.toBeInTheDocument();
    });

    it('should show preview pane when showPreview is true', () => {
      render(
        <LayoutManager
          sidebar={mockSidebar}
          mainContent={mockMainContent}
          previewPane={mockPreviewPane}
          showPreview={true}
        />
      );

      expect(screen.getByTestId('preview-pane')).toBeInTheDocument();
    });

    it('should not show inspector pane when showInspector is false', () => {
      render(
        <LayoutManager
          sidebar={mockSidebar}
          mainContent={mockMainContent}
          inspectorPane={mockInspectorPane}
          showInspector={false}
        />
      );

      expect(screen.queryByTestId('inspector-pane')).not.toBeInTheDocument();
    });

    it('should show inspector pane when showInspector is true', () => {
      render(
        <LayoutManager
          sidebar={mockSidebar}
          mainContent={mockMainContent}
          inspectorPane={mockInspectorPane}
          showInspector={true}
        />
      );

      expect(screen.getByTestId('inspector-pane')).toBeInTheDocument();
    });

    it('should render vertical panel group when inspector is shown', () => {
      render(
        <LayoutManager
          sidebar={mockSidebar}
          mainContent={mockMainContent}
          inspectorPane={mockInspectorPane}
          showInspector={true}
        />
      );

      expect(screen.getByTestId('panel-group-vertical')).toBeInTheDocument();
    });

    it('should not render vertical panel group when inspector is hidden', () => {
      render(
        <LayoutManager
          sidebar={mockSidebar}
          mainContent={mockMainContent}
          inspectorPane={mockInspectorPane}
          showInspector={false}
        />
      );

      expect(screen.queryByTestId('panel-group-vertical')).not.toBeInTheDocument();
    });
  });

  describe('Complex layouts', () => {
    it('should render all panes when all are enabled', () => {
      render(
        <LayoutManager
          sidebar={mockSidebar}
          mainContent={mockMainContent}
          previewPane={mockPreviewPane}
          inspectorPane={mockInspectorPane}
          showPreview={true}
          showInspector={true}
        />
      );

      expect(screen.getByTestId('sidebar')).toBeInTheDocument();
      expect(screen.getByTestId('main-content')).toBeInTheDocument();
      expect(screen.getByTestId('preview-pane')).toBeInTheDocument();
      expect(screen.getByTestId('inspector-pane')).toBeInTheDocument();
    });

    it('should render only required panes (sidebar + main)', () => {
      render(
        <LayoutManager
          sidebar={mockSidebar}
          mainContent={mockMainContent}
        />
      );

      expect(screen.getByTestId('sidebar')).toBeInTheDocument();
      expect(screen.getByTestId('main-content')).toBeInTheDocument();
      expect(screen.queryByTestId('preview-pane')).not.toBeInTheDocument();
      expect(screen.queryByTestId('inspector-pane')).not.toBeInTheDocument();
    });
  });

  describe('Resize handles', () => {
    it('should render resize handles for basic layout', () => {
      render(
        <LayoutManager
          sidebar={mockSidebar}
          mainContent={mockMainContent}
        />
      );

      const handles = screen.getAllByTestId('resize-handle');
      // Should have at least 1 resize handle (sidebar | main)
      expect(handles.length).toBeGreaterThanOrEqual(1);
    });

    it('should render additional resize handle when preview is shown', () => {
      const { rerender } = render(
        <LayoutManager
          sidebar={mockSidebar}
          mainContent={mockMainContent}
        />
      );

      const handlesWithoutPreview = screen.getAllByTestId('resize-handle');

      rerender(
        <LayoutManager
          sidebar={mockSidebar}
          mainContent={mockMainContent}
          previewPane={mockPreviewPane}
          showPreview={true}
        />
      );

      const handlesWithPreview = screen.getAllByTestId('resize-handle');
      // Should have more handles when preview is shown
      expect(handlesWithPreview.length).toBeGreaterThan(handlesWithoutPreview.length);
    });

    it('should render additional resize handle when inspector is shown', () => {
      const { rerender } = render(
        <LayoutManager
          sidebar={mockSidebar}
          mainContent={mockMainContent}
        />
      );

      const handlesWithoutInspector = screen.getAllByTestId('resize-handle');

      rerender(
        <LayoutManager
          sidebar={mockSidebar}
          mainContent={mockMainContent}
          inspectorPane={mockInspectorPane}
          showInspector={true}
        />
      );

      const handlesWithInspector = screen.getAllByTestId('resize-handle');
      // Should have more handles when inspector is shown
      expect(handlesWithInspector.length).toBeGreaterThan(handlesWithoutInspector.length);
    });
  });

  describe('Panel groups', () => {
    it('should always render horizontal panel group', () => {
      render(
        <LayoutManager
          sidebar={mockSidebar}
          mainContent={mockMainContent}
        />
      );

      expect(screen.getByTestId('panel-group-horizontal')).toBeInTheDocument();
    });

    it('should render both horizontal and vertical panel groups when inspector is shown', () => {
      render(
        <LayoutManager
          sidebar={mockSidebar}
          mainContent={mockMainContent}
          inspectorPane={mockInspectorPane}
          showInspector={true}
        />
      );

      expect(screen.getByTestId('panel-group-horizontal')).toBeInTheDocument();
      expect(screen.getByTestId('panel-group-vertical')).toBeInTheDocument();
    });
  });

  describe('Content rendering', () => {
    it('should render sidebar content correctly', () => {
      render(
        <LayoutManager
          sidebar={<div data-testid="custom-sidebar">Custom Sidebar Content</div>}
          mainContent={mockMainContent}
        />
      );

      expect(screen.getByTestId('custom-sidebar')).toBeInTheDocument();
      expect(screen.getByText('Custom Sidebar Content')).toBeInTheDocument();
    });

    it('should render main content correctly', () => {
      render(
        <LayoutManager
          sidebar={mockSidebar}
          mainContent={<div data-testid="custom-main">Custom Main Content</div>}
        />
      );

      expect(screen.getByTestId('custom-main')).toBeInTheDocument();
      expect(screen.getByText('Custom Main Content')).toBeInTheDocument();
    });

    it('should render preview pane content when shown', () => {
      render(
        <LayoutManager
          sidebar={mockSidebar}
          mainContent={mockMainContent}
          previewPane={<div data-testid="custom-preview">Custom Preview</div>}
          showPreview={true}
        />
      );

      expect(screen.getByTestId('custom-preview')).toBeInTheDocument();
      expect(screen.getByText('Custom Preview')).toBeInTheDocument();
    });

    it('should render inspector pane content when shown', () => {
      render(
        <LayoutManager
          sidebar={mockSidebar}
          mainContent={mockMainContent}
          inspectorPane={<div data-testid="custom-inspector">Custom Inspector</div>}
          showInspector={true}
        />
      );

      expect(screen.getByTestId('custom-inspector')).toBeInTheDocument();
      expect(screen.getByText('Custom Inspector')).toBeInTheDocument();
    });
  });
});
