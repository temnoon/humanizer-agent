import { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import { Panel, PanelGroup, PanelResizeHandle } from 'react-resizable-panels';

/**
 * LayoutManager - Unified pane management for entire workspace
 *
 * Manages ALL resizable panes in the application:
 * - Sidebar (left)
 * - Main content area (center)
 * - Preview pane (right, optional)
 * - Inspector/details pane (bottom, optional)
 *
 * Features:
 * - All pane sizes persist to localStorage
 * - Consistent resize behavior throughout app
 * - No nested pane systems - ONE manager for all
 */
export default function LayoutManager({
  sidebar,
  mainContent,
  previewPane = null,
  inspectorPane = null,
  showPreview = false,
  showInspector = false
}) {
  // Load persisted layout from localStorage
  const [layout, setLayout] = useState(() => {
    try {
      const saved = localStorage.getItem('humanizer-layout');
      return saved ? JSON.parse(saved) : {
        sidebarSize: 25,      // 25% of viewport
        mainSize: 50,          // 50% of viewport
        previewSize: 25,       // 25% of viewport
        inspectorSize: 30      // 30% of main pane height
      };
    } catch {
      return {
        sidebarSize: 25,
        mainSize: 50,
        previewSize: 25,
        inspectorSize: 30
      };
    }
  });

  // Save layout changes to localStorage
  const handleLayoutChange = (sizes, paneType) => {
    const newLayout = { ...layout };

    if (paneType === 'horizontal') {
      // Main horizontal split (sidebar | main | preview)
      if (sizes.length === 2) {
        // Sidebar + Main (no preview)
        newLayout.sidebarSize = sizes[0];
        newLayout.mainSize = sizes[1];
      } else if (sizes.length === 3) {
        // Sidebar + Main + Preview
        newLayout.sidebarSize = sizes[0];
        newLayout.mainSize = sizes[1];
        newLayout.previewSize = sizes[2];
      }
    } else if (paneType === 'vertical') {
      // Vertical split (main content | inspector)
      if (sizes.length === 2) {
        newLayout.inspectorSize = sizes[1];
      }
    }

    setLayout(newLayout);

    // Persist to localStorage
    try {
      localStorage.setItem('humanizer-layout', JSON.stringify(newLayout));
    } catch (err) {
      console.error('Failed to save layout:', err);
    }
  };

  return (
    <div className="h-screen w-screen flex bg-gray-950">
      {/* Horizontal split: Sidebar | Main | Preview */}
      <PanelGroup
        direction="horizontal"
        onLayout={(sizes) => handleLayoutChange(sizes, 'horizontal')}
        className="flex-1"
      >
        {/* Left Sidebar */}
        <Panel
          defaultSize={layout.sidebarSize}
          minSize={15}
          maxSize={40}
          className="bg-gray-900 border-r border-gray-800"
        >
          {sidebar}
        </Panel>

        <PanelResizeHandle className="w-1 hover:w-2 bg-gray-800 hover:bg-realm-symbolic transition-all cursor-col-resize active:bg-realm-symbolic-light" />

        {/* Main Content Area */}
        <Panel
          defaultSize={layout.mainSize}
          minSize={30}
          className="bg-gray-950"
        >
          {/* Vertical split if inspector is shown */}
          {showInspector && inspectorPane ? (
            <PanelGroup
              direction="vertical"
              onLayout={(sizes) => handleLayoutChange(sizes, 'vertical')}
            >
              {/* Main content */}
              <Panel minSize={40}>
                {mainContent}
              </Panel>

              <PanelResizeHandle className="h-1 hover:h-2 bg-gray-800 hover:bg-realm-symbolic transition-all cursor-row-resize active:bg-realm-symbolic-light" />

              {/* Inspector pane (bottom) */}
              <Panel
                defaultSize={layout.inspectorSize}
                minSize={20}
                maxSize={50}
                className="bg-gray-900 border-t border-gray-800"
              >
                {inspectorPane}
              </Panel>
            </PanelGroup>
          ) : (
            mainContent
          )}
        </Panel>

        {/* Preview Pane (right, optional) */}
        {showPreview && previewPane && (
          <>
            <PanelResizeHandle className="w-1 hover:w-2 bg-gray-800 hover:bg-realm-symbolic transition-all cursor-col-resize active:bg-realm-symbolic-light" />

            <Panel
              defaultSize={layout.previewSize}
              minSize={20}
              maxSize={50}
              className="bg-gray-900 border-l border-gray-800"
            >
              {previewPane}
            </Panel>
          </>
        )}
      </PanelGroup>
    </div>
  );
}

LayoutManager.propTypes = {
  sidebar: PropTypes.node.isRequired,
  mainContent: PropTypes.node.isRequired,
  previewPane: PropTypes.node,
  inspectorPane: PropTypes.node,
  showPreview: PropTypes.bool,
  showInspector: PropTypes.bool
};
