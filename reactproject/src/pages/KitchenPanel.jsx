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
  const [activeTab, setActiveTab] = useState('COCINA'); // COCINA, CAJA
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

  // Polling cada 8 segundos
  useEffect(() => {
    fetchOrders();
    const interval = setInterval(fetchOrders, 8000);
    return () => clearInterval(interval);
  }, []);

  const markAsReady = async (orderId) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/cocina/orders/${orderId}/ready/`, {
        method: 'POST',
      });
      if (response.ok) {
        setOrders(orders.filter(o => o.id !== orderId));
        alert('¡Pedido marcado como listo! ✅');
      } else {
        alert('Error al actualizar pedido');
      }
    } catch (error) {
      console.error('Error marking order:', error);
    }
  };

  const approvePayment = async (orderId) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/cocina/orders/${orderId}/approve-payment/`, {
        method: 'POST',
      });
      if (response.ok) {
        alert('¡Pago APROBADO! El pedido se movió a Cocina. ✅');
        fetchOrders(); // Recargar para ver el cambio
      }
    } catch (error) {
      console.error('Error approving payment:', error);
    }
  };

  const rejectPayment = async (orderId) => {
    if (!window.confirm("¿Rechazar comprobante de pago? El cliente será notificado.")) return;
    try {
      const response = await fetch(`${API_BASE_URL}/api/cocina/orders/${orderId}/reject-payment/`, {
        method: 'POST',
      });
      if (response.ok) {
        alert('Pago rechazado. ❌');
        fetchOrders();
      }
    } catch (error) {
      console.error('Error rejecting payment:', error);
    }
  };

  // 🧪 Lógica de Filtrado por Pestaña
  // CAJA: Pedidos Externos con pago enviado pero NO aprobado aún.
  const cajaOrders = orders.filter(o => 
    o.payment_status === 'payment_submitted' && o.service_type !== 'HERE'
  );

  // COCINA: Pedidos aprobados O pedidos locales (Comer Aquí)
  const cocinaOrders = orders.filter(o => 
    o.payment_status === 'payment_approved' || o.service_type === 'HERE'
  );

  const OrderGrid = ({ title, orderList, icon, isCaja = false }) => (
    <div className="orders-section">
      <h2 className="section-title">{icon} {title} ({orderList.length})</h2>
      {orderList.length === 0 ? (
        <p className="no-orders-msg">No hay pedidos pendientes en esta sección.</p>
      ) : (
        <div className="orders-grid">
          {orderList.map(order => (
            <div key={order.id} className="order-card-premium">
              <div className="order-card-header">
                <span className="order-id">ORDEN #{order.id}</span>
                <span className="order-timer">{new Date(order.fecha).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</span>
              </div>
              
              <div className="order-logistics-badges">
                <span className={`badge ${order.service_type === 'HERE' ? 'here' : 'togo'}`}>
                  {order.service_type_display}
                </span>
                {order.delivery_mode !== 'N/A' && (
                  <span className={`badge mode ${order.delivery_mode === 'Delivery' ? 'delivery' : 'pickup'}`}>
                    {order.delivery_mode}
                  </span>
                )}
              </div>

              <div className="order-items-content">
                <h3>Detalle del Pedido:</h3>
                <p className="items-list">{order.item}</p>
              </div>

              {order.location !== 'N/A' && (
                <div className="order-location-box">
                  <strong>📍 Entrega:</strong> {order.location}
                </div>
              )}

              <div className="order-footer">
                <div className="order-total-price">
                  Total: ${parseFloat(order.precio).toFixed(2)}
                </div>
                
                {isCaja ? (
                  <div className="caja-actions">
                    {order.payment_proof && (
                      <div className="payment-thumbnail-preview" onClick={() => openImageModal(order.payment_proof)}>
                        <img src={`http://localhost:8000${order.payment_proof}`} alt="Miniatura de pago" />
                        <span className="expand-hint">🔍 Ampliar Comprobante</span>
                      </div>
                    )}
                    <div style={{ display: 'flex', gap: '10px', marginTop: '10px' }}>
                      <button className="reject-btn-glow" onClick={() => rejectPayment(order.id)}>RECHAZAR</button>
                      <button className="mark-ready-btn-glow" onClick={() => approvePayment(order.id)} style={{ flex: 1 }}>
                        APROBAR PAGO
                      </button>
                    </div>
                  </div>
                ) : (
                  <div style={{ display: 'flex', gap: '10px' }}>
                    <button className="mark-ready-btn-glow" onClick={() => markAsReady(order.id)} style={{ flex: 1 }}>
                      MARCAR COMO LISTO ✅
                    </button>
                  </div>
                )}
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
        <h1 className="kitchen-title">Panel de Control</h1>
        
        {/* TABS SELECTOR */}
        <div className="kitchen-tabs">
          <button 
            className={`tab-btn ${activeTab === 'COCINA' ? 'active' : ''}`}
            onClick={() => setActiveTab('COCINA')}
          >
            👨‍🍳 COCINA <span className="tab-count">{cocinaOrders.length}</span>
          </button>
          <button 
            className={`tab-btn ${activeTab === 'CAJA' ? 'active' : ''}`}
            onClick={() => setActiveTab('CAJA')}
          >
            💸 CAJA <span className="tab-count">{cajaOrders.length}</span>
          </button>
        </div>
      </div>

      {loading ? (
        <div className="kitchen-loader">
          <div className="ai-spinner"></div>
          <p>Sincronizando...</p>
        </div>
      ) : (
        <div className="kitchen-sections-wrapper">
          {activeTab === 'COCINA' ? (
            <OrderGrid title="Pedidos para Preparar" orderList={cocinaOrders} icon="🍽️" />
          ) : (
            <OrderGrid title="Pagos por Verificar" orderList={cajaOrders} icon="🔍" isCaja={true} />
          )}
        </div>
      )}
    </div>
  );
}

export default KitchenPanel;
