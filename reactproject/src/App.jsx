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
import TelegramButton from './components/TelegramButton';
import KitchenPanel from './pages/KitchenPanel';
import Profile from './pages/Profile';
import ProtectedRoute from './components/ProtectedRoute';

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

  const vaciarCarrito = () => {
    setCarrito([]);
  };

  const totalItems = carrito.reduce((acc, item) => acc + item.cantidad, 0);

  return { carrito, agregarAlCarrito, eliminarDelCarrito, vaciarCarrito, totalItems };
  return { carrito, agregarAlCarrito, eliminarDelCarrito, vaciarCarrito, totalItems };
}

// 🛑 LÓGICA DE SEGUIMIENTO DE PEDIDO
function useOrderTracking() {
  const [activeOrderId, setActiveOrderId] = useState(null);
  const [isOrderReady, setIsOrderReady] = useState(false);

  const startTracking = (id) => {
    console.log("Iniciando seguimiento para orden:", id);
    setActiveOrderId(id);
    setIsOrderReady(false);
  };

  const stopTracking = () => {
    setActiveOrderId(null);
    setIsOrderReady(false);
  };

  React.useEffect(() => {
    if (!activeOrderId) return;

    // Polling cada 10 segundos
    const interval = setInterval(async () => {
       try {
         // Necesitamos importar API o usar fetch. API está en components/CarritoTelegram, 
         // mejor usar fetch directo o importar API si es posible. 
         // Asumiremos que API se puede importar o usar fetch relativo.
         // Backend URL: http://localhost:8000/api/bot/orders/{id}/
         // Ajustar puerto si es necesario.
         
         const response = await fetch(`http://localhost:8000/api/bot/orders/${activeOrderId}/`);
         if (response.ok) {
            const data = await response.json();
            console.log("Polling orden:", data.status);
            if (data.status === 'listo') {
                setIsOrderReady(true);
                // No limpiamos activeOrderId aún para mostrar el modal.
                // El modal limpiará al cerrar.
            }
         }
       } catch (e) {
         console.error("Error polling order:", e);
       }
    }, 10000);

    return () => clearInterval(interval);
  }, [activeOrderId]);

  return { startTracking, stopTracking, isOrderReady };
}

const OrderReadyModal = ({ onClose }) => (
  <div style={{
    position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
    backgroundColor: 'rgba(0,0,0,0.85)', zIndex: 9999,
    display: 'flex', alignItems: 'center', justifyContent: 'center'
  }}>
    <div style={{
      background: '#222', padding: '40px', borderRadius: '16px',
      textAlign: 'center', border: '2px solid #00ff88',
      animation: 'popIn 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275)'
    }}>
      <div style={{fontSize: '60px', marginBottom: '20px'}}>👨‍🍳</div>
      <h2 style={{fontSize: '2rem', color: '#fff', marginBottom: '10px'}}>¡Tu pedido está listo!</h2>
      <p style={{color: '#ccc', marginBottom: '30px', fontSize: '1.1rem'}}>
        Puedes pasar a retirarlo en barra. <br/> ¡Que lo disfrutes!
      </p>
      <button 
        onClick={onClose}
        style={{
          background: '#00ff88', color: '#000', border: 'none',
          padding: '12px 30px', fontSize: '1.1rem', fontWeight: 'bold',
          borderRadius: '50px', cursor: 'pointer',
          boxShadow: '0 4px 15px rgba(0,255,136,0.3)'
        }}
      >
        ¡Gracias!
      </button>
    </div>
    <style>{`
      @keyframes popIn {
        from { transform: scale(0.8); opacity: 0; }
        to { transform: scale(1); opacity: 1; }
      }
    `}</style>
  </div>
);

function AnimatedRoutes({ carrito, agregarAlCarrito, eliminarDelCarrito, vaciarCarrito, startTracking }) { 
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
                      vaciarCarrito={vaciarCarrito}
                      startTracking={startTracking}
                  />} 
        />

        <Route 
          path="/admin" 
          element={
            <ProtectedRoute requiredRole="admin">
              <AdminPanel />
            </ProtectedRoute>
          } 
        />
        <Route path="/register" element={<Register/>} />
        <Route path="/forgot-password" element={<ForgotPassword />} />
        <Route path="/reset-password/:uid/:token" element={<ResetPassword />} />
        
        {/* RUTA DE COCINA (CHEF) */}
        <Route path="/kitchen-panel" element={<KitchenPanel />} />
        
        {/* RUTA DE PERFIL */}
        <Route path="/profile" element={<Profile />} />
      </Routes>
    </AnimatePresence>
  );
}

function CartButtonWrapper({ totalItems }) {
  const location = useLocation();

  const hiddenPaths = ['/', '/carrito', '/login', '/Login', '/admin', '/register', '/forgot-password', '/reset-password', '/kitchen-panel'];
  const shouldHide = hiddenPaths.includes(location.pathname);

  if (shouldHide) {
    return null;
  }

  return <CartButton totalItems={totalItems} />;
}

// ✅ Aquí está la función App completa
function App() {
  const { carrito, agregarAlCarrito, eliminarDelCarrito, vaciarCarrito, totalItems } = useCartLogic();
  const { startTracking, stopTracking, isOrderReady } = useOrderTracking();

  return (
    <Router>
      <AppContent 
        carrito={carrito} 
        agregarAlCarrito={agregarAlCarrito} 
        eliminarDelCarrito={eliminarDelCarrito} 
        vaciarCarrito={vaciarCarrito}
        totalItems={totalItems} 
        startTracking={startTracking}
        isOrderReady={isOrderReady}
        stopTracking={stopTracking}
      />
    </Router>
  );
}

import Navbar from './components/Navbar';

// ✅ Componente hijo que sí puede usar useLocation
function AppContent({ carrito, agregarAlCarrito, eliminarDelCarrito, vaciarCarrito, totalItems, startTracking, isOrderReady, stopTracking }) {
  const location = useLocation();

  // Rutas donde quieres mostrar el fondo aurora
  const showAurora = ['/', '/login', '/Login', '/register', '/forgot-password', '/reset-password', '/profile'].some(path => location.pathname.startsWith(path));

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

      <Navbar />

      <AnimatedRoutes 
        carrito={carrito} 
        agregarAlCarrito={agregarAlCarrito} 
        eliminarDelCarrito={eliminarDelCarrito} 
        vaciarCarrito={vaciarCarrito}
        startTracking={startTracking}
      />

      <CartButtonWrapper totalItems={totalItems} />
      {location.pathname !== '/kitchen-panel' && <TelegramButton />}
      
      {isOrderReady && <OrderReadyModal onClose={stopTracking} />}
    </>
  );
}

export default App;
