import { useState, useEffect } from 'react';
import API from '../api/axios'; // Se asume que esta instancia tiene la baseURL correcta (ej. http://localhost:8000/api/)
import { useNavigate } from 'react-router-dom';
import './Login.css';
import logo from '../assets/images/logo.jpeg';

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


const handleLogin = async () => {
  setError('');
  setLoading(true);

    try {
        // CORRECCIÓN CLAVE: Envía el valor del input 'email' como 'username' 
        // que es lo que Django espera por defecto.
        const res = await API.post('/auth/jwt/create/', { 
            username: email, 
            password: password 
        });
        
        // 1. Asignar y Almacenar el token
        const accessToken = res.data.access; 
        localStorage.setItem('token', accessToken);
        
        // 2. Decodificar el token para obtener el payload (rol)
        const payload = JSON.parse(atob(accessToken.split('.')[1])); 
        
        // 3. Redireccionar (Requiere configuración de CustomJWTSerializer en Django)
        navigate(payload.rol === 'admin' ? '/admin' : '/menu');
        
    } catch (err) {
        // Manejo de la respuesta 401 de Django (Credenciales incorrectas)
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
  <div className="page-container">
    <div className="login-content">
      <img className="logo" src={logo} alt="Logo" />
      <h2>Iniciar sesión</h2>

      <div className="form-group">
        <input
          placeholder="Usuario"
          value={email} // El estado se llama 'email' pero contiene el 'username'
          onChange={(e) => setEmail(e.target.value)}
          disabled={loading}
        />
        <input
          placeholder="Contraseña"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          disabled={loading}
        />
        <button onClick={handleLogin} disabled={loading}>
          {loading ? 'Cargando...' : 'Entrar'}
        </button>
        <div className="login-links">
          <button onClick={() => navigate('/register')}>
            ¿No tienes cuenta? Regístrate
          </button>
          <button onClick={() => navigate('/forgot-password')}>
            ¿Olvidaste tu contraseña?
          </button>
        </div>
      </div> 

      {error && <p className="error-msg">{error}</p>}

      <button onClick={() => navigate('/')} className="decorative-button-prueba">
        <span>Back</span>
      </button>
    </div>
  </div>
  );
}