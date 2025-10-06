import { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import PropTypes from 'prop-types';

/**
 * ImageUploader Component
 *
 * Supports:
 * - Folder upload (drag-drop or select)
 * - Multiple file selection
 * - Batch upload to /api/vision/upload-bulk
 * - Progress tracking
 * - Image preview
 */
export default function ImageUploader({ onUploadComplete }) {
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [uploadedCount, setUploadedCount] = useState(0);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  const [dragActive, setDragActive] = useState(false);

  // Apple Photos state
  const [applePhotosAvailable, setApplePhotosAvailable] = useState(false);
  const [albums, setAlbums] = useState([]);
  const [showAlbums, setShowAlbums] = useState(false);
  const [exporting, setExporting] = useState(false);

  const fileInputRef = useRef(null);
  const folderInputRef = useRef(null);

  const API_BASE = 'http://localhost:8000';

  // Check if Apple Photos is available
  useEffect(() => {
    checkApplePhotos();
  }, []);

  const checkApplePhotos = async () => {
    try {
      const response = await axios.get(`${API_BASE}/api/vision/apple-photos/available`);
      setApplePhotosAvailable(response.data.available);
    } catch (err) {
      console.error('Failed to check Apple Photos:', err);
    }
  };

  const loadAlbums = async () => {
    try {
      const response = await axios.get(`${API_BASE}/api/vision/apple-photos/albums`);
      setAlbums(response.data.albums || []);
      setShowAlbums(true);
    } catch (err) {
      setError('Failed to load Apple Photos albums: ' + err.message);
    }
  };

  const exportFromAlbum = async (albumName, limit = 50) => {
    const homeDir = window.location.hostname === 'localhost' ? '/Users/tem' : (process.env.HOME || '~');
    const exportPath = `${homeDir}/humanizer-agent/tmp/photos_export_${Date.now()}`;

    setExporting(true);
    setError(null);

    try {
      const response = await axios.post(`${API_BASE}/api/vision/apple-photos/export-album`, null, {
        params: {
          album_name: albumName,
          export_path: exportPath,
          limit: limit
        }
      });

      alert(`Exported ${response.data.files_exported} photos to ${exportPath}.\n\nNow use "Select Folder" to upload these images.`);
      setShowAlbums(false);

    } catch (err) {
      setError('Failed to export album: ' + (err.response?.data?.detail || err.message));
    } finally {
      setExporting(false);
    }
  };

  const exportRecent = async (days = 30, limit = 100) => {
    const homeDir = window.location.hostname === 'localhost' ? '/Users/tem' : (process.env.HOME || '~');
    const exportPath = `${homeDir}/humanizer-agent/tmp/photos_recent_${Date.now()}`;

    setExporting(true);
    setError(null);

    try {
      const response = await axios.post(`${API_BASE}/api/vision/apple-photos/export-recent`, null, {
        params: {
          export_path: exportPath,
          days: days,
          limit: limit
        }
      });

      alert(`Exported ${response.data.files_exported} recent photos to ${exportPath}.\n\nNow use "Select Folder" to upload these images.`);

    } catch (err) {
      setError('Failed to export recent photos: ' + (err.response?.data?.detail || err.message));
    } finally {
      setExporting(false);
    }
  };

  // Get user ID from localStorage
  const getUserId = () => {
    return localStorage.getItem('humanizer_user_id') || 'default_user';
  };

  // Handle file selection
  const handleFileSelect = (event) => {
    const files = Array.from(event.target.files || []);
    const imageFiles = files.filter(file =>
      file.type.startsWith('image/')
    );
    setSelectedFiles(prev => [...prev, ...imageFiles]);
    setError(null);
  };

  // Handle drag events
  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  // Handle drop
  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    const files = Array.from(e.dataTransfer.files || []);
    const imageFiles = files.filter(file =>
      file.type.startsWith('image/')
    );
    setSelectedFiles(prev => [...prev, ...imageFiles]);
    setError(null);
  };

  // Upload images in batches
  const handleUpload = async () => {
    if (selectedFiles.length === 0) {
      setError('Please select images to upload');
      return;
    }

    setUploading(true);
    setError(null);
    setResult(null);
    setProgress(0);
    setUploadedCount(0);

    const userId = getUserId();
    const batchSize = 10; // Upload 10 images at a time
    const totalBatches = Math.ceil(selectedFiles.length / batchSize);
    let successCount = 0;
    let failureCount = 0;

    try {
      for (let i = 0; i < totalBatches; i++) {
        const batch = selectedFiles.slice(i * batchSize, (i + 1) * batchSize);
        const formData = new FormData();

        formData.append('user_id', userId);

        batch.forEach((file) => {
          formData.append('files', file);
        });

        try {
          const response = await axios.post(
            `${API_BASE}/api/vision/upload-bulk`,
            formData,
            {
              headers: {
                'Content-Type': 'multipart/form-data'
              }
            }
          );

          successCount += response.data.uploaded?.length || 0;
          failureCount += response.data.failed?.length || 0;

        } catch (err) {
          console.error(`Batch ${i + 1} failed:`, err);
          failureCount += batch.length;
        }

        // Update progress
        const uploaded = (i + 1) * batchSize;
        setUploadedCount(Math.min(uploaded, selectedFiles.length));
        setProgress(Math.min(100, Math.round((uploaded / selectedFiles.length) * 100)));
      }

      setResult({
        total: selectedFiles.length,
        success: successCount,
        failed: failureCount
      });

      if (onUploadComplete) {
        onUploadComplete({ successCount, failureCount });
      }

      // Clear selected files on success
      if (failureCount === 0) {
        setSelectedFiles([]);
      }

    } catch (err) {
      setError(err.message || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  // Remove file from selection
  const removeFile = (index) => {
    setSelectedFiles(prev => prev.filter((_, i) => i !== index));
  };

  // Clear all files
  const clearFiles = () => {
    setSelectedFiles([]);
    setResult(null);
    setError(null);
  };

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-bold text-white">Upload Images</h2>

      {/* Drag and Drop Area */}
      <div
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
          dragActive
            ? 'border-blue-500 bg-blue-500/10'
            : 'border-gray-600 bg-gray-800/50'
        }`}
      >
        <svg
          className="w-16 h-16 mx-auto mb-4 text-gray-400"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
          />
        </svg>
        <p className="text-lg text-gray-300 mb-2">
          Drag and drop images or folders here
        </p>
        <p className="text-sm text-gray-500 mb-4">
          or click to browse
        </p>

        <div className="flex gap-3 justify-center">
          {/* Select Files Button */}
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={uploading}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white rounded-md font-medium transition-colors"
          >
            Select Files
          </button>

          {/* Select Folder Button */}
          <button
            onClick={() => folderInputRef.current?.click()}
            disabled={uploading}
            className="px-4 py-2 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-600 text-white rounded-md font-medium transition-colors"
          >
            Select Folder
          </button>
        </div>

        {/* Hidden file inputs */}
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept="image/*"
          onChange={handleFileSelect}
          className="hidden"
        />
        <input
          ref={folderInputRef}
          type="file"
          webkitdirectory=""
          directory=""
          onChange={handleFileSelect}
          className="hidden"
        />
      </div>

      {/* Selected Files Preview */}
      {selectedFiles.length > 0 && (
        <div className="bg-gray-800 rounded-lg p-4">
          <div className="flex justify-between items-center mb-3">
            <h3 className="font-medium text-white">
              Selected Images ({selectedFiles.length})
            </h3>
            <button
              onClick={clearFiles}
              disabled={uploading}
              className="text-sm text-red-400 hover:text-red-300 disabled:text-gray-500"
            >
              Clear All
            </button>
          </div>

          <div className="grid grid-cols-4 gap-2 max-h-64 overflow-y-auto">
            {selectedFiles.slice(0, 50).map((file, index) => (
              <div key={index} className="relative group">
                <div className="aspect-square bg-gray-700 rounded overflow-hidden">
                  <img
                    src={URL.createObjectURL(file)}
                    alt={file.name}
                    className="w-full h-full object-cover"
                  />
                </div>
                <button
                  onClick={() => removeFile(index)}
                  disabled={uploading}
                  className="absolute top-1 right-1 bg-red-600 hover:bg-red-700 text-white rounded-full p-1 opacity-0 group-hover:opacity-100 transition-opacity"
                  title="Remove"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            ))}
          </div>

          {selectedFiles.length > 50 && (
            <p className="text-xs text-gray-500 mt-2">
              + {selectedFiles.length - 50} more images
            </p>
          )}

          {/* Upload Button */}
          <button
            onClick={handleUpload}
            disabled={uploading}
            className={`w-full mt-4 py-3 px-4 rounded font-medium transition-colors ${
              uploading
                ? 'bg-gray-600 text-gray-400 cursor-not-allowed'
                : 'bg-green-600 hover:bg-green-700 text-white'
            }`}
          >
            {uploading ? `Uploading... ${uploadedCount}/${selectedFiles.length}` : 'Upload All Images'}
          </button>
        </div>
      )}

      {/* Progress Bar */}
      {uploading && (
        <div className="bg-gray-800 rounded-lg p-4">
          <div className="flex justify-between text-sm mb-2">
            <span className="text-gray-300">Uploading images...</span>
            <span className="text-gray-300">{progress}%</span>
          </div>
          <div className="w-full bg-gray-700 rounded-full h-2.5">
            <div
              className="bg-blue-500 h-2.5 rounded-full transition-all duration-300"
              style={{ width: `${progress}%` }}
            ></div>
          </div>
          <p className="text-xs text-gray-400 mt-2">
            {uploadedCount} of {selectedFiles.length} images uploaded
          </p>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="bg-red-900/50 border border-red-700 rounded-lg p-4">
          <div className="flex items-start">
            <svg className="w-5 h-5 text-red-500 mt-0.5 mr-2" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd"/>
            </svg>
            <div className="flex-1">
              <h4 className="text-red-300 font-medium">Upload Error</h4>
              <p className="text-red-200 text-sm mt-1">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Success Result */}
      {result && !uploading && (
        <div className={`border rounded-lg p-4 ${
          result.failed > 0
            ? 'bg-yellow-900/50 border-yellow-700'
            : 'bg-green-900/50 border-green-700'
        }`}>
          <h4 className={`font-medium mb-2 ${
            result.failed > 0 ? 'text-yellow-300' : 'text-green-300'
          }`}>
            Upload {result.failed > 0 ? 'Completed with Warnings' : 'Successful'}!
          </h4>
          <div className="grid grid-cols-3 gap-2 text-sm">
            <div className="text-gray-200">
              <span className="font-medium">Total:</span> {result.total}
            </div>
            <div className="text-green-200">
              <span className="font-medium">Success:</span> {result.success}
            </div>
            <div className={result.failed > 0 ? 'text-red-200' : 'text-gray-200'}>
              <span className="font-medium">Failed:</span> {result.failed}
            </div>
          </div>
        </div>
      )}

      {/* Apple Photos Integration (Mac only) */}
      {applePhotosAvailable && (
        <div className="bg-purple-900/20 border border-purple-700 rounded-lg p-4">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-medium text-purple-300 flex items-center gap-2">
              <span>📷</span> Apple Photos (Mac)
            </h3>
            {!showAlbums && (
              <button
                onClick={loadAlbums}
                disabled={exporting}
                className="px-3 py-1 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-600 text-white rounded text-sm font-medium transition-colors"
              >
                Browse Albums
              </button>
            )}
          </div>

          {!showAlbums ? (
            <div className="space-y-2">
              <p className="text-sm text-gray-300">
                Export photos directly from your Apple Photos library
              </p>
              <button
                onClick={() => exportRecent(30, 100)}
                disabled={exporting}
                className="w-full px-3 py-2 bg-purple-600/50 hover:bg-purple-600 disabled:bg-gray-700 text-white rounded text-sm transition-colors"
              >
                {exporting ? 'Exporting...' : 'Export Recent Photos (Last 30 Days, Max 100)'}
              </button>
            </div>
          ) : (
            <div className="space-y-2">
              <div className="flex justify-between items-center mb-2">
                <p className="text-sm text-gray-300">Select an album to export:</p>
                <button
                  onClick={() => setShowAlbums(false)}
                  className="text-xs text-gray-400 hover:text-gray-300"
                >
                  Cancel
                </button>
              </div>
              <div className="max-h-64 overflow-y-auto space-y-1">
                {albums.map((album, idx) => (
                  <button
                    key={idx}
                    onClick={() => exportFromAlbum(album.name, 50)}
                    disabled={exporting}
                    className="w-full text-left px-3 py-2 bg-gray-700 hover:bg-gray-600 disabled:bg-gray-800 rounded text-sm transition-colors flex justify-between items-center"
                  >
                    <span className="text-white">{album.name}</span>
                    <span className="text-xs text-gray-400">{album.count} photos</span>
                  </button>
                ))}
              </div>
              <p className="text-xs text-gray-400 mt-2">
                Note: Will export up to 50 photos per album to ~/humanizer-agent/tmp, then you can upload them using "Select Folder"
              </p>
            </div>
          )}
        </div>
      )}

      {/* Instructions */}
      <div className="bg-gray-700/50 rounded-lg p-4 text-sm text-gray-300">
        <h4 className="font-medium mb-2">Supported Features:</h4>
        <ul className="list-disc list-inside space-y-1">
          <li>Drag and drop multiple images or entire folders</li>
          <li>Automatic metadata extraction (EXIF, AI prompts, dimensions)</li>
          <li>AI prompt detection for DALL-E, Stable Diffusion, Midjourney</li>
          <li>Batch upload with progress tracking</li>
          <li>Apple Photos integration (Mac only)</li>
          <li>Supported formats: JPG, PNG, WebP, GIF</li>
        </ul>
      </div>
    </div>
  );
}

ImageUploader.propTypes = {
  onUploadComplete: PropTypes.func
};
