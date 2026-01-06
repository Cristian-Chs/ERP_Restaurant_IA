import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line, PieChart, Pie, Cell, Legend 
} from 'recharts';
import { 
  LayoutDashboard, ShoppingBag, List, ClipboardList, LogOut, Plus, Edit, Trash2, Brain, Menu, X, CheckSquare, Tag, Users, TrendingUp, Star, Download 
} from 'lucide-react';
import API from '../api/axios';
import './AdminPanel.css';

// Sub-componente para el formulario de producto
const ProductForm = ({ newItem, setNewItem, ingredients, flavors, onSave, onCancel, isEditing }) => (
  <div className="form-container inline">
    <h2 className="form-title">{isEditing ? '✏️ Editar Platillo' : '✨ Nuevo Platillo'}</h2>
    
    <div className="form-group-inline">
      <label>Nombre:</label>
      <input className="form-input" placeholder="Ej: Hamburguesa Especial" value={newItem.name} onChange={e => setNewItem({...newItem, name: e.target.value})} />
    </div>

    <div className="form-group-inline">
      <label>Precio ($):</label>
      <input className="form-input" type="number" placeholder="0.00" value={newItem.price} onChange={e => setNewItem({...newItem, price: e.target.value})} />
    </div>

    <div className="form-group-inline">
      <label>Costo ($):</label>
      <input className="form-input" type="number" placeholder="0.00" value={newItem.cost_price || ''} onChange={e => setNewItem({...newItem, cost_price: e.target.value})} />
    </div>

    <div className="form-group-inline">
      <label>Imagen:</label>
      <div style={{ flex: 1 }}>
        <input className="form-input" placeholder="Nombre de la imagen (ej: pizza.png)" value={newItem.imagen || ''} onChange={e => setNewItem({...newItem, imagen: e.target.value})} />
        <small className="help-text">Ej: burguer.png</small>
      </div>
    </div>

    <div className="form-group-inline">
      <label>Categoría:</label>
      <select className="form-input" value={newItem.category} onChange={e => setNewItem({...newItem, category: e.target.value})}>
        <option value="entradas">Entradas</option>
        <option value="principales">Principales</option>
        <option value="postres">Postres</option>
        <option value="bebidas">Bebidas</option>
        <option value="promociones">Promociones</option>
      </select>
    </div>

    <div className="form-group-inline">
      <label>Descripción:</label>
      <textarea className="form-input" placeholder="Descripción breve..." value={newItem.description} onChange={e => setNewItem({...newItem, description: e.target.value})} />
    </div>

    <div className="form-group">
      <label>Ingredientes:</label>
      <div className="tag-list clickable">
        {ingredients.map(ing => (
          <button 
            key={ing.id} 
            className={`tag-mini ${newItem.ingredientes?.includes(ing.id) ? 'active' : ''}`}
            onClick={(e) => {
              e.preventDefault();
              const updated = newItem.ingredientes?.includes(ing.id) 
                ? newItem.ingredientes.filter(i => i !== ing.id) 
                : [...(newItem.ingredientes || []), ing.id];
              setNewItem({...newItem, ingredientes: updated});
            }}
          >
            {ing.nombre}
          </button>
        ))}
      </div>
    </div>

    <div className="form-group">
      <label>Sabores:</label>
      <div className="tag-list clickable">
        {flavors.map(flav => (
          <button 
            key={flav.id} 
            className={`tag-mini ${newItem.sabores?.includes(flav.id) ? 'active' : ''}`}
            onClick={(e) => {
              e.preventDefault();
              const updated = newItem.sabores?.includes(flav.id) 
                ? newItem.sabores.filter(i => i !== flav.id) 
                : [...(newItem.sabores || []), flav.id];
              setNewItem({...newItem, sabores: updated});
            }}
          >
            {flav.nombre}
          </button>
        ))}
      </div>
    </div>

    <div className="form-actions">
      <button className="btn-secondary" onClick={onCancel}>Cancelar</button>
      <button className="btn-primary" onClick={onSave}>Guardar</button>
    </div>
  </div>
);

