import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import './KitchenPanel.css';
import '../components/AuroraBackground.css'; // Reutilizar fondo si se desea, o mantener limpio

const API_BASE_URL = 'http://localhost:8000/bot'; // Ajustar según entorno

function KitchenPanel() {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  // Función para obtener pedidos
  const fetchOrders = async () => {
    try {
      // Necesitaremos un endpoint JSON para esto. 
      // Por ahora usaremos el endpoint de cocina_panel existente si devuelve JSON, o crearemos uno nuevo.
      // Asumiremos que crearemos un endpoint API específico: /bot/api/cocina/orders/
      const response = await fetch(`${API_BASE_URL}/api/cocina/orders/`);
      if (response.ok) {
        const data = await response.json();
        setOrders(data);
      }
    } catch (error) {
      console.error('Error fetching orders:', error);
    } finally {
      setLoading(false);
    }
  };

  // Polling cada 10 segundos
  useEffect(() => {
    fetchOrders();
    const interval = setInterval(fetchOrders, 10000);
    return () => clearInterval(interval);
  }, []);

  const markAsReady = async (orderId) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/cocina/orders/${orderId}/ready/`, {
        method: 'POST',
      });
      if (response.ok) {
        // Eliminar localmente para feedback inmediato
        setOrders(orders.filter(o => o.id !== orderId));
        alert('¡Pedido marcado como listo! ✅'); // O usar un toast mejor
      } else {
        alert('Error al actualizar pedido');
      }
    } catch (error) {
      console.error('Error marking order:', error);
    }
  };

  return (
    <div className="kitchen-container">
      <div className="kitchen-header">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%' }}>
          <h1 className="kitchen-title">👨‍🍳 Panel de Cocina</h1>
          <button onClick={() => navigate('/profile')} className="ready-btn" style={{ width: 'auto', padding: '0.5rem 1rem' }}>
            👤 Mi Perfil
          </button>
        </div>
        <p>Pedidos pendientes: {orders.length}</p>
      </div>

      {loading ? (
        <p style={{ textAlign: 'center' }}>Cargando pedidos...</p>
      ) : orders.length === 0 ? (
        <div className="no-orders">
          <p>🎉 ¡Todo está limpio! No hay pedidos pendientes.</p>
        </div>
      ) : (
        <div className="orders-grid">
          {orders.map(order => (
            <div key={order.id} className="order-card">
              <div className="order-header">
                <span className="order-id">#{order.id}</span>
                <span className="order-time">{new Date(order.fecha).toLocaleTimeString()}</span>
              </div>
              <div className="order-item">
                {order.item}
              </div>
              <div className="order-client">
                Cliente: {order.telegram_id}
              </div>
              <button 
                className="ready-btn"
                onClick={() => markAsReady(order.id)}
              >
                ✅ LISTO
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default KitchenPanel;
