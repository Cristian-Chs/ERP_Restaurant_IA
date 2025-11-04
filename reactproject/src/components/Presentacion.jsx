import React from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import './Presentacion.css';
import logo from '../assets/images/logo.jpeg';

function Presentacion() {
  const navigate = useNavigate();

  return (
    <motion.div
      className="presentacion-container"
      initial={{ opacity: 0 }}
      animate={{ opacity: 10 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.5 }}
    >
      <img className="logo" src={logo} alt="Logo" />
      <h1>Bienvenido a 4 Sabores Restaurant 🍽️</h1>
      <button onClick={() => navigate('/Login')} className="btn-comenzar-presentacion">
        Comenzar
      </button>
    </motion.div>
  );
}

export default Presentacion;
