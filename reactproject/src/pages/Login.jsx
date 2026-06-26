import { useState, useEffect } from 'react';
import API from '../api/axios';
import { useNavigate } from 'react-router-dom';
import './Login.css';
import { UtensilsCrossed } from 'lucide-react'; // Ensure lucide-react is installed or use fallback

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    if (error) {
      const timer = setTimeout(() => setError(''), 3000);
      return () => clearTimeout(timer);
    }
  }, [error]);

  const handleLogin = async (e) => {
    if (e) e.preventDefault(); // Handle form submit
    setError('');
    setLoading(true);

    try {
        const res = await API.post('/auth/jwt/create/', { 
            username: email, 
            password: password 
        });
        
        const accessToken = res.data.access; 
        localStorage.setItem('token', accessToken);
        
        const payload = JSON.parse(atob(accessToken.split('.')[1])); 
        localStorage.setItem('rol', payload.rol);
        
        if (payload.rol === 'admin') navigate('/admin');
        else if (payload.rol === 'cocina') navigate('/kitchen-panel');
        else navigate('/menu');
        
    } catch (err) {
        if (err.response?.status === 401) {
            setError('Usuario o contraseña incorrectos');
        } else {
            setError('Error de conexión o fallo interno del servidor.');
            console.error('Error de Login:', err);
        }
    } finally {
        setLoading(false);
    }
  };

  return (
    <div className="login-page-wrapper">
      <div className="login-card">
        <div className="login-card-header">
          <div className="login-icon-wrapper">
             <div className="login-icon-bg">
               {/* Fallback svg if UtensilsCrossed fails or just use it directly */}
               <UtensilsCrossed size={32} color="white" />
             </div>
          </div>
          <h2 className="login-title">Sabor Venezolano</h2>
          <p className="login-description">Ingresa tus credenciales para acceder</p>
        </div>

        <div className="login-card-content">
          <form onSubmit={handleLogin} className="login-form">
            <div className="form-group-login">
              <label htmlFor="username">Usuario</label>
              <input
                id="username"
                type="text"
                placeholder="usuario"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                disabled={loading}
                required
              />
            </div>
            <div className="form-group-login">
              <label htmlFor="password">Contraseña</label>
              <input
                id="password"
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                disabled={loading}
                required
              />
            </div>

            {error && <p className="error-msg">{error}</p>}

            <button type="submit" className="btn-login-submit" disabled={loading}>
              {loading ? 'Cargando...' : 'Iniciar Sesión'}
            </button>

            <p className="login-footer-text">
              ¿No tienes cuenta?{' '}
              <button type="button" onClick={() => navigate('/register')} className="login-link">
                Regístrate aquí
              </button>
            </p>
          </form>

          <div className="login-credentials-info">
             <p className="credentials-title">Usuarios de prueba:</p>
             <div className="credentials-list">
               <p>Cliente: <span className="font-mono">cliente / 123</span></p>
               <p>Admin: <span className="font-mono">admin / admin</span></p>
               <p>Cocina: <span className="font-mono">cocina / cocina</span></p>
             </div>
          </div>
        </div>
      </div>
    </div>
  );
}
