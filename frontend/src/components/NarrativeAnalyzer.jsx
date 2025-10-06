import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkMath from 'remark-math';
import remarkGfm from 'remark-gfm';
import rehypeKatex from 'rehype-katex';
import 'katex/dist/katex.min.css';

const NarrativeAnalyzer = () => {
  const [text, setText] = useState('');
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [primaryMetric, setPrimaryMetric] = useState('middle_path');
  const [showOverlay, setShowOverlay] = useState(true);
  const [renderAsMarkdown, setRenderAsMarkdown] = useState(false);

  const sampleText = `For every tool we gain, we lose a skill. This is the fundamental truth of human progress. Technology shapes us completely. But we must adapt and find balance in all things. Sometimes the old ways have merit, sometimes innovation serves us better.`;

  const analyzeNarrative = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch('http://localhost:8000/api/madhyamaka/analyze-narrative', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text: text,
          primary_metric: primaryMetric
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setAnalysis(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const getMetricLabel = (metric) => {
    const labels = {
      middle_path: 'Middle Path',
      eternalism: 'Eternalism',
      nihilism: 'Nihilism'
    };
    return labels[metric] || metric;
  };

  const getScoreLabel = (score, metric) => {
    if (metric === 'middle_path') {
      if (score >= 0.7) return 'Very Close';
      if (score >= 0.5) return 'Close';
      if (score >= 0.3) return 'Approaching';
      return 'Far';
    } else {
      if (score >= 0.7) return 'High';
      if (score >= 0.5) return 'Medium';
      if (score >= 0.3) return 'Low';
      return 'Very Low';
    }
  };

  const SentenceWithOverlay = ({ sentence, index }) => {
    const [showTooltip, setShowTooltip] = useState(false);

    const opacity = showOverlay ? '40' : '00'; // 25% opacity when active, 0% when hidden
    const backgroundColor = `${sentence.primary_color}${opacity}`;

    return (
      <span
        key={index}
        style={{
          backgroundColor: backgroundColor,
          transition: 'background-color 0.3s ease',
          padding: '2px 0',
          position: 'relative',
          cursor: 'help'
        }}
        onMouseEnter={() => setShowTooltip(true)}
        onMouseLeave={() => setShowTooltip(false)}
      >
        {sentence.text}
        {showTooltip && (
          <div
            style={{
              position: 'absolute',
              bottom: '100%',
              left: '0',
              backgroundColor: '#1f2937',
              color: 'white',
              padding: '12px',
              borderRadius: '8px',
              fontSize: '0.875rem',
              minWidth: '250px',
              zIndex: 1000,
              boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
              marginBottom: '8px'
            }}
          >
            <div className="font-semibold mb-2 border-b border-gray-600 pb-2">
              Sentence {index + 1} Scores
            </div>
            <div className="space-y-1">
              <div className="flex justify-between items-center">
                <span>Middle Path:</span>
                <span className="font-mono">
                  {sentence.scores.middle_path.toFixed(3)}
                  <span className="ml-2 text-xs text-gray-400">
                    ({getScoreLabel(sentence.scores.middle_path, 'middle_path')})
                  </span>
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span>Eternalism:</span>
                <span className="font-mono">
                  {sentence.scores.eternalism.toFixed(3)}
                  <span className="ml-2 text-xs text-gray-400">
                    ({getScoreLabel(sentence.scores.eternalism, 'eternalism')})
                  </span>
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span>Nihilism:</span>
                <span className="font-mono">
                  {sentence.scores.nihilism.toFixed(3)}
                  <span className="ml-2 text-xs text-gray-400">
                    ({getScoreLabel(sentence.scores.nihilism, 'nihilism')})
                  </span>
                </span>
              </div>
              <div className="mt-2 pt-2 border-t border-gray-600 text-xs text-gray-300">
                Dominant: <span className="font-semibold">{getMetricLabel(sentence.dominant)}</span>
              </div>
            </div>
          </div>
        )}
      </span>
    );
  };

  return (
    <div className="max-w-7xl mx-auto p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Narrative Analyzer
        </h1>
        <p className="text-gray-600">
          Sentence-by-sentence Madhyamaka analysis with color-coded visualization
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Input Panel */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4 text-gray-800">Input Text</h2>

          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Enter your narrative here..."
            className="w-full h-64 p-4 border-2 border-gray-300 rounded-lg focus:border-blue-500 focus:ring focus:ring-blue-200 transition font-mono text-sm"
          />

          <div className="mt-4 space-y-4">
            {/* Metric Selector */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Primary Metric
              </label>
              <select
                value={primaryMetric}
                onChange={(e) => setPrimaryMetric(e.target.value)}
                className="w-full p-2 border-2 border-gray-300 rounded-lg focus:border-blue-500 focus:ring focus:ring-blue-200 text-gray-900"
              >
                <option value="middle_path">Middle Path Proximity</option>
                <option value="eternalism">Eternalism Detection</option>
                <option value="nihilism">Nihilism Detection</option>
              </select>
            </div>

            {/* Controls */}
            <div className="flex gap-2">
              <button
                onClick={analyzeNarrative}
                disabled={!text || loading}
                className="flex-1 bg-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition"
              >
                {loading ? 'Analyzing...' : 'Analyze'}
              </button>
              <button
                onClick={() => setText(sampleText)}
                className="px-4 py-3 border-2 border-gray-300 rounded-lg text-gray-700 font-semibold hover:bg-gray-50 transition"
              >
                Load Sample
              </button>
            </div>
          </div>

          {error && (
            <div className="mt-4 p-4 bg-red-50 border-2 border-red-200 rounded-lg text-red-700">
              <strong>Error:</strong> {error}
            </div>
          )}
        </div>

        {/* Analysis Panel */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-gray-800">Analysis</h2>
            {analysis && (
              <div className="flex gap-2">
                <button
                  onClick={() => setShowOverlay(!showOverlay)}
                  className={`px-4 py-2 rounded-lg font-semibold transition ${
                    showOverlay
                      ? 'bg-green-600 text-white hover:bg-green-700'
                      : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                  }`}
                >
                  {showOverlay ? 'Hide' : 'Show'} Overlay
                </button>
                <button
                  onClick={() => setRenderAsMarkdown(!renderAsMarkdown)}
                  className={`px-4 py-2 rounded-lg font-semibold transition ${
                    renderAsMarkdown
                      ? 'bg-purple-600 text-white hover:bg-purple-700'
                      : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                  }`}
                >
                  {renderAsMarkdown ? 'Plain' : 'Markdown'}
                </button>
              </div>
            )}
          </div>

          {!analysis ? (
            <div className="h-64 flex items-center justify-center text-gray-400">
              <div className="text-center">
                <svg className="mx-auto h-12 w-12 text-gray-300 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <p>Enter text and click Analyze to see results</p>
              </div>
            </div>
          ) : (
            <div>
              {/* Summary */}
              <div className="mb-4 p-4 bg-blue-50 rounded-lg border-2 border-blue-200">
                <div className="text-sm font-semibold text-blue-900 mb-2">
                  Overall Analysis
                </div>
                <div className="text-sm text-blue-800">
                  {analysis.summary}
                </div>
                <div className="mt-2 text-xs text-blue-700">
                  {analysis.sentence_count} sentences analyzed
                </div>
              </div>

              {/* Color Legend */}
              <div className="mb-4 p-4 bg-gray-50 rounded-lg border-2 border-gray-200">
                <div className="text-xs font-semibold text-gray-700 mb-2">
                  Color Scale ({getMetricLabel(primaryMetric)}):
                </div>
                <div className="flex gap-2 text-xs">
                  <div className="flex items-center gap-1">
                    <div className="w-4 h-4 rounded" style={{backgroundColor: '#22c55e'}}></div>
                    <span>Very Close</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <div className="w-4 h-4 rounded" style={{backgroundColor: '#4ade80'}}></div>
                    <span>Close</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <div className="w-4 h-4 rounded" style={{backgroundColor: '#fbbf24'}}></div>
                    <span>Approaching</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <div className="w-4 h-4 rounded" style={{backgroundColor: '#fb923c'}}></div>
                    <span>Far</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <div className="w-4 h-4 rounded" style={{backgroundColor: '#ef4444'}}></div>
                    <span>Very Far</span>
                  </div>
                </div>
              </div>

              {/* Rendered Text */}
              <div className="prose prose-sm max-w-none p-4 bg-gray-50 rounded-lg border-2 border-gray-200 min-h-[200px] leading-relaxed">
                {renderAsMarkdown ? (
                  <ReactMarkdown
                    remarkPlugins={[remarkMath, remarkGfm]}
                    rehypePlugins={[rehypeKatex]}
                  >
                    {analysis.sentences.map((s, i) =>
                      `<span style="background-color: ${s.primary_color}${showOverlay ? '40' : '00'}; padding: 2px 0;">${s.text}</span>`
                    ).join(' ')}
                  </ReactMarkdown>
                ) : (
                  <div className="text-gray-900">
                    {analysis.sentences.map((sentence, index) => (
                      <React.Fragment key={index}>
                        <SentenceWithOverlay sentence={sentence} index={index} />
                        {' '}
                      </React.Fragment>
                    ))}
                  </div>
                )}
              </div>

              {/* Hover hint */}
              <div className="mt-2 text-xs text-gray-500 italic">
                💡 Hover over sentences to see detailed scores
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default NarrativeAnalyzer;
