import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Plus, Edit, Trash2, Tag, CheckSquare, X } from 'lucide-react';
import API from '../api/axios';

export default function CouponSection() {
  const [coupons, setCoupons] = useState([]);
  const [redemptions, setRedemptions] = useState([]);
  const [showModal, setShowModal] = useState(false);
  const [editingCoupon, setEditingCoupon] = useState(null);
  const [newCoupon, setNewCoupon] = useState({
    code: '',
    discount_type: 'fixed',
    discount_amount: '',
    points_cost: 0,
    is_active: true,
    valid_from: '',
    valid_until: '',
    max_uses: 0,
    min_order_amount: 0
  });

  useEffect(() => {
    fetchCoupons();
    fetchRedemptions();
  }, []);

  const fetchCoupons = async () => {
    try {
      const res = await API.get('/bot/coupons/');
      setCoupons(res.data);
    } catch (err) {
      console.error('Error fetching coupons:', err);
    }
  };

  const fetchRedemptions = async () => {
    try {
      const res = await API.get('/bot/coupons/redemptions/');
      setRedemptions(res.data);
    } catch (err) {
      console.error('Error fetching redemptions:', err);
    }
  };

  const saveCoupon = async () => {
    try {
      const payload = {
        ...newCoupon,
        discount_amount: parseFloat(newCoupon.discount_amount),
        min_order_amount: parseFloat(newCoupon.min_order_amount || 0),
        points_cost: parseInt(newCoupon.points_cost || 0),
        max_uses: parseInt(newCoupon.max_uses || 0)
      };

      if (editingCoupon) {
        await API.put(`/bot/coupons/${editingCoupon.id}/`, payload);
      } else {
        await API.post('/bot/coupons/', payload);
      }

      setShowModal(false);
      setEditingCoupon(null);
      setNewCoupon({
        code: '',
        discount_type: 'fixed',
        discount_amount: '',
        points_cost: 0,
        is_active: true,
        valid_from: '',
        valid_until: '',
        max_uses: 0,
        min_order_amount: 0
      });
      fetchCoupons();
      alert('✅ Cupón guardado exitosamente');
    } catch (err) {
      console.error('Error saving coupon:', err);
      alert('Error al guardar cupón: ' + (err.response?.data?.error || 'Error desconocido'));
    }
  };

  const deleteCoupon = async (id) => {
    if (window.confirm('¿Seguro que quieres eliminar este cupón?')) {
      try {
        await API.delete(`/bot/coupons/${id}/`);
        fetchCoupons();
        alert('✅ Cupón eliminado');
      } catch (err) {
        console.error('Error deleting coupon:', err);
        alert('Error al eliminar cupón');
      }
    }
  };

  const toggleCouponStatus = async (coupon) => {
    try {
      await API.put(`/bot/coupons/${coupon.id}/`, {
        ...coupon,
        is_active: !coupon.is_active
      });
      fetchCoupons();
    } catch (err) {
      console.error('Error toggling coupon:', err);
    }
  };

  const getUsageColor = (current, max) => {
    if (max === 0) return '#2ecc71';
    const percentage = (current / max) * 100;
    if (percentage >= 100) return '#ff4d4d';
    if (percentage >= 75) return '#f1bc00';
    return '#2ecc71';
  };

  return (
    <div className="admin-section">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <h1 className="section-title">🎟️ Gestión de Cupones</h1>
        <button 
          className="btn-primary" 
          onClick={() => { 
            setEditingCoupon(null); 
            setShowModal(true); 
          }}
        >
          <Plus size={18} /> Nuevo Cupón
        </button>
      </div>

      {/* TABLA DE CUPONES */}
      <div className="admin-table-container" style={{ marginBottom: '2rem' }}>
        <h3 style={{ color: '#fff', marginBottom: '1rem' }}>Cupones Activos e Inactivos</h3>
        <table className="admin-table">
          <thead>
            <tr>
              <th>Código</th>
              <th>Tipo</th>
              <th>Descuento</th>
              <th>Costo (Puntos)</th>
              <th>Uso</th>
              <th>Válido Hasta</th>
              <th>Estado</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {coupons.map(c => (
              <tr key={c.id}>
                <td>
                  <code style={{ 
                    background: '#0d1117', 
                    padding: '4px 8px', 
                    borderRadius: '4px',
                    color: '#58a6ff',
                    fontWeight: 'bold'
                  }}>
                    {c.code}
                  </code>
                </td>
                <td>
                  <span className={`tag tag-${c.discount_type}`}>
                    {c.discount_type === 'fixed' ? 'Fijo' : 'Porcentaje'}
                  </span>
                </td>
                <td>
                  <span style={{ fontWeight: 600, color: '#2ecc71' }}>
                    {c.discount_type === 'fixed' ? `$${c.discount_amount}` : `${c.discount_amount}%`}
                  </span>
                </td>
                <td>
                  {c.points_cost > 0 ? (
                    <span style={{ color: '#f1bc00' }}>💎 {c.points_cost}</span>
                  ) : (
                    <span style={{ color: '#8b949e' }}>Manual</span>
                  )}
                </td>
                <td>
                  <span style={{ color: getUsageColor(c.current_uses, c.max_uses), fontWeight: 'bold' }}>
                    {c.current_uses} / {c.max_uses === 0 ? '∞' : c.max_uses}
                  </span>
                </td>
                <td>
                  {c.valid_until ? (
                    <span style={{ color: '#8b949e', fontSize: '0.9rem' }}>
                      {new Date(c.valid_until).toLocaleDateString('es-ES')}
                    </span>
                  ) : (
                    <span style={{ color: '#8b949e' }}>Sin límite</span>
                  )}
                </td>
                <td>
                  <button
                    onClick={() => toggleCouponStatus(c)}
                    style={{
                      background: c.is_active ? '#238636' : '#8b949e',
                      border: 'none',
                      padding: '4px 12px',
                      borderRadius: '12px',
                      color: '#fff',
                      fontSize: '0.8rem',
                      cursor: 'pointer',
                      fontWeight: 600
                    }}
                  >
                    {c.is_active ? '✅ Activo' : '❌ Inactivo'}
                  </button>
                </td>
                <td>
                  <div className="action-btns">
                    <button 
                      className="btn-icon-styled" 
                      title="Editar"
                      onClick={() => {
                        setEditingCoupon(c);
                        setNewCoupon({...c});
                        setShowModal(true);
                      }}
                    >
                      <Edit size={18} />
                    </button>
                    <button 
                      className="btn-icon-styled btn-danger-text" 
                      title="Eliminar"
                      onClick={() => deleteCoupon(c.id)}
                    >
                      <Trash2 size={18} />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* TABLA DE CANJES */}
      <div className="admin-table-container">
        <h3 style={{ color: '#fff', marginBottom: '1rem' }}>Historial de Canjes</h3>
        <table className="admin-table">
          <thead>
            <tr>
              <th>Cupón</th>
              <th>Usuario (Telegram ID)</th>
              <th>Descuento Aplicado</th>
              <th>Fecha de Canje</th>
              <th>Orden</th>
            </tr>
          </thead>
          <tbody>
            {redemptions.map(r => (
              <tr key={r.id}>
                <td>
                  <code style={{ 
                    background: '#0d1117', 
                    padding: '4px 8px', 
                    borderRadius: '4px',
                    color: '#a371f7'
                  }}>
                    {r.coupon_code}
                  </code>
                </td>
                <td><code>{r.telegram_id}</code></td>
                <td>
                  <span style={{ color: '#2ecc71', fontWeight: 'bold' }}>
                    ${r.discount_applied}
                  </span>
                </td>
                <td style={{ color: '#8b949e', fontSize: '0.9rem' }}>
                  {new Date(r.fecha_canje).toLocaleString('es-ES')}
                </td>
                <td>
                  {r.order_id ? (
                    <span style={{ color: '#58a6ff' }}>#{r.order_id}</span>
                  ) : (
                    <span style={{ color: '#8b949e' }}>-</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* MODAL DE CREACIÓN/EDICIÓN */}
      {showModal && (
        <div className="admin-modal-overlay">
          <div className="admin-modal" style={{ maxWidth: '600px' }}>
            <div className="form-container">
              <h2 className="form-title">
                {editingCoupon ? '✏️ Editar Cupón' : '✨ Nuevo Cupón'}
              </h2>

              <div className="form-group-inline">
                <label>Código del Cupón:</label>
                <input 
                  className="form-input" 
                  placeholder="Ej: PROMO2026" 
                  value={newCoupon.code} 
                  onChange={e => setNewCoupon({...newCoupon, code: e.target.value.toUpperCase()})} 
                />
              </div>

              <div className="form-group-inline">
                <label>Tipo de Descuento:</label>
                <select 
                  className="form-input" 
                  value={newCoupon.discount_type} 
                  onChange={e => setNewCoupon({...newCoupon, discount_type: e.target.value})}
                >
                  <option value="fixed">Descuento Fijo ($)</option>
                  <option value="percentage">Porcentaje (%)</option>
                </select>
              </div>

              <div className="form-group-inline">
                <label>Monto del Descuento:</label>
                <input 
                  className="form-input" 
                  type="number" 
                  step="0.01"
                  placeholder={newCoupon.discount_type === 'fixed' ? '5.00' : '10'} 
                  value={newCoupon.discount_amount} 
                  onChange={e => setNewCoupon({...newCoupon, discount_amount: e.target.value})} 
                />
              </div>

              <div className="form-group-inline">
                <label>Costo en Puntos (0 = manual):</label>
                <input 
                  className="form-input" 
                  type="number" 
                  placeholder="0" 
                  value={newCoupon.points_cost} 
                  onChange={e => setNewCoupon({...newCoupon, points_cost: e.target.value})} 
                />
              </div>

              <div className="form-group-inline">
                <label>Monto Mínimo del Pedido:</label>
                <input 
                  className="form-input" 
                  type="number" 
                  step="0.01"
                  placeholder="0.00" 
                  value={newCoupon.min_order_amount} 
                  onChange={e => setNewCoupon({...newCoupon, min_order_amount: e.target.value})} 
                />
              </div>

              <div className="form-group-inline">
                <label>Usos Máximos (0 = ilimitado):</label>
                <input 
                  className="form-input" 
                  type="number" 
                  placeholder="0" 
                  value={newCoupon.max_uses} 
                  onChange={e => setNewCoupon({...newCoupon, max_uses: e.target.value})} 
                />
              </div>

              <div className="form-group-inline">
                <label>Válido Desde:</label>
                <input 
                  className="form-input" 
                  type="date" 
                  value={newCoupon.valid_from ? newCoupon.valid_from.slice(0, 10) : ''} 
                  onChange={e => setNewCoupon({...newCoupon, valid_from: e.target.value})} 
                />
              </div>

              <div className="form-group-inline">
                <label>Válido Hasta:</label>
                <input 
                  className="form-input" 
                  type="date" 
                  value={newCoupon.valid_until ? newCoupon.valid_until.slice(0, 10) : ''} 
                  onChange={e => setNewCoupon({...newCoupon, valid_until: e.target.value})} 
                />
              </div>

              <div className="form-group-inline">
                <label style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <input 
                    type="checkbox" 
                    checked={newCoupon.is_active} 
                    onChange={e => setNewCoupon({...newCoupon, is_active: e.target.checked})} 
                  />
                  Cupón Activo
                </label>
              </div>

              <div className="form-actions">
                <button className="btn-secondary" onClick={() => setShowModal(false)}>
                  Cancelar
                </button>
                <button className="btn-primary" onClick={saveCoupon}>
                  Guardar
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
