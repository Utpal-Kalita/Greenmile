const fs = require('fs');
const content = `import { useState } from 'react';
import { MapContainer, TileLayer, CircleMarker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';

export default function App() {
  return (
    <div className='p-8 w-full max-w-7xl mx-auto'>
      <h1 className='text-3xl font-bold mb-4'>Greenmile Optimizer Dashboard</h1>
      <div className='h-[500px] w-full border rounded overflow-hidden shadow-lg'>
        <MapContainer center={[28.5245, 77.2066]} zoom={12} style={{ height: '100%', width: '100%' }}>
          <TileLayer url='https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png' />
        </MapContainer>
      </div>
    </div>
  );
}`;
fs.writeFileSync('C:/Users/Utpal Kalita/Greenmile/frontend/src/App.jsx', content, 'utf8');