export default function AdminPanel() {
  const [activeSection, setActiveSection] = useState('dashboard');
  const [stats, setStats] = useState({ diarias: [], mensuales: [], anuales: [] });
  const [prediction, setPrediction] = useState(null);
  const [products, setProducts] = useState([]);
  const [ingredients, setIngredients] = useState([]);
  const [flavors, setFlavors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const navigate = useNavigate();

  // Form states
  const [showProductModal, setShowProductModal] = useState(false);
  const [showGenericModal, setShowGenericModal] = useState(false); // For Flavors/Ingredients
  const [editingItem, setEditingItem] = useState(null);
  const [newItem, setNewItem] = useState({ 
    name: '', price: '', cost_price: '', category: 'principales', description: '', imagen: '', is_active: true,
    ingredientes: [], sabores: [] 
  });
  const [genericItem, setGenericItem] = useState({ nombre: '', id: null });

  useEffect(() => {
    fetchInitialData();
  }, []);

  const fetchInitialData = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        navigate('/Login');
        return;
      }

      const [statsRes, predictRes, prodRes, ingRes, flavRes] = await Promise.all([
        API.get('/admin/stats/'),
        API.get('/admin/prediction/'),
        API.get('/products-admin/'),
        API.get('/ingredients-admin/'),
        API.get('/flavors-admin/')
      ]);
      setStats(statsRes.data);
      setPrediction(predictRes.data);
      setProducts(prodRes.data || []);
      setIngredients(ingRes.data || []);
      setFlavors(flavRes.data || []);
    } catch (err) {
      console.error("Error al cargar datos de admin", err);
      if (err.response?.status === 401) {
        localStorage.removeItem('token');
        navigate('/Login');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/Login');
  };

  const handleExportPDF = async () => {
    try {
      const response = await API.get('/admin/export/pdf/', { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `Reporte_Financiero_${new Date().toISOString().slice(0, 7)}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.parentNode.removeChild(link);
    } catch (err) {
      console.error("Error downloading PDF", err);
      alert("Error al descargar el reporte PDF");
    }
  };

  // --- CRUD ACTIONS ---
  const saveProduct = async () => {
    try {
      const payload = { ...newItem, price: parseFloat(newItem.price), cost_price: parseFloat(newItem.cost_price || 0) };
      if (editingItem) {
        await API.put(`/products-admin/${editingItem.id}/`, payload);
      } else {
        await API.post('/products-admin/', payload);
      }
      setShowProductModal(false);
      setEditingItem(null);
      setNewItem({ name: '', price: '', category: 'principales', description: '', imagen: '', is_active: true, ingredientes: [], sabores: [] });
      fetchInitialData();
    } catch (err) {
      console.error("Error al guardar producto:", err);
      if (err.response?.status === 401) {
        alert("Tu sesión ha expirado. Por favor, inicia sesión de nuevo.");
        navigate('/Login');
      } else {
        alert("Error al guardar producto: " + (err.response?.data?.detail || "Error desconocido"));
      }
    }
  };

  const saveGeneric = async (type) => {
    try {
      const endpoint = type === 'ingredients' ? '/ingredients-admin/' : '/flavors-admin/';
      if (genericItem.id) {
        await API.put(`${endpoint}${genericItem.id}/`, genericItem);
      } else {
        await API.post(endpoint, genericItem);
      }
      setShowGenericModal(false);
      fetchInitialData();
    } catch (err) {
      alert("Error al guardar");
    }
  };

  const deleteItem = async (type, id) => {
    if (window.confirm("¿Seguro que quieres eliminar este elemento?")) {
      const endpoint = type === 'products' ? '/products-admin/' : (type === 'ingredients' ? '/ingredients-admin/' : '/flavors-admin/');
      await API.delete(`${endpoint}${id}/`);
      fetchInitialData();
    }
  };

  // --- SECTIONS ---

  const renderInsights = () => (
    <div className="admin-section">
      <h1 className="section-title">Inteligencia de Negocio</h1>
      
      <div className="insights-grid">
        <div className="insight-card full-width">
          <h3><Star size={20} color="#f1bc00" /> Top 5 Productos Mas Vendidos y Valorados</h3>
          <div className="insights-table-wrapper">
            <table className="insights-table">
              <thead>
                <tr>
                  <th>Plato</th>
                  <th>Pedidos</th>
                  <th>Rating Promedio</th>
                  <th>Recaudado</th>
                </tr>
              </thead>
              <tbody>
                {stats.top_products?.map((p, i) => (
                  <tr key={i}>
                    <td><strong>{p.item}</strong></td>
                    <td>{p.total_pedidos}</td>
                    <td>
                      <div className="rating-pill">
                        {p.avg_stars} ★
                      </div>
                    </td>
                    <td>${parseFloat(p.recaudado).toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="insight-card full-width">
          <h3><Users size={20} color="#58a6ff" /> Top 5 Clientes VIP (Más Compras)</h3>
          <div className="insights-table-wrapper">
            <table className="insights-table">
              <thead>
                <tr>
                  <th>Telegram ID</th>
                  <th>Total Pedidos</th>
                  <th>Inversión Total</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {stats.top_customers?.map((c, i) => (
                  <tr key={i}>
                    <td><code>{c.telegram_id}</code></td>
                    <td>{c.total_pedidos}</td>
                    <td>${parseFloat(c.total_gastado).toFixed(2)}</td>
                    <td>
                      <span className="customer-badge">Cliente Fiel</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="insight-card full-width">
          <h3><TrendingUp size={20} color="#2ecc71" /> Distribución de Canales (Local vs Para Llevar)</h3>
          <div className="pie-chart-container" style={{ marginTop: '1rem' }}>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={[
                    { name: 'Local (Eat Here)', value: stats.service_breakdown?.HERE || 0 },
                    { name: 'Para Llevar (To Go)', value: stats.service_breakdown?.TOGO || 0 },
                  ]}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={100}
                  paddingAngle={5}
                  dataKey="value"
                >
                  <Cell fill="#00f0ff" />
                  <Cell fill="#00ff88" />
                </Pie>
                <Tooltip 
                  contentStyle={{ backgroundColor: '#161b22', border: '1px solid #30363d', borderRadius: '8px' }}
                  itemStyle={{ color: '#fff' }}
                />
                <Legend iconType="circle" wrapperStyle={{ color: '#fff' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );

  const renderDashboard = () => (
    <div className="admin-section">
      <h1 className="section-title">Panel de Control</h1>

      {/* ✅ MODULO FINANCIERO (NUEVO) */}
      {stats.financial_summary && (
        <div className="financial-module-container" style={{ marginBottom: '2rem', padding: '1.5rem', background: 'linear-gradient(135deg, #1f2428 0%, #161b22 100%)', borderRadius: '12px', border: '1px solid #30363d', boxShadow: '0 4px 6px rgba(0,0,0,0.1)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h2 style={{ fontSize: '1.2rem', color: '#fff', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <TrendingUp size={24} color="#2ecc71" /> Resumen Financiero (Mes Actual)
              <button 
                onClick={handleExportPDF}
                className="btn-icon"
                title="Descargar Reporte PDF"
                style={{ marginLeft: '10px', background: 'rgba(255,255,255,0.1)', border: '1px solid #30363d', color: '#fff' }}
              >
                <Download size={18} />
              </button>
            </h2>
            {stats.reliability_score && (
              <div className="reliability-badge" style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '6px 12px', background: 'rgba(56, 139, 253, 0.15)', border: '1px solid #388bfd', borderRadius: '20px', color: '#58a6ff', fontSize: '0.85rem' }}>
                <Brain size={16} /> 
                <span>Confiabilidad IA: <strong>{stats.reliability_score.score}/100</strong> ({stats.reliability_score.label})</span>
              </div>
            )}
          </div>

          <div className="financial-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1.5rem' }}>
            {/* Dinero Reunido */}
            <div className="fin-card">
              <span className="fin-label" style={{ color: '#8b949e', fontSize: '0.9rem' }}>Dinero Reunido</span>
              <div className="fin-value" style={{ fontSize: '1.8rem', fontWeight: 'bold', color: '#fff' }}>
                ${parseFloat(stats.financial_summary.current_month_revenue).toFixed(2)}
              </div>
              <small style={{ color: '#2ecc71', fontSize: '0.8rem' }}>+ Ingresos Brutos</small>
            </div>

            {/* Impuesto Estimado */}
            <div className="fin-card">
              <span className="fin-label" style={{ color: '#8b949e', fontSize: '0.9rem' }}>Impuesto / Presupuesto (10%)</span>
              <div className="fin-value" style={{ fontSize: '1.8rem', fontWeight: 'bold', color: '#f1bc00' }}>
                ${parseFloat(stats.financial_summary.estimated_tax).toFixed(2)}
              </div>
              <small style={{ color: '#f1bc00', fontSize: '0.8rem' }}>Reserva Sugerida</small>
            </div>

            {/* Utilidad Neta (Estimada) */}
            <div className="fin-card">
              <span className="fin-label" style={{ color: '#8b949e', fontSize: '0.9rem' }}>Dinero Utilizable (Neto)</span>
              <div className="fin-value" style={{ fontSize: '1.8rem', fontWeight: 'bold', color: '#58a6ff' }}>
                ${parseFloat(stats.financial_summary.net_profit).toFixed(2)}
              </div>
              <small style={{ color: '#58a6ff', fontSize: '0.8rem' }}>Disponible Real</small>
            </div>

            {/* Método de Pago Top */}
            <div className="fin-card">
              <span className="fin-label" style={{ color: '#8b949e', fontSize: '0.9rem' }}>Método Frecuente</span>
              <div className="fin-value" style={{ fontSize: '1.4rem', fontWeight: 'bold', color: '#a371f7' }}>
                {stats.financial_summary.top_payment_method}
              </div>
              <small style={{ color: '#a371f7', fontSize: '0.8rem' }}>Más Usado</small>
            </div>
          </div>
        </div>
      )}
      
      <div className="stats-grid">
        <div className="stat-card">
          <span className="stat-label">Total Productos</span>
          <span className="stat-value">{products.length}</span>
        </div>
        <div className="stat-card">
          <span className="stat-label">Ingredientes</span>
          <span className="stat-value">{ingredients.length}</span>
        </div>
        <div className="stat-card">
          <span className="stat-label">Predicción IA (Tendencia)</span>
          <span className="stat-value" style={{ color: prediction?.trend === 'up' ? '#238636' : '#da3633' }}>
            {prediction?.trend === 'up' ? '📈 Alza' : '📉 Baja'}
          </span>
        </div>
      </div>

      <div className="dashboard-charts">
        <div className="chart-container">
          <h3>Ventas por Día (Últimos 30 días)</h3>
          <div className="chart-wrapper">
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={stats.diarias}>
                <CartesianGrid strokeDasharray="3 3" stroke="#30363d" />
                <XAxis dataKey="dia" stroke="#8b949e" tickFormatter={(v) => v ? v.split('T')[0] : ''} />
                <YAxis stroke="#8b949e" />
                <Tooltip 
                  cursor={{ fill: 'rgba(255,255,255,0.05)' }}
                  content={({ active, payload, label }) => {
                    if (active && payload && payload.length) {
                      const dateStr = label ? new Date(label).toLocaleDateString('es-ES', { day: 'numeric', month: 'short', year: 'numeric' }) : '';
                      return (
                        <div style={{ backgroundColor: '#161b22', border: '1px solid #30363d', padding: '12px', borderRadius: '8px', boxShadow: '0 8px 16px rgba(0,0,0,0.5)' }}>
                          <p style={{ color: '#c9d1d9', margin: 0, fontSize: '0.85rem', marginBottom: '4px' }}>📅 {dateStr}</p>
                          <p style={{ color: '#58a6ff', margin: 0, fontSize: '1rem', fontWeight: 'bold' }}>💰 Ventas: ${parseFloat(payload[0].value).toFixed(2)}</p>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                <Bar dataKey="total" fill="#1f6feb" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {prediction && (
          <div className="chart-container">
            <h3 style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <Brain size={20} /> Predicción de Ventas (IA)
            </h3>
            <div className="chart-wrapper">
              {prediction.predicciones_proximos_7_dias && prediction.predicciones_proximos_7_dias.length > 0 ? (
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={prediction.predicciones_proximos_7_dias.map((p, i) => ({ day: i+1, valor: p }))}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#30363d" />
                    <XAxis dataKey="day" stroke="#8b949e" label={{ value: 'Días futuros', position: 'insideBottom', offset: -5 }} />
                    <YAxis stroke="#8b949e" />
                    <Tooltip contentStyle={{ backgroundColor: '#161b22', border: '1px solid #30363d' }} />
                    <Line type="monotone" dataKey="valor" stroke="#ab7df8" strokeWidth={3} />
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <div style={{ height: '300px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', color: '#8b949e', textAlign: 'center', padding: '1rem' }}>
                  <TrendingUp size={48} style={{ marginBottom: '1rem', opacity: 0.5 }} />
                  <p style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: '0.5rem' }}>Recopilando Datos</p>
                  <p style={{ fontSize: '0.9rem', maxWidth: '300px' }}>
                    La IA necesita un historial de ventas de al menos <strong>5 días</strong> para poder generar predicciones precisas.
                  </p>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );

  const renderProducts = () => (
    <div className="admin-section">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <h1 className="section-title">Gestión de Platos</h1>
        <button className="btn-primary" onClick={() => { setEditingItem(null); setShowProductModal(true); }}>
          <Plus size={18} /> Nuevo Platillo
        </button>
      </div>

      <div className="admin-table-container">
        <table className="admin-table">
          <thead>
            <tr>
              <th>Nombre</th>
              <th>Ingredientes</th>
              <th>Sabores</th>
              <th>Precio</th>
              <th>Costo</th>
              <th>Margen</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {products.map(p => (
              <React.Fragment key={p.id}>
                <tr className="product-row">
                  <td>
                    <div className="product-name-cell">
                      <div style={{ fontWeight: 600, color: '#ffffff' }}>{p.name}</div>
                      <div className={`tag tag-${p.category}`} style={{ fontSize: '0.7rem', marginTop: '4px' }}>{p.category}</div>
                    </div>
                  </td>
                  <td>
                    <div className="tag-list mini">
                      {p.ingredientes?.map(id => {
                        const ing = ingredients.find(i => i.id === id);
                        return ing ? <span key={id} className="tag-mini-simple" style={{ color: '#888' }}>• {ing.nombre}</span> : null;
                      })}
                    </div>
                  </td>
                  <td>
                    <div className="tag-list mini">
                      {p.sabores?.map(id => {
                        const flav = flavors.find(f => f.id === id);
                        return flav ? <span key={id} className="tag-mini-simple" style={{ color: '#888' }}>◦ {flav.nombre}</span> : null;
                      })}
                    </div>
                  </td>
                  <td><span style={{ fontWeight: 600, color: '#58a6ff' }}>${p.price}</span></td>
                  <td><span style={{ color: '#8b949e' }}>${p.cost_price || '0.00'}</span></td>
                  <td>
                    {(() => {
                      const margin = parseFloat(p.price) - parseFloat(p.cost_price || 0);
                      const percent = parseFloat(p.price) > 0 ? ((margin / parseFloat(p.price)) * 100).toFixed(0) : 0;
                      return (
                        <span style={{ color: margin > 0 ? '#2ecc71' : '#ff4d4d', fontWeight: 'bold', fontSize: '0.9rem' }}>
                          ${margin.toFixed(2)} ({percent}%)
                        </span>
                      );
                    })()}
                  </td>
                  <td>
                    <div className="action-btns">
                      <button className="btn-icon-styled" title="Editar" onClick={(e) => { 
                        e.stopPropagation();
                        if (editingItem?.id === p.id) {
                          setEditingItem(null);
                          setShowProductModal(false);
                        } else {
                          setEditingItem(p); 
                          setNewItem({...p}); 
                          setShowProductModal(true); 
                        }
                      }}>
                        <Edit size={18} />
                      </button>
                      <button className="btn-icon-styled btn-danger-text" title="Eliminar" onClick={(e) => { e.stopPropagation(); deleteItem('products', p.id); }}>
                        <Trash2 size={18} />
                      </button>
                    </div>
                  </td>
                </tr>
                {/* FORMULARIO INLINE */}
                <AnimatePresence>
                  {showProductModal && editingItem?.id === p.id && (
                    <tr className="inline-edit-row">
                      <td colSpan="5" className="inline-edit-cell">
                        <motion.div 
                          initial={{ opacity: 0, height: 0 }}
                          animate={{ opacity: 1, height: 'auto' }}
                          exit={{ opacity: 0, height: 0 }}
                          className="inline-edit-container"
                        >
                          <ProductForm 
                            newItem={newItem} 
                            setNewItem={setNewItem} 
                            ingredients={ingredients} 
                            flavors={flavors} 
                            onSave={saveProduct} 
                            onCancel={() => { setShowProductModal(false); setEditingItem(null); }}
                            isEditing={true}
                          />
                        </motion.div>
                      </td>
                    </tr>
                  )}
                </AnimatePresence>
              </React.Fragment>
            ))}
          </tbody>
        </table>
      </div>

      {showProductModal && !editingItem && (
        <div className="admin-modal-overlay">
          <div className="admin-modal">
            <ProductForm 
              newItem={newItem} 
              setNewItem={setNewItem} 
              ingredients={ingredients} 
              flavors={flavors} 
              onSave={saveProduct} 
              onCancel={() => setShowProductModal(false)}
              isEditing={false}
            />
          </div>
        </div>
      )}
    </div>
  );

  const renderGenericSection = (type, data) => (
    <div className="admin-section">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <h1 className="section-title">{type === 'ingredients' ? 'Ingredientes' : 'Sabores'}</h1>
        <button className="btn-primary" onClick={() => { setGenericItem({ nombre: '', cost: '', unit: 'und', id: null }); setShowGenericModal(true); }}>
          <Plus size={18} /> Nuevo {type === 'ingredients' ? 'Ingrediente' : 'Sabor'}
        </button>
      </div>
      <div className="admin-table-container">
        <table className="admin-table">
          <thead>
            <tr>
              <th>Nombre</th>
              {type === 'ingredients' && <th>Costo</th>}
              {type === 'ingredients' && <th>Unidad</th>}
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {data.map(item => (
              <React.Fragment key={item.id}>
                <tr>
                  <td>{item.nombre}</td>
                  {type === 'ingredients' && <td>${item.cost}</td>}
                  {type === 'ingredients' && <td><span className="tag-mini-simple">{item.unit === 'kg' ? 'Kg' : (item.unit === 'l' ? 'Litro' : 'Und')}</span></td>}
                  <td>
                    <div style={{ display: 'flex', gap: '10px' }}>
                      <button className="btn-icon" onClick={() => { 
                        if (genericItem?.id === item.id) {
                          setGenericItem({ nombre: '', id: null });
                          setShowGenericModal(false);
                        } else {
                          setGenericItem(item); 
                          setShowGenericModal(true); 
                        }
                      }}>
                        <Edit size={16} />
                      </button>
                      <button className="btn-icon btn-danger-text" onClick={() => deleteItem(type, item.id)}>
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </td>
                </tr>
                {/* FORMULARIO INLINE GENERICO */}
                <AnimatePresence>
                  {showGenericModal && genericItem?.id === item.id && (
                    <tr>
                      <td colSpan={type === 'ingredients' ? "4" : "2"} className="inline-edit-cell">
                        <motion.div 
                          initial={{ opacity: 0, height: 0 }}
                          animate={{ opacity: 1, height: 'auto' }}
                          exit={{ opacity: 0, height: 0 }}
                          className="inline-edit-container"
                        >
                          <div className="form-container inline">
                            <div className="form-group-inline">
                              <label>Nombre:</label>
                              <input 
                                className="form-input" 
                                placeholder="Nombre" 
                                value={genericItem.nombre} 
                                onChange={e => setGenericItem({...genericItem, nombre: e.target.value})} 
                              />
                            </div>
                            {type === 'ingredients' && (
                                <>
                                    <div className="form-group-inline">
                                        <label>Costo ($):</label>
                                        <input 
                                            type="number"
                                            className="form-input" 
                                            placeholder="0.00" 
                                            value={genericItem.cost || ''} 
                                            onChange={e => setGenericItem({...genericItem, cost: e.target.value})} 
                                        />
                                    </div>
                                    <div className="form-group-inline">
                                        <label>Unidad:</label>
                                        <select 
                                            className="form-input" 
                                            value={genericItem.unit || 'und'} 
                                            onChange={e => setGenericItem({...genericItem, unit: e.target.value})}
                                        >
                                            <option value="und">Unidad</option>
                                            <option value="kg">Kilogramo</option>
                                            <option value="l">Litro</option>
                                        </select>
                                    </div>
                                </>
                            )}
                            <div className="form-actions">
                              <button onClick={() => setShowGenericModal(false)} className="btn-secondary">Cancelar</button>
                              <button className="btn-primary" onClick={() => saveGeneric(type)}>Guardar</button>
                            </div>
                          </div>
                        </motion.div>
                      </td>
                    </tr>
                  )}
                </AnimatePresence>
              </React.Fragment>
            ))}
          </tbody>
        </table>
      </div>

      {showGenericModal && !genericItem.id && (
        <div className="admin-modal-overlay">
          <div className="admin-modal" style={{ maxWidth: '500px' }}>
            <h2 className="form-title">✨ Nuevo {type === 'ingredients' ? 'Ingrediente' : 'Sabor'}</h2>
            <div className="form-group-inline">
              <label>Nombre:</label>
              <input 
                className="form-input" 
                placeholder="Nombre" 
                value={genericItem.nombre} 
                onChange={e => setGenericItem({...genericItem, nombre: e.target.value})} 
              />
            </div>
            {type === 'ingredients' && (
                <>
                    <div className="form-group-inline">
                        <label>Costo ($):</label>
                        <input 
                            type="number"
                            className="form-input" 
                            placeholder="0.00" 
                            value={genericItem.cost || ''} 
                            onChange={e => setGenericItem({...genericItem, cost: e.target.value})} 
                        />
                    </div>
                    <div className="form-group-inline">
                        <label>Unidad:</label>
                        <select 
                            className="form-input" 
                            value={genericItem.unit || 'und'} 
                            onChange={e => setGenericItem({...genericItem, unit: e.target.value})}
                        >
                            <option value="und">Unidad</option>
                            <option value="kg">Kilogramo</option>
                            <option value="l">Litro</option>
                        </select>
                    </div>
                </>
            )}
            <div className="form-actions">
              <button onClick={() => setShowGenericModal(false)} className="btn-secondary">Cancelar</button>
              <button className="btn-primary" onClick={() => saveGeneric(type)}>Guardar</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );

  // --- HR MODULE ---
  const [employees, setEmployees] = useState([]);
  const [payments, setPayments] = useState([]);
  const [hrTab, setHrTab] = useState('employees'); // 'employees' | 'payroll'
  const [showEmployeeModal, setShowEmployeeModal] = useState(false);
  const [showPayrollModal, setShowPayrollModal] = useState(false);
  const [newEmployee, setNewEmployee] = useState({ name: '', role: 'WAITER', salary_base: '', phone: '' });
  const [newPayment, setNewPayment] = useState({ employee: '', amount: '', notes: '' });

  const fetchHRData = async () => {
    try {
      const [empRes, payRes] = await Promise.all([
        API.get('/employees/'),
        API.get('/payroll/')
      ]);
      setEmployees(empRes.data);
      setPayments(payRes.data);
    } catch (err) {
      console.error("Error loading HR data", err);
    }
  };

  useEffect(() => {
    if (activeSection === 'hr') {
      fetchHRData();
    }
  }, [activeSection]);

  const saveEmployee = async () => {
    try {
      if (editingItem) {
        await API.put(`/employees/${editingItem.id}/`, newEmployee);
      } else {
        await API.post('/employees/', newEmployee);
      }
      setShowEmployeeModal(false);
      setEditingItem(null);
      setNewEmployee({ name: '', role: 'WAITER', salary_base: '', phone: '' });
      fetchHRData();
    } catch (err) {
      alert("Error saving employee");
    }
  };

  const registerPayment = async () => {
    try {
      if (!newPayment.employee || !newPayment.amount) return alert("Faltan datos");
      await API.post('/payroll/', newPayment);
      setShowPayrollModal(false);
      setNewPayment({ employee: '', amount: '', notes: '' });
      fetchHRData();
    } catch (err) {
      alert("Error registering payment");
    }
  };
  
  const deleteEmployee = async (id) => {
      if(window.confirm("Eliminar empleado?")) {
          await API.delete(`/employees/${id}/`);
          fetchHRData();
      }
  };

  const renderHR = () => (
    <div className="admin-section">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <h1 className="section-title">Recursos Humanos</h1>
        <div style={{ display: 'flex', gap: '10px' }}>
            <button className={`btn-secondary ${hrTab === 'employees' ? 'active-tab' : ''}`} onClick={() => setHrTab('employees')}>Empleados</button>
            <button className={`btn-secondary ${hrTab === 'payroll' ? 'active-tab' : ''}`} onClick={() => setHrTab('payroll')}>Nómina</button>
        </div>
      </div>

      {hrTab === 'employees' && (
        <>
            <button className="btn-primary" style={{marginBottom: '1rem'}} onClick={() => { setEditingItem(null); setNewEmployee({ name: '', role: 'WAITER', salary_base: '', phone: '' }); setShowEmployeeModal(true); }}>
                <Plus size={18} /> Nuevo Empleado
            </button>
            <div className="admin-table-container">
            <table className="admin-table">
                <thead>
                    <tr><th>Nombre</th><th>Rol</th><th>Salario Base</th><th>Teléfono</th><th>Acciones</th></tr>
                </thead>
                <tbody>
                    {employees.map(e => (
                        <tr key={e.id}>
                            <td style={{fontWeight: 'bold'}}>{e.name}</td>
                            <td><span className="tag-mini-simple">{e.role}</span></td>
                            <td>${e.salary_base}</td>
                            <td>{e.phone}</td>
                            <td>
                                <button className="btn-icon" onClick={() => { setEditingItem(e); setNewEmployee(e); setShowEmployeeModal(true); }}><Edit size={16}/></button>
                                <button className="btn-icon btn-danger-text" onClick={() => deleteEmployee(e.id)}><Trash2 size={16}/></button>
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
            </div>
        </>
      )}

      {hrTab === 'payroll' && (
        <>
            <div style={{display: 'flex', justifyContent: 'space-between', marginBottom: '1rem'}}>
                <button className="btn-primary" onClick={() => setShowPayrollModal(true)}>
                    <Plus size={18} /> Registrar Pago
                </button>
                <button className="btn-secondary" onClick={async () => {
                    try {
                        const response = await API.get('/admin/export/payroll-pdf/', { responseType: 'blob' });
                        const url = window.URL.createObjectURL(new Blob([response.data]));
                        const link = document.createElement('a');
                        link.href = url;
                        link.setAttribute('download', `Nomina_Reporte_${new Date().toLocaleDateString()}.pdf`);
                        document.body.appendChild(link);
                        link.click();
                        link.remove();
                    } catch(err) { alert("Error exportando PDF"); }
                }}>
                    <Download size={18} /> Exportar PDF
                </button>
            </div>
            <div className="admin-table-container">
            <table className="admin-table">
                <thead>
                    <tr><th>Fecha</th><th>Empleado</th><th>Monto</th><th>Notas</th></tr>
                </thead>
                <tbody>
                    {payments.map(p => (
                        <tr key={p.id}>
                            <td style={{color: '#888'}}>{p.payment_date}</td>
                            <td style={{fontWeight: 'bold', color: '#fff'}}>{p.employee_name}</td>
                            <td style={{color: '#2ecc71', fontWeight: 'bold'}}>${p.amount}</td>
                            <td>{p.notes}</td>
                        </tr>
                    ))}
                </tbody>
            </table>
            </div>
        </>
      )}

      {/* MODAL EMPLEADO */}
      {showEmployeeModal && (
        <div className="admin-modal-overlay">
          <div className="admin-modal" style={{maxWidth: '400px'}}>
            <h2 className="form-title">{editingItem ? 'Editar Empleado' : 'Nuevo Empleado'}</h2>
            <div className="form-group"><label>Nombre</label><input className="form-input" value={newEmployee.name} onChange={e => setNewEmployee({...newEmployee, name: e.target.value})} /></div>
            <div className="form-group"><label>Rol</label>
                <select className="form-input" value={newEmployee.role} onChange={e => setNewEmployee({...newEmployee, role: e.target.value})}>
                    <option value="CHEF">Chef</option><option value="WAITER">Mesero</option><option value="DELIVERY">Repartidor</option><option value="MANAGER">Gerente</option>
                </select>
            </div>
            <div className="form-group"><label>Salario Base ($)</label><input type="number" className="form-input" value={newEmployee.salary_base} onChange={e => setNewEmployee({...newEmployee, salary_base: e.target.value})} /></div>
            <div className="form-group"><label>Teléfono</label><input className="form-input" value={newEmployee.phone} onChange={e => setNewEmployee({...newEmployee, phone: e.target.value})} /></div>
            <div className="form-actions">
                <button className="btn-secondary" onClick={() => setShowEmployeeModal(false)}>Cancelar</button>
                <button className="btn-primary" onClick={saveEmployee}>Guardar</button>
            </div>
          </div>
        </div>
      )}

      {/* MODAL PAGO */}
      {showPayrollModal && (
        <div className="admin-modal-overlay">
          <div className="admin-modal" style={{maxWidth: '400px'}}>
            <h2 className="form-title">Registrar Pago</h2>
            <div className="form-group"><label>Empleado</label>
                <select className="form-input" value={newPayment.employee} onChange={e => setNewPayment({...newPayment, employee: e.target.value})}>
                    <option value="">Seleccionar...</option>
                    {employees.map(e => <option key={e.id} value={e.id}>{e.name} ({e.role})</option>)}
                </select>
            </div>
            <div className="form-group"><label>Monto ($)</label><input type="number" className="form-input" value={newPayment.amount} onChange={e => setNewPayment({...newPayment, amount: e.target.value})} /></div>
            <div className="form-group"><label>Notas</label><textarea className="form-input" value={newPayment.notes} onChange={e => setNewPayment({...newPayment, notes: e.target.value})} /></div>
            <div className="form-actions">
                <button className="btn-secondary" onClick={() => setShowPayrollModal(false)}>Cancelar</button>
                <button className="btn-primary" onClick={registerPayment}>Registrar</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );

  return (
    <div className={`admin-dashboard ${mobileMenuOpen ? 'sidebar-open' : ''}`}>
      <div className={`admin-sidebar ${mobileMenuOpen ? 'open' : ''}`}>
        <div className="sidebar-title">
          <ClipboardList size={28} /> Admin Sabores
          <button className="mobile-only btn-icon" style={{ marginLeft: 'auto', background: 'transparent', border: 'none', color: 'white' }} onClick={() => setMobileMenuOpen(false)}>
            <X size={24} />
          </button>
        </div>
        <nav className="sidebar-nav">
          <div className={`nav-item ${activeSection === 'dashboard' ? 'active' : ''}`} onClick={() => { setActiveSection('dashboard'); setMobileMenuOpen(false); }}>
            <LayoutDashboard size={20} /> Dashboard
          </div>
          <div className={`nav-item ${activeSection === 'products' ? 'active' : ''}`} onClick={() => { setActiveSection('products'); setMobileMenuOpen(false); }}>
            <ShoppingBag size={20} /> Platos
          </div>
          <div className={`nav-item ${activeSection === 'ingredients' ? 'active' : ''}`} onClick={() => { setActiveSection('ingredients'); setMobileMenuOpen(false); }}>
            <CheckSquare size={20} /> Ingredientes
          </div>
          <div className={`nav-item ${activeSection === 'flavors' ? 'active' : ''}`} onClick={() => { setActiveSection('flavors'); setMobileMenuOpen(false); }}>
            <Tag size={20} /> Sabores
          </div>
          <div className={`nav-item ${activeSection === 'insights' ? 'active' : ''}`} onClick={() => { setActiveSection('insights'); setMobileMenuOpen(false); }}>
            <TrendingUp size={20} /> Inteligencia
          </div>
          <div className={`nav-item ${activeSection === 'hr' ? 'active' : ''}`} onClick={() => { setActiveSection('hr'); setMobileMenuOpen(false); }}>
            <Users size={20} /> Recursos Humanos
          </div>
          <hr style={{ border: '0.5px solid #30363d', margin: '1rem 0' }} />
          <div className="nav-item" onClick={handleLogout} style={{ color: '#da3633' }}>
            <LogOut size={20} /> Cerrar Sesión
          </div>
        </nav>
      </div>

      {mobileMenuOpen && <div className="sidebar-overlay" onClick={() => setMobileMenuOpen(false)}></div>}

      <div className="mobile-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <ClipboardList size={24} color="#58a6ff" />
          <span style={{ fontWeight: 700 }}>Admin Sabores</span>
        </div>
        <button className="btn-icon" onClick={() => setMobileMenuOpen(true)} style={{ background: 'transparent', border: 'none', color: 'white' }}>
          <Menu size={24} />
        </button>
      </div>

      <div className="admin-content">
        {activeSection === 'dashboard' && renderDashboard()}
        {activeSection === 'products' && renderProducts()}
        {activeSection === 'insights' && renderInsights()}
        {activeSection === 'ingredients' && renderGenericSection('ingredients', ingredients)}
        {activeSection === 'flavors' && renderGenericSection('flavors', flavors)}
        {activeSection === 'hr' && renderHR()}
      </div>
    </div>
  );
}
