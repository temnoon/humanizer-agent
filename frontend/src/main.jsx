import React from 'react'
import ReactDOM from 'react-dom/client'
import WorkstationApp from './WorkstationApp.jsx'
// import PhilosophicalApp from './PhilosophicalApp.jsx' // Alternative philosophical interface
// import App from './App.jsx' // Original utility-focused version
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <WorkstationApp />
  </React.StrictMode>,
)
