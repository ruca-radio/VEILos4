import React from 'react';
import ReactDOM from 'react-dom/client';
import VeilosTerminalConsole from './VeilosTerminalConsole';

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);

root.render(
  <React.StrictMode>
    <VeilosTerminalConsole />
  </React.StrictMode>
);
