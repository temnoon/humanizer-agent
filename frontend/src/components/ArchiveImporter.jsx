import { useState } from 'react';
import axios from 'axios';

/**
 * ArchiveImporter Component
 *
 * Allows users to import ChatGPT archives by specifying the folder path.
 * Displays import progress and handles embedding generation.
 */
export default function ArchiveImporter() {
  const [archivePath, setArchivePath] = useState('');
  const [generateEmbeddings, setGenerateEmbeddings] = useState(true);
  const [importing, setImporting] = useState(false);
  const [jobId, setJobId] = useState(null);
  const [progress, setProgress] = useState(null);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);

  // Poll for import status
  const pollStatus = async (id) => {
    const maxAttempts = 600; // 10 minutes max
    let attempts = 0;

    const poll = async () => {
      try {
        const response = await axios.get(`/api/import/jobs/${id}`);
        const status = response.data;

        setProgress(status);

        if (status.status === 'completed') {
          setResult(status.stats);
          setImporting(false);
          return;
        } else if (status.status === 'failed') {
          setError(status.error || 'Import failed');
          setImporting(false);
          return;
        }

        // Continue polling
        attempts++;
        if (attempts < maxAttempts) {
          setTimeout(poll, 1000); // Poll every second
        } else {
          setError('Import timeout - job may still be running');
          setImporting(false);
        }
      } catch (err) {
        setError(`Failed to check status: ${err.message}`);
        setImporting(false);
      }
    };

    poll();
  };

  const handleImport = async () => {
    if (!archivePath.trim()) {
      setError('Please enter an archive folder path');
      return;
    }

    setImporting(true);
    setError(null);
    setResult(null);
    setProgress(null);

    try {
      // Start import
      const response = await axios.post('/api/import/chatgpt', {
        archive_path: archivePath,
        generate_embeddings: generateEmbeddings
      });

      const { job_id } = response.data;
      setJobId(job_id);

      // Start polling for status
      pollStatus(job_id);

    } catch (err) {
      setError(err.response?.data?.detail || err.message);
      setImporting(false);
    }
  };

  const getProgressBar = () => {
    if (!progress) return null;

    const percent = progress.progress || 0;
    const color =
      progress.status === 'completed' ? 'bg-green-500' :
      progress.status === 'failed' ? 'bg-red-500' :
      'bg-blue-500';

    return (
      <div className="mt-4">
        <div className="flex justify-between text-sm mb-1">
          <span>Progress: {progress.current_item || 'Starting...'}</span>
          <span>{percent}%</span>
        </div>
        <div className="w-full bg-gray-700 rounded-full h-2.5">
          <div
            className={`${color} h-2.5 rounded-full transition-all duration-300`}
            style={{ width: `${percent}%` }}
          ></div>
        </div>
        {progress.total_items && (
          <div className="text-xs text-gray-400 mt-1">
            Processing conversation {progress.total_items - (progress.total_items - Math.floor((progress.total_items * percent) / 100))} of {progress.total_items}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="bg-gray-800 rounded-lg p-6 shadow-xl">
      <h2 className="text-2xl font-bold mb-4 text-white">Import ChatGPT Archive</h2>

      <div className="space-y-4">
        {/* Archive Path Input */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Archive Folder Path
          </label>
          <input
            type="text"
            value={archivePath}
            onChange={(e) => setArchivePath(e.target.value)}
            placeholder="/path/to/extracted/chatgpt/archive"
            className="w-full px-4 py-2 bg-gray-700 text-white rounded border border-gray-600 focus:border-blue-500 focus:outline-none"
            disabled={importing}
          />
          <p className="text-xs text-gray-400 mt-1">
            Path to the extracted ChatGPT archive folder (must contain conversations.json)
          </p>
        </div>

        {/* Generate Embeddings Checkbox */}
        <div className="flex items-center">
          <input
            type="checkbox"
            id="generate-embeddings"
            checked={generateEmbeddings}
            onChange={(e) => setGenerateEmbeddings(e.target.checked)}
            className="w-4 h-4 text-blue-600 bg-gray-700 border-gray-600 rounded focus:ring-blue-500"
            disabled={importing}
          />
          <label htmlFor="generate-embeddings" className="ml-2 text-sm text-gray-300">
            Generate embeddings (enables semantic search)
          </label>
        </div>

        {/* Import Button */}
        <button
          onClick={handleImport}
          disabled={importing}
          className={`w-full py-3 px-4 rounded font-medium transition-colors ${
            importing
              ? 'bg-gray-600 text-gray-400 cursor-not-allowed'
              : 'bg-blue-600 hover:bg-blue-700 text-white'
          }`}
        >
          {importing ? 'Importing...' : 'Start Import'}
        </button>

        {/* Progress Bar */}
        {getProgressBar()}

        {/* Error Message */}
        {error && (
          <div className="bg-red-900/50 border border-red-700 rounded p-4">
            <div className="flex items-start">
              <svg className="w-5 h-5 text-red-500 mt-0.5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd"/>
              </svg>
              <div className="flex-1">
                <h4 className="text-red-300 font-medium">Import Error</h4>
                <p className="text-red-200 text-sm mt-1">{error}</p>
              </div>
            </div>
          </div>
        )}

        {/* Success Result */}
        {result && (
          <div className="bg-green-900/50 border border-green-700 rounded p-4">
            <h4 className="text-green-300 font-medium mb-2">Import Complete!</h4>
            <div className="grid grid-cols-2 gap-2 text-sm">
              <div className="text-green-200">
                <span className="font-medium">Conversations:</span> {result.conversations_imported}
              </div>
              <div className="text-green-200">
                <span className="font-medium">Messages:</span> {result.messages_imported}
              </div>
              <div className="text-green-200">
                <span className="font-medium">Text Chunks:</span> {result.chunks_created}
              </div>
              <div className="text-green-200">
                <span className="font-medium">Media Files:</span> {result.media_imported}
              </div>
              <div className="text-green-200 col-span-2">
                <span className="font-medium">Embeddings Queued:</span> {result.embeddings_queued}
              </div>
            </div>
            {result.errors && result.errors.length > 0 && (
              <div className="mt-3 text-yellow-300 text-sm">
                <p className="font-medium">Warnings ({result.errors.length}):</p>
                <ul className="list-disc list-inside mt-1 text-xs">
                  {result.errors.slice(0, 5).map((err, idx) => (
                    <li key={idx}>{err}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {/* Instructions */}
        <div className="bg-gray-700/50 rounded p-4 text-sm text-gray-300">
          <h4 className="font-medium mb-2">Instructions:</h4>
          <ol className="list-decimal list-inside space-y-1">
            <li>Export your ChatGPT data from OpenAI (Settings → Data Controls → Export)</li>
            <li>Extract the downloaded ZIP file to a folder</li>
            <li>Enter the path to the extracted folder above</li>
            <li>Click "Start Import" and wait for processing to complete</li>
            <li>Embeddings will be generated in the background for semantic search</li>
          </ol>
        </div>

        {/* Supported Formats */}
        <div className="bg-blue-900/20 border border-blue-700 rounded p-4 text-sm">
          <h4 className="font-medium text-blue-300 mb-2">Supported Archive Formats:</h4>
          <ul className="list-disc list-inside text-gray-300 space-y-1">
            <li>ChatGPT exports (2024-2025 formats)</li>
            <li>Conversations with images, audio, and DALL-E generations</li>
            <li>Multiple media file formats (.dat, .webp, .wav, etc.)</li>
            <li>Custom GPT conversations</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
