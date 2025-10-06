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
export default function BookBuilder({ onSelect }) {
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

  // Load books when user is set
  useEffect(() => {
    if (currentUserId) {
      loadBooks();
    }
  }, [currentUserId]);

  const loadBooks = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get(`${API_BASE}/api/books/`, {
        params: { user_id: currentUserId, limit: 100 }
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

    if (!confirm('Delete this section?')) return;

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
          /* EDITOR VIEW */
          selectedSection && (
            <div className="h-full flex flex-col">
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
                />
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
                  onClick={() => loadBookHierarchy(book.id)}
                  className="bg-gray-800 border border-gray-700 p-4 rounded hover:bg-gray-750 cursor-pointer"
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

                    <span className="px-2 py-1 rounded text-xs bg-gray-700 text-gray-300">
                      {book.book_type}
                    </span>
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
                <div className="flex items-center gap-3 mb-3">
                  <span className="text-4xl">{getBookTypeIcon(bookHierarchy.book_type)}</span>
                  <div>
                    <h2 className="text-2xl font-bold">{bookHierarchy.title}</h2>
                    {bookHierarchy.subtitle && (
                      <p className="text-gray-400">{bookHierarchy.subtitle}</p>
                    )}
                  </div>
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
  onSelect: PropTypes.func
};
