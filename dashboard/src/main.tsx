import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App'
import './styles/index.css'

console.log('Starting React app...')

// Add error handling
window.addEventListener('error', (event) => {
  console.error('JavaScript error:', event.error)
  console.error('Error at:', event.filename, event.lineno, event.colno)
})

window.addEventListener('unhandledrejection', (event) => {
  console.error('Unhandled promise rejection:', event.reason)
})

const container = document.getElementById('root')
if (!container) {
  console.error('Root element not found!')
  document.body.innerHTML = '<div style="padding: 20px; color: red;">Error: Root element not found!</div>'
} else {
  console.log('Root element found, creating React root...')
  const root = createRoot(container)
  
  try {
    root.render(
      <StrictMode>
        <BrowserRouter>
          <App />
        </BrowserRouter>
      </StrictMode>
    )
    console.log('React app rendered successfully')
  } catch (error) {
    console.error('Error rendering React app:', error)
    container.innerHTML = `
      <div style="padding: 20px; color: red; font-family: Arial, sans-serif;">
        <h2>React App Error</h2>
        <p>Error: ${error}</p>
        <p>Check the browser console for more details.</p>
      </div>
    `
  }
} 