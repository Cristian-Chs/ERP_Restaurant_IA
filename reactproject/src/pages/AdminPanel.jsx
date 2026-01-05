import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line, PieChart, Pie, Cell, Legend 
} from 'recharts';
import { 
  LayoutDashboard, ShoppingBag, List, ClipboardList, LogOut, Plus, Edit, Trash2, Brain, Menu, X, CheckSquare, Tag, Users, TrendingUp, Star 
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
    name: '', price: '', category: 'principales', description: '', imagen: '', is_active: true,
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

  // --- CRUD ACTIONS ---
  const saveProduct = async () => {
    try {
      const payload = { ...newItem, price: parseFloat(newItem.price) };
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
                <Tooltip contentStyle={{ backgroundColor: '#161b22', border: '1px solid #30363d' }} />
                <Bar dataKey="total" fill="#1f6feb" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {prediction?.predicciones_proximos_7_dias && (
          <div className="chart-container">
            <h3 style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <Brain size={20} /> Predicción de Ventas (IA)
            </h3>
            <div className="chart-wrapper">
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={prediction.predicciones_proximos_7_dias.map((p, i) => ({ day: i+1, valor: p }))}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#30363d" />
                  <XAxis dataKey="day" stroke="#8b949e" label={{ value: 'Días futuros', position: 'insideBottom', offset: -5 }} />
                  <YAxis stroke="#8b949e" />
                  <Tooltip />
                  <Line type="monotone" dataKey="valor" stroke="#ab7df8" strokeWidth={3} />
                </LineChart>
              </ResponsiveContainer>
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
        <button className="btn-primary" onClick={() => { setGenericItem({ nombre: '', id: null }); setShowGenericModal(true); }}>
          <Plus size={18} /> Nuevo {type === 'ingredients' ? 'Ingrediente' : 'Sabor'}
        </button>
      </div>
      <div className="admin-table-container">
        <table className="admin-table">
          <thead>
            <tr>
              <th>Nombre</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {data.map(item => (
              <React.Fragment key={item.id}>
                <tr>
                  <td>{item.nombre}</td>
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
                      <td colSpan="2" className="inline-edit-cell">
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
          <div className="admin-modal" style={{ maxWidth: '400px' }}>
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
            <div className="form-actions">
              <button onClick={() => setShowGenericModal(false)} className="btn-secondary">Cancelar</button>
              <button className="btn-primary" onClick={() => saveGeneric(type)}>Guardar</button>
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
      </div>
    </div>
  );
}
