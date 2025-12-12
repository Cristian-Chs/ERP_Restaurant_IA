import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axiosPublic from '../api/axiosPublic'; 
import './Register.css';

export default function Register() {
  const [nombre, setNombre] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false); // 👈 estado para visibilidad
  const navigate = useNavigate();

  const handleRegister = async () => {
    try {
      await axiosPublic.post('/auth/users/', { 
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
            type={showPassword ? "text" : "password"} // 👈 alterna entre text y password
            onChange={(e) => setPassword(e.target.value)}
          />
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)} // 👈 toggle
            className="toggle-btn"
          >
            {showPassword ? "🙈" : "👁️"}
          </button>
        </div>

        <button onClick={handleRegister}>Registrarse</button>
        <button onClick={() => navigate('/login')} className="decorative-button-prueba">
          <span>Back</span>
        </button>
      </div>
    </div>
  );
}
