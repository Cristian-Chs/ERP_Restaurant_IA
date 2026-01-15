import React, { useEffect, useState, useMemo } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import API from '../api/axios';
import parsedImages from '../assets/utils/loadImages';

import MenuCategorias from './MenuCategorias';
import BackButton from './BackButton';
import PlatilloCard from './PlatilloCard';
import './Menu.css';

const MenuSection = ({ title, items, agregarAlCarrito }) => (
  <section>
    <h1>{title}</h1>
    <div className="menu-grid">
      {items && items.length > 0 ? (
        items.map((p, i) => (
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

function Menu({ agregarAlCarrito }) {
  const navigate = useNavigate();
  const [categoriaActiva, setCategoriaActiva] = useState('promociones');
  const [allProducts, setAllProducts] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [exchangeRate, setExchangeRate] = useState(35); // Default fallback

  useEffect(() => {
    API.get('/currency/rates/')
      .then(res => {
        if (res.data && res.data.VES) {
          setExchangeRate(res.data.VES);
        }
      })
      .catch(e => console.error("Error fetching rates", e));
  }, []);



// El fondo se maneja ahora via CSS en .menu-grid
useEffect(() => {
  // Solo si necesitas alguna lógica de montaje específica
}, []);


  const transformar = (data) =>
    Array.isArray(data)
      ? data.map(p => ({
          ...p,
          price: parseFloat(p.price),
          imagen: parsedImages[p.imagen] || 'https://via.placeholder.com/150',
          category: (p.category || 'promociones').toLowerCase(),
        }))
      : [];

  useEffect(() => {
    API.get('/products/')
      .then(res => {
        const groupedData = {};
        for (const category in res.data) {
          groupedData[category] = transformar(res.data[category]);
        }
        setAllProducts(groupedData);
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

  const menuData = useMemo(() => allProducts, [allProducts]);

  if (loading) return <div className="menu-container"><p>Cargando menú...</p></div>;
  if (error) return <div className="menu-container"><p>{error}</p></div>;

  const renderSeccionActiva = () => {
    const activeKey = categoriaActiva.toLowerCase();
    const items = menuData[activeKey] || [];

    return (
      <div className="menu-grid-wrapper">
        <div className="menu-grid">
          <AnimatePresence mode="wait">
            <motion.div
              key={activeKey}
              className="menu-section-content"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.2 }}
            >
              <h1 className="menu-section-title">
                {activeKey.charAt(0).toUpperCase() + activeKey.slice(1)}
              </h1>
              <div className="menu-items-container">
                {items && items.length > 0 ? (
                  items.map((p, i) => (
                    <PlatilloCard 
                      key={p.id || i} 
                      {...p} 
                      agregarAlCarrito={agregarAlCarrito} 
                      exchangeRate={exchangeRate}
                    />
                  ))
                ) : (
                  <p className="no-items">No hay items disponibles en esta categoría.</p>
                )}
              </div>
            </motion.div>
          </AnimatePresence>
        </div>
      </div>
    );
  };

  return (
    <motion.div 
      className="menu-container"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
    >
      <div className="menu-header-actions" style={{ marginBottom: '20px' }}>
        {/* El Navbar global ya maneja la navegación. Dejamos el espacio o ajustes si es necesario */}
      </div>
      <MenuCategorias active={categoriaActiva} onSelect={setCategoriaActiva} />
      {renderSeccionActiva()}
    </motion.div>
  );
}

export default Menu;
