import { useState, useEffect } from 'react'
import PropTypes from 'prop-types'

/**
 * StyleConfigurator - Visual SCSS/CSS variable editor
 *
 * Allows users to customize the workstation theme in real-time
 * by editing CSS custom properties and SCSS variables
 */
function StyleConfigurator({ isOpen, onClose }) {
  const [theme, setTheme] = useState({
    realmCorporeal: '#2D7D6E',
    realmSymbolic: '#6B46C1',
    realmSubjective: '#1E1B4B',
    bgPrimary: '#030712',
    bgSecondary: '#111827',
    textPrimary: '#f9fafb',
    fontScale: 1.0,
    sidebarWidth: 320
  })

  const [presets] = useState([
    {
      name: 'Default (Three Realms)',
      theme: {
        realmCorporeal: '#2D7D6E',
        realmSymbolic: '#6B46C1',
        realmSubjective: '#1E1B4B',
        bgPrimary: '#030712',
        bgSecondary: '#111827',
        textPrimary: '#f9fafb',
        fontScale: 1.0,
        sidebarWidth: 320
      }
    },
    {
      name: 'Ocean',
      theme: {
        realmCorporeal: '#0891b2',
        realmSymbolic: '#2563eb',
        realmSubjective: '#1e1b4b',
        bgPrimary: '#020617',
        bgSecondary: '#0f172a',
        textPrimary: '#f1f5f9',
        fontScale: 1.0,
        sidebarWidth: 320
      }
    },
    {
      name: 'Forest',
      theme: {
        realmCorporeal: '#059669',
        realmSymbolic: '#84cc16',
        realmSubjective: '#1e293b',
        bgPrimary: '#0f172a',
        bgSecondary: '#1e293b',
        textPrimary: '#f1f5f9',
        fontScale: 1.0,
        sidebarWidth: 320
      }
    },
    {
      name: 'Sunset',
      theme: {
        realmCorporeal: '#dc2626',
        realmSymbolic: '#f59e0b',
        realmSubjective: '#1e1b4b',
        bgPrimary: '#1c1917',
        bgSecondary: '#292524',
        textPrimary: '#fafaf9',
        fontScale: 1.0,
        sidebarWidth: 320
      }
    }
  ])

  // Load saved theme from localStorage
  useEffect(() => {
    const savedTheme = localStorage.getItem('workstation_theme')
    if (savedTheme) {
      try {
        setTheme(JSON.parse(savedTheme))
      } catch (err) {
        console.error('Error loading theme:', err)
      }
    }
  }, [])

  // Apply theme to CSS custom properties
  useEffect(() => {
    const root = document.documentElement
    root.style.setProperty('--realm-corporeal', theme.realmCorporeal)
    root.style.setProperty('--realm-symbolic', theme.realmSymbolic)
    root.style.setProperty('--realm-subjective', theme.realmSubjective)
    root.style.setProperty('--bg-primary', theme.bgPrimary)
    root.style.setProperty('--bg-secondary', theme.bgSecondary)
    root.style.setProperty('--text-primary', theme.textPrimary)
    root.style.setProperty('--font-scale', theme.fontScale)
    root.style.setProperty('--sidebar-width', `${theme.sidebarWidth}px`)

    // Save to localStorage
    localStorage.setItem('workstation_theme', JSON.stringify(theme))
  }, [theme])

  const handleThemeChange = (key, value) => {
    setTheme(prev => ({ ...prev, [key]: value }))
  }

  const loadPreset = (preset) => {
    setTheme(preset.theme)
  }

  const resetToDefault = () => {
    setTheme(presets[0].theme)
  }

  const exportTheme = () => {
    const dataStr = JSON.stringify(theme, null, 2)
    const dataBlob = new Blob([dataStr], { type: 'application/json' })
    const url = URL.createObjectURL(dataBlob)
    const link = document.createElement('a')
    link.href = url
    link.download = 'workstation-theme.json'
    link.click()
  }

  const importTheme = (event) => {
    const file = event.target.files[0]
    if (file) {
      const reader = new FileReader()
      reader.onload = (e) => {
        try {
          const imported = JSON.parse(e.target.result)
          setTheme(imported)
        } catch (err) {
          alert('Invalid theme file')
        }
      }
      reader.readAsText(file)
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-gray-900 border border-gray-700 rounded-lg w-full max-w-3xl max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-700">
          <h2 className="text-xl font-structural font-semibold text-white">
            Style Configurator
          </h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-800 rounded-md transition-colors text-gray-400 hover:text-white"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Presets */}
          <div>
            <h3 className="text-sm font-medium text-gray-400 mb-3">Presets</h3>
            <div className="grid grid-cols-2 gap-2">
              {presets.map((preset, idx) => (
                <button
                  key={idx}
                  onClick={() => loadPreset(preset)}
                  className="px-4 py-2 bg-gray-800 hover:bg-gray-700 text-white rounded-md transition-colors text-sm"
                >
                  {preset.name}
                </button>
              ))}
            </div>
          </div>

          {/* Three Realms Colors */}
          <div>
            <h3 className="text-sm font-medium text-gray-400 mb-3">Three Realms Colors</h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <label className="text-sm text-gray-300">Corporeal (Physical)</label>
                <input
                  type="color"
                  value={theme.realmCorporeal}
                  onChange={(e) => handleThemeChange('realmCorporeal', e.target.value)}
                  className="w-16 h-8 rounded cursor-pointer"
                />
              </div>
              <div className="flex items-center justify-between">
                <label className="text-sm text-gray-300">Symbolic (Abstract)</label>
                <input
                  type="color"
                  value={theme.realmSymbolic}
                  onChange={(e) => handleThemeChange('realmSymbolic', e.target.value)}
                  className="w-16 h-8 rounded cursor-pointer"
                />
              </div>
              <div className="flex items-center justify-between">
                <label className="text-sm text-gray-300">Subjective (Conscious)</label>
                <input
                  type="color"
                  value={theme.realmSubjective}
                  onChange={(e) => handleThemeChange('realmSubjective', e.target.value)}
                  className="w-16 h-8 rounded cursor-pointer"
                />
              </div>
            </div>
          </div>

          {/* Background Colors */}
          <div>
            <h3 className="text-sm font-medium text-gray-400 mb-3">Background Colors</h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <label className="text-sm text-gray-300">Primary Background</label>
                <input
                  type="color"
                  value={theme.bgPrimary}
                  onChange={(e) => handleThemeChange('bgPrimary', e.target.value)}
                  className="w-16 h-8 rounded cursor-pointer"
                />
              </div>
              <div className="flex items-center justify-between">
                <label className="text-sm text-gray-300">Secondary Background</label>
                <input
                  type="color"
                  value={theme.bgSecondary}
                  onChange={(e) => handleThemeChange('bgSecondary', e.target.value)}
                  className="w-16 h-8 rounded cursor-pointer"
                />
              </div>
            </div>
          </div>

          {/* Text Color */}
          <div>
            <h3 className="text-sm font-medium text-gray-400 mb-3">Text Color</h3>
            <div className="flex items-center justify-between">
              <label className="text-sm text-gray-300">Primary Text</label>
              <input
                type="color"
                value={theme.textPrimary}
                onChange={(e) => handleThemeChange('textPrimary', e.target.value)}
                className="w-16 h-8 rounded cursor-pointer"
              />
            </div>
          </div>

          {/* Font Scale */}
          <div>
            <h3 className="text-sm font-medium text-gray-400 mb-3">Font Scale</h3>
            <div className="flex items-center space-x-4">
              <input
                type="range"
                min="0.8"
                max="1.4"
                step="0.1"
                value={theme.fontScale}
                onChange={(e) => handleThemeChange('fontScale', parseFloat(e.target.value))}
                className="flex-1"
              />
              <span className="text-sm text-gray-300 w-12">{theme.fontScale.toFixed(1)}x</span>
            </div>
          </div>

          {/* Sidebar Width */}
          <div>
            <h3 className="text-sm font-medium text-gray-400 mb-3">Sidebar Width</h3>
            <div className="flex items-center space-x-4">
              <input
                type="range"
                min="240"
                max="600"
                step="10"
                value={theme.sidebarWidth}
                onChange={(e) => handleThemeChange('sidebarWidth', parseInt(e.target.value))}
                className="flex-1"
              />
              <span className="text-sm text-gray-300 w-16">{theme.sidebarWidth}px</span>
            </div>
          </div>

          {/* Import/Export */}
          <div>
            <h3 className="text-sm font-medium text-gray-400 mb-3">Import/Export</h3>
            <div className="flex gap-2">
              <button
                onClick={exportTheme}
                className="flex-1 px-4 py-2 bg-realm-symbolic hover:bg-realm-symbolic-light text-white rounded-md transition-colors text-sm"
              >
                Export Theme
              </button>
              <label className="flex-1 px-4 py-2 bg-realm-corporeal hover:bg-realm-corporeal-light text-white rounded-md transition-colors text-sm cursor-pointer text-center">
                Import Theme
                <input
                  type="file"
                  accept=".json"
                  onChange={importTheme}
                  className="hidden"
                />
              </label>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-gray-700 flex justify-between">
          <button
            onClick={resetToDefault}
            className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-md transition-colors text-sm"
          >
            Reset to Default
          </button>
          <button
            onClick={onClose}
            className="px-4 py-2 bg-realm-symbolic hover:bg-realm-symbolic-light text-white rounded-md transition-colors text-sm"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  )
}

StyleConfigurator.propTypes = {
  isOpen: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired
}

export default StyleConfigurator
