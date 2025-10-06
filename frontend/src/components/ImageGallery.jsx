import { useState, useEffect } from 'react';
import axios from 'axios';
import PropTypes from 'prop-types';

/**
 * ImageGallery Component
 *
 * Browse all images in the system or filter by collection.
 * Features:
 * - Grid view with thumbnails
 * - Filter by collection, generator, date
 * - View metadata (AI prompts, EXIF, dimensions)
 * - Full-size lightbox viewer
 * - Search by filename or prompt
 */
export default function ImageGallery({ selectedCollection = null }) {
  const [images, setImages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterGenerator, setFilterGenerator] = useState('all');
  const [selectedImage, setSelectedImage] = useState(null);
  const [showLightbox, setShowLightbox] = useState(false);

  const API_BASE = 'http://localhost:8000';

  // Available generators for filtering
  const generators = ['all', 'dall-e', 'stable-diffusion', 'midjourney', 'user-upload', 'unknown'];

  useEffect(() => {
    loadImages();
  }, [selectedCollection]);

  const loadImages = async () => {
    setLoading(true);
    setError(null);

    try {
      const params = {};
      if (selectedCollection) {
        params.collection_id = selectedCollection.id;
      }

      const response = await axios.get(`${API_BASE}/api/library/media`, {
        params: {
          limit: 500,
          offset: 0,
          ...params
        }
      });

      setImages(response.data.media || []);
    } catch (err) {
      console.error('Failed to load images:', err);
      setError('Failed to load images: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  const getImageUrl = (image) => {
    if (image.storage_path) {
      // Backend serves files from storage_path via media/{id}/file endpoint
      return `${API_BASE}/api/library/media/${image.id}/file`;
    }
    return null;
  };

  const filterImages = () => {
    let filtered = images;

    // Filter by search query (filename or prompt)
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(img =>
        img.filename?.toLowerCase().includes(query) ||
        img.custom_metadata?.ai_prompt?.toLowerCase().includes(query)
      );
    }

    // Filter by generator
    if (filterGenerator !== 'all') {
      filtered = filtered.filter(img => {
        const generator = img.custom_metadata?.generator?.toLowerCase() || 'unknown';
        return generator === filterGenerator;
      });
    }

    return filtered;
  };

  const openLightbox = (image) => {
    setSelectedImage(image);
    setShowLightbox(true);
  };

  const closeLightbox = () => {
    setShowLightbox(false);
    setSelectedImage(null);
  };

  const filteredImages = filterImages();

  return (
    <div className="h-full flex flex-col">
      {/* Header with Filters */}
      <div className="p-4 border-b border-gray-800 space-y-3">
        <h3 className="text-lg font-semibold text-white">
          {selectedCollection ? `Images from ${selectedCollection.title}` : 'All Images'}
        </h3>

        {/* Search */}
        <div className="relative">
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

        {/* Generator Filter */}
        <div className="flex items-center gap-2">
          <label className="text-sm text-gray-400">Filter:</label>
          <select
            value={filterGenerator}
            onChange={(e) => setFilterGenerator(e.target.value)}
            className="flex-1 px-3 py-2 bg-gray-800 border border-gray-700 rounded-md text-sm text-white focus:outline-none focus:ring-2 focus:ring-realm-symbolic"
          >
            {generators.map(gen => (
              <option key={gen} value={gen}>
                {gen === 'all' ? 'All Generators' : gen.split('-').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')}
              </option>
            ))}
          </select>
        </div>

        {/* Stats */}
        <div className="text-xs text-gray-400">
          {filteredImages.length} of {images.length} images
        </div>
      </div>

      {/* Image Grid */}
      <div className="flex-1 overflow-y-auto p-4">
        {loading && (
          <div className="flex items-center justify-center h-full">
            <div className="text-gray-400">Loading images...</div>
          </div>
        )}

        {error && (
          <div className="bg-red-900/50 border border-red-700 rounded-lg p-4 m-4">
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
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
            {filteredImages.map((image) => {
              const imageUrl = getImageUrl(image);
              const hasFile = !!image.storage_path;

              return (
                <div
                  key={image.id}
                  onClick={() => hasFile && openLightbox(image)}
                  className={`relative aspect-square rounded-lg overflow-hidden group ${
                    hasFile ? 'cursor-pointer' : 'cursor-not-allowed opacity-50'
                  }`}
                >
                  {hasFile ? (
                    <>
                      <img
                        src={imageUrl}
                        alt={image.filename}
                        className="w-full h-full object-cover transition-transform group-hover:scale-105"
                        loading="lazy"
                      />

                      {/* Overlay with metadata */}
                      <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity">
                        <div className="absolute bottom-0 left-0 right-0 p-2">
                          <p className="text-xs text-white font-medium truncate">
                            {image.filename}
                          </p>
                          {image.custom_metadata?.generator && (
                            <div className="flex items-center gap-1 mt-1">
                              <span className="text-xs px-2 py-0.5 bg-purple-600 rounded text-white">
                                {image.custom_metadata.generator}
                              </span>
                            </div>
                          )}
                        </div>
                      </div>
                    </>
                  ) : (
                    <div className="w-full h-full bg-gray-800 flex items-center justify-center">
                      <div className="text-center p-3">
                        <svg className="w-8 h-8 mx-auto text-gray-600 mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                        </svg>
                        <p className="text-xs text-gray-500 truncate">{image.filename}</p>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Lightbox */}
      {showLightbox && selectedImage && (
        <div
          className="fixed inset-0 bg-black/90 z-50 flex items-center justify-center p-4"
          onClick={closeLightbox}
        >
          <div className="relative max-w-6xl max-h-full" onClick={(e) => e.stopPropagation()}>
            {/* Close button */}
            <button
              onClick={closeLightbox}
              className="absolute top-4 right-4 p-2 bg-gray-900/80 hover:bg-gray-800 text-white rounded-full transition-colors z-10"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>

            {/* Image */}
            <img
              src={getImageUrl(selectedImage)}
              alt={selectedImage.filename}
              className="max-w-full max-h-[80vh] object-contain rounded-lg"
            />

            {/* Metadata panel */}
            <div className="mt-4 bg-gray-900 rounded-lg p-4 max-h-48 overflow-y-auto">
              <h4 className="font-semibold text-white mb-2">{selectedImage.filename}</h4>

              <div className="grid grid-cols-2 gap-3 text-sm">
                {selectedImage.custom_metadata?.width && (
                  <div>
                    <span className="text-gray-400">Dimensions:</span>
                    <span className="text-white ml-2">
                      {selectedImage.custom_metadata.width} × {selectedImage.custom_metadata.height}
                    </span>
                  </div>
                )}

                {selectedImage.custom_metadata?.generator && (
                  <div>
                    <span className="text-gray-400">Generator:</span>
                    <span className="text-white ml-2">{selectedImage.custom_metadata.generator}</span>
                  </div>
                )}

                {selectedImage.created_at && (
                  <div className="col-span-2">
                    <span className="text-gray-400">Created:</span>
                    <span className="text-white ml-2">
                      {new Date(selectedImage.created_at).toLocaleString()}
                    </span>
                  </div>
                )}

                {selectedImage.custom_metadata?.ai_prompt && (
                  <div className="col-span-2">
                    <span className="text-gray-400">AI Prompt:</span>
                    <p className="text-white mt-1 text-xs bg-gray-800 p-2 rounded">
                      {selectedImage.custom_metadata.ai_prompt}
                    </p>
                  </div>
                )}

                {selectedImage.custom_metadata?.model && (
                  <div className="col-span-2">
                    <span className="text-gray-400">Model:</span>
                    <span className="text-white ml-2">{selectedImage.custom_metadata.model}</span>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

ImageGallery.propTypes = {
  selectedCollection: PropTypes.object
};
