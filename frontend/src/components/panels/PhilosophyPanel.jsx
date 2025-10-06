import { useState } from 'react';
import PropTypes from 'prop-types';
import axios from 'axios';

/**
 * PhilosophyPanel - Multi-perspective analysis
 *
 * Exposes the philosophical API:
 * - Multi-perspective transformations
 * - Framework explanations
 * - Contemplative exercises
 */
function PhilosophyPanel({ isOpen, onClose, currentDocument, onResultReady }) {
  const [mode, setMode] = useState('perspectives');
  const [loading, setLoading] = useState(false);
  const [perspectives, setPerspectives] = useState([]);
  const [exercise, setExercise] = useState(null);
  const [error, setError] = useState(null);

  const [personaList, setPersonaList] = useState('Scholar,Mystic,Scientist');
  const [namespaceList, setNamespaceList] = useState('philosophy,spirituality,physics');
  const [styleList, setStyleList] = useState('academic,poetic,technical');

  const [exerciseType, setExerciseType] = useState('neti_neti');
  const [targetConcept, setTargetConcept] = useState('self');

  const API_BASE = 'http://localhost:8000';

  const handleGeneratePerspectives = async () => {
    if (!currentDocument?.content) {
      setError('No document content available');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const personas = personaList.split(',').map(p => p.trim());
      const namespaces = namespaceList.split(',').map(n => n.trim());
      const styles = styleList.split(',').map(s => s.trim());

      const response = await axios.post(`${API_BASE}/api/philosophical/perspectives`, {
        content: currentDocument.content,
        personas,
        namespaces,
        styles
      });

      setPerspectives(response.data.perspectives);
      setLoading(false);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to generate perspectives');
      setLoading(false);
    }
  };

  const handleGenerateExercise = async () => {
    setLoading(true);
    setError(null);

    try {
      let response;

      if (exerciseType === 'neti_neti') {
        response = await axios.post(`${API_BASE}/api/madhyamaka/contemplate/neti-neti`, {
          target_concept: targetConcept,
          depth: 'progressive'
        });
      } else if (exerciseType === 'two_truths') {
        response = await axios.post(`${API_BASE}/api/madhyamaka/contemplate/two-truths`, {
          phenomenon: targetConcept
        });
      } else {
        response = await axios.post(`${API_BASE}/api/madhyamaka/contemplate/dependent-origination`, {
          starting_point: targetConcept
        });
      }

      setExercise(response.data);
      setLoading(false);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to generate exercise');
      setLoading(false);
    }
  };

  const viewPerspective = (perspective) => {
    if (onResultReady) {
      onResultReady({
        content: perspective.text,
        type: 'markdown',
        metadata: {
          persona: perspective.persona,
          namespace: perspective.namespace,
          style: perspective.style
        }
      });
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-y-0 right-0 w-96 bg-gray-900 border-l border-gray-800 shadow-xl z-50 flex flex-col overflow-hidden">
      <div className="flex items-center justify-between p-4 border-b border-gray-800">
        <div className="flex items-center space-x-2">
          <span className="text-2xl">🔮</span>
          <h2 className="text-lg font-structural font-semibold text-white">Philosophy</h2>
        </div>
        <button onClick={onClose} className="p-2 hover:bg-gray-800 rounded-md transition-colors text-gray-400 hover:text-white">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <div className="flex border-b border-gray-800">
        <button onClick={() => setMode('perspectives')} className={`flex-1 px-4 py-3 text-sm font-medium transition-colors ${mode === 'perspectives' ? 'text-white border-b-2 border-realm-symbolic bg-gray-800' : 'text-gray-400 hover:text-white hover:bg-gray-800'}`}>
          Perspectives
        </button>
        <button onClick={() => setMode('contemplate')} className={`flex-1 px-4 py-3 text-sm font-medium transition-colors ${mode === 'contemplate' ? 'text-white border-b-2 border-realm-symbolic bg-gray-800' : 'text-gray-400 hover:text-white hover:bg-gray-800'}`}>
          Contemplate
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {mode === 'perspectives' && (
          <>
            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Personas (comma-separated)</label>
                <input type="text" value={personaList} onChange={(e) => setPersonaList(e.target.value)} disabled={loading} className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-md text-white text-sm focus:outline-none focus:ring-2 focus:ring-realm-symbolic" />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Namespaces (comma-separated)</label>
                <input type="text" value={namespaceList} onChange={(e) => setNamespaceList(e.target.value)} disabled={loading} className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-md text-white text-sm focus:outline-none focus:ring-2 focus:ring-realm-symbolic" />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Styles (comma-separated)</label>
                <input type="text" value={styleList} onChange={(e) => setStyleList(e.target.value)} disabled={loading} className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-md text-white text-sm focus:outline-none focus:ring-2 focus:ring-realm-symbolic" />
              </div>

              <button onClick={handleGeneratePerspectives} disabled={loading || !currentDocument?.content} className="w-full px-4 py-2 bg-realm-symbolic hover:bg-realm-symbolic-light disabled:bg-gray-700 text-white rounded-md text-sm font-medium transition-colors">
                {loading ? 'Generating...' : 'Generate Perspectives'}
              </button>
            </div>

            {perspectives.length > 0 && (
              <div className="space-y-2">
                <div className="text-sm font-medium text-gray-400">{perspectives.length} Perspectives</div>
                {perspectives.map((p, idx) => (
                  <div key={idx} onClick={() => viewPerspective(p)} className="bg-gray-800 p-3 rounded-md cursor-pointer hover:bg-gray-750 transition-colors">
                    <div className="flex items-center justify-between mb-2">
                      <div className="text-sm font-medium text-white">{p.persona}</div>
                      <div className="text-xs px-2 py-1 rounded bg-realm-symbolic/20 text-realm-symbolic">{p.namespace}</div>
                    </div>
                    <div className="text-xs text-gray-400 line-clamp-2">{p.text.substring(0, 120)}...</div>
                  </div>
                ))}
              </div>
            )}
          </>
        )}

        {mode === 'contemplate' && (
          <>
            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Exercise Type</label>
                <select value={exerciseType} onChange={(e) => setExerciseType(e.target.value)} disabled={loading} className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-md text-white text-sm focus:outline-none focus:ring-2 focus:ring-realm-symbolic">
                  <option value="neti_neti">Neti Neti (Not this, not that)</option>
                  <option value="two_truths">Two Truths</option>
                  <option value="dependent_origination">Dependent Origination</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Target Concept</label>
                <input type="text" value={targetConcept} onChange={(e) => setTargetConcept(e.target.value)} placeholder="e.g., self, language, time" disabled={loading} className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-md text-white text-sm focus:outline-none focus:ring-2 focus:ring-realm-symbolic" />
              </div>

              <button onClick={handleGenerateExercise} disabled={loading || !targetConcept} className="w-full px-4 py-2 bg-realm-subjective hover:bg-realm-subjective-light disabled:bg-gray-700 text-white rounded-md text-sm font-medium transition-colors">
                {loading ? 'Generating...' : 'Generate Exercise'}
              </button>
            </div>

            {exercise && (
              <div className="bg-gray-800 p-4 rounded-md space-y-3">
                <div className="text-sm font-medium text-realm-subjective-lighter">
                  {exercise.exercise_type?.replace(/_/g, ' ').toUpperCase()}
                </div>
                {exercise.instructions && (
                  <div className="text-sm text-gray-300 whitespace-pre-wrap">{exercise.instructions}</div>
                )}
                {exercise.stages && (
                  <div className="space-y-2">
                    {exercise.stages.map((stage, idx) => (
                      <div key={idx} className="bg-gray-900 p-2 rounded text-xs">
                        <div className="text-realm-subjective font-medium mb-1">{stage.name || `Stage ${idx + 1}`}</div>
                        <div className="text-gray-400">{stage.description || stage.instruction}</div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </>
        )}

        {error && (
          <div className="bg-red-900/20 border border-red-500 p-3 rounded-md">
            <div className="text-sm text-red-400">{error}</div>
          </div>
        )}
      </div>
    </div>
  );
}

PhilosophyPanel.propTypes = {
  isOpen: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
  currentDocument: PropTypes.shape({
    content: PropTypes.string,
    type: PropTypes.string
  }),
  onResultReady: PropTypes.func
};

export default PhilosophyPanel;
