import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axiosPublic from '../api/axiosPublic'; // ✅ instancia sin token
import './ResetPassword.css'; // opcional para estilos

export default function ResetPassword() {
  const { token } = useParams();
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
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
      const res = await axiosPublic.post('/auth/reset-password', {
        token,
        newPassword,
      });
      setSuccess(res.data.msg);
      setTimeout(() => navigate('/'), 3000);
    } catch (err) {
      setError(err.response?.data?.msg || 'Error al cambiar la contraseña');
    }
  };

  return (
    <div className="reset-container">
      <h2>Restablecer contraseña</h2>
      <input
        type="password"
        placeholder="Nueva contraseña"
        value={newPassword}
        onChange={(e) => setNewPassword(e.target.value)}
      />
      <input
        type="password"
        placeholder="Confirmar contraseña"
        value={confirmPassword}
        onChange={(e) => setConfirmPassword(e.target.value)}
      />
      <button onClick={handleReset}>Actualizar contraseña</button>

      {error && <p className="error-msg">{error}</p>}
      {success && <p className="success-msg">{success}</p>}
    </div>
  );
}
