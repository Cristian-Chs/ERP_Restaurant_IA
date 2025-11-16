// PlatilloCard.jsx - CORREGIDO PARA EL CARRITO

import React from 'react';
import './PlatilloCard.css';

// 🛑 MODIFICADO: Aceptar todas las props (incluido 'id', que es crucial)
// y la función 'agregarAlCarrito'
export default function PlatilloCard(props) { 
    // Desestructuramos solo lo que vamos a mostrar
    const { id, name, description, imagen, price, agregarAlCarrito } = props;

    // Función que se ejecuta al hacer clic en el botón
    const handleAdd = () => {
        if (agregarAlCarrito) {
            // 🚀 CRÍTICO: Llamamos a la función global, pasando el objeto COMPLETO del plato (props)
            // Esto incluye el id, name, price, etc., que necesitamos para el carrito.
            agregarAlCarrito(props);
            
            // Opcional: Puedes añadir una confirmación visual aquí (ej: un toast)
            console.log(`Añadido al carrito: ${name}`);
        }
    };

  return (
    <div className="platillo-card">
      <img src={imagen} alt={name} />
      <h3>{name}</h3>
      <p>{description}</p>
      <div className="precios">
        <span>Precio: ${price}</span> 
      </div>
        
        {/* 🚀 BOTÓN DE ACCIÓN PARA AÑADIR AL CARRITO */}
        <button 
            className="add-to-cart-btn" 
            onClick={handleAdd}
            // Aseguramos que solo se pueda hacer clic si la función existe
            disabled={!agregarAlCarrito} 
        >
            Añadir al Pedido
        </button>
    </div>
  );
}