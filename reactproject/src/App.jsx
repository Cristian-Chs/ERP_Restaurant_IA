// src/App.jsx - VERIFICADO Y CORREGIDO

import React, { useState } from 'react'; 
import { BrowserRouter as Router, Routes, Route, useLocation } from 'react-router-dom';
import { AnimatePresence } from 'framer-motion';

// Componentes
import Presentacion from './components/Presentacion';
import CartButton from './components/CartButton';
import Menu from './components/menu'; // 
import Carrito from './components/CarritoTelegram'; // Importar Carrito.jsx
import AuroraBackground from './components/AuroraBackground';
import Login from './pages/Login';
import AdminPanel from './pages/AdminPanel';
import Register from './pages/Register';
import ForgotPassword from './pages/ForgotPassword';
import ResetPassword from './pages/ResetPassword';
import WhatsAppButton from './components/TelegramButton';


// 🛑 LÓGICA DE CARRITO - CORREGIDA Y ÚNICA DEFINICIÓN
function useCartLogic() {
    const [carrito, setCarrito] = useState([]);
    
    // Función para añadir o aumentar la cantidad de un producto
    const agregarAlCarrito = (producto) => {
        setCarrito(prevCarrito => {
            const existe = prevCarrito.find(item => item.id === producto.id);

            if (existe) {
                return prevCarrito.map(item =>
                    item.id === producto.id
                        ? { ...item, cantidad: item.cantidad + 1 }
                        : item
                );
            } else {
                return [...prevCarrito, { ...producto, cantidad: 1 }];
            }
        });
    };
    
    // Función para eliminar un item completamente
    const eliminarDelCarrito = (id) => {
        setCarrito(prevCarrito => prevCarrito.filter(item => item.id !== id));
    };

    // 🚀 Cálculo del total de artículos para el indicador visual
    const totalItems = carrito.reduce((acc, item) => acc + item.cantidad, 0);

    // 🚀 Retornar todas las piezas necesarias (carrito, funciones y el contador)
    return { carrito, agregarAlCarrito, eliminarDelCarrito, totalItems };
}


function AnimatedRoutes({ carrito, agregarAlCarrito, eliminarDelCarrito }) { 
  const location = useLocation();

  return (
    <AnimatePresence mode="wait">
      <Routes location={location} key={location.pathname}>
      <Route path="/" element={<Presentacion />} />
      <Route path="/Login" element={<Login />} />
      
        {/* RUTA DEL MENÚ: PASAR FUNCIÓN PARA AGREGAR */}
      <Route 
            path="/menu" 
            element={<Menu agregarAlCarrito={agregarAlCarrito} />} 
        />
        
        {/* RUTA DEL CARRITO: PASAR ESTADO Y FUNCIÓN PARA ELIMINAR/ACTUALIZAR */}
        <Route 
            path="/carrito" 
            element={<Carrito 
                        carrito={carrito} 
                        eliminarDelCarrito={eliminarDelCarrito} 
                    />} 
        />

      <Route path="/admin" element={<AdminPanel />} />
      <Route path="/register" element={<Register/>} />
      <Route path="/forgot-password" element={<ForgotPassword />} />
      <Route path="/reset-password/:token" element={<ResetPassword />} />
      </Routes>

    </AnimatePresence>
  );
}


function App() {
    // 4. Inicializar la lógica del carrito (Recibiendo totalItems)
    const { carrito, agregarAlCarrito, eliminarDelCarrito, totalItems } = useCartLogic();

  return (
    <Router>
      <AuroraBackground 
    colorStops={["#BA6E8F", "#da381b", "#f6ff00"]}
    //colorStops={["#f6ff00", "#0008ff", "#FF3232"]}
    blend={0.5}
    amplitude={1.0}
    speed={1.0}/>
      
        {/* 5. Pasar las props a AnimatedRoutes */}
      <AnimatedRoutes 
            carrito={carrito} 
            agregarAlCarrito={agregarAlCarrito} 
            eliminarDelCarrito={eliminarDelCarrito} 
        />
        {/* 🚀 Mostrar el botón flotante del carrito */}
        <CartButtonWrapper totalItems={totalItems} />

      <WhatsAppButton />
    </Router>
  );
}

function CartButtonWrapper({ totalItems }) {
const location = useLocation();

  // 🛑 Rutas donde NO debe aparecer
const hiddenPaths = ['/', '/carrito', '/Login', '/admin', '/register', '/forgot-password', '/reset-password'];

  // Comparación exacta
const shouldHide = hiddenPaths.includes(location.pathname);

if (shouldHide) {
    return null;
}

return <CartButton totalItems={totalItems} />;
}


export default App;
