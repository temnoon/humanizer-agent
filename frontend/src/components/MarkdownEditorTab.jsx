import { useState } from 'react';
import PropTypes from 'prop-types';
import ReactMarkdown from 'react-markdown';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import 'katex/dist/katex.min.css';

/**
 * MarkdownEditorTab - Full-page markdown editor with flip view
 *
 * Features:
 * - Edit mode: Raw markdown text editor
 * - Preview mode: Rendered markdown with LaTeX, images, code blocks
 * - Flip toggle to switch between modes (like flipping a coin)
 * - Reusable for any markdown content (messages, books, documents)
 */
export default function MarkdownEditorTab({
  content = '',
  onChange,
  metadata = {},
  readOnly = false,
  title = 'Markdown Editor'
}) {
  const [mode, setMode] = useState('preview'); // 'edit' or 'preview'

  const toggleMode = () => {
    setMode(prev => prev === 'edit' ? 'preview' : 'edit');
  };

  // Preprocess content to fix LaTeX delimiters and convert image metadata to markdown
  const preprocessContent = (text) => {
    if (!text) return '';

    let processed = text;

    // STEP 1: Convert image metadata dictionaries to markdown images
    // Pattern matches: {'content_type': 'image_asset_pointer', 'asset_pointer': '(protocol)://(id)', ...}
    // Supports: file-service://, sediment://, and future protocols
    const imageMetadataPattern = /\{'content_type':\s*'image_asset_pointer',\s*'asset_pointer':\s*'(?:file-service|sediment|[a-z-]+):\/\/([^']+)'[^}]*\}/g;

    processed = processed.replace(imageMetadataPattern, (match, assetId) => {
      // Normalize ID format to match database storage (file-XXXXX with dashes)
      // Old sediment format uses: file_XXXXX (underscore prefix)
      // New file-service format uses: file-XXXXX (dash prefix)
      // Database always stores: file-XXXXX (dash prefix)
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

    // STEP 4: Handle cases where $ might already exist but needs spaces
    // This helps with inline math detection
    processed = processed.replace(/\$([^\$\n]+)\$/g, (match, math) => {
      return '$' + math + '$';
    });

    return processed;
  };

  return (
    <div className="h-full flex flex-col bg-gray-950">
      {/* Header with flip toggle */}
      <div className="flex-none bg-gray-900 border-b border-gray-800 px-6 py-3 flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <h2 className="text-lg font-medium text-gray-200">{title}</h2>
          {metadata.platform && (
            <span className="text-sm text-gray-500 bg-gray-800 px-2 py-1 rounded">
              {metadata.platform}
            </span>
          )}
          {metadata.date && (
            <span className="text-sm text-gray-500">
              {new Date(metadata.date).toLocaleDateString()}
            </span>
          )}
        </div>

        {/* Flip Toggle Button */}
        <button
          onClick={toggleMode}
          className="flex items-center space-x-2 px-4 py-2 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg transition-all transform hover:scale-105"
          title={`Switch to ${mode === 'edit' ? 'preview' : 'edit'} mode`}
        >
          <span className="text-xl">
            {mode === 'edit' ? '👁️' : '📝'}
          </span>
          <span className="text-sm font-medium">
            {mode === 'edit' ? 'Preview' : 'Edit'}
          </span>
          <svg
            className="w-4 h-4 transition-transform duration-300"
            style={{ transform: mode === 'preview' ? 'rotateY(180deg)' : 'rotateY(0deg)' }}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4" />
          </svg>
        </button>
      </div>

      {/* Content Area - Full page */}
      <div className="flex-1 overflow-hidden">
        {mode === 'edit' ? (
          /* Edit Mode: Raw Markdown */
          <div className="h-full p-6">
            <textarea
              value={content}
              onChange={(e) => onChange?.(e.target.value)}
              readOnly={readOnly}
              className="w-full h-full bg-gray-900 text-gray-200 font-mono text-sm p-4 rounded-lg border border-gray-800 focus:border-realm-symbolic focus:outline-none resize-none"
              placeholder="Write your markdown here..."
            />
          </div>
        ) : (
          /* Preview Mode: Rendered Markdown */
          <div className="h-full overflow-auto bg-gray-950">
            <div className="max-w-4xl mx-auto px-12 py-16">
              <article className="prose prose-invert prose-xl max-w-none
                [&_.katex]:text-gray-100
                [&_.katex-display]:my-6 [&_.katex-display]:py-4
                [&_p]:leading-relaxed [&_p]:mb-4
                [&_h1]:text-3xl [&_h1]:font-bold [&_h1]:mb-6 [&_h1]:mt-8
                [&_h2]:text-2xl [&_h2]:font-semibold [&_h2]:mb-4 [&_h2]:mt-6
                [&_h3]:text-xl [&_h3]:font-medium [&_h3]:mb-3 [&_h3]:mt-4
                [&_ul]:my-4 [&_ol]:my-4
                [&_li]:mb-2
                [&_code]:bg-gray-800 [&_code]:px-1.5 [&_code]:py-0.5 [&_code]:rounded [&_code]:text-sm
                [&_pre]:bg-gray-900 [&_pre]:rounded-lg [&_pre]:p-4 [&_pre]:my-4
              ">
                <ReactMarkdown
                  remarkPlugins={[remarkMath]}
                  rehypePlugins={[rehypeKatex]}
                  components={{
                    // Custom paragraph rendering (prevent nesting block elements)
                    p: ({ node, children, ...props }) => {
                      // Check if children contain block elements (pre, div, etc)
                      const hasBlockChild = node?.children?.some(
                        child => child.type === 'element' && ['pre', 'div'].includes(child.tagName)
                      );

                      // If contains block elements, render as div to avoid nesting issues
                      if (hasBlockChild) {
                        return <div {...props}>{children}</div>;
                      }

                      return <p className="leading-relaxed mb-4" {...props}>{children}</p>;
                    },
                    // Custom image rendering
                    img: ({ node, ...props }) => (
                      <img
                        {...props}
                        className="rounded-lg shadow-lg my-4 max-w-full h-auto"
                        loading="lazy"
                      />
                    ),
                    // Custom code block rendering
                    code: ({ node, inline, className, children, ...props }) => {
                      const match = /language-(\w+)/.exec(className || '');
                      return !inline ? (
                        <pre className="bg-gray-900 rounded-lg p-4 overflow-x-auto my-4">
                          <code className={className} {...props}>
                            {children}
                          </code>
                        </pre>
                      ) : (
                        <code className="bg-gray-800 px-1.5 py-0.5 rounded text-sm" {...props}>
                          {children}
                        </code>
                      );
                    },
                    // Custom link rendering
                    a: ({ node, ...props }) => (
                      <a
                        {...props}
                        className="text-realm-symbolic hover:text-realm-symbolic-light underline"
                        target="_blank"
                        rel="noopener noreferrer"
                      />
                    ),
                  }}
                >
                  {preprocessContent(content)}
                </ReactMarkdown>
              </article>
            </div>
          </div>
        )}
      </div>

      {/* Footer - Metadata/Info */}
      {metadata.wordCount && (
        <div className="flex-none bg-gray-900 border-t border-gray-800 px-6 py-2 text-sm text-gray-500 flex items-center justify-between">
          <span>{metadata.wordCount} words</span>
          {metadata.tokens && <span>{metadata.tokens} tokens</span>}
        </div>
      )}
    </div>
  );
}

MarkdownEditorTab.propTypes = {
  content: PropTypes.string,
  onChange: PropTypes.func,
  metadata: PropTypes.shape({
    platform: PropTypes.string,
    date: PropTypes.string,
    wordCount: PropTypes.number,
    tokens: PropTypes.number,
  }),
  readOnly: PropTypes.bool,
  title: PropTypes.string,
};
