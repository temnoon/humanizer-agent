# Frontend Refinements - Phase 2 Implementation Guide

**Date:** October 6, 2025
**Status:** Core components created, integration pending

## Overview

Per CLAUDE.md Priority 2, the following frontend refinements have been implemented:

1. ✅ Unified SearchBar component
2. ✅ Keyboard shortcuts system
3. ✅ MessageViewer (non-modal replacement for MessageLightbox)
4. ✅ SettingsModal for configurable limits
5. ⏳ Integration into existing components (pending)

---

## 1. Unified SearchBar Component

**File:** `src/components/SearchBar.jsx`

### Features
- Consistent styling across all search implementations
- Keyboard shortcut display (Ctrl+K/Cmd+K)
- Clear button (Esc to clear)
- Loading state support
- Focus ring animations

### Usage Example

**Before (ImageBrowser.jsx):**
```jsx
const [searchQuery, setSearchQuery] = useState('');

<input
  type="text"
  value={searchQuery}
  onChange={(e) => setSearchQuery(e.target.value)}
  placeholder="Search images..."
  className="..."
/>
```

**After:**
```jsx
import SearchBar from './SearchBar';

<SearchBar
  value={searchQuery}
  onChange={setSearchQuery}
  onSearch={handleSearch}
  placeholder="Search images..."
  loading={loading}
/>
```

### Components to Update
- [ ] `ImageBrowser.jsx` (line 40)
- [ ] `LibraryBrowser.jsx` (line 22)
- [ ] `TransformationsLibrary.jsx` (line 19)
- [ ] `ConversationViewer.jsx` (if applicable)

---

## 2. Keyboard Shortcuts System

**File:** `src/hooks/useKeyboardShortcuts.js`

### Hooks Provided

#### `useKeyboardShortcuts(options)`
General-purpose keyboard shortcut hook

**Options:**
```javascript
{
  onSearch,        // Ctrl/Cmd+K
  onEscape,        // Escape key
  onArrowUp,       // Arrow up (when not in input)
  onArrowDown,     // Arrow down (when not in input)
  onArrowLeft,     // Arrow left (when not in input)
  onArrowRight,    // Arrow right (when not in input)
  onNew,           // Ctrl/Cmd+N
  onSave,          // Ctrl/Cmd+S
  enabled: true    // Enable/disable shortcuts
}
```

#### `useGlobalSearch(searchInputRef)`
Simpler hook for just Ctrl/Cmd+K to focus search

### Usage Example

```jsx
import { useKeyboardShortcuts } from '../hooks/useKeyboardShortcuts';

function MyComponent() {
  const [selectedIndex, setSelectedIndex] = useState(0);

  useKeyboardShortcuts({
    onArrowUp: () => setSelectedIndex(i => Math.max(0, i - 1)),
    onArrowDown: () => setSelectedIndex(i => i + 1),
    onEscape: () => setSelectedIndex(-1),
    enabled: true
  });

  return <div>...</div>;
}
```

### Components to Update
- [ ] `Workstation.jsx` - Add global shortcuts
- [ ] `ImageBrowser.jsx` - Navigate images with arrows
- [ ] `ConversationViewer.jsx` - Navigate messages
- [ ] `LibraryBrowser.jsx` - Navigate collections

---

## 3. MessageViewer (Non-Modal)

**File:** `src/components/MessageViewer.jsx`

### Features
- **No modal overlay** - fits into layout system
- Built-in keyboard navigation (already implemented)
- Same markdown/LaTeX rendering as MessageLightbox
- Metadata collapsible section
- Arrow key navigation between messages
- Esc to close

### Differences from MessageLightbox

| Feature | MessageLightbox | MessageViewer |
|---------|----------------|---------------|
| Display | Modal overlay | Inline pane |
| Background | Fixed black overlay | Transparent |
| Height | 80vh max | 100% of parent |
| Integration | onClick overlay | Layout pane |
| Keyboard | Arrow keys | Arrow keys (via hook) |

### Usage Example

**Before (ConversationViewer.jsx):**
```jsx
import MessageLightbox from './MessageLightbox';

{showLightbox && (
  <MessageLightbox
    message={selectedMessage}
    messages={messages}
    onClose={() => setShowLightbox(false)}
  />
)}
```

**After (in LayoutManager preview pane):**
```jsx
import MessageViewer from './MessageViewer';

<LayoutManager
  sidebar={<Sidebar />}
  mainContent={<ConversationList />}
  previewPane={
    <MessageViewer
      message={selectedMessage}
      messages={messages}
      onClose={() => setSelectedMessage(null)}
    />
  }
  showPreview={!!selectedMessage}
/>
```

### Components to Update
- [ ] `ConversationViewer.jsx` - Replace MessageLightbox with MessageViewer
- [ ] `Workstation.jsx` - Integrate into preview pane

---

## 4. SettingsModal

**File:** `src/components/SettingsModal.jsx`

### Features
- Configure items per page (50, 100, 200, 500, 1000, 2000)
- Configure default API limit
- Toggle system messages visibility
- Theme selection (dark/light/auto)
- Keyboard shortcuts reference
- Reset to defaults button

### Integration

