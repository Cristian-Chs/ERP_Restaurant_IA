// MenuCategorias.jsx - CORREGIDO

import React from 'react';
import { motion } from 'framer-motion';
import './MenuCategorias.css';

// Las categorías se pueden mantener en Mayúscula/Minúscula para la visualización
const categorias = ['Promociones', 'Entradas', 'Principales', 'Postres', 'Bebidas']; 
// Nota: 'Platillos' debe ser renombrado a 'Promociones' si no existe la clave 'platillos' en tu API.

export default function MenuCategorias({ active, onSelect }) {
  return (
    <div className="categorias-container">
      {categorias.map((cat) => (
        <motion.button
          key={cat}
            // 🚨 SOLUCIÓN 1: Normalizar la comparación a minúsculas
          className={`categoria-btn ${active.toLowerCase() === cat.toLowerCase() ? 'active' : ''}`}
            // 🚨 SOLUCIÓN 2: Asegurar que el estado SÓLO guarde minúsculas
          onClick={() => onSelect(cat.toLowerCase())} 
          whileTap={{ scale: 0.95 }}
          whileHover={{ scale: 1.05 }}
          transition={{ type: 'spring', stiffness: 300 }}
        >
          {cat}
        </motion.button>
      ))}
    </div>
  );
}