# Book Builder Testing Guide
## Phase 1 & Phase 2 Manual Testing

**Date**: October 5, 2025
**Servers Running**:
- Backend: http://localhost:8000
- Frontend: http://localhost:5173
- API Docs: http://localhost:8000/docs

---

## ✅ Pre-Testing Verification (COMPLETE)

### Backend API Testing (PASSED)
All API endpoints tested via curl:

1. **Create Book** ✅
   ```bash
   curl -L -X POST "http://localhost:8000/api/books/?user_id=<USER_ID>" \
     -H "Content-Type: application/json" \
     -d '{"title":"Test Book","book_type":"paper","configuration":{},"custom_metadata":{}}'
   ```
   Result: Book created successfully

2. **List Books** ✅
   ```bash
   curl -L "http://localhost:8000/api/books/?user_id=<USER_ID>"
   ```
   Result: Returns array of books

3. **Create Section** ✅
   ```bash
   curl -L -X POST "http://localhost:8000/api/books/<BOOK_ID>/sections/" \
     -H "Content-Type: application/json" \
     -d '{"title":"Introduction","section_type":"chapter","sequence_number":1,"content":"# Test","custom_metadata":{}}'
   ```
   Result: Section created successfully

4. **Get Sections** ✅
   ```bash
   curl -L "http://localhost:8000/api/books/<BOOK_ID>/sections/"
   ```
   Result: Returns array of sections

### Database Schema (VERIFIED)
```sql
-- Books table has custom_metadata column ✅
\d books

-- Sections table has custom_metadata column ✅
\d book_sections

-- Content links table exists ✅
\d book_content_links
```

### Bug Fixes Applied
1. **Backend**: Renamed `metadata` → `custom_metadata` in:
   - `backend/models/book_models.py` (Book & BookSection models)
   - `backend/api/book_routes.py` (Pydantic schemas & endpoints)

2. **Frontend**: Renamed `metadata` → `custom_metadata` in:
   - `frontend/src/components/BookBuilder.jsx` (2 locations)
   - `frontend/src/components/modals/BookSectionSelector.jsx` (2 locations)

---

## 📋 Manual UI Testing Instructions

### Setup
1. Open browser to http://localhost:5173
2. Verify you're logged in (check localStorage for `humanizer_user_id`)
3. Navigate to **Books** tab in sidebar

---

## Phase 1 Testing - Foundation

### Test 1.1: View Books List
**Steps**:
1. Click "📖 Books" tab in sidebar
2. Observe the books list view

**Expected**:
- ✅ Shows "Create New Book" button
- ✅ Lists existing books (if any)
- ✅ Each book shows: title, subtitle, book_type, timestamps
- ✅ No errors in browser console

**Actual**: _[Fill in during testing]_

---

### Test 1.2: Create New Book
**Steps**:
1. Click "Create New Book" button
2. Enter title: "My Test Paper"
3. Submit

**Expected**:
- ✅ Prompt appears for book title
- ✅ Book created and appears in list
- ✅ Book shows correct title
- ✅ No errors in console
- ✅ Backend API receives `custom_metadata` field (check network tab)

**Actual**: _[Fill in during testing]_

---

### Test 1.3: View Book Outline
**Steps**:
1. Click on the newly created book
2. Observe the book detail view

**Expected**:
- ✅ Shows book title and metadata
- ✅ Shows "Add Section" button
- ✅ Shows section list (empty initially)
- ✅ Shows "Back to Books" button
- ✅ No errors in console

**Actual**: _[Fill in during testing]_

---

### Test 1.4: Create Section
**Steps**:
1. In book detail view, click "Add Section"
2. Enter title: "Introduction"
3. Submit

**Expected**:
- ✅ Prompt appears for section title
- ✅ Section created and appears in list
- ✅ Section shows correct title, sequence number
- ✅ Backend API receives `custom_metadata` field
- ✅ No errors in console

**Actual**: _[Fill in during testing]_

---

## Phase 2 Testing - Editor & Integration

### Test 2.1: 'Add to Book' Button in Message Lightbox
**Steps**:
1. Navigate to a conversation (Library or Conversations tab)
2. Click on a message to open the lightbox
3. Look for "📖 Add to Book" button

**Expected**:
- ✅ Button appears next to Pipeline button
- ✅ Button is green with book icon
- ✅ Button is clickable
- ✅ No errors in console

**Actual**: _[Fill in during testing]_

---

### Test 2.2: BookSectionSelector Modal - Select Existing
**Steps**:
1. Click "📖 Add to Book" button in message lightbox
2. Observe the BookSectionSelector modal
3. Select an existing book from dropdown
4. Select an existing section
5. Click "Add to Book"

