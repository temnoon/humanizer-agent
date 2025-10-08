import Workstation from './components/Workstation'
import { WorkspaceProvider } from './contexts/WorkspaceContext'
import './styles/workstation.css'

/**
 * WorkstationApp - Main application wrapper for the Workstation
 *
 * This is the new primary interface for the Humanizer Agent,
 * providing a professional, full-featured workstation for text archaeology,
 * transformation, and philosophical exploration.
 *
 * Wrapped with WorkspaceProvider for unified state management.
 */
function WorkstationApp() {
  return (
    <WorkspaceProvider>
      <Workstation />
    </WorkspaceProvider>
  )
}

export default WorkstationApp