**Add to Workstation.jsx:**

```jsx
import SettingsModal from './components/SettingsModal';
import { useState } from 'react';

function Workstation() {
  const [showSettings, setShowSettings] = useState(false);

  return (
    <>
      {/* Settings button in nav */}
      <button onClick={() => setShowSettings(true)}>
        ⚙️ Settings
      </button>

      {/* Settings modal */}
      <SettingsModal
        isOpen={showSettings}
        onClose={() => setShowSettings(false)}
      />
    </>
  );
}
```

**Use preferences from WorkspaceContext:**

```jsx
import { useWorkspace } from '../contexts/WorkspaceContext';

function ImageBrowser() {
  const { preferences } = useWorkspace();

  // Use preferences.itemsPerPage instead of hardcoded value
  const [itemsPerPage, setItemsPerPage] = useState(preferences.itemsPerPage);

  // Update when preferences change
  useEffect(() => {
    setItemsPerPage(preferences.itemsPerPage);
  }, [preferences.itemsPerPage]);
}
```

### Components to Update
- [ ] `Workstation.jsx` - Add settings button + modal
- [ ] `ImageBrowser.jsx` - Use `preferences.itemsPerPage`
- [ ] `LibraryBrowser.jsx` - Use `preferences.defaultLimit`
- [ ] `TransformationsLibrary.jsx` - Use `preferences.defaultLimit`
- [ ] `ConversationViewer.jsx` - Use `preferences.showSystemMessages`

---

## Integration Checklist

### Phase 1: SearchBar Integration
1. [ ] Import SearchBar into ImageBrowser.jsx
2. [ ] Replace search input in ImageBrowser
3. [ ] Import SearchBar into LibraryBrowser.jsx
4. [ ] Replace search input in LibraryBrowser
5. [ ] Import SearchBar into TransformationsLibrary.jsx
6. [ ] Replace search input in TransformationsLibrary
7. [ ] Test search functionality

### Phase 2: Keyboard Shortcuts
1. [ ] Add useKeyboardShortcuts to Workstation.jsx
2. [ ] Add arrow key navigation to ImageBrowser
3. [ ] Add arrow key navigation to conversation lists
4. [ ] Test all keyboard shortcuts

### Phase 3: MessageViewer Migration
1. [ ] Update ConversationViewer to use MessageViewer instead of MessageLightbox
2. [ ] Integrate MessageViewer into LayoutManager preview pane
3. [ ] Test message navigation
4. [ ] Remove/deprecate MessageLightbox (keep for reference)

### Phase 4: SettingsModal Integration
1. [ ] Add SettingsModal to Workstation
2. [ ] Add settings button to navigation
3. [ ] Update all components to use preferences from WorkspaceContext
4. [ ] Test settings persistence

---

## Testing Strategy

### Manual Testing
1. **Search functionality**
   - Type in search bar
   - Press Ctrl+K to focus
   - Press Esc to clear
   - Verify loading states

2. **Keyboard navigation**
   - Arrow keys navigate items
   - Esc closes modals
   - Ctrl+S saves (where applicable)
   - No conflicts with text inputs

3. **MessageViewer**
   - Opens in pane (not modal)
   - Arrow keys navigate messages
   - Metadata toggles correctly
   - Markdown/LaTeX renders

4. **Settings**
   - Change items per page
   - Verify updates reflected in browsers
   - Reset to defaults works
   - Settings persist after refresh

### Automated Tests
(To be added after integration)

```bash
# Add to test suite
npm test -- SearchBar.test.jsx
npm test -- MessageViewer.test.jsx
npm test -- SettingsModal.test.jsx
npm test -- useKeyboardShortcuts.test.js
```

---

## Known Issues & Future Work

### Current Limitations
- SettingsModal theme switcher (light/auto themes not yet implemented)
- Global search across all content types (planned for future)
- Keyboard shortcut customization (planned for future)

### Future Enhancements
- [ ] Add search history
- [ ] Add search suggestions/autocomplete
- [ ] Implement light theme
- [ ] Add more keyboard shortcuts (Ctrl+B for books, etc.)
- [ ] Add keyboard shortcut editor
- [ ] Add search filters in SearchBar (by date, type, etc.)

---

## File Manifest

### New Files Created
```
src/components/SearchBar.jsx           (119 lines)
src/components/MessageViewer.jsx       (399 lines)
src/components/SettingsModal.jsx       (264 lines)
src/hooks/useKeyboardShortcuts.js      (100 lines)
```

### Files to Modify (Integration)
```
src/components/ImageBrowser.jsx
src/components/LibraryBrowser.jsx
src/components/TransformationsLibrary.jsx
src/components/ConversationViewer.jsx
src/components/Workstation.jsx
```

### Files Deprecated (Keep for Reference)
```
src/components/MessageLightbox.jsx     (Keep until migration complete)
```

---

## Documentation Updates Needed

- [ ] Update CLAUDE.md with Phase 2 completion status
- [ ] Update README with new keyboard shortcuts
- [ ] Add examples to component documentation
- [ ] Update testing guide with new components

---

**Last Updated:** October 6, 2025
**Next Session:** Integrate components + test + update CLAUDE.md
