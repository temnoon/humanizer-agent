import { createContext, useContext, useState, useCallback } from 'react';
import PropTypes from 'prop-types';

/**
 * WorkspaceContext - Unified state management for the Humanizer workspace
 *
 * Replaces scattered state in Workstation.jsx with a single source of truth.
 * Manages:
 * - Current view/tab state
 * - Navigation history
 * - Interest list (breadcrumb trail of user's browse path)
 * - User preferences (limits, settings)
 */

const WorkspaceContext = createContext(null);

export function WorkspaceProvider({ children }) {
  // Current view state
  const [currentTab, setCurrentTab] = useState(null); // {type, id, title, data}
  const [tabs, setTabs] = useState([]);
  const [activeTabIndex, setActiveTabIndex] = useState(-1);

  // Inspector pane state - for viewing message details, metadata, etc.
  const [inspectorContent, setInspectorContent] = useState(null); // {type, data}

  // Interest list - hierarchical browse path
  const [interestList, setInterestList] = useState([]);

  // User preferences (persisted to localStorage)
  const [preferences, setPreferences] = useState(() => {
    try {
      const saved = localStorage.getItem('humanizer-preferences');
      return saved ? JSON.parse(saved) : {
        defaultLimit: 100,
        itemsPerPage: 100,
        showSystemMessages: false,
        theme: 'dark'
      };
    } catch {
      return {
        defaultLimit: 100,
        itemsPerPage: 100,
        showSystemMessages: false,
        theme: 'dark'
      };
    }
  });

  // Persist preferences to localStorage
  const updatePreferences = useCallback((updates) => {
    setPreferences(prev => {
      const newPrefs = { ...prev, ...updates };
      try {
        localStorage.setItem('humanizer-preferences', JSON.stringify(newPrefs));
      } catch (err) {
        console.error('Failed to save preferences:', err);
      }
      return newPrefs;
    });
  }, []);

  // Tab management
  const addTab = useCallback((type, title, data) => {
    const newTab = {
      id: `${type}-${Date.now()}`,
      type, // 'conversation', 'book', 'image', 'message', 'transformation', etc.
      title,
      data,
      timestamp: Date.now()
    };

    setTabs(prev => {
      setActiveTabIndex(prev.length); // New tab becomes active
      setCurrentTab(newTab);
      return [...prev, newTab];
    });

    return newTab;
  }, []);

  const closeTab = useCallback((index) => {
    setTabs(prevTabs => {
      const newTabs = prevTabs.filter((_, i) => i !== index);

      setActiveTabIndex(prevIndex => {
        let newIndex = prevIndex;

        if (prevIndex >= index && prevIndex > 0) {
          newIndex = prevIndex - 1;
        } else if (prevIndex >= newTabs.length && newTabs.length > 0) {
          newIndex = newTabs.length - 1;
        } else if (newTabs.length === 0) {
          newIndex = -1;
        }

        setCurrentTab(newIndex >= 0 ? newTabs[newIndex] : null);
        return newIndex;
      });

      return newTabs;
    });
  }, []);

  const switchToTab = useCallback((index) => {
    setTabs(prevTabs => {
      if (index >= 0 && index < prevTabs.length) {
        setActiveTabIndex(index);
        setCurrentTab(prevTabs[index]);
      }
      return prevTabs;
    });
  }, []);

  const navigateToNextTab = useCallback(() => {
    setActiveTabIndex(prevIndex => {
      setTabs(prevTabs => {
        if (prevTabs.length > 0) {
          const newIndex = (prevIndex + 1) % prevTabs.length;
          setCurrentTab(prevTabs[newIndex]);
          setActiveTabIndex(newIndex);
        }
        return prevTabs;
      });
      return prevIndex;
    });
  }, []);

  const navigateToPrevTab = useCallback(() => {
    setActiveTabIndex(prevIndex => {
      setTabs(prevTabs => {
        if (prevTabs.length > 0) {
          const newIndex = (prevIndex - 1 + prevTabs.length) % prevTabs.length;
          setCurrentTab(prevTabs[newIndex]);
          setActiveTabIndex(newIndex);
        }
        return prevTabs;
      });
      return prevIndex;
    });
  }, []);

  // Interest list management - track user's browse path
  const addToInterest = useCallback((item) => {
    // item: {type, id, title, context, parent}
    setInterestList(prev => {
      // Check if item already exists
      const exists = prev.find(i => i.type === item.type && i.id === item.id);
      if (exists) return prev;

      return [...prev, {
        ...item,
        timestamp: Date.now()
      }];
    });
  }, []);

  const removeFromInterest = useCallback((itemId) => {
    setInterestList(prev => prev.filter(i => i.id !== itemId));
  }, []);

  const clearInterestList = useCallback(() => {
    setInterestList([]);
  }, []);

  // Navigate to an interest item
  const navigateToInterest = useCallback((item) => {
    addTab(item.type, item.title, item.data || { id: item.id });
  }, [addTab]);

  // Inspector pane management
  const showInspector = useCallback((type, data) => {
    setInspectorContent({ type, data });
  }, []);

  const closeInspector = useCallback(() => {
    setInspectorContent(null);
  }, []);

  // Context value
  const value = {
    // Current state
    currentTab,
    tabs,
    activeTabIndex,

    // Tab management
    addTab,
    closeTab,
    switchToTab,
    navigateToNextTab,
    navigateToPrevTab,

    // Inspector pane
    inspectorContent,
    showInspector,
    closeInspector,

    // Interest list
    interestList,
    addToInterest,
    removeFromInterest,
    clearInterestList,
    navigateToInterest,

    // Preferences
    preferences,
    updatePreferences
  };

  return (
    <WorkspaceContext.Provider value={value}>
      {children}
    </WorkspaceContext.Provider>
  );
}

WorkspaceProvider.propTypes = {
  children: PropTypes.node.isRequired
};

// Custom hook to use workspace context
export function useWorkspace() {
  const context = useContext(WorkspaceContext);
  if (!context) {
    throw new Error('useWorkspace must be used within a WorkspaceProvider');
  }
  return context;
}

export default WorkspaceContext;
