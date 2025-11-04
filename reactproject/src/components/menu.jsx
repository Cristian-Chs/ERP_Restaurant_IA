// src/components/menu.jsx

import React, { useEffect, useState } from 'react';
import images from '../assets/utils/loadImages';
import { useNavigate } from 'react-router-dom';
import PlatilloCard from './PlatilloCard';
import './Menu.css';
import { motion } from 'framer-motion';
import API from '../api/axios'; // Usamos la instancia con el interceptor
import BackButton from './BackButton'; // Componente reutilizable

// Componente funcional auxiliar para renderizar cada sección del menú
const MenuSection = ({ title, items }) => (
  <section>
    <h1>{title}</h1>
    <div className="menu-grid">
      {items.map((p, i) => (
        // Usamos p.id como key si está disponible en la data del backend, si no, el índice (i)
        <PlatilloCard key={p.id || i} {...p} /> 
      ))}
    </div>
  </section>
);


function Menu() {
  const navigate = useNavigate();

  const [menuData, setMenuData] = useState({
    platillos: [],
    entradas: [],
    principales: [],
    postres: [],
    bebidas: [],
  });

  useEffect(() => {
    const token = localStorage.getItem('token');
    
    // **Validación de seguridad:** si no hay token, redirigir al login.
    if (!token) {
      navigate('/login');
      return;
    }

    // El interceptor en axios.js ya agrega el header Authorization: `Bearer ${token}`
    API.get('/cliente/menu') 
      .then(res => {
        const data = res.data;
        console.log('Respuesta del backend:', data);

        const transformar = (lista) =>
          Array.isArray(lista)
            ? lista.map(p => ({
                ...p,
                // Asigna la imagen cargada o un placeholder por defecto
                imagen: images[p.imagen] || 'https://via.placeholder.com/150' 
              }))
            : [];

        setMenuData({
            platillos: transformar(data.platillos),
            entradas: transformar(data.entradas),
            principales: transformar(data.principales),
            postres: transformar(data.postres),
            bebidas: transformar(data.bebidas),
        });
      })
      .catch(err => {
        console.error('Error al cargar el menú:', err);
        // Si falla la carga del menú (ej. token expirado), redirigir al login
        navigate('/login'); 
      });
  }, [navigate]); // navigate como dependencia del hook

  // Desestructuración para usar en las secciones
  const { platillos, entradas, principales, postres, bebidas } = menuData;

  return (
    <motion.div
      className="menu-container"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.5 }}
    >
      {/* ⬅️ Uso del BackButton unificado */}
      <BackButton to="/Login" />

      {/* 🚀 Renderizado optimizado y sin repeticiones (DRY) */}
      <MenuSection title="Platillos" items={platillos} />
      <MenuSection title="Entradas" items={entradas} />
      <MenuSection title="Principales" items={principales} />
      <MenuSection title="Postres" items={postres} />
      <MenuSection title="Bebidas" items={bebidas} />
    </motion.div>
  );
}

export default Menu;