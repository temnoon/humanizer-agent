import { useState, useEffect } from 'react';
import axios from 'axios';
import PropTypes from 'prop-types';
import { chunksToMarkdown } from '../../services/contentFormatter';

/**
 * BookSectionSelector Modal
 *
 * Allows user to select a book and section to add content to.
 * Features:
 * - List all user's books
 * - Show sections in selected book (tree view)
 * - Create new book on-the-fly
 * - Create new section on-the-fly
 * - Add content via POST /api/books/{id}/sections/{id}/content
 */
export default function BookSectionSelector({ message, chunks, onClose, onSuccess }) {
  const [books, setBooks] = useState([]);
  const [selectedBook, setSelectedBook] = useState(null);
  const [sections, setSections] = useState([]);
  const [selectedSection, setSelectedSection] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [currentUserId, setCurrentUserId] = useState(null);
  const [viewMode, setViewMode] = useState('selectBook'); // 'selectBook', 'selectSection', 'createBook', 'createSection'

  // Form states
  const [newBookTitle, setNewBookTitle] = useState('');
  const [newBookType, setNewBookType] = useState('paper');
  const [newSectionTitle, setNewSectionTitle] = useState('');
  const [newSectionType, setNewSectionType] = useState('section');

  const API_BASE = 'http://localhost:8000';

  useEffect(() => {
    const storedUserId = localStorage.getItem('humanizer_user_id');
    if (storedUserId) {
      setCurrentUserId(storedUserId);
      loadBooks(storedUserId);
    }
  }, []);

  const loadBooks = async (userId) => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get(`${API_BASE}/api/books/`, {
        params: { user_id: userId, limit: 100 }
      });
      setBooks(response.data);
    } catch (err) {
      setError('Failed to load books');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const loadSections = async (bookId) => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get(`${API_BASE}/api/books/${bookId}/sections`);
      setSections(response.data);
    } catch (err) {
      setError('Failed to load sections');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectBook = (book) => {
    setSelectedBook(book);
    loadSections(book.id);
    setViewMode('selectSection');
  };

  const handleCreateBook = async (e) => {
    e.preventDefault();
    if (!newBookTitle.trim()) return;

    setLoading(true);
    setError(null);
    try {
      const response = await axios.post(
        `${API_BASE}/api/books/`,
        {
          title: newBookTitle,
          book_type: newBookType,
          configuration: {},
          custom_metadata: {}
        },
        { params: { user_id: currentUserId } }
      );

      const newBook = response.data;
      setBooks([newBook, ...books]);
      setNewBookTitle('');
      setSelectedBook(newBook);
      setSections([]);
      setViewMode('selectSection');
    } catch (err) {
      setError('Failed to create book');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateSection = async (e) => {
    e.preventDefault();
    if (!newSectionTitle.trim() || !selectedBook) return;

    setLoading(true);
    setError(null);
    try {
      const response = await axios.post(
        `${API_BASE}/api/books/${selectedBook.id}/sections`,
        {
          title: newSectionTitle,
          section_type: newSectionType,
          sequence_number: sections.length,
          content: '',
          custom_metadata: {}
        }
      );

      const newSection = response.data;
      setSections([...sections, newSection]);
      setNewSectionTitle('');
      setSelectedSection(newSection);
      await handleAddContent(newSection);
    } catch (err) {
      setError('Failed to create section');
      console.error(err);
      setLoading(false);
    }
  };

  const handleAddContent = async (section) => {
    if (!section || !selectedBook) return;

    setLoading(true);
    setError(null);
    try {
      // Get existing content links to determine sequence number
      const linksResponse = await axios.get(
        `${API_BASE}/api/books/${selectedBook.id}/sections/${section.id}/content`
      );
      const existingLinks = linksResponse.data || [];
      const nextSequenceNumber = existingLinks.length;

      // Create content link
      await axios.post(
        `${API_BASE}/api/books/${selectedBook.id}/sections/${section.id}/content`,
        {
          chunk_id: chunks && chunks.length > 0 ? chunks[0].id : null,
          transformation_job_id: null,
          sequence_number: nextSequenceNumber,
          notes: `Added from message #${message.sequence_number}`
        }
      );

      // Append to section content (don't replace)
      if (chunks && chunks.length > 0) {
        const newContent = chunksToMarkdown(chunks);

        // Fetch current section to get existing content
        const sectionResponse = await axios.get(
          `${API_BASE}/api/books/${selectedBook.id}/sections/${section.id}`
        );
        const currentContent = sectionResponse.data.content || '';

        // Append with separator if there's existing content
        const separator = currentContent.trim() ? '\n\n---\n\n' : '';
        const updatedContent = currentContent + separator + newContent;

        await axios.patch(
          `${API_BASE}/api/books/${selectedBook.id}/sections/${section.id}`,
          { content: updatedContent }
        );
      }

      if (onSuccess) {
        onSuccess(selectedBook, section);
      }
      onClose();
    } catch (err) {
      setError('Failed to add content to section');
      console.error(err);
    } finally {
      setLoading(false);
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

  return (
    <div
      className="fixed inset-0 bg-black bg-opacity-80 z-50 flex items-center justify-center p-4"
      onClick={onClose}
    >
      <div
        className="bg-gray-900 rounded-lg shadow-2xl max-w-2xl w-full max-h-[80vh] flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="bg-gray-800 border-b border-gray-700 p-4 flex items-center justify-between rounded-t-lg">
          <h2 className="text-lg font-bold text-white">
            📖 Add to Book
            {selectedBook && ` - ${selectedBook.title}`}
          </h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-700 rounded transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
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
          ) : viewMode === 'selectBook' ? (
            /* SELECT BOOK */
            <div className="space-y-3">
              <div className="flex justify-between items-center mb-3">
                <h3 className="font-bold">Select a Book</h3>
                <button
                  onClick={() => setViewMode('createBook')}
                  className="px-3 py-1 bg-blue-600 hover:bg-blue-700 rounded text-sm"
                >
                  + New Book
                </button>
              </div>

              {books.length === 0 ? (
                <div className="text-center text-gray-500 py-6">
                  <p className="mb-2">No books yet.</p>
                  <button
                    onClick={() => setViewMode('createBook')}
                    className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded"
                  >
                    Create Your First Book
                  </button>
                </div>
              ) : (
                books.map((book) => (
                  <div
                    key={book.id}
                    onClick={() => handleSelectBook(book)}
                    className="bg-gray-800 border border-gray-700 p-3 rounded hover:bg-gray-750 cursor-pointer"
                  >
                    <div className="flex items-center gap-3">
                      <span className="text-2xl">{getBookTypeIcon(book.book_type)}</span>
                      <div>
                        <h4 className="font-medium">{book.title}</h4>
                        {book.subtitle && (
                          <p className="text-sm text-gray-400">{book.subtitle}</p>
                        )}
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          ) : viewMode === 'createBook' ? (
            /* CREATE BOOK */
            <form onSubmit={handleCreateBook} className="space-y-4">
              <div className="flex justify-between items-center mb-3">
                <h3 className="font-bold">Create New Book</h3>
                <button
                  type="button"
                  onClick={() => setViewMode('selectBook')}
                  className="px-3 py-1 bg-gray-700 hover:bg-gray-600 rounded text-sm"
                >
                  ← Back
                </button>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Title</label>
                <input
                  type="text"
                  value={newBookTitle}
                  onChange={(e) => setNewBookTitle(e.target.value)}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-white"
                  placeholder="Enter book title"
                  required
                  autoFocus
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Type</label>
                <select
                  value={newBookType}
                  onChange={(e) => setNewBookType(e.target.value)}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-white"
                >
                  <option value="paper">Paper</option>
                  <option value="book">Book</option>
                  <option value="article">Article</option>
                  <option value="report">Report</option>
                  <option value="thesis">Thesis</option>
                  <option value="documentation">Documentation</option>
                </select>
              </div>

              <button
                type="submit"
                className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded font-bold"
              >
                Create Book
              </button>
            </form>
          ) : viewMode === 'selectSection' ? (
            /* SELECT SECTION */
            <div className="space-y-3">
              <div className="flex justify-between items-center mb-3">
                <div>
                  <button
                    onClick={() => {
                      setViewMode('selectBook');
                      setSelectedBook(null);
                      setSections([]);
                    }}
                    className="text-blue-400 hover:text-blue-300 text-sm mb-1"
                  >
                    ← Change Book
                  </button>
                  <h3 className="font-bold">Select a Section</h3>
                </div>
                <button
                  onClick={() => setViewMode('createSection')}
                  className="px-3 py-1 bg-green-600 hover:bg-green-700 rounded text-sm"
                >
                  + New Section
                </button>
              </div>

              {sections.length === 0 ? (
                <div className="text-center text-gray-500 py-6">
                  <p className="mb-2">No sections in this book yet.</p>
                  <button
                    onClick={() => setViewMode('createSection')}
                    className="px-4 py-2 bg-green-600 hover:bg-green-700 rounded"
                  >
                    Create First Section
                  </button>
                </div>
              ) : (
                sections.map((section) => (
                  <div
                    key={section.id}
                    onClick={() => {
                      setSelectedSection(section);
                      handleAddContent(section);
                    }}
                    className="bg-gray-800 border border-gray-700 p-3 rounded hover:bg-gray-750 cursor-pointer"
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <h4 className="font-medium">{section.title}</h4>
                        {section.section_type && (
                          <span className="text-xs text-gray-500">({section.section_type})</span>
                        )}
                      </div>
                      <span className="text-xs text-gray-500">#{section.sequence_number}</span>
                    </div>
                  </div>
                ))
              )}
            </div>
          ) : viewMode === 'createSection' ? (
            /* CREATE SECTION */
            <form onSubmit={handleCreateSection} className="space-y-4">
              <div className="flex justify-between items-center mb-3">
                <h3 className="font-bold">Create New Section</h3>
                <button
                  type="button"
                  onClick={() => setViewMode('selectSection')}
                  className="px-3 py-1 bg-gray-700 hover:bg-gray-600 rounded text-sm"
                >
                  ← Back
                </button>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Title</label>
                <input
                  type="text"
                  value={newSectionTitle}
                  onChange={(e) => setNewSectionTitle(e.target.value)}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-white"
                  placeholder="Enter section title"
                  required
                  autoFocus
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Type</label>
                <select
                  value={newSectionType}
                  onChange={(e) => setNewSectionType(e.target.value)}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-white"
                >
                  <option value="chapter">Chapter</option>
                  <option value="section">Section</option>
                  <option value="subsection">Subsection</option>
                  <option value="appendix">Appendix</option>
                </select>
              </div>

              <button
                type="submit"
                className="w-full px-4 py-2 bg-green-600 hover:bg-green-700 rounded font-bold"
              >
                Create Section & Add Content
              </button>
            </form>
          ) : null}
        </div>
      </div>
    </div>
  );
}

BookSectionSelector.propTypes = {
  message: PropTypes.object.isRequired,
  chunks: PropTypes.array,
  onClose: PropTypes.func.isRequired,
  onSuccess: PropTypes.func
};
