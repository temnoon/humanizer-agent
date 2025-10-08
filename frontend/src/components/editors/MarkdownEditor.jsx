import { useState, useEffect, useCallback } from 'react';
import PropTypes from 'prop-types';
import CodeMirror from '@uiw/react-codemirror';
import { markdown } from '@codemirror/lang-markdown';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import 'katex/dist/katex.min.css';
import { Panel, PanelGroup, PanelResizeHandle } from 'react-resizable-panels';
import ContentCard from '../ContentCard';

/**
 * Preprocess content for rendering: images and LaTeX
 * - Converts image_asset_pointer JSON to markdown images
 * - Converts LaTeX delimiters: \[...\] to $$...$$ and \(...\) to $...$
 */
const preprocessContent = (text) => {
  if (!text) return '';

  let processed = text;

  // STEP 1: Convert image metadata dictionaries to markdown images
  // Pattern matches: {'content_type': 'image_asset_pointer', 'asset_pointer': '(protocol)://(id)', ...}
  // Supports: file-service://, sediment://, and future protocols
  const imageMetadataPattern = /\{'content_type':\s*'image_asset_pointer',\s*'asset_pointer':\s*'(?:file-service|sediment|[a-z-]+):\/\/([^']+)'[^}]*\}/g;

  processed = processed.replace(imageMetadataPattern, (match, assetId) => {
    // Normalize ID format to match database storage (file-XXXXX with dashes)
    // Only replace the prefix: file_ → file- (not all underscores)
    const mediaId = assetId.replace(/^file_/, 'file-');
    const imageUrl = `http://localhost:8000/api/library/media/${mediaId}/file`;

    // Generate markdown image with alt text
    return `\n\n![Image](${imageUrl})\n\n`;
  });

  // STEP 2: Convert LaTeX display math \[ ... \] to $$...$$
  processed = processed.replace(/\\\[([\s\S]*?)\\\]/g, (match, math) => {
    return '\n$$' + math.trim() + '$$\n';
  });

  // STEP 3: Convert LaTeX inline math \( ... \) to $...$
  processed = processed.replace(/\\\(([\s\S]*?)\\\)/g, (match, math) => {
    return '$' + math.trim() + '$';
  });

  return processed;
};

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
 * - LaTeX math rendering (converts \[...\] and \(...\) to KaTeX format)
 */
