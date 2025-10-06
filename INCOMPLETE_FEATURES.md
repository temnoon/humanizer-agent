# Incomplete Features - Image Browser & Photos.app Integration

## Session Ended: Oct 6, 2025

### ⏳ What's Incomplete

#### 1. **Photos.app Direct Album Viewing**
**Status**: Export-only workflow implemented
**What works**:
- Albums list loads from Photos.app
- Can export album (up to 50 photos) to /tmp
- Can export recent photos (last 30 days, up to 100)

**What's missing**:
- Cannot view Photos.app images directly in the browser without exporting
- No way to browse full-resolution Photos.app images inline
- Export → Upload workflow is clunky

**Why incomplete**:
- Photos.app doesn't expose direct file paths via AppleScript
- Would need to either:
  a) Auto-export on album select (expensive)
  b) Use Photos.app's internal database (complex)
  c) Keep current export workflow (current solution)

**Recommendation**: Keep export workflow for now, but add auto-cleanup of /tmp exports

---

#### 2. **Library Images Filtering in Photos.app View**
**Status**: Confusing UX
**Issue**: When in Photos.app view, the main grid still shows Library images until an album is selected. This creates confusion about what you're viewing.

**What should happen**:
- When clicking "Photos.app" button, hide Library grid
- Show album selection UI immediately
- Only show images when an album is exported and uploaded

**Quick fix needed**: Hide Library grid when `view === 'photos'`

---

#### 3. **Infinite Scroll State Management**
**Status**: Works but could be better
**What works**:
- Infinite scroll loads 100 images at a time
- IntersectionObserver triggers next page

**What's missing**:
- No way to jump to a specific page/date
- No visual feedback for total count
- Search/filter resets scroll position

**Recommendation**: Add pagination controls or date range selector

---

#### 4. **Image Metadata → Transformation Links**
**Status**: TODO placeholder
**File**: `backend/api/library_routes.py:684`

**Code**:
```python
# TODO: Find transformations that reference this media
# For now, transformations list is empty
# Will be implemented when transformation linkage is established
```

**What's needed**:
- Establish foreign key relationship between TransformationJob and Media
- Or use JSONB metadata search to find transformations that reference media
- Display transformation list in metadata panel

---

#### 5. **Photos.app Export UX**
**Status**: Functional but clunky
**Current flow**:
1. Image Browser → Photos.app → Select album
2. Click "Export Album"
3. Alert shows /tmp path
4. Close Image Browser
5. Go to Import tab → Images → Select Folder
6. Navigate to /tmp path
7. Upload

**Better flow**:
- After export, show inline upload dialog
- Or auto-navigate to Import tab with folder pre-selected
- Or show exported images inline immediately

---

### ✅ What's Complete

1. ✅ Infinite scroll for Library images (100 per page, loads all 8,640+)
2. ✅ Gizmo ID double-click editing (fixed text selection issue)
3. ✅ Image metadata endpoint with conversation/message links
4. ✅ Navigate from image → source conversation
5. ✅ Photos.app album export buttons
6. ✅ Search and filter by generator type
7. ✅ Detailed metadata panel with AI prompts, EXIF, dimensions

---

### 🔧 Quick Fixes for Next Session

**Priority 1: Hide Library grid in Photos.app view**
```jsx
// In ImageBrowser.jsx, around line 285
{!loading && !error && filteredImages.length > 0 && view === 'library' && (
  // ... grid code
)}
```

**Priority 2: Add auto-navigation after export**
```jsx
// After successful export:
window.openImportTab?.(); // Signal to parent to open Import tab
```

---

### ✅ Fixed After Initial Documentation

**Export Path Changed**: `/tmp` → `~/humanizer-agent/tmp`
- Easier to access from file picker
- All export functions updated in ImageBrowser and ImageUploader
- Directory created at `/Users/tem/humanizer-agent/tmp`

**Priority 3: Implement transformation linking**
```python
# In library_routes.py get_media_metadata
# Search for transformations by source_id or metadata
jobs_result = await db.execute(
    select(TransformationJob)
    .where(TransformationJob.config['source_media_id'].astext == media_id)
)
```

---

### 📝 Notes

- Backend running on port 8000
- Frontend running on port 5173
- All Sass removed (no deprecation warnings)
- Database has 8,640+ media records from ChatGPT archive
- Image Browser component: 622 lines
- Metadata endpoint working with conversation links

**Total session accomplishments**:
- Book Builder Phase 2 complete with LaTeX rendering
- Image Upload system with Apple Photos integration
- Image Browser with infinite scroll
- Multiple bug fixes (Gizmo editing, AppleScript syntax, HTML nesting)
- SCSS → CSS conversion
