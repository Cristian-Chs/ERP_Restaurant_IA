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



useEffect(() => {
  document.body.classList.add('menu-background');
  return () => {
    document.body.classList.remove('menu-background');
  };
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

    const seccion = (() => {
      switch (activeKey) {
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
      <div className="menu-header-actions">
        <BackButton to="/Login" />
        <Link to="/profile" className="profile-btn-link">👤 Mi Perfil</Link>
      </div>
      <MenuCategorias active={categoriaActiva} onSelect={setCategoriaActiva} />
      {renderSeccionActiva()}
    </motion.div>
  );
}

export default Menu;
