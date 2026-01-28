import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import API from '../api/axios'; 
import './Register.css';
import TelegramLogin from '../components/TelegramLogin';

export default function Register() {
  const [nombre, setNombre] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleTelegramLogin = async (user) => {
    setLoading(true);
    try {
      const res = await API.post('/auth/telegram/', user);
      const accessToken = res.data.access;
      localStorage.setItem('token', accessToken);
      const payload = JSON.parse(atob(accessToken.split('.')[1]));
      localStorage.setItem('rol', payload.rol);
      navigate('/menu');
    } catch (err) {
      alert('Error registrándose con Telegram');
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async () => {
    try {
      await API.post('/auth/users/', { 
        username: nombre,
        email: email,
        password: password
      });
      alert('Usuario registrado exitosamente. Por favor, inicia sesión.');
      navigate('/login');
    } catch (error) {
      const errors = error.response?.data;
      alert(`Error: ${JSON.stringify(errors)}`);
    }
  };

  return (
    <div className="page-container">
      <h2>Registro</h2>
      <div className="form-group">
        <input placeholder="Nombre" onChange={(e) => setNombre(e.target.value)} />
        <input placeholder="Email" onChange={(e) => setEmail(e.target.value)} />
        
        <div className="password-container">
          <input
            placeholder="Contraseña"
            type={showPassword ? "text" : "password"} //  alterna entre text y password
            onChange={(e) => setPassword(e.target.value)}
          />
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)} //  toggle
            className="toggle-btn"
          >
            {showPassword ? "" : ""}
          </button>
        </div>

        <button onClick={handleRegister}>Registrarse</button>

        {/* Telegram Login deshabilitado temporalmente */}
        {/* 
        <div className="login-divider">O también puedes</div>

        <div className="telegram-btn-wrapper">
          <TelegramLogin onAuth={handleTelegramLogin} />
        </div>
        */}

        <button onClick={() => navigate('/login')} className="decorative-button-prueba">
          <span>Back</span>
        </button>
      </div>
    </div>
  );
}
