// PlatilloCard.jsx - MODIFICADO para incluir opciones de sabor

import React, { useState } from 'react'; //  Importamos useState
import PlatilloOpciones from './PlatilloOpciones'; //  Importamos el nuevo componente
import './PlatilloCard.css';

export default function PlatilloCard(props) { 
    const { id, name, description, imagen, price, agregarAlCarrito } = props;

    // 1. Lógica dinámica: Si el producto tiene sabores asignados en DB
    const flavors = props.sabor_nombres || [];
    const hasFlavors = flavors.length > 0;

    // 2. Estado para el sabor seleccionado. Por defecto el primero de la lista.
    const [saborSeleccionado, setSaborSeleccionado] = useState(flavors[0] || '');

    // 3. Función para manejar la adición al carrito
    const handleAdd = () => {
        if (agregarAlCarrito) {
            
            // Creamos una copia del objeto del plato
            let itemToAdd = { ...props };

            // Si el producto tiene sabores, los incluimos en el nombre del carrito solo si uno está seleccionado
            if (hasFlavors) {
                if (saborSeleccionado) {
                    itemToAdd.name = `${name} (${saborSeleccionado})`;
                    itemToAdd.sabor = saborSeleccionado;
                } else {
                    itemToAdd.name = name;
                    itemToAdd.sabor = 'Sin especificar';
                }
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

      {/* 4. Renderizamos el selector SOLO si el producto tiene sabores definidos */}
      {hasFlavors && (
          <PlatilloOpciones 
              id={id}
              selectedOption={saborSeleccionado}
              onOptionChange={setSaborSeleccionado} 
              opciones={flavors}
          />
      )}
      
      <div className="precios">
        <span className="price-usd">Precio: ${price}</span> 
        {props.exchangeRate && (
            <span className="price-ves">~ { (price * props.exchangeRate).toFixed(2) } Bs.</span>
        )}
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