import { useState, useEffect } from 'react';
import axios from 'axios';
import PropTypes from 'prop-types';
import MarkdownEditor from './editors/MarkdownEditor';

/**
 * BookViewer Component
 *
 * Full-screen book editor for the main workspace pane.
 * Shows book sections with markdown editor/preview.
 */
export default function BookViewer({ bookId, onClose }) {
  const [bookHierarchy, setBookHierarchy] = useState(null);
  const [selectedSection, setSelectedSection] = useState(null);
  const [sectionContent, setSectionContent] = useState('');
  const [contentLinks, setContentLinks] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const API_BASE = 'http://localhost:8000';

  // Load book hierarchy on mount
  useEffect(() => {
    loadBookHierarchy();
  }, [bookId]);

  const loadBookHierarchy = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get(`${API_BASE}/api/books/${bookId}`, {
        params: { include_sections: true }
      });
      setBookHierarchy(response.data);

      // Auto-select first section if available
      if (response.data.sections && response.data.sections.length > 0) {
        handleSelectSection(response.data.sections[0]);
      }
    } catch (err) {
      setError('Failed to load book');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectSection = async (section) => {
    setSelectedSection(section);
    setSectionContent(section.content || '');

    // Fetch content links for this section
    try {
      const response = await axios.get(
        `${API_BASE}/api/books/${bookId}/sections/${section.id}/content`
      );
      setContentLinks(response.data || []);
    } catch (err) {
      console.error('Failed to load content links:', err);
      setContentLinks([]);
    }
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

  const handleSaveSection = async (content) => {
    if (!selectedSection || !bookId) return;

    try {
      await axios.patch(
        `${API_BASE}/api/books/${bookId}/sections/${selectedSection.id}`,
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

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center bg-gray-950 text-white">
        <div className="text-center">
          <div className="text-4xl mb-4">📖</div>
          <div className="text-xl text-gray-400">Loading book...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="h-full flex items-center justify-center bg-gray-950 text-white">
        <div className="text-center">
          <div className="text-4xl mb-4 text-red-400">⚠️</div>
          <div className="text-xl text-red-400 mb-4">{error}</div>
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded"
          >
            Close
          </button>
        </div>
      </div>
    );
  }

  if (!bookHierarchy) return null;

  return (
    <div className="h-full w-full flex bg-gray-950">
      {/* Section Navigator Sidebar */}
      <div className="w-64 bg-gray-900 border-r border-gray-800 overflow-y-auto flex-shrink-0">
        {/* Header */}
        <div className="sticky top-0 bg-gray-900 border-b border-gray-800 p-4 z-10">
          <div className="flex items-center justify-between mb-2">
            <h2 className="text-sm font-bold text-gray-400 uppercase tracking-wider">Book Outline</h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-white text-xl leading-none"
              title="Close book"
            >
              ×
            </button>
          </div>
          <h3 className="text-base font-semibold text-white truncate">{bookHierarchy.title}</h3>
          <p className="text-xs text-gray-500 mt-1">
            {bookHierarchy.sections?.length || 0} sections
          </p>
        </div>

        {/* Section List */}
        <div className="p-3 space-y-1">
          {bookHierarchy.sections?.length > 0 ? (
            bookHierarchy.sections.map((section, idx) => (
              <div
                key={section.id}
                onClick={() => handleSelectSection(section)}
                className={`p-3 rounded cursor-pointer transition-colors ${
                  section.id === selectedSection?.id
                    ? 'bg-blue-600 text-white shadow-lg'
                    : 'hover:bg-gray-800 text-gray-300'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium truncate">{section.title}</span>
                  <span className="text-xs text-gray-400 ml-2">#{idx + 1}</span>
                </div>
                {section.section_type && (
                  <span className="text-xs text-gray-400">{section.section_type}</span>
                )}
              </div>
            ))
          ) : (
            <div className="text-center text-gray-500 py-8 text-sm">
              No sections yet.
            </div>
          )}
        </div>
      </div>

      {/* Main Editor Area */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {selectedSection ? (
          <MarkdownEditor
            content={sectionContent}
            contentLinks={contentLinks}
            bookId={bookId}
            sectionId={selectedSection.id}
            onSave={handleSaveSection}
            onContentChange={(content) => setSectionContent(content)}
            placeholder={`Start writing "${selectedSection.title}"...`}
            onPreviousSection={handlePreviousSection}
            onNextSection={handleNextSection}
            hasPrevious={hasPreviousSection()}
            hasNext={hasNextSection()}
          />
        ) : (
          <div className="flex-1 flex items-center justify-center text-gray-500">
            <div className="text-center">
              <div className="text-6xl mb-4">📖</div>
              <div className="text-xl">Select a section to begin editing</div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

BookViewer.propTypes = {
  bookId: PropTypes.string.isRequired,
  onClose: PropTypes.func.isRequired
};
