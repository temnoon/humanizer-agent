import { useState, useEffect } from 'react';
import axios from 'axios';
import PropTypes from 'prop-types';
import MarkdownEditor from './editors/MarkdownEditor';

/**
 * BookBuilder Component
 *
 * Inspired by Joplin's notebook structure but focused on academic/technical writing.
 * Features:
 * - Hierarchical book/section organization
 * - Markdown editing for sections
 * - Link transformation results to sections
 * - Export to LaTeX/PDF (future)
 */
export default function BookBuilder({ onSelect, onBookSelect }) {
  const [books, setBooks] = useState([]);
  const [selectedBook, setSelectedBook] = useState(null);
  const [bookHierarchy, setBookHierarchy] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [viewMode, setViewMode] = useState('list'); // 'list', 'book', 'editor'
  const [currentUserId, setCurrentUserId] = useState(null);
  const [selectedSection, setSelectedSection] = useState(null);
  const [sectionContent, setSectionContent] = useState('');

  const API_BASE = 'http://localhost:8000';

  // Initialize user
  useEffect(() => {
    const storedUserId = localStorage.getItem('humanizer_user_id');
    if (storedUserId) {
      setCurrentUserId(storedUserId);
    }
  }, []);

  // Load books on mount (no user_id required)
  useEffect(() => {
    loadBooks();
  }, []);

  const loadBooks = async () => {
    setLoading(true);
    setError(null);
    try {
      // No user_id filter - show all books (single-user mode)
      const response = await axios.get(`${API_BASE}/api/books/`, {
        params: { limit: 100 }
      });
      setBooks(response.data);
    } catch (err) {
      setError('Failed to load books');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const loadBookHierarchy = async (bookId) => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get(`${API_BASE}/api/books/${bookId}`, {
        params: { include_sections: true }
      });
      setBookHierarchy(response.data);
      setSelectedBook(bookId);
      setViewMode('book');
    } catch (err) {
      setError('Failed to load book details');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const createBook = async () => {
    const title = prompt('Enter book title:');
    if (!title) return;

    try {
      const response = await axios.post(
        `${API_BASE}/api/books/`,
        {
          title,
          book_type: 'paper',
          configuration: {},
          custom_metadata: {}
        },
        { params: { user_id: currentUserId } }
      );
      setBooks([response.data, ...books]);
    } catch (err) {
      setError('Failed to create book');
      console.error(err);
    }
  };

  const handleBackToList = () => {
    setViewMode('list');
    setSelectedBook(null);
    setBookHierarchy(null);
    setSelectedSection(null);
    setSectionContent('');
  };

  const handleBackToBook = () => {
    setViewMode('book');
    setSelectedSection(null);
    setSectionContent('');
  };

  const handleSelectSection = async (section) => {
    setSelectedSection(section);
    setSectionContent(section.content || '');
    setViewMode('editor');
  };

  const handlePreviousSection = () => {
    if (!bookHierarchy?.sections || !selectedSection) return;
    const currentIndex = bookHierarchy.sections.findIndex(s => s.id === selectedSection.id);
    if (currentIndex > 0) {
      handleSelectSection(bookHierarchy.sections[currentIndex - 1]);
    }
  };

  const handleNextSection = () => {
    if (!bookHierarchy?.sections || !selectedSection) return;
    const currentIndex = bookHierarchy.sections.findIndex(s => s.id === selectedSection.id);
    if (currentIndex < bookHierarchy.sections.length - 1) {
      handleSelectSection(bookHierarchy.sections[currentIndex + 1]);
    }
  };

  const getCurrentSectionIndex = () => {
    if (!bookHierarchy?.sections || !selectedSection) return -1;
    return bookHierarchy.sections.findIndex(s => s.id === selectedSection.id);
  };

  const hasPreviousSection = () => getCurrentSectionIndex() > 0;
  const hasNextSection = () => {
    const index = getCurrentSectionIndex();
    return index >= 0 && index < (bookHierarchy?.sections?.length || 0) - 1;
  };

  // Keyboard shortcuts for section navigation (Ctrl+→/←)
  useEffect(() => {
    const handleKeyDown = (e) => {
      // Only handle shortcuts when in editor mode
      if (viewMode !== 'editor') return;

      // Ctrl/Cmd + Arrow Right: Next section
      if ((e.ctrlKey || e.metaKey) && e.key === 'ArrowRight' && hasNextSection()) {
        e.preventDefault();
        handleNextSection();
      }

      // Ctrl/Cmd + Arrow Left: Previous section
      if ((e.ctrlKey || e.metaKey) && e.key === 'ArrowLeft' && hasPreviousSection()) {
        e.preventDefault();
        handlePreviousSection();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [viewMode, selectedSection, bookHierarchy]);

  const handleSaveSection = async (content) => {
    if (!selectedSection || !selectedBook) return;

    try {
      await axios.patch(
        `${API_BASE}/api/books/${selectedBook}/sections/${selectedSection.id}`,
        { content }
      );
      setSectionContent(content);
      // Update local state
      if (bookHierarchy) {
        const updatedSections = bookHierarchy.sections.map(s =>
          s.id === selectedSection.id ? { ...s, content } : s
        );
        setBookHierarchy({ ...bookHierarchy, sections: updatedSections });
      }
    } catch (err) {
      setError('Failed to save section');
      console.error(err);
      throw err;
    }
  };

  const handleAddSection = async () => {
    const title = prompt('Enter section title:');
    if (!title || !selectedBook) return;

    try {
      const response = await axios.post(
        `${API_BASE}/api/books/${selectedBook}/sections`,
        {
          title,
          section_type: 'section',
          sequence_number: bookHierarchy.sections?.length || 0,
          content: '',
          custom_metadata: {}
        }
      );

      const newSection = response.data;
      setBookHierarchy({
        ...bookHierarchy,
        sections: [...(bookHierarchy.sections || []), newSection]
      });
    } catch (err) {
      setError('Failed to add section');
      console.error(err);
    }
  };

  const handleDeleteSection = async (sectionId, e) => {
    e.stopPropagation();

    if (!confirm('Are you sure you want to delete this section? This cannot be undone.')) return;

    try {
      await axios.delete(
        `${API_BASE}/api/books/${selectedBook}/sections/${sectionId}`
      );

      setBookHierarchy({
        ...bookHierarchy,
        sections: bookHierarchy.sections.filter(s => s.id !== sectionId)
      });
    } catch (err) {
      setError('Failed to delete section');
      console.error(err);
    }
  };

  const handleDeleteBook = async (bookId, e) => {
    e.stopPropagation();

    const book = books.find(b => b.id === bookId);
    const bookTitle = book ? book.title : 'this book';

    if (!confirm(`Are you sure you want to delete "${bookTitle}"?\n\nThis will permanently delete the book and all its sections. This cannot be undone.`)) return;

    try {
      await axios.delete(`${API_BASE}/api/books/${bookId}`);
      setBooks(books.filter(b => b.id !== bookId));

      // If we're viewing this book, go back to list
      if (selectedBook === bookId) {
        handleBackToList();
      }
    } catch (err) {
      setError('Failed to delete book');
      console.error(err);
    }
  };

  const getBookTypeIcon = (bookType) => {
    const icons = {
      paper: '📄',
      book: '📖',
      article: '📰',
      report: '📊',
      thesis: '🎓',
      documentation: '📚'
    };
    return icons[bookType] || '📄';
  };

  const formatDate = (isoString) => {
    if (!isoString) return 'N/A';
    const date = new Date(isoString);
    return date.toLocaleDateString();
  };

  return (
    <div className="flex flex-col h-full bg-gray-900 text-white">
      {/* Header */}
      <div className="bg-gray-800 border-b border-gray-700 p-4 sticky top-0 z-10">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-xl font-bold">📖 Books</h2>
          {viewMode === 'editor' ? (
            <button
              onClick={handleBackToBook}
              className="px-3 py-1 bg-gray-700 hover:bg-gray-600 rounded text-sm"
            >
              ← Back to Book
            </button>
          ) : viewMode === 'book' ? (
            <button
              onClick={handleBackToList}
              className="px-3 py-1 bg-gray-700 hover:bg-gray-600 rounded text-sm"
            >
              ← Back to List
            </button>
          ) : (
            <button
              onClick={createBook}
              className="px-3 py-1 bg-blue-600 hover:bg-blue-700 rounded text-sm font-bold"
            >
              + New Book
            </button>
          )}
        </div>

        {viewMode === 'list' && (
          <p className="text-sm text-gray-400">
            Create books and papers from your transformation results
          </p>
        )}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4">
        {error && (
          <div className="bg-red-900 border border-red-700 text-red-200 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}

        {loading ? (
          <div className="text-center text-gray-400 py-8">Loading...</div>
        ) : viewMode === 'editor' ? (
          /* EDITOR VIEW WITH SIDEBAR */
          selectedSection && (
            <div className="h-full flex gap-3">
              {/* Section Navigator Sidebar */}
              <div className="w-64 bg-gray-800 border border-gray-700 rounded p-3 overflow-y-auto flex-shrink-0">
                <div className="mb-4 pb-3 border-b border-gray-700">
                  <h3 className="font-bold text-sm text-gray-400 uppercase tracking-wider">Book Outline</h3>
                  {bookHierarchy && (
                    <p className="text-xs text-gray-500 mt-1">{bookHierarchy.title}</p>
                  )}
                </div>

                {/* Section List */}
                <div className="space-y-1">
                  {bookHierarchy?.sections?.map((section, idx) => (
                    <div
                      key={section.id}
                      onClick={() => handleSelectSection(section)}
                      className={`p-2 rounded cursor-pointer transition-colors ${
                        section.id === selectedSection.id
                          ? 'bg-blue-600 text-white'
                          : 'hover:bg-gray-700 text-gray-300'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium truncate">{section.title}</span>
                        <span className="text-xs text-gray-500 ml-2">#{idx + 1}</span>
                      </div>
                      {section.section_type && (
                        <span className="text-xs text-gray-500">{section.section_type}</span>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* Editor Area */}
              <div className="flex-1 flex flex-col min-w-0">
                <div className="bg-gray-800 border border-gray-700 p-3 rounded mb-3">
                  <h3 className="font-bold">{selectedSection.title}</h3>
                  {selectedSection.section_type && (
                    <p className="text-sm text-gray-400">{selectedSection.section_type}</p>
                  )}
                </div>
                <div className="flex-1 bg-gray-800 rounded overflow-hidden">
                  <MarkdownEditor
                    content={sectionContent}
                    onSave={handleSaveSection}
                    placeholder={`Start writing "${selectedSection.title}"...`}
                    onPreviousSection={handlePreviousSection}
                    onNextSection={handleNextSection}
                    hasPrevious={hasPreviousSection()}
                    hasNext={hasNextSection()}
                  />
                </div>
              </div>
            </div>
          )
        ) : viewMode === 'list' ? (
          /* LIST VIEW */
          <div className="space-y-3">
            {books.length === 0 ? (
              <div className="text-center text-gray-500 py-8">
                <p className="mb-3">No books yet.</p>
                <p className="text-sm">Create your first book to organize transformation results into structured documents.</p>
              </div>
            ) : (
              books.map((book) => (
                <div
                  key={book.id}
                  onClick={() => {
                    // If onBookSelect is provided, open in main pane
                    // Otherwise, open in sidebar (legacy behavior)
                    if (onBookSelect) {
                      onBookSelect(book);
                    } else {
                      loadBookHierarchy(book.id);
                    }
                  }}
                  className="bg-gray-800 border border-gray-700 p-4 rounded hover:bg-gray-750 cursor-pointer transition-colors group"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3 mb-2">
                      <span className="text-3xl">{getBookTypeIcon(book.book_type)}</span>
                      <div>
                        <h3 className="font-bold">{book.title}</h3>
                        {book.subtitle && (
                          <p className="text-sm text-gray-400">{book.subtitle}</p>
                        )}
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      <span className="px-2 py-1 rounded text-xs bg-gray-700 text-gray-300">
                        {book.book_type}
                      </span>
                      <button
                        onClick={(e) => handleDeleteBook(book.id, e)}
                        className="opacity-0 group-hover:opacity-100 px-2 py-1 bg-red-600 hover:bg-red-700 rounded text-xs transition-opacity"
                        title="Delete book"
                      >
                        🗑
                      </button>
                    </div>
                  </div>

                  <div className="flex gap-4 text-xs text-gray-500 mt-2">
                    <span>📅 {formatDate(book.created_at)}</span>
                    <span>🕒 Updated {formatDate(book.updated_at)}</span>
                  </div>
                </div>
              ))
            )}
          </div>
        ) : (
          /* BOOK VIEW */
          bookHierarchy && (
            <div className="space-y-4">
              {/* Book Header */}
              <div className="bg-gray-800 border border-gray-700 p-6 rounded">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <span className="text-4xl">{getBookTypeIcon(bookHierarchy.book_type)}</span>
                    <div>
                      <h2 className="text-2xl font-bold">{bookHierarchy.title}</h2>
                      {bookHierarchy.subtitle && (
                        <p className="text-gray-400">{bookHierarchy.subtitle}</p>
                      )}
                    </div>
                  </div>

                  <button
                    onClick={(e) => handleDeleteBook(bookHierarchy.id, e)}
                    className="px-3 py-1 bg-red-600 hover:bg-red-700 rounded text-sm"
                    title="Delete this book"
                  >
                    🗑 Delete Book
                  </button>
                </div>

                <div className="flex gap-4 text-sm text-gray-400">
                  <span>Type: {bookHierarchy.book_type}</span>
                  <span>Created: {formatDate(bookHierarchy.created_at)}</span>
                </div>
              </div>

              {/* Sections */}
              <div className="bg-gray-800 border border-gray-700 p-4 rounded">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-bold">Sections</h3>
                  <button
                    onClick={handleAddSection}
                    className="px-3 py-1 bg-green-600 hover:bg-green-700 rounded text-sm"
                  >
                    + Add Section
                  </button>
                </div>

                {bookHierarchy.sections && bookHierarchy.sections.length > 0 ? (
                  <div className="space-y-2">
                    {bookHierarchy.sections.map((section) => (
                      <div
                        key={section.id}
                        onClick={() => handleSelectSection(section)}
                        className="p-3 bg-gray-900 rounded border border-gray-700 hover:border-blue-600 cursor-pointer group"
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex-1">
                            <span className="font-medium">{section.title}</span>
                            {section.section_type && (
                              <span className="ml-2 text-xs text-gray-500">({section.section_type})</span>
                            )}
                          </div>
                          <div className="flex items-center gap-2">
                            <span className="text-xs text-gray-500">#{section.sequence_number}</span>
                            <button
                              onClick={(e) => handleDeleteSection(section.id, e)}
                              className="opacity-0 group-hover:opacity-100 px-2 py-1 bg-red-600 hover:bg-red-700 rounded text-xs"
                              title="Delete section"
                            >
                              🗑
                            </button>
                          </div>
                        </div>
                        {section.content && (
                          <p className="text-xs text-gray-500 mt-1 line-clamp-1">
                            {section.content.substring(0, 80)}...
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center text-gray-500 py-6">
                    <p className="mb-2">No sections yet.</p>
                    <p className="text-sm">Add sections to structure your book.</p>
                  </div>
                )}
              </div>

              {/* Configuration Preview */}
              {Object.keys(bookHierarchy.configuration).length > 0 && (
                <div className="bg-gray-800 border border-gray-700 p-4 rounded">
                  <h3 className="font-bold mb-3">Configuration</h3>
                  <pre className="text-xs text-gray-400 overflow-x-auto">
                    {JSON.stringify(bookHierarchy.configuration, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          )
        )}
      </div>
    </div>
  );
}

BookBuilder.propTypes = {
  onSelect: PropTypes.func,
  onBookSelect: PropTypes.func
};
