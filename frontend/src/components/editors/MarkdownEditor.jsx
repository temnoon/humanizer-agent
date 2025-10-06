import { useState, useEffect, useCallback } from 'react';
import PropTypes from 'prop-types';
import CodeMirror from '@uiw/react-codemirror';
import { markdown } from '@codemirror/lang-markdown';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

/**
 * MarkdownEditor Component
 *
 * Split-pane markdown editor with live preview.
 * Features:
 * - CodeMirror editor (left pane)
 * - Live markdown preview (right pane)
 * - Auto-save on blur or Ctrl+S
 * - Syntax highlighting
 * - Unsaved changes indicator
 */
export default function MarkdownEditor({
  content,
  onSave,
  onContentChange,
  placeholder = 'Start writing your section...',
  readOnly = false
}) {
  const [editorContent, setEditorContent] = useState(content || '');
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const [saving, setSaving] = useState(false);

  // Update editor when content prop changes
  useEffect(() => {
    setEditorContent(content || '');
    setHasUnsavedChanges(false);
  }, [content]);

  // Handle content changes
  const handleChange = useCallback((value) => {
    setEditorContent(value);
    setHasUnsavedChanges(true);

    if (onContentChange) {
      onContentChange(value);
    }
  }, [onContentChange]);

  // Save function
  const handleSave = useCallback(async () => {
    if (!hasUnsavedChanges || !onSave) return;

    setSaving(true);
    try {
      await onSave(editorContent);
      setHasUnsavedChanges(false);
    } catch (error) {
      console.error('Failed to save:', error);
    } finally {
      setSaving(false);
    }
  }, [editorContent, hasUnsavedChanges, onSave]);

  // Keyboard shortcut for save (Ctrl+S / Cmd+S)
  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault();
        handleSave();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleSave]);

  return (
    <div className="flex flex-col h-full">
      {/* Toolbar */}
      <div className="bg-gray-800 border-b border-gray-700 px-4 py-2 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="text-sm font-medium">Markdown Editor</span>
          {hasUnsavedChanges && (
            <span className="text-xs text-yellow-400 flex items-center gap-1">
              <span className="w-2 h-2 bg-yellow-400 rounded-full"></span>
              Unsaved changes
            </span>
          )}
        </div>

        <div className="flex items-center gap-2">
          {!readOnly && (
            <>
              <button
                onClick={handleSave}
                disabled={!hasUnsavedChanges || saving}
                className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                  hasUnsavedChanges && !saving
                    ? 'bg-blue-600 hover:bg-blue-700 text-white'
                    : 'bg-gray-700 text-gray-400 cursor-not-allowed'
                }`}
              >
                {saving ? 'Saving...' : 'Save'}
              </button>
              <span className="text-xs text-gray-500">Ctrl/Cmd+S</span>
            </>
          )}
        </div>
      </div>

      {/* Editor and Preview Panes */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Pane: Editor */}
        <div className="w-1/2 border-r border-gray-700 overflow-hidden flex flex-col">
          <div className="bg-gray-850 px-3 py-1 border-b border-gray-700">
            <span className="text-xs text-gray-400 font-medium">Editor</span>
          </div>
          <div className="flex-1 overflow-auto">
            <CodeMirror
              value={editorContent}
              height="100%"
              extensions={[markdown()]}
              onChange={handleChange}
              readOnly={readOnly}
              theme="dark"
              basicSetup={{
                lineNumbers: true,
                highlightActiveLineGutter: true,
                highlightActiveLine: true,
                foldGutter: true,
                dropCursor: true,
                indentOnInput: true,
                syntaxHighlighting: true,
                bracketMatching: true,
                closeBrackets: true,
                autocompletion: true,
                rectangularSelection: true,
                crosshairCursor: true,
                highlightSelectionMatches: true,
                closeBracketsKeymap: true,
                searchKeymap: true,
                foldKeymap: true,
                completionKeymap: true,
                lintKeymap: true,
              }}
              style={{
                fontSize: '14px',
                backgroundColor: '#1f2937', // gray-800
                height: '100%'
              }}
            />
          </div>
        </div>

        {/* Right Pane: Preview */}
        <div className="w-1/2 overflow-hidden flex flex-col bg-gray-900">
          <div className="bg-gray-850 px-3 py-1 border-b border-gray-700">
            <span className="text-xs text-gray-400 font-medium">Preview</span>
          </div>
          <div className="flex-1 overflow-auto p-6">
            <div className="prose prose-invert prose-lg max-w-none
                          prose-headings:font-bold prose-headings:tracking-tight
                          prose-h1:text-3xl prose-h1:mb-4 prose-h1:mt-6
                          prose-h2:text-2xl prose-h2:mb-3 prose-h2:mt-5
                          prose-h3:text-xl prose-h3:mb-2 prose-h3:mt-4
                          prose-p:mb-4 prose-p:leading-relaxed
                          prose-ul:my-4 prose-ul:space-y-2
                          prose-ol:my-4 prose-ol:space-y-2
                          prose-li:my-1
                          prose-blockquote:border-l-4 prose-blockquote:border-blue-500 prose-blockquote:pl-4 prose-blockquote:italic
                          prose-code:bg-gray-800 prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded prose-code:text-sm
                          prose-pre:bg-gray-800 prose-pre:border prose-pre:border-gray-700">
              {editorContent ? (
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  components={{
                    p: ({children}) => <p className="mb-4 leading-relaxed">{children}</p>,
                    h1: ({children}) => <h1 className="text-3xl font-bold mb-4 mt-6 text-white">{children}</h1>,
                    h2: ({children}) => <h2 className="text-2xl font-bold mb-3 mt-5 text-white">{children}</h2>,
                    h3: ({children}) => <h3 className="text-xl font-semibold mb-2 mt-4 text-gray-100">{children}</h3>,
                    ul: ({children}) => <ul className="my-4 space-y-2 list-disc pl-6">{children}</ul>,
                    ol: ({children}) => <ol className="my-4 space-y-2 list-decimal pl-6">{children}</ol>,
                    code: ({inline, children}) =>
                      inline
                        ? <code className="bg-gray-800 px-1.5 py-0.5 rounded text-sm text-blue-300">{children}</code>
                        : <code className="block bg-gray-800 p-3 rounded border border-gray-700 text-sm">{children}</code>
                  }}
                >
                  {editorContent}
                </ReactMarkdown>
              ) : (
                <p className="text-gray-500 italic">{placeholder}</p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

MarkdownEditor.propTypes = {
  content: PropTypes.string,
  onSave: PropTypes.func,
  onContentChange: PropTypes.func,
  placeholder: PropTypes.string,
  readOnly: PropTypes.bool
};
