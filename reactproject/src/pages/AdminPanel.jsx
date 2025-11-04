import { useState } from 'react';
import API from '../api/axios';
import './AdminPanel.css'; // Asegúrate de que este archivo contenga tus estilos
import { useNavigate } from 'react-router-dom';

export default function AdminPanel() {
  const [nombre, setNombre] = useState('');
  const [descripcion, setDescripcion] = useState('');
  const [precio, setPrecio] = useState('');
  const navigate = useNavigate();

  const crearPlatillo = async () => {
    await API.post('/admin/crear-platillo', { nombre, descripcion, precio });
    alert('Platillo creado');
  };

  return (
    
    <div className="panel-container">
      <button onClick={() => navigate('/')} className="decorative-button-prueba">
        <span>Back</span>
      </button>
      <h2>Panel Admin</h2>
      <div className="panel-form">
        <input
          placeholder="Nombre"
          value={nombre}
          onChange={(e) => setNombre(e.target.value)}
        />
        <input
          placeholder="Descripción"
          value={descripcion}
          onChange={(e) => setDescripcion(e.target.value)}
        />
        <input
          placeholder="Precio"
          value={precio}
          onChange={(e) => setPrecio(e.target.value)}
        />
        <button onClick={crearPlatillo}>Crear platillo</button>
      </div>
    </div>
  );
}
