import { useState, useEffect, useRef, useCallback } from 'react';
import axios from 'axios';
import PropTypes from 'prop-types';

/**
 * ImageBrowser Component
 *
 * Full-featured image browser for main document pane.
 * Features:
 * - Browse Photos.app albums and folders
 * - Browse filesystem folders with hierarchy
 * - Grid view of images with infinite scroll
 * - Detailed metadata panel with conversation/transformation links
 * - Navigate to source conversation
 */
export default function ImageBrowser({ onNavigateToConversation, onNavigateToTransformation }) {
  const [view, setView] = useState('library'); // 'library', 'photos', 'filesystem'
  const [images, setImages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedImage, setSelectedImage] = useState(null);
  const [imageMetadata, setImageMetadata] = useState(null);

  // Pagination state for infinite scroll
  const [hasMore, setHasMore] = useState(true);
  const [page, setPage] = useState(0);
  const observerTarget = useRef(null);

  // Photos.app state
  const [photosAvailable, setPhotosAvailable] = useState(false);
  const [albums, setAlbums] = useState([]);
  const [selectedAlbum, setSelectedAlbum] = useState(null);
  const [albumImages, setAlbumImages] = useState([]); // Images from selected album

  // Filesystem state
  const [currentPath, setCurrentPath] = useState(null);
  const [folders, setFolders] = useState([]);

  // Filters
  const [searchQuery, setSearchQuery] = useState('');
  const [filterGenerator, setFilterGenerator] = useState('all');

  const API_BASE = 'http://localhost:8000';

  // Check Photos.app availability
  useEffect(() => {
    checkPhotosAvailability();
  }, []);

  // Load images when view changes
  useEffect(() => {
    if (view === 'library') {
      setImages([]);
      setPage(0);
      setHasMore(true);
      loadLibraryImages(0);
    }
  }, [view]);

  // Infinite scroll observer
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && hasMore && !loading && view === 'library') {
          loadLibraryImages(page + 1);
        }
      },
      { threshold: 0.1 }
    );

    if (observerTarget.current) {
      observer.observe(observerTarget.current);
    }

    return () => observer.disconnect();
  }, [hasMore, loading, page, view]);

  const checkPhotosAvailability = async () => {
    try {
      const response = await axios.get(`${API_BASE}/api/vision/apple-photos/available`);
      setPhotosAvailable(response.data.available);
    } catch (err) {
      console.error('Failed to check Photos availability:', err);
    }
  };

  const loadLibraryImages = async (pageNum) => {
    if (loading) return;

    setLoading(true);
    setError(null);

    const ITEMS_PER_PAGE = 100;

    try {
      const response = await axios.get(`${API_BASE}/api/library/media`, {
        params: {
          limit: ITEMS_PER_PAGE,
          offset: pageNum * ITEMS_PER_PAGE
        }
      });

      const newImages = response.data.media || [];

      if (pageNum === 0) {
        setImages(newImages);
      } else {
        setImages(prev => [...prev, ...newImages]);
      }

      setPage(pageNum);
      setHasMore(newImages.length === ITEMS_PER_PAGE);
    } catch (err) {
      setError('Failed to load images: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  const loadPhotosAlbums = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await axios.get(`${API_BASE}/api/vision/apple-photos/albums`);
      setAlbums(response.data.albums || []);
    } catch (err) {
      setError('Failed to load albums: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  const handleAlbumSelect = async (album) => {
    setSelectedAlbum(album);
  };

  const handleExportAlbum = async (albumName, limit = 50) => {
    const homeDir = window.location.hostname === 'localhost' ? '/Users/tem' : (process.env.HOME || '~');
    const exportPath = `${homeDir}/humanizer-agent/tmp/photos_export_${Date.now()}`;

    setLoading(true);
    setError(null);

    try {
      const response = await axios.post(`${API_BASE}/api/vision/apple-photos/export-album`, null, {
        params: {
          album_name: albumName,
          export_path: exportPath,
          limit: limit
        }
      });

      alert(`✓ Exported ${response.data.files_exported} photos to:\n${exportPath}\n\nNow go to Import tab → Images → Select Folder and choose this folder to upload.`);

    } catch (err) {
      setError('Failed to export album: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  const handleExportRecent = async (days = 30, limit = 100) => {
    const homeDir = window.location.hostname === 'localhost' ? '/Users/tem' : (process.env.HOME || '~');
    const exportPath = `${homeDir}/humanizer-agent/tmp/photos_recent_${Date.now()}`;

    setLoading(true);
    setError(null);

    try {
      const response = await axios.post(`${API_BASE}/api/vision/apple-photos/export-recent`, null, {
        params: {
          export_path: exportPath,
          days: days,
          limit: limit
        }
      });

      alert(`✓ Exported ${response.data.files_exported} recent photos to:\n${exportPath}\n\nNow go to Import tab → Images → Select Folder and choose this folder to upload.`);

    } catch (err) {
      setError('Failed to export recent photos: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  const selectImage = async (image) => {
    setSelectedImage(image);

    // Load detailed metadata
    try {
      const response = await axios.get(`${API_BASE}/api/library/media/${image.id}/metadata`);
      setImageMetadata(response.data);
    } catch (err) {
      console.error('Failed to load image metadata:', err);
      setImageMetadata(null);
    }
  };

  const getImageUrl = (image) => {
    if (image.storage_path) {
      return `${API_BASE}/api/library/media/${image.id}/file`;
    }
    return null;
  };

  const filterImages = () => {
    let filtered = images;

    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(img =>
        img.filename?.toLowerCase().includes(query) ||
        img.custom_metadata?.ai_prompt?.toLowerCase().includes(query)
      );
    }

    if (filterGenerator !== 'all') {
      filtered = filtered.filter(img => {
        const generator = img.custom_metadata?.generator?.toLowerCase() || 'unknown';
        return generator === filterGenerator;
      });
    }

    return filtered;
  };

  const filteredImages = filterImages();

  return (
    <div className="h-full flex flex-col bg-gray-950">
      {/* Header */}
      <div className="flex-none border-b border-gray-800 bg-gray-900">
        <div className="p-4">
          <h1 className="text-2xl font-bold text-white mb-4">Image Browser</h1>

          {/* View Selector */}
          <div className="flex gap-2 mb-4">
            <button
              onClick={() => setView('library')}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                view === 'library'
                  ? 'bg-realm-symbolic text-white'
                  : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
              }`}
            >
              📚 Library ({images.length})
            </button>

            {photosAvailable && (
              <button
                onClick={() => {
                  setView('photos');
                  loadPhotosAlbums();
                }}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  view === 'photos'
                    ? 'bg-realm-symbolic text-white'
                    : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
                }`}
              >
                📷 Photos.app
              </button>
            )}
          </div>

          {/* Search and Filters */}
          {view === 'library' && (
            <div className="flex gap-3">
              <div className="relative flex-1">
                <input
                  type="text"
                  placeholder="Search filename or prompt..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full px-3 py-2 pl-9 bg-gray-800 border border-gray-700 rounded-md text-sm text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-realm-symbolic"
                />
                <svg className="w-4 h-4 absolute left-3 top-2.5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>

              <select
                value={filterGenerator}
                onChange={(e) => setFilterGenerator(e.target.value)}
                className="px-3 py-2 bg-gray-800 border border-gray-700 rounded-md text-sm text-white focus:outline-none focus:ring-2 focus:ring-realm-symbolic"
              >
                <option value="all">All Generators</option>
                <option value="dall-e">DALL-E</option>
                <option value="stable-diffusion">Stable Diffusion</option>
                <option value="midjourney">Midjourney</option>
                <option value="user-upload">User Upload</option>
                <option value="unknown">Unknown</option>
              </select>
            </div>
          )}
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Panel - Albums/Folders (if Photos view) */}
        {view === 'photos' && (
          <div className="w-64 border-r border-gray-800 overflow-y-auto bg-gray-900">
            <div className="p-3">
              <h3 className="text-sm font-semibold text-gray-400 mb-2">Albums</h3>
              {loading && <div className="text-gray-500 text-sm">Loading albums...</div>}
              {albums.map((album, idx) => (
                <button
                  key={idx}
                  onClick={() => handleAlbumSelect(album)}
                  className={`w-full text-left px-3 py-2 rounded-lg mb-1 transition-colors ${
                    selectedAlbum?.name === album.name
                      ? 'bg-realm-symbolic text-white'
                      : 'text-gray-300 hover:bg-gray-800'
                  }`}
                >
                  <div className="text-sm font-medium">{album.name}</div>
                  <div className="text-xs text-gray-500">{album.count} photos</div>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Center Panel - Image Grid */}
        <div className={`flex-1 overflow-y-auto p-6 ${selectedImage ? 'w-2/3' : 'w-full'}`}>
          {loading && (
            <div className="flex items-center justify-center h-full">
              <div className="text-gray-400">Loading images...</div>
            </div>
          )}

          {error && (
            <div className="bg-red-900/50 border border-red-700 rounded-lg p-4">
              <p className="text-red-200 text-sm">{error}</p>
            </div>
          )}

          {!loading && !error && filteredImages.length === 0 && (
            <div className="flex items-center justify-center h-full">
              <div className="text-center text-gray-400">
                <svg className="w-16 h-16 mx-auto mb-3 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
                <p>No images found</p>
              </div>
            </div>
          )}

          {!loading && !error && filteredImages.length > 0 && (
            <div>
              <div className="text-sm text-gray-400 mb-4">
                {filteredImages.length} image{filteredImages.length !== 1 ? 's' : ''}
              </div>

              <div className="grid grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
                {filteredImages.map((image) => {
                  const imageUrl = getImageUrl(image);
                  const hasFile = !!image.storage_path;

                  return (
                    <div
                      key={image.id}
                      onClick={() => hasFile && selectImage(image)}
                      className={`relative aspect-square rounded-lg overflow-hidden group ${
                        hasFile ? 'cursor-pointer' : 'cursor-not-allowed opacity-50'
                      } ${selectedImage?.id === image.id ? 'ring-2 ring-realm-symbolic' : ''}`}
                    >
                      {hasFile ? (
                        <>
                          <img
                            src={imageUrl}
                            alt={image.filename}
                            className="w-full h-full object-cover transition-transform group-hover:scale-105"
                            loading="lazy"
                          />

                          <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity">
                            <div className="absolute bottom-0 left-0 right-0 p-2">
                              <p className="text-xs text-white font-medium truncate">
                                {image.filename}
                              </p>
                            </div>
                          </div>
                        </>
                      ) : (
                        <div className="w-full h-full bg-gray-800 flex items-center justify-center">
                          <svg className="w-8 h-8 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                          </svg>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>

              {/* Infinite scroll target */}
              {view === 'library' && hasMore && (
                <div ref={observerTarget} className="h-20 flex items-center justify-center">
                  <div className="text-gray-500 text-sm">Loading more...</div>
                </div>
              )}
            </div>
          )}

          {/* Photos.app album export view */}
          {view === 'photos' && selectedAlbum && (
            <div className="flex items-center justify-center h-full">
              <div className="text-center text-gray-400 max-w-md">
                <svg className="w-16 h-16 mx-auto mb-3 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
                <p className="text-lg font-medium mb-2">Album: {selectedAlbum.name}</p>
                <p className="text-sm mb-4">{selectedAlbum.count} photos in this album</p>

                <div className="space-y-3 mt-6">
                  <button
                    onClick={() => handleExportAlbum(selectedAlbum.name, 50)}
                    disabled={loading}
                    className="w-full px-4 py-3 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-700 text-white rounded-lg font-medium transition-colors"
                  >
                    {loading ? 'Exporting...' : `Export Album (up to 50 photos)`}
                  </button>

                  <button
                    onClick={() => handleExportRecent(30, 100)}
                    disabled={loading}
                    className="w-full px-4 py-3 bg-purple-600/50 hover:bg-purple-600 disabled:bg-gray-700 text-white rounded-lg font-medium transition-colors"
                  >
                    {loading ? 'Exporting...' : 'Export Recent Photos (Last 30 Days)'}
                  </button>

                  <p className="text-xs text-gray-500 mt-4">
                    Photos will be exported to ~/humanizer-agent/tmp folder. After export, go to Import tab → Images → Select Folder to upload.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Photos.app albums list (when no album selected) */}
          {view === 'photos' && !selectedAlbum && (
            <div className="flex items-center justify-center h-full">
              <div className="text-center text-gray-400">
                <svg className="w-16 h-16 mx-auto mb-3 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                </svg>
                <p className="text-lg">Select an album from the left sidebar</p>
                <p className="text-sm text-gray-500 mt-2">{albums.length} albums available</p>
              </div>
            </div>
          )}
        </div>

        {/* Right Panel - Metadata (when image selected) */}
        {selectedImage && (
          <div className="w-1/3 border-l border-gray-800 overflow-y-auto bg-gray-900">
            <div className="p-4">
              {/* Close button */}
              <div className="flex justify-between items-start mb-4">
                <h3 className="text-lg font-semibold text-white">Image Details</h3>
                <button
                  onClick={() => {
                    setSelectedImage(null);
                    setImageMetadata(null);
                  }}
                  className="text-gray-400 hover:text-white"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              {/* Image Preview */}
              <div className="mb-4 rounded-lg overflow-hidden bg-gray-800">
                <img
                  src={getImageUrl(selectedImage)}
                  alt={selectedImage.filename}
                  className="w-full h-auto"
                />
              </div>

              {/* Filename */}
              <div className="mb-4">
                <h4 className="text-sm font-semibold text-gray-400 mb-1">Filename</h4>
                <p className="text-white text-sm break-all">{selectedImage.filename}</p>
              </div>

              {/* Basic Metadata */}
              <div className="space-y-3 mb-4">
                {selectedImage.mime_type && (
                  <div>
                    <span className="text-sm text-gray-400">Type:</span>
                    <span className="text-white text-sm ml-2">{selectedImage.mime_type}</span>
                  </div>
                )}

                {selectedImage.custom_metadata?.width && (
                  <div>
                    <span className="text-sm text-gray-400">Dimensions:</span>
                    <span className="text-white text-sm ml-2">
                      {selectedImage.custom_metadata.width} × {selectedImage.custom_metadata.height}
                    </span>
                  </div>
                )}

                {selectedImage.custom_metadata?.generator && (
                  <div>
                    <span className="text-sm text-gray-400">Generator:</span>
                    <span className="text-white text-sm ml-2 px-2 py-0.5 bg-purple-600 rounded">
                      {selectedImage.custom_metadata.generator}
                    </span>
                  </div>
                )}

                {selectedImage.created_at && (
                  <div>
                    <span className="text-sm text-gray-400">Created:</span>
                    <span className="text-white text-sm ml-2">
                      {new Date(selectedImage.created_at).toLocaleString()}
                    </span>
                  </div>
                )}
              </div>

              {/* AI Prompt */}
              {selectedImage.custom_metadata?.ai_prompt && (
                <div className="mb-4">
                  <h4 className="text-sm font-semibold text-gray-400 mb-1">AI Prompt</h4>
                  <p className="text-white text-sm bg-gray-800 p-3 rounded-lg">
                    {selectedImage.custom_metadata.ai_prompt}
                  </p>
                </div>
              )}

              {/* Model Info */}
              {selectedImage.custom_metadata?.model && (
                <div className="mb-4">
                  <h4 className="text-sm font-semibold text-gray-400 mb-1">Model</h4>
                  <p className="text-white text-sm">{selectedImage.custom_metadata.model}</p>
                </div>
              )}

              {/* Conversation Link */}
              {imageMetadata?.conversation && (
                <div className="mb-4">
                  <h4 className="text-sm font-semibold text-gray-400 mb-2">Source Conversation</h4>
                  <button
                    onClick={() => onNavigateToConversation && onNavigateToConversation(imageMetadata.conversation)}
                    className="w-full text-left p-3 bg-gray-800 hover:bg-gray-700 rounded-lg transition-colors group"
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="text-white text-sm font-medium">
                          {imageMetadata.conversation.title}
                        </div>
                        <div className="text-gray-400 text-xs mt-1">
                          {new Date(imageMetadata.conversation.created_at).toLocaleDateString()}
                        </div>
                      </div>
                      <svg className="w-4 h-4 text-gray-400 group-hover:text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                      </svg>
                    </div>
                  </button>
                </div>
              )}

              {/* Message Link */}
              {imageMetadata?.message && (
                <div className="mb-4">
                  <h4 className="text-sm font-semibold text-gray-400 mb-2">Source Message</h4>
                  <div className="p-3 bg-gray-800 rounded-lg">
                    <div className="text-gray-400 text-xs mb-1">
                      {imageMetadata.message.role} • {new Date(imageMetadata.message.created_at).toLocaleString()}
                    </div>
                    <div className="text-white text-sm line-clamp-3">
                      {imageMetadata.message.content?.substring(0, 150)}
                      {imageMetadata.message.content?.length > 150 ? '...' : ''}
                    </div>
                  </div>
                </div>
              )}

              {/* Transformations */}
              {imageMetadata?.transformations && imageMetadata.transformations.length > 0 && (
                <div className="mb-4">
                  <h4 className="text-sm font-semibold text-gray-400 mb-2">
                    Transformations ({imageMetadata.transformations.length})
                  </h4>
                  <div className="space-y-2">
                    {imageMetadata.transformations.map((transform, idx) => (
                      <button
                        key={idx}
                        onClick={() => onNavigateToTransformation && onNavigateToTransformation(transform)}
                        className="w-full text-left p-3 bg-gray-800 hover:bg-gray-700 rounded-lg transition-colors group"
                      >
                        <div className="flex items-center justify-between">
                          <div>
                            <div className="text-white text-sm font-medium">{transform.job_type}</div>
                            <div className="text-gray-400 text-xs mt-1">{transform.status}</div>
                          </div>
                          <svg className="w-4 h-4 text-gray-400 group-hover:text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                          </svg>
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* EXIF Data */}
              {selectedImage.custom_metadata?.exif && Object.keys(selectedImage.custom_metadata.exif).length > 0 && (
                <div className="mb-4">
                  <h4 className="text-sm font-semibold text-gray-400 mb-2">EXIF Data</h4>
                  <div className="bg-gray-800 rounded-lg p-3 space-y-1 text-xs font-mono">
                    {Object.entries(selectedImage.custom_metadata.exif).slice(0, 10).map(([key, value]) => (
                      <div key={key} className="flex justify-between">
                        <span className="text-gray-400">{key}:</span>
                        <span className="text-white">{String(value).substring(0, 40)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

ImageBrowser.propTypes = {
  onNavigateToConversation: PropTypes.func,
  onNavigateToTransformation: PropTypes.func
};
