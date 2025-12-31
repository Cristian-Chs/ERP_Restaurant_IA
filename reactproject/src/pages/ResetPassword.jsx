import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axiosPublic from '../api/axiosPublic'; 
import './Register.css'; // ✅ Usar el mismo CSS de Registro

export default function ResetPassword() {
  const { uid, token } = useParams(); 
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false); // 👈 Agregar toggle
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const navigate = useNavigate();

  const handleReset = async () => {
    setError('');
    setSuccess('');

    if (!newPassword || !confirmPassword) {
      setError('Por favor completa ambos campos');
      return;
    }

    if (newPassword !== confirmPassword) {
      setError('Las contraseñas no coinciden');
      return;
    }

    try {
      await axiosPublic.post('/auth/users/reset_password_confirm/', {
        uid,
        token,
        new_password: newPassword,
        re_new_password: confirmPassword,
      });
      setSuccess('Contraseña restablecida correctamente.');
      setTimeout(() => navigate('/login'), 3000);
    } catch (err) {
      const errorData = err.response?.data;
      const errorMsg = errorData ? JSON.stringify(errorData) : 'Error al cambiar la contraseña';
      setError(errorMsg);
    }
  };

  return (
    <div className="page-container">
      <h2>Restablecer contraseña</h2>
      <div className="form-group">
        <div className="password-container">
          <input
            type={showPassword ? "text" : "password"}
            placeholder="Nueva contraseña"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
          />
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            className="toggle-btn"
          >
            {showPassword ? "🙈" : "👁️"}
          </button>
        </div>

        <input
          type="password"
          placeholder="Confirmar contraseña"
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
        />
        
        <button onClick={handleReset}>Actualizar contraseña</button>
        <button onClick={() => navigate('/login')} className="decorative-button-prueba">
          <span>Back</span>
        </button>

        {error && <p className="error-msg" style={{ color: '#c0392b' }}>{error}</p>}
        {success && <p className="success-msg" style={{ color: '#27ae60' }}>{success}</p>}
      </div>
    </div>
  );
}
