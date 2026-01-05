import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import './KitchenPanel.css';
import '../components/AuroraBackground.css'; // Reutilizar fondo si se desea, o mantener limpio

/* Modal Styles injected here directly or should be in CSS. 
   Since I can't edit CSS easily without finding it, I will add inline styles or assume CSS file exists. I'll edit the CSS file.
*/

const API_BASE_URL = 'http://localhost:8000/api/bot'; // Ajustado para incluir /api

function KitchenPanel() {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  /* Modal State */
  const [selectedImage, setSelectedImage] = useState(null);

  const openImageModal = (imageUrl) => {
    setSelectedImage(imageUrl);
  };

  const closeImageModal = () => {
    setSelectedImage(null);
  };

  // Función para obtener pedidos
  const fetchOrders = async () => {
    try {
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

  const rejectOrder = async (orderId) => {
    if (!window.confirm("¿Seguro que deseas RECHAZAR este pedido?")) return;

    try {
      const response = await fetch(`${API_BASE_URL}/api/cocina/orders/${orderId}/reject/`, {
        method: 'POST',
      });
      if (response.ok) {
        setOrders(orders.filter(o => o.id !== orderId));
        alert('Pedido RECHAZADO ❌'); 
      } else {
        alert('Error al rechazar pedido');
      }
    } catch (error) {
      console.error('Error rejecting order:', error);
    }
  };

  const localOrders = orders.filter(o => o.service_type === 'Eat Here');
  const externalOrders = orders.filter(o => o.service_type !== 'Eat Here');

  const OrderGrid = ({ title, orderList, icon }) => (
    <div className="orders-section">
      <h2 className="section-title">{icon} {title} ({orderList.length})</h2>
      {orderList.length === 0 ? (
        <p className="no-orders-msg">No hay pedidos en esta sección.</p>
      ) : (
        <div className="orders-grid">
          {orderList.map(order => (
            <div key={order.id} className="order-card-premium">
              <div className="order-card-header">
                <span className="order-id">ORDEN #{order.id}</span>
                <span className="order-timer">{new Date(order.fecha).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</span>
              </div>
              
              <div className="order-logistics-badges">
                <span className={`badge ${order.service_type === 'Eat Here' ? 'here' : 'togo'}`}>
                  {order.service_type === 'Eat Here' ? '🍽️ Local' : '🛍️ Para Llevar'}
                </span>
                {order.delivery_mode !== 'N/A' && (
                  <span className={`badge mode ${order.delivery_mode === 'Delivery' ? 'delivery' : 'pickup'}`}>
                    {order.delivery_mode === 'Delivery' ? '🛵 Domicilio' : '🏪 Retiro'}
                  </span>
                )}
              </div>

              <div className="order-items-content">
                <h3>Detalle del Pedido:</h3>
                <p className="items-list">{order.item}</p>
              </div>

              {order.location !== 'N/A' && (
                <div className="order-location-box">
                  <strong>📍 Entrega en:</strong>
                  <p>{order.location}</p>
                </div>
              )}

              <div className="order-footer">
                <div className="order-total-price">
                  Total: ${parseFloat(order.precio).toFixed(2)}
                </div>
                
                {order.payment_proof && (
                  <button className="view-proof-btn" onClick={() => openImageModal(order.payment_proof)}>
                    🖼️ Ver Pago
                  </button>
                )}

                <div style={{ display: 'flex', gap: '10px' }}>
                  <button 
                    className="reject-btn-glow"
                    onClick={() => rejectOrder(order.id)}
                  >
                    ❌
                  </button>
                  <button 
                    className="mark-ready-btn-glow"
                    onClick={() => markAsReady(order.id)}
                    style={{ flex: 1 }}
                  >
                    LISTO
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );

  return (
    <div className="kitchen-container">
      {/* MODAL OVERLAY */}
      {selectedImage && (
        <div className="modal-overlay" onClick={closeImageModal}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <button className="modal-close-btn" onClick={closeImageModal}>✖</button>
            <img src={`http://localhost:8000${selectedImage}`} alt="Comprobante de Pago" className="modal-image" />
          </div>
        </div>
      )}

      <div className="kitchen-header">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%' }}>
          <h1 className="kitchen-title">Panel de Cocina</h1>
        </div>
        <p>Total pendientes: {orders.length}</p>
      </div>

      {loading ? (
        <div className="kitchen-loader">
          <div className="spinner"></div>
          <p>Sincronizando con Cocina...</p>
        </div>
      ) : (
        <div className="kitchen-sections-wrapper">
          <OrderGrid title="Sección Local (Comer Aquí)" orderList={localOrders} icon="🍽️" />
          <div className="section-divider" />
          <OrderGrid title="Sección Externo (Delivery / Para Llevar)" orderList={externalOrders} icon="🛵" />
        </div>
      )}
    </div>
  );
}

export default KitchenPanel;
