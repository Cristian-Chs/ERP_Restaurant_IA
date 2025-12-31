import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axiosPublic from '../api/axiosPublic'; 
import './Register.css'; // ✅ Usar el mismo CSS de Registro

export default function ForgotPassword() {
  const [email, setEmail] = useState('');
  const [mensaje, setMensaje] = useState('');
  const [error, setError] = useState('');
  const [recoveryData, setRecoveryData] = useState(null); // Para guardar uid y token
  const navigate = useNavigate();

  const handleCheckAccount = async () => {
    setMensaje('');
    setError('');
    setRecoveryData(null);

    if (!email) {
      setError('Por favor ingresa tu email');
      return;
    }

    try {
      // ✅ Llamar al nuevo endpoint de verificación directa
      const res = await axiosPublic.get(`/auth/check-recovery?email=${email}`); 
      
      if (res.data.exists) {
        setMensaje('Cuenta encontrada. Haz clic en el botón de abajo para restablecer.');
        setRecoveryData({ uid: res.data.uid, token: res.data.token });
      } else {
        setError('Cuenta no existe. Verifica el email ingresado.');
      }
    } catch (err) {
      setError('Error al conectar con el servidor.');
    }
  };

  return (
    <div className="page-container">
      <h2>Recuperar contraseña</h2>
      <div className="form-group">
        <input
          placeholder="Ingresa tu email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
        
        {!recoveryData ? (
          <button onClick={handleCheckAccount}>Verificar Cuenta</button>
        ) : (
          <button 
            onClick={() => navigate(`/reset-password/${recoveryData.uid}/${recoveryData.token}`)}
            style={{ backgroundColor: '#27ae60', color: 'white' }}
          >
            RESTABLECER AHORA
          </button>
        )}

        <button onClick={() => navigate('/login')} className="decorative-button-prueba">
          <span>Back</span>
        </button>
        {mensaje && <p className="success-msg" style={{ color: '#27ae60' }}>{mensaje}</p>}
        {error && <p className="error-msg" style={{ color: '#c0392b' }}>{error}</p>}
      </div>
    </div>
  );
}
