import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App.jsx'
import './index.css'
import './styles/theme.css'
import './styles/base.css'
import './styles/layout.css'
import './styles/components.css'
import './styles/pages/overview.css'
import './styles/pages/planning.css'
import './styles/pages/intel.css'
import './styles/pages/history.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>
)
