// src/App.jsx

import React, { useState } from 'react'; 
import { BrowserRouter as Router, Routes, Route, useLocation } from 'react-router-dom';
import { AnimatePresence } from 'framer-motion';

// Componentes
import Presentacion from './components/Presentacion';
import CartButton from './components/CartButton';
import Menu from './components/menu'; 
import Carrito from './components/CarritoTelegram'; 
import AuroraBackground from './components/AuroraBackground';
import Login from './pages/Login';
import AdminPanel from './pages/AdminPanel';
import Register from './pages/Register';
import ForgotPassword from './pages/ForgotPassword';
import ResetPassword from './pages/ResetPassword';
import WhatsAppButton from './components/TelegramButton';

// 🛑 LÓGICA DE CARRITO
function useCartLogic() {
  const [carrito, setCarrito] = useState([]);
  
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
  
  const eliminarDelCarrito = (id) => {
    setCarrito(prevCarrito => prevCarrito.filter(item => item.id !== id));
  };

  const totalItems = carrito.reduce((acc, item) => acc + item.cantidad, 0);

  return { carrito, agregarAlCarrito, eliminarDelCarrito, totalItems };
}

function AnimatedRoutes({ carrito, agregarAlCarrito, eliminarDelCarrito }) { 
  const location = useLocation();

  return (
    <AnimatePresence mode="wait">
      <Routes location={location} key={location.pathname}>
        <Route path="/" element={<Presentacion />} />
        <Route path="/Login" element={<Login />} />
        
        {/* RUTA DEL MENÚ */}
        <Route 
          path="/menu" 
          element={<Menu agregarAlCarrito={agregarAlCarrito} />} 
        />
        
        {/* RUTA DEL CARRITO */}
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

function CartButtonWrapper({ totalItems }) {
  const location = useLocation();

  const hiddenPaths = ['/', '/carrito', '/login', '/Login', '/admin', '/register', '/forgot-password', '/reset-password'];
  const shouldHide = hiddenPaths.includes(location.pathname);

  if (shouldHide) {
    return null;
  }

  return <CartButton totalItems={totalItems} />;
}

// ✅ Aquí está la función App completa
function App() {
  const { carrito, agregarAlCarrito, eliminarDelCarrito, totalItems } = useCartLogic();

  return (
    <Router>
      <AppContent 
        carrito={carrito} 
        agregarAlCarrito={agregarAlCarrito} 
        eliminarDelCarrito={eliminarDelCarrito} 
        totalItems={totalItems} 
      />
    </Router>
  );
}

// ✅ Componente hijo que sí puede usar useLocation
function AppContent({ carrito, agregarAlCarrito, eliminarDelCarrito, totalItems }) {
  const location = useLocation();

  // Rutas donde quieres mostrar el fondo aurora
  const showAurora = ['/', '/login', '/Login', '/register'].includes(location.pathname);

  return (
    <>
      {showAurora && (
        <AuroraBackground 
          colorStops={["#BA6E8F", "#da381b", "#f6ff00"]}
          blend={0.5}
          amplitude={1.0}
          speed={1.0}
          canvasBackground="#051F20"
        />
      )}

      <AnimatedRoutes 
        carrito={carrito} 
        agregarAlCarrito={agregarAlCarrito} 
        eliminarDelCarrito={eliminarDelCarrito} 
      />

      <CartButtonWrapper totalItems={totalItems} />
      <WhatsAppButton />
    </>
  );
}

export default App;
