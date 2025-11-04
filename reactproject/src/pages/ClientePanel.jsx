// src/pages/ClientePanel.jsx
import API from '../api/axios';
import { useEffect, useState } from 'react';

export default function ClientePanel() {
  const [platillos, setPlatillos] = useState([]);

  useEffect(() => {
    API.get('/cliente/menu').then((res) => setPlatillos(res.data));
  }, []);

  return (
    <div>
      <h2>Menú del cliente</h2>
      {platillos.map((p) => (
        <div key={p.id}>
          <h3>{p.nombre}</h3>
          <p>{p.descripcion}</p>
          <p>${p.precio}</p>
        </div>
      ))}
    </div>
  );
}
