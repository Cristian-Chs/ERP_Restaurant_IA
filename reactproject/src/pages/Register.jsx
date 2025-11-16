import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
// CORRECCIÓN 1: Usar axiosPublic para el registro (No necesita Token)
import axiosPublic from '../api/axiosPublic'; 
import './Register.css';

export default function Register() {
  const [nombre, setNombre] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [rol, setRol] = useState('cliente');
  const navigate = useNavigate();

  const handleRegister = async () => {
    try {
        // CORRECCIÓN 2: Usar el endpoint de registro de Djoser
        await axiosPublic.post('/auth/users/', { 
            // Djoser necesita 'username' y 'password'.
            // Tu backend debe estar configurado para aceptar 'nombre' o usar email como nombre de usuario.
            // Si Djoser requiere campos específicos, revisa la documentación. Asumiremos que Djoser acepta 'email' y 'password' por defecto.
            email, 
            password, 
            nombre,
            rol // Nota: Si quieres guardar el rol, necesitarás extender el modelo de usuario de Django.
        });
        
        alert('Usuario registrado exitosamente. Por favor, inicia sesión.');
        navigate('/login'); // Redirigir al login después del registro
    } catch (error) {
        // Mejor manejo de errores para el usuario
        const errorMsg = error.response?.data?.email || error.response?.data?.detail || 'Error en el registro';
        alert(`Error: ${errorMsg}`);
    }
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