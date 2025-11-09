import 'antd/dist/reset.css'
import './index.css'
import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App'
import { worker } from './mocks/browser'

async function initApp() {
    if (process.env.NODE_ENV === 'development') {
        // await worker.start() // Temporarily disabled to test against the real backend
    }

    ReactDOM.createRoot(document.getElementById('root')!).render(
        <React.StrictMode>
            <BrowserRouter>
                <App />
            </BrowserRouter>
        </React.StrictMode>
    )
}

initApp()


