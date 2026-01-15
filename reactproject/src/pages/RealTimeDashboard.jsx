import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  BarChart, Bar, Cell
} from 'recharts';
import { TrendingUp, ShoppingBag, Clock, Award, Activity, Users, MessageSquare, Smile, Frown, Meh } from 'lucide-react';
import axios from 'axios';
import './RealTimeDashboard.css';

const RealTimeDashboard = () => {
  const [metrics, setMetrics] = useState({
    ingresos_hoy: 0,
    pedidos_activos: 0,
    top_items: [],
    timestamp: '--:--:--',
    recent_ratings: []
  });
  const [history, setHistory] = useState([]);
  const [status, setStatus] = useState('connecting');
  const [forecast, setForecast] = useState([]);

  const fetchForecast = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/analytics/demand-prediction/', {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      if (response.data.status === 'success') {
        // Solo las próximas 8 horas para no saturar
        setForecast(response.data.predictions.slice(0, 8));
      }
    } catch (err) {
      console.error("Error fetching forecast:", err);
    }
  };

  useEffect(() => {
    const socket = new WebSocket('ws://localhost:8000/ws/metrics/');

    socket.onopen = () => {
      console.log('WebSocket connected');
      setStatus('connected');
    };

    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setMetrics(data);
      setHistory(prev => {
        const newHistory = [...prev, { time: data.timestamp, val: data.ingresos_hoy }];
        return newHistory.slice(-10); // Mantener últimos 10 puntos
      });
    };

    socket.onclose = () => {
      console.log('WebSocket disconnected');
      setStatus('disconnected');
      // Reintento de conexión en 5 segundos
      setTimeout(() => setStatus('reconnecting'), 5000);
    };

    return () => socket.close();
  }, [status === 'reconnecting']);

  useEffect(() => {
    fetchForecast();
    const interval = setInterval(fetchForecast, 300000); // Cada 5 minutos
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="rt-dashboard-container">
      <header className="rt-header">
        <div className="header-left">
          <h1>Dashboard en Tiempo Real <Activity className={`status-icon ${status}`} /></h1>
          <p>Métricas actualizadas cada 5 segundos</p>
        </div>
        <div className="last-update">
          Última actualización: <span>{metrics.timestamp}</span>
        </div>
      </header>

      <div className="metrics-grid">
        <motion.div className="metric-card gold" whileHover={{ y: -5 }}>
          <div className="card-icon"><TrendingUp /></div>
          <div className="card-info">
            <h3>Ingresos Hoy</h3>
            <p className="value">${metrics.ingresos_hoy.toFixed(2)}</p>
          </div>
        </motion.div>

        <motion.div className="metric-card blue" whileHover={{ y: -5 }}>
          <div className="card-icon"><ShoppingBag /></div>
          <div className="card-info">
            <h3>Pedidos Activos</h3>
            <p className="value">{metrics.pedidos_activos}</p>
          </div>
        </motion.div>

        <motion.div className="metric-card green" whileHover={{ y: -5 }}>
          <div className="card-icon"><Clock /></div>
          <div className="card-info">
            <h3>Preparación</h3>
            <p className="value">~12 min</p>
          </div>
        </motion.div>
      </div>

      <div className="charts-section">
        <div className="chart-box main-chart">
          <h3>Evolución de Ingresos (Últimas Actualizaciones)</h3>
          <div style={{ width: '100%', height: 300 }}>
            <ResponsiveContainer>
              <LineChart data={history}>
                <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                <XAxis dataKey="time" stroke="#888" />
                <YAxis stroke="#888" />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#1a1a1a', border: '1px solid #444' }}
                  itemStyle={{ color: '#f9cb28' }}
                />
                <Line 
                  type="monotone" 
                  dataKey="val" 
                  stroke="#f9cb28" 
                  strokeWidth={3} 
                  dot={{ r: 6, fill: '#f9cb28' }}
                  activeDot={{ r: 8, fill: '#fff' }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="sentiment-section" style={{ marginTop: '30px' }}>
        <div className="chart-box full-width">
          <div className="chart-header">
            <h3>🎭 El Muro de los Sentimientos</h3>
            <p className="subtitle">Opiniones analizadas en tiempo real por la IA</p>
          </div>
          <div className="sentiment-wall" style={{ maxHeight: '300px', overflowY: 'auto' }}>
            {metrics.recent_ratings && metrics.recent_ratings.length > 0 ? (
              metrics.recent_ratings.map((rate, idx) => (
                <motion.div 
                  key={idx} 
                  className={`sentiment-bubble ${rate.sentimiento?.toLowerCase()}`}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: idx * 0.1 }}
                >
                  <div className="bubble-header">
                    <span className="stars">{"⭐".repeat(rate.estrellas)}</span>
                    <span className="plato">{rate.plato}</span>
                    <span className="sentiment-icon">
                      {rate.sentimiento === 'Positivo' && <Smile size={16} />}
                      {rate.sentimiento === 'Negativo' && <Frown size={16} />}
                      {rate.sentimiento === 'Neutral' && <Meh size={16} />}
                    </span>
                  </div>
                  <p className="comment">"{rate.comentario || "Sin comentario"}"</p>
                </motion.div>
              ))
            ) : (
              <p style={{ color: '#444', textAlign: 'center', padding: '20px' }}>Esperando nuevo feedback...</p>
            )}
          </div>
        </div>
      </div>

      <div className="forecast-section" style={{ marginTop: '30px' }}>
        <div className="chart-box full-width">
          <div className="chart-header">
            <h3>📈 Proyección de Carga de Trabajo (Próximas Horas)</h3>
            <p className="subtitle">Basado en Inteligencia Artificial (Facebook Prophet)</p>
          </div>
          <div style={{ width: '100%', height: 250 }}>
            <ResponsiveContainer>
              <LineChart data={forecast}>
                <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                <XAxis dataKey="hora" stroke="#888" tickFormatter={(str) => str.split(" ")[1]} />
                <YAxis stroke="#888" />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#1a1a1a', border: '1px solid #444' }}
                  labelStyle={{ color: '#fff' }}
                />
                <Line 
                  type="monotone" 
                  dataKey="pedidos_esperados" 
                  name="Pedidos Estimados"
                  stroke="#3498db" 
                  strokeWidth={4} 
                  dot={{ r: 4, fill: '#3498db' }}
                />
                <Line 
                  type="monotone" 
                  dataKey="rango_max" 
                  name="Pico Máximo"
                  stroke="#e74c3c" 
                  strokeWidth={2} 
                  strokeDasharray="5 5"
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
          <div className="forecast-footer">
            <Users size={16} /> <span>Recomendación: {
              forecast.length > 0 && forecast[0].pedidos_esperados > 10 ? "Reforzar Cocina" : "Staff Normal"
            }</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RealTimeDashboard;