**Expected**:
- ✅ Modal opens with two-step workflow
- ✅ Shows list of existing books in dropdown
- ✅ After selecting book, shows list of sections
- ✅ "Add to Book" button enabled
- ✅ Modal closes after submission
- ✅ Content added to section (check in Books tab)
- ✅ No errors in console

**Actual**: _[Fill in during testing]_

---

### Test 2.3: BookSectionSelector Modal - Create New Book
**Steps**:
1. Click "📖 Add to Book" button in message lightbox
2. In modal, click "Create New Book"
3. Enter title: "Test Book from Message"
4. Select book type: "paper"
5. Create book
6. Create a new section in the new book
7. Click "Add to Book"

**Expected**:
- ✅ "Create New Book" form appears
- ✅ Can enter title and select type
- ✅ Book created successfully
- ✅ UI switches to section selection
- ✅ Can create new section
- ✅ Content added successfully
- ✅ Backend receives `custom_metadata` field
- ✅ No errors in console

**Actual**: _[Fill in during testing]_

---

### Test 2.4: BookSectionSelector Modal - Create New Section
**Steps**:
1. Click "📖 Add to Book" button
2. Select existing book
3. Click "Create New Section"
4. Enter title: "Chapter 2"
5. Select section type: "chapter"
6. Create section
7. Click "Add to Book"

**Expected**:
- ✅ "Create New Section" form appears
- ✅ Can enter title and select type
- ✅ Section created successfully
- ✅ Section appears in dropdown
- ✅ Content added successfully
- ✅ Backend receives `custom_metadata` field
- ✅ No errors in console

**Actual**: _[Fill in during testing]_

---

### Test 2.5: Markdown Editor - Basic Editing
**Steps**:
1. Go to Books tab
2. Click on a book
3. Click on a section
4. Observe the markdown editor

**Expected**:
- ✅ Split-pane view appears (editor left, preview right)
- ✅ Editor shows existing content (or empty if new)
- ✅ Can type markdown in editor
- ✅ Preview updates in real-time
- ✅ Syntax highlighting works
- ✅ No errors in console

**Actual**: _[Fill in during testing]_

---

### Test 2.6: Markdown Editor - Save Content
**Steps**:
1. In markdown editor, edit content
2. Add some markdown (headings, lists, bold, italic)
3. Press Ctrl/Cmd+S (or click Save button)

**Expected**:
- ✅ Save button appears (or keyboard shortcut works)
- ✅ Content saved successfully
- ✅ Preview renders markdown correctly
- ✅ No errors in console
- ✅ Refresh page and content persists

**Actual**: _[Fill in during testing]_

---

### Test 2.7: Markdown Editor - Live Preview
**Steps**:
1. In editor, type various markdown:
   ```markdown
   # Heading 1
   ## Heading 2

   **Bold text** and *italic text*

   - List item 1
   - List item 2

   [Link](https://example.com)

   `inline code`

   ```code block```
   ```

**Expected**:
- ✅ Preview updates as you type (debounced)
- ✅ Headings rendered correctly
- ✅ Bold/italic styled correctly
- ✅ Lists rendered correctly
- ✅ Links clickable in preview
- ✅ Code blocks styled correctly
- ✅ No errors in console

**Actual**: _[Fill in during testing]_

---

### Test 2.8: Section Management - Add Section
**Steps**:
1. In book detail view
2. Click "Add Section"
3. Create new section: "Conclusion"
4. Verify section appears in list

**Expected**:
- ✅ Section added to list
- ✅ Correct sequence number assigned
- ✅ Can click on section to edit
- ✅ No errors in console

**Actual**: _[Fill in during testing]_

---

### Test 2.9: Section Management - Delete Section
**Steps**:
1. In book detail view with multiple sections
2. Find delete button for a section
3. Delete a section
4. Confirm deletion

**Expected**:
- ✅ Delete button appears for each section
- ✅ Confirmation dialog appears
- ✅ Section removed from list
- ✅ Section deleted from database
- ✅ No errors in console

**Actual**: _[Fill in during testing]_

---

### Test 2.10: Content Links - Verify Provenance
**Steps**:
1. Add message content to a book section
2. In database, check `book_content_links` table:
   ```sql
   SELECT * FROM book_content_links;
   ```

**Expected**:
- ✅ Content link created
- ✅ `chunk_id` populated (links to message chunk)
- ✅ `section_id` populated
- ✅ `sequence_number` set
- ✅ Provenance preserved

**Actual**: _[Fill in during testing]_

---

## Browser Console Checks

