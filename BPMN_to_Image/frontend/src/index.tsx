import React from 'react';
import ReactDOM from 'react-dom/client';
import BPMN_to_image from './bpmn_to_image';

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);

root.render(
  <React.StrictMode>
    <Bpmn_to_image />
  </React.StrictMode>
);