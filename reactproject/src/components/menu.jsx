// Menu.jsx

import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import API from '../api/axios'; 

// CRÍTICO: Asegúrate de que la ruta sea correcta
import parsedImages from '../assets/utils/loadImages'; 

import MenuCategorias from './MenuCategorias'; 
import BackButton from './BackButton';
import PlatilloCard from './PlatilloCard'; 
import './Menu.css';

// Componente helper para renderizar una sección del menú
// 🛑 MODIFICADO: Ahora también acepta agregarAlCarrito
const MenuSection = ({ title, items, agregarAlCarrito }) => ( 
  <section>
    <h1>{title}</h1>
    <div className="menu-grid">
      {items && items.length > 0 ? (
        items.map((p, i) => (
          // 🚀 PASAMOS LA FUNCIÓN A PLATILLOCARD
          <PlatilloCard 
                key={p.id || i} 
                {...p} 
                agregarAlCarrito={agregarAlCarrito} 
            />
        ))
      ) : (
        <p>No hay items disponibles en esta categoría.</p>
      )}
    </div>
  </section>
);

// 🛑 MODIFICADO: ACEPTAR 'agregarAlCarrito' COMO PROP
function Menu({ agregarAlCarrito }) { 
  const navigate = useNavigate();
  
  // Estado de la categoría activa (debe estar en minúsculas)
  const [categoriaActiva, setCategoriaActiva] = useState('promociones'); 
  
  // Cambiado a objeto para reflejar la estructura de la API agrupada
  const [allProducts, setAllProducts] = useState({}); 
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);


    // Función de transformación: Convierte la clave de texto 'imagen' a la URL real
    const transformar = (data) =>
      Array.isArray(data)
        ? data.map(p => ({
            ...p, // Pasa name, price, description, ID, etc.
            
            price: parseFloat(p.price),
            // CONVERSIÓN DE IMAGEN
            imagen: parsedImages[p.imagen] || 'https://via.placeholder.com/150',
            
            // Mantiene la categoría en minúsculas
            category: (p.category || 'promociones').toLowerCase(), 
            }))
        : [];


  useEffect(() => {
    
    API.get('/products/') 
      .then(res => {
        
        // LÓGICA CORREGIDA: Procesar el objeto agrupado de la API
        const groupedData = {};
        
        for (const category in res.data) {
            groupedData[category] = transformar(res.data[category]);
        }
        
        setAllProducts(groupedData); // Guardar el objeto agrupado
        setError(null);
      })
      .catch(err => {
        console.error('Error al cargar el menú:', err);
        setError('No se pudo cargar el menú. Por favor, verifica la conexión.');
      })
      .finally(() => {
          setLoading(false);
      });
  }, []); 

  // Lógica de Agrupación (Ahora solo devuelve el objeto ya procesado)
  const menuData = useMemo(() => {
      return allProducts;
  }, [allProducts]);
  
  
  if (loading) return <div className="menu-container"><p>Cargando menú...</p></div>;
  if (error) return <div className="menu-container"><p>{error}</p></div>;


  const renderSeccionActiva = () => {
    // La clave de renderizado siempre en minúsculas
    const activeKey = categoriaActiva.toLowerCase();
    // Accede directamente a la propiedad del objeto 'menuData'
    const items = menuData[activeKey] || []; 
    
    const seccion = (() => {
      switch (activeKey) { // USAMOS LA CLAVE EN MINÚSCULAS
        case 'promociones': return <MenuSection title="Promociones" items={items} agregarAlCarrito={agregarAlCarrito} />; 
        case 'entradas': return <MenuSection title="Entradas" items={items} agregarAlCarrito={agregarAlCarrito} />;
        case 'principales': return <MenuSection title="Principales" items={items} agregarAlCarrito={agregarAlCarrito} />;
        case 'postres': return <MenuSection title="Postres" items={items} agregarAlCarrito={agregarAlCarrito} />;
        case 'bebidas': return <MenuSection title="Bebidas" items={items} agregarAlCarrito={agregarAlCarrito} />;
        default: return <p>Categoría no encontrada.</p>;
      }
    })();

    return (
      <AnimatePresence mode="wait">
        <motion.div
          key={activeKey}
          initial={{ opacity: 0, x: 30 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -30 }}
          transition={{ duration: 0.3 }}
        >
          {seccion}
        </motion.div>
      </AnimatePresence>
    );
  };

  return (
    <motion.div
      className="menu-container"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.5 }}
    >
      <BackButton to="/Login" />
      <MenuCategorias active={categoriaActiva} onSelect={setCategoriaActiva} />
      {renderSeccionActiva()}
    </motion.div>
  );
}

export default Menu;