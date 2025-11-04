import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import API from '../api/axios';
import './Register.css';

export default function Register() {
  const [nombre, setNombre] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [rol, setRol] = useState('cliente');
  const navigate = useNavigate();

  const handleRegister = async () => {
    await API.post('/auth/register', { nombre, email, password, rol });
    alert('Usuario registrado');
  };

return (
  <div className="page-container">
    <h2>Registro</h2>
    <div className="form-group">
      <input placeholder="Nombre" onChange={(e) => setNombre(e.target.value)} />
      <input placeholder="Email" onChange={(e) => setEmail(e.target.value)} />
      <input placeholder="Contraseña" type="password" onChange={(e) => setPassword(e.target.value)} />
      <select onChange={(e) => setRol(e.target.value)}>
        <option value="cliente">Cliente</option>
        <option value="admin">Admin</option>
      </select>
      <button onClick={handleRegister}>Registrarse</button>
      <button onClick={() => navigate('/login')} className="decorative-button-prueba">
        <span>Back</span>
      </button>
    </div>
  </div>
);
}
