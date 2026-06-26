import React, { useState, useEffect } from 'react';
import './KitchenPanel.css';
import '../components/AuroraBackground.css'; // Reutilizar fondo si se desea, o mantener limpio

/* Modal Styles injected here directly or should be in CSS. 
   Since I can't edit CSS easily without finding it, I will add inline styles or assume CSS file exists. I'll edit the CSS file.
*/

import API from '../api/axios';

function KitchenPanel() {
  const [orders, setOrders] = useState([]);
  const [allPayments, setAllPayments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('COCINA'); // COCINA, CAJA, PAGOS
  const [selectedImage, setSelectedImage] = useState(null);

  const openImageModal = (imageUrl) => {
    if (imageUrl && !imageUrl.startsWith('http')) {
        setSelectedImage(`http://localhost:8000${imageUrl}`);
    } else {
        setSelectedImage(imageUrl);
    }
  };

  const closeImageModal = () => setSelectedImage(null);

  const [tables, setTables] = useState([]);

  const fetchOrders = async () => {
    try {
      const res = await API.get('/bot/api/cocina/orders/');
      setOrders(res.data);
    } catch (error) {
      console.error('Error fetching orders:', error);
    }
  };

  const fetchAllPayments = async () => {
    try {
      const res = await API.get('/bot/api/cocina/payments/');
      setAllPayments(res.data);
    } catch (error) {
      console.error('Error fetching payments:', error);
    }
  };

  const fetchTables = async () => {
    try {
      const res = await API.get('/tables/');
      setTables(res.data);
    } catch (error) {
      console.error('Error fetching tables:', error);
    }
  };

  const toggleTable = async (id, currentStatus) => {
    try {
      await API.patch(`/tables/${id}/`, { is_occupied: !currentStatus });
      fetchTables();
    } catch (error) {
      console.error('Error toggling table:', error);
    }
  };

  // Polling cada 8 segundos
  useEffect(() => {
    const fetchData = async () => {
        setLoading(true);
        await Promise.all([fetchOrders(), fetchAllPayments(), fetchTables()]);
        setLoading(false);
    };
    fetchData();
    
    const interval = setInterval(async () => {
        await Promise.all([fetchOrders(), fetchAllPayments(), fetchTables()]);
    }, 8000);
    return () => clearInterval(interval);
  }, []);

  const markAsReady = async (orderId) => {
    try {
      await API.post(`/bot/api/cocina/orders/${orderId}/ready/`);
      setOrders(prev => prev.filter(o => o.id !== orderId));
      alert('¡Pedido marcado como listo!');
    } catch (error) {
      console.error('Error marking order:', error);
      alert('Error al actualizar pedido');
    }
  };

  const approvePayment = async (orderId) => {
    try {
      await API.post(`/bot/api/cocina/orders/${orderId}/approve-payment/`);
      alert('¡Pago APROBADO! El pedido se movió a Cocina.');
      fetchOrders();
    } catch (error) {
      console.error('Error approving payment:', error);
    }
  };

  const rejectPayment = async (orderId) => {
    if (!window.confirm("¿Rechazar comprobante de pago? El cliente será notificado.")) return;
    try {
      await API.post(`/bot/api/cocina/orders/${orderId}/reject-payment/`);
      alert('Pago rechazado.');
      fetchOrders();
    } catch (error) {
      console.error('Error rejecting payment:', error);
    }
  };

  //  Lógica de Filtrado por Pestaña
  // CAJA: Pedidos Externos con pago enviado pero NO aprobado aún (incluye sospecha de fraude)
  const cajaOrders = orders.filter(o => 
    (o.payment_status === 'payment_submitted' || o.status === 'fraude_sospecha') && o.service_type !== 'HERE'
  );

  // COCINA: Pedidos aprobados O pedidos locales (Comer Aquí)
  const cocinaOrders = orders.filter(o => 
    o.payment_status === 'payment_approved' || o.service_type === 'HERE'
  );

  const TablesGrid = () => (
      <div className="orders-section">
          <h2 className="section-title">Disponibilidad de Mesas</h2>
          <div className="tables-grid-container" style={{ display: 'flex', gap: '20px', flexWrap: 'wrap', padding: '20px' }}>
              {tables.map(table => (
                  <div 
                    key={table.id} 
                    onClick={() => toggleTable(table.id, table.is_occupied)}
                    style={{
                        width: '120px',
                        height: '120px',
                        borderRadius: '15px',
                        backgroundColor: table.is_occupied ? '#ff4b4b' : '#2ecc71',
                        display: 'flex',
                        flexDirection: 'column',
                        justifyContent: 'center',
                        alignItems: 'center',
                        cursor: 'pointer',
                        boxShadow: '0 4px 15px rgba(0,0,0,0.3)',
                        transition: 'transform 0.2s',
                        border: '2px solid rgba(255,255,255,0.1)'
                    }}
                    onMouseEnter={(e) => e.currentTarget.style.transform = 'scale(1.05)'}
                    onMouseLeave={(e) => e.currentTarget.style.transform = 'scale(1)'}
                  >
                      <span style={{ fontSize: '2rem', fontWeight: 'bold' }}>{table.number}</span>
                      <span style={{ marginTop: '5px', fontSize: '0.9rem' }}>
                          {table.is_occupied ? 'OCUPADA' : 'LIBRE'}
                      </span>
                  </div>
              ))}
          </div>
          <p style={{ marginTop: '10px', opacity: 0.7, paddingLeft: '20px' }}>* Click en la mesa para cambiar estado</p>
      </div>
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
                <span className="order-id">#{order.id}</span>
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
                  <strong>Entrega:</strong> {order.location}
                </div>
              )}

              {order.status === 'fraude_sospecha' && (
                <div className="fraud-alert-box">
                  ALERTA: AUTODETECCIÓN DE FRAUDE
                  {order.payment_data?.fraud_error && <p>{order.payment_data.fraud_error}</p>}
                </div>
              )}

              <div className="order-footer">
                <div className="order-total-price">
                  Total: {order.currency === 'USD' ? '$' : 'Bs. '}
                  {(parseFloat(order.precio) * (order.currency === 'VES' ? parseFloat(order.exchange_rate || 1) : 1)).toFixed(2)}
                  {order.currency === 'VES' && (
                    <small className="rate-badge"> (Tasa: {order.exchange_rate})</small>
                  )}
                </div>
                
                {isCaja ? (
                  <div className="caja-actions">
                    {order.payment_proof && (
                      <div className="payment-thumbnail-preview" onClick={() => openImageModal(order.payment_proof)}>
                        <img src={`http://localhost:8000${order.payment_proof}`} alt="Miniatura de pago" />
                        <span className="expand-hint">Ampliar Comprobante</span>
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
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px', width: '100%' }}>
                    <button className="mark-ready-btn-glow" onClick={() => markAsReady(order.id)} style={{ flex: 1, minWidth: '150px' }}>
                      MARCAR COMO LISTO
                    </button>
                    {(order.payment_status === 'payment_approved' || order.service_type === 'HERE') && (
                      <a 
                        href={`http://localhost:8000/api/bot/invoices/${order.id}/`} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="mark-ready-btn-glow" 
                        style={{ flex: 1, minWidth: '150px', background: '#2ecc71', color: 'white', textDecoration: 'none', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
                      >
                        VER FACTURA
                      </a>
                    )}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );

  const PaymentHistoryGrid = () => (
    <div className="orders-section">
      <h2 className="section-title">Historial de Pagos Realizados ({allPayments.length})</h2>
      {allPayments.length === 0 ? (
        <p className="no-orders-msg">No hay pagos registrados en el sistema.</p>
      ) : (
        <div className="payments-audit-table-container">
          <table className="audit-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Fecha</th>
                <th>Monto</th>
                <th>Estado</th>
                <th>Comprobante</th>
                <th>Análisis OCR (Riesgo)</th>
              </tr>
            </thead>
            <tbody>
              {allPayments.map(p => (
                <tr key={p.id} className={p.is_suspicious ? 'row-suspicious' : ''}>
                  <td>#{p.id}</td>
                  <td>{new Date(p.fecha).toLocaleString()}</td>
                  <td><strong>${p.precio}</strong> {p.currency}</td>
                  <td>
                    <span className={`status-pill ${p.payment_status}`}>
                      {p.payment_status === 'payment_approved' ? 'Aprobado' : 
                       p.payment_status === 'payment_submitted' ? 'Pendiente' : 'Rechazado'}
                    </span>
                  </td>
                  <td>
                    {p.payment_proof && (
                      <button className="view-mini-btn" onClick={() => openImageModal(p.payment_proof)}>
                        Ver Imagen
                      </button>
                    )}
                  </td>
                  <td>
                    {p.is_suspicious ? (
                      <span className="fraud-tag-high">RIESGO: {p.fraud_reason}</span>
                    ) : (
                      <span className="fraud-tag-low">Verificado</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
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
            <button className="modal-close-btn" onClick={closeImageModal}>X</button>
            <img src={selectedImage} alt="Comprobante de Pago" className="modal-image" />
          </div>
        </div>
      )}

      <div className="kitchen-header">
        
        {/* TABS SELECTOR */}
        <div className="kitchen-tabs">
          <button 
            className={`tab-btn ${activeTab === 'COCINA' ? 'active' : ''}`}
            onClick={() => setActiveTab('COCINA')}
          >
            COCINA <span className="tab-count">{cocinaOrders.length}</span>
          </button>
          <button 
            className={`tab-btn ${activeTab === 'CAJA' ? 'active' : ''}`}
            onClick={() => setActiveTab('CAJA')}
          >
            CAJA <span className="tab-count">{cajaOrders.length}</span>
          </button>
          <button 
            className={`tab-btn ${activeTab === 'PAGOS' ? 'active' : ''}`}
            onClick={() => setActiveTab('PAGOS')}
          >
            HISTORIAL DE PAGOS <span className="tab-count">{allPayments.length}</span>
          </button>
          <button 
            className={`tab-btn ${activeTab === 'MESAS' ? 'active' : ''}`}
            onClick={() => setActiveTab('MESAS')}
          >
            MESAS 
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
          {activeTab === 'COCINA' && <OrderGrid title="Pedidos para Preparar" orderList={cocinaOrders} icon="" />}
          {activeTab === 'CAJA' && <OrderGrid title="Pagos por Verificar" orderList={cajaOrders} icon="" isCaja={true} />}
          {activeTab === 'PAGOS' && <PaymentHistoryGrid />}
          {activeTab === 'MESAS' && <TablesGrid />}
        </div>
      )}
    </div>
  );
}

export default KitchenPanel;
