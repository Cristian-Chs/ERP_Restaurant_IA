// src/components/PlatilloOpciones.jsx

import { color } from 'framer-motion';
import React from 'react';

/**
 * Componente selector de opciones (ej. sabor de empanada).
 * @param {string} selectedOption - La opción actualmente seleccionada ('Pollo' o 'Cazón').
 * @param {function} onOptionChange - Función a llamar cuando una opción es seleccionada.
 */
export default function PlatilloOpciones({ selectedOption, onOptionChange }) {
    
    // Lista de opciones disponibles
    const opciones = ['Pollo', 'Cazón'];

    // Estilos muy básicos para replicar el look de radio buttons de la imagen
    const optionStyle = {
        marginRight: '15px',
        fontSize: '14px',
        color: '#333',
    };

    const labelStyle = {
        display: 'inline-block',
        marginRight: '10px',
        cursor: 'pointer',
    };

    return (
        <div className="platillo-opciones-selector" style={optionStyle}>
            <p style={{ margin: '5px 0 10px 0', fontSize: '14px', color: '#555' }}>
                ¿Qué tipo deseas?
            </p>
            
            {opciones.map((opcion) => (
                <label key={opcion} style={labelStyle}>
                    <input
                        type="radio"
                        name="saborEmpanada" // Nombre del grupo para asegurar que solo uno sea checked
                        value={opcion}
                        checked={selectedOption === opcion}
                        onChange={(e) => onOptionChange(e.target.value)}
                        style={{ marginRight: '5px' }}
                    />
                    {opcion}
                </label>
            ))}
        </div>
    );
}