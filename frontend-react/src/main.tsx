import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './index.css'

// Restore auth token before first render
const stored = localStorage.getItem('qd_access')
if (stored) {
  // injected into axios in api/client.ts on import
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)