Throughout testing, monitor the browser console for:
- ❌ **Errors**: Should be ZERO errors
- ⚠️ **Warnings**: Note any warnings
- 🔍 **Network**: Check API requests/responses

### Common Issues to Watch For
1. **404 errors**: Missing API routes (should have trailing slash)
2. **400 errors**: Invalid request body (check `custom_metadata` field)
3. **500 errors**: Backend crashes (check backend logs)
4. **CORS errors**: Should not occur (same origin)
5. **React warnings**: PropTypes, key props, etc.

---

## Database Verification

After UI testing, verify database state:

```sql
-- Count books created
SELECT COUNT(*) FROM books;

-- View all books
SELECT id, title, book_type, custom_metadata FROM books;

-- Count sections
SELECT COUNT(*) FROM book_sections;

-- View sections with book titles
SELECT
  bs.id,
  bs.title as section_title,
  b.title as book_title,
  bs.section_type,
  bs.sequence_number
FROM book_sections bs
JOIN books b ON bs.book_id = b.id
ORDER BY b.title, bs.sequence_number;

-- Count content links
SELECT COUNT(*) FROM book_content_links;

-- View content links with details
SELECT
  bcl.id,
  bs.title as section_title,
  b.title as book_title,
  bcl.chunk_id,
  bcl.transformation_job_id,
  bcl.sequence_number
FROM book_content_links bcl
JOIN book_sections bs ON bcl.section_id = bs.id
JOIN books b ON bs.book_id = b.id;
```

---

## Test Results Summary

| Test | Status | Notes |
|------|--------|-------|
| API Endpoints | ✅ PASS | All curl tests passed |
| Database Schema | ✅ PASS | Tables created with custom_metadata |
| View Books List | ⏳ PENDING | Manual UI test |
| Create Book | ⏳ PENDING | Manual UI test |
| View Book Outline | ⏳ PENDING | Manual UI test |
| Create Section | ⏳ PENDING | Manual UI test |
| Add to Book Button | ⏳ PENDING | Manual UI test |
| BookSectionSelector - Existing | ⏳ PENDING | Manual UI test |
| BookSectionSelector - New Book | ⏳ PENDING | Manual UI test |
| BookSectionSelector - New Section | ⏳ PENDING | Manual UI test |
| Markdown Editor - Editing | ⏳ PENDING | Manual UI test |
| Markdown Editor - Save | ⏳ PENDING | Manual UI test |
| Markdown Editor - Preview | ⏳ PENDING | Manual UI test |
| Section Management - Add | ⏳ PENDING | Manual UI test |
| Section Management - Delete | ⏳ PENDING | Manual UI test |
| Content Links - Provenance | ⏳ PENDING | Manual UI test |

---

## Known Issues & Fixes Applied

### Issue 1: SQLAlchemy Reserved Name Conflict ✅ FIXED
**Problem**: `metadata` is reserved by SQLAlchemy's Declarative API
**Error**: `InvalidRequestError: Attribute name 'metadata' is reserved`
**Fix**: Renamed all `metadata` fields to `custom_metadata`
- Backend models: `Book.custom_metadata`, `BookSection.custom_metadata`
- Backend schemas: Updated Pydantic models
- Backend API: Updated all endpoint handlers
- Frontend: Updated all axios POST requests

**Files Modified**:
- `backend/models/book_models.py`
- `backend/api/book_routes.py`
- `frontend/src/components/BookBuilder.jsx`
- `frontend/src/components/modals/BookSectionSelector.jsx`

### Issue 2: FastAPI Trailing Slash Redirects
**Problem**: POST requests to `/api/books` return 307 redirect
**Workaround**: Use trailing slash `/api/books/` or follow redirects with `curl -L`
**Status**: Not a bug, expected FastAPI behavior

---

## Next Steps After Testing

1. **If all tests pass**: Move to Phase 3 (Configuration & Export)
   - TOML-assisted configuration UI
   - Export to Markdown
   - Export to LaTeX
   - PDF generation pipeline

2. **If tests fail**: Document failures, fix bugs, retest

3. **Documentation**: Update CLAUDE.md with test results and Phase 2 completion status

---

## Quick Reference

**Servers**:
```bash
# Start both servers
./start.sh

# Stop servers
Ctrl+C (in terminal where start.sh is running)
```

**Database**:
```bash
# Connect to database
psql -U humanizer -d humanizer

# Check tables
\dt

# View schema
\d books
\d book_sections
\d book_content_links
```

**Useful SQL**:
```sql
-- Clear all books (cascade deletes sections and links)
DELETE FROM books;

-- Reset for fresh testing
TRUNCATE books, book_sections, book_content_links RESTART IDENTITY CASCADE;
```

---

**Happy Testing!** 🚀
