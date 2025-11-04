// src/pages/Login.jsx
import { useState } from 'react';
import API from '../api/axios';
import { useNavigate } from 'react-router-dom';
import './Login.css'
import logo from '../assets/images/logo.jpeg';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const navigate = useNavigate();

  const handleLogin = async () => {
    const res = await API.post('/auth/login', { email, password });
    localStorage.setItem('token', res.data.token);
    const payload = JSON.parse(atob(res.data.token.split('.')[1]));
    navigate(payload.rol === 'admin' ? '/admin' : '/menu');
  };

return (
  <div className="page-container">
    <div className="login-content">
      <img className="logo" src={logo} alt="Logo" />

      <h2>Iniciar sesión</h2>
      <div className="form-group">
        <input placeholder="Email" onChange={(e) => setEmail(e.target.value)} />
        <input placeholder="Contraseña" type="password" onChange={(e) => setPassword(e.target.value)} />
        <button onClick={handleLogin}>Entrar</button>
        <button onClick={() => navigate('/register')}>¿No tienes cuenta? Regístrate</button>
      </div>
      <button onClick={() => navigate('/')} className="decorative-button-prueba">
        <span>Back</span>
      </button>
    </div>
  </div>
);

}