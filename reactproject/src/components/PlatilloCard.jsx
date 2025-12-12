// PlatilloCard.jsx - MODIFICADO para incluir opciones de sabor

import React, { useState } from 'react'; // 🚨 Importamos useState
import PlatilloOpciones from './PlatilloOpciones'; // 🚨 Importamos el nuevo componente
import './PlatilloCard.css';

export default function PlatilloCard(props) { 
    const { id, name, description, imagen, price, agregarAlCarrito } = props;

    // 1. Lógica para detectar si es el plato de las empanadas (puedes usar el id o el nombre)
    // 🚨 ASUMIMOS que el nombre 'Empanadas' lo identifica
    const isEmpanada = name && name.toLowerCase().includes('empanada');

    // 2. Estado para el sabor, solo si es una empanada. Por defecto 'Pollo'.
    const [saborSeleccionado, setSaborSeleccionado] = useState('Pollo');

    // 3. Función para manejar la adición al carrito
    const handleAdd = () => {
        if (agregarAlCarrito) {
            
            // Creamos una copia del objeto del plato
            let itemToAdd = { ...props };

            // Si es una empanada, modificamos el nombre y agregamos el sabor
            if (isEmpanada) {
                // Modificamos el nombre para el carrito: "Empanadas (Cazón)"
                itemToAdd.name = `${name} (${saborSeleccionado})`;
                // Agregamos una propiedad extra al objeto
                itemToAdd.sabor = saborSeleccionado;
            }

            // Llamamos a la función global con el objeto final
            agregarAlCarrito(itemToAdd);
            
            console.log(`Añadido al carrito: ${itemToAdd.name}`);
        }
    };

  return (
    <div className="platillo-card">
      <img src={imagen} alt={name} />
      <h3>{name}</h3>
      <p>{description}</p>

      {/* 4. Renderizamos el selector SOLO si es el plato de empanadas */}
      {isEmpanada && (
          <PlatilloOpciones 
              selectedOption={saborSeleccionado}
              onOptionChange={setSaborSeleccionado} // setSaborSeleccionado directamente maneja el cambio
          />
      )}
      
      <div className="precios">
        <span>Precio: ${price}</span> 
      </div>
        
        <button 
            className="add-to-cart-btn" 
            onClick={handleAdd}
            disabled={!agregarAlCarrito} 
        >
            Añadir al Pedido
        </button>
    </div>
  );
}