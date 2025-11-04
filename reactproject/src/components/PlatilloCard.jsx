import React from 'react';
import './PlatilloCard.css';

function PlatilloCard({ nombre, descripcion, precio, imagen }) {
  return (
    <div className="card">
      <div className="image">
        <img src={imagen || 'https://via.placeholder.com/150'} alt={nombre} />
        <span className="text">{nombre || 'Sin nombre'}</span>
      </div>
      <span className="title">{descripcion || 'Sin descripción'}</span>
      <span className="price">${precio || '0'}</span>
    </div>
  );
}

export default PlatilloCard;
