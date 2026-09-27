import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import { InterfazProvider } from './components/ui';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <InterfazProvider>
      <App />
    </InterfazProvider>
  </React.StrictMode>,
);
