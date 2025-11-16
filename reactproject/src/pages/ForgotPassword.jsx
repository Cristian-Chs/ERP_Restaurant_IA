import { useState } from 'react';
import axiosPublic from '../api/axiosPublic'; // ✅ esta es la instancia sin token
import './Login.css';

export default function ForgotPassword() {
  const [email, setEmail] = useState('');
  const [mensaje, setMensaje] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async () => {
    setMensaje('');
    setError('');

    try {
      await axiosPublic.post('/auth/forgot-password', { email }); // ✅ usa axiosPublic
      setMensaje('Te hemos enviado un correo para restablecer tu contraseña.');
    } catch (err) {
      setError('No se pudo enviar el correo. Verifica el email.');
    }
  };

  return (
    <div className="page-container">
      <div className="login-content">
        <h2>Recuperar contraseña</h2>
        <input
          placeholder="Ingresa tu email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
        <button onClick={handleSubmit}>Enviar instrucciones</button>
        {mensaje && <p className="success-msg">{mensaje}</p>}
        {error && <p className="error-msg">{error}</p>}
      </div>
    </div>
  );
}