export default function MarkdownEditor({
  content,
  contentLinks = [],
  bookId,
  sectionId,
  onSave,
  onContentChange,
  placeholder = 'Start writing your section...',
  readOnly = false,
  onPreviousSection,
  onNextSection,
  hasPrevious = false,
  hasNext = false
}) {
  const [editorContent, setEditorContent] = useState(content || '');
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const [saving, setSaving] = useState(false);

  // Load persisted split sizes from localStorage
  const [editorSize, setEditorSize] = useState(() => {
    try {
      const saved = localStorage.getItem('markdownEditor-splitSizes');
      return saved ? JSON.parse(saved).editor : 50;
    } catch {
      return 50;
    }
  });

  const [previewSize, setPreviewSize] = useState(() => {
    try {
      const saved = localStorage.getItem('markdownEditor-splitSizes');
      return saved ? JSON.parse(saved).preview : 50;
    } catch {
      return 50;
    }
  });

  // Save split sizes to localStorage when they change
  const handleLayoutChange = (sizes) => {
    if (sizes && sizes.length === 2) {
      setEditorSize(sizes[0]);
      setPreviewSize(sizes[1]);
      try {
        localStorage.setItem('markdownEditor-splitSizes', JSON.stringify({
          editor: sizes[0],
          preview: sizes[1]
        }));
      } catch (err) {
        console.error('Failed to save split sizes:', err);
      }
    }
  };

  // Concatenate content links + inline content for preview
  const getFullContent = useCallback(() => {
    const parts = [];

    // Add content from content links (in order)
    contentLinks.forEach((link, idx) => {
      const linkContent = link.chunk_content || link.job_content || '';
      if (linkContent) {
        // Add separator between cards
        if (idx > 0) parts.push('\n\n---\n\n');
        parts.push(linkContent);
      }
    });

    // Add inline section content if present
    if (editorContent) {
      if (parts.length > 0) parts.push('\n\n---\n\n');
      parts.push(editorContent);
    }

    // Preprocess content (images + LaTeX)
    return preprocessContent(parts.join(''));
  }, [contentLinks, editorContent]);

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
          {/* Section Navigation */}
          {(onPreviousSection || onNextSection) && (
            <div className="flex items-center gap-1 mr-2 border-r border-gray-700 pr-3">
              <button
                onClick={onPreviousSection}
                disabled={!hasPrevious}
                className={`px-2 py-1 rounded text-sm transition-colors ${
                  hasPrevious
                    ? 'bg-gray-700 hover:bg-gray-600 text-white'
                    : 'bg-gray-800 text-gray-600 cursor-not-allowed'
                }`}
                title="Previous section (Ctrl+←)"
              >
                ← Prev
              </button>
              <button
                onClick={onNextSection}
                disabled={!hasNext}
                className={`px-2 py-1 rounded text-sm transition-colors ${
                  hasNext
                    ? 'bg-gray-700 hover:bg-gray-600 text-white'
                    : 'bg-gray-800 text-gray-600 cursor-not-allowed'
                }`}
                title="Next section (Ctrl+→)"
              >
                Next →
              </button>
            </div>
          )}

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
        <PanelGroup direction="horizontal" onLayout={handleLayoutChange}>
          {/* Left Pane: Editor with Content Cards */}
          <Panel defaultSize={editorSize} minSize={25} maxSize={75}>
            <div className="h-full border-r border-gray-700 overflow-hidden flex flex-col">
          <div className="bg-gray-850 px-3 py-1 border-b border-gray-700">
            <span className="text-xs text-gray-400 font-medium">Editor</span>
            {contentLinks.length > 0 && (
              <span className="ml-2 text-xs text-blue-400">({contentLinks.length} linked content{contentLinks.length > 1 ? 's' : ''})</span>
            )}
          </div>
          <div className="flex-1 overflow-auto">
            {/* Content Cards Section */}
            {contentLinks.length > 0 && (
              <div className="bg-gray-900 p-3 border-b-2 border-blue-900">
                <div className="mb-2 text-xs font-semibold text-blue-300 uppercase tracking-wide">
                  Linked Content Cards
                </div>
                {contentLinks.map((link, idx) => (
                  <ContentCard
                    key={link.id}
                    contentLink={link}
                    sequenceNumber={idx}
                  />
                ))}
              </div>
            )}

            {/* Inline Content Editor */}
            <div className={contentLinks.length > 0 ? 'border-t border-gray-700' : ''}>
              {contentLinks.length > 0 && (
                <div className="bg-gray-850 px-3 py-1 border-b border-gray-700">
                  <span className="text-xs text-gray-400 font-medium">Additional Content (Inline)</span>
                </div>
              )}
              <CodeMirror
                value={editorContent}
                height={contentLinks.length > 0 ? '400px' : '100%'}
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
                  height: contentLinks.length > 0 ? '400px' : '100%'
                }}
              />
            </div>
          </div>
            </div>
          </Panel>

          <PanelResizeHandle className="w-2 bg-gray-700 hover:bg-realm-symbolic transition-colors cursor-col-resize active:bg-realm-symbolic-light" />

          {/* Right Pane: Preview */}
          <Panel defaultSize={previewSize} minSize={25} maxSize={75}>
            <div className="h-full overflow-hidden flex flex-col bg-gray-900">
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
              {getFullContent() ? (
                <ReactMarkdown
                  remarkPlugins={[remarkGfm, remarkMath]}
                  rehypePlugins={[rehypeKatex]}
                  components={{
                    p: ({children}) => <p className="mb-4 leading-relaxed">{children}</p>,
                    h1: ({children}) => <h1 className="text-3xl font-bold mb-4 mt-6 text-white">{children}</h1>,
                    h2: ({children}) => <h2 className="text-2xl font-bold mb-3 mt-5 text-white">{children}</h2>,
                    h3: ({children}) => <h3 className="text-xl font-semibold mb-2 mt-4 text-gray-100">{children}</h3>,
                    ul: ({children}) => <ul className="my-4 space-y-2 list-disc pl-6">{children}</ul>,
                    ol: ({children}) => <ol className="my-4 space-y-2 list-decimal pl-6">{children}</ol>,
                    code: ({node, inline, className, children, ...props}) => {
                      const match = /language-(\w+)/.exec(className || '');
                      return !inline && match ? (
                        <div className="my-4 overflow-x-auto max-w-full">
                          <SyntaxHighlighter
                            language={match[1]}
                            style={vscDarkPlus}
                            PreTag="div"
                            showLineNumbers={true}
                            wrapLines={false}
                            wrapLongLines={false}
                            customStyle={{
                              borderRadius: '0.375rem',
                              fontSize: '0.875rem',
                              margin: 0,
                              maxWidth: '100%',
                              overflowX: 'auto'
                            }}
                            codeTagProps={{
                              style: {
                                whiteSpace: 'pre',
                                overflowWrap: 'normal',
                                wordBreak: 'normal'
                              }
                            }}
                            {...props}
                          >
                            {String(children).replace(/\n$/, '')}
                          </SyntaxHighlighter>
                        </div>
                      ) : (
                        <code className="bg-gray-800 px-1.5 py-0.5 rounded text-sm text-blue-300" {...props}>
                          {children}
                        </code>
                      );
                    },
                    table: ({children}) => (
                      <div className="my-6 overflow-x-auto">
                        <table className="min-w-full divide-y divide-gray-700 border border-gray-700">
                          {children}
                        </table>
                      </div>
                    ),
                    thead: ({children}) => <thead className="bg-gray-800">{children}</thead>,
                    tbody: ({children}) => <tbody className="divide-y divide-gray-700 bg-gray-900">{children}</tbody>,
                    tr: ({children}) => <tr>{children}</tr>,
                    th: ({children}) => (
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-300 uppercase tracking-wider">
                        {children}
                      </th>
                    ),
                    td: ({children}) => (
                      <td className="px-4 py-3 text-sm text-gray-300">
                        {children}
                      </td>
                    ),
                    img: ({node, src, alt, ...props}) => (
                      <img
                        src={src}
                        alt={alt || 'Image'}
                        className="max-w-full h-auto rounded-lg border border-gray-700 my-4"
                        loading="lazy"
                        {...props}
                      />
                    )
                  }}
                >
                  {getFullContent()}
                </ReactMarkdown>
              ) : (
                <p className="text-gray-500 italic">{placeholder}</p>
              )}
            </div>
          </div>
            </div>
          </Panel>
        </PanelGroup>
      </div>
    </div>
  );
}

MarkdownEditor.propTypes = {
  content: PropTypes.string,
  contentLinks: PropTypes.arrayOf(PropTypes.object),
  bookId: PropTypes.string,
  sectionId: PropTypes.string,
  onSave: PropTypes.func,
  onContentChange: PropTypes.func,
  placeholder: PropTypes.string,
  readOnly: PropTypes.bool,
  onPreviousSection: PropTypes.func,
  onNextSection: PropTypes.func,
  hasPrevious: PropTypes.bool,
  hasNext: PropTypes.bool
};
