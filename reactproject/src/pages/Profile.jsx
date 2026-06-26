import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import API from '../api/axios'; 
import './Register.css'; 

export default function Profile() {
  const [userData, setUserData] = useState({ username: '', email: '' });
  const [newPassword, setNewPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(true);
  const [mensaje, setMensaje] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const res = await API.get('/auth/users/me/');
        setUserData({ username: res.data.username, email: res.data.email });
      } catch (err) {
        setError('No se pudieron cargar los datos del perfil.');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchProfile();
  }, []);

  const handleUpdateData = async () => {
    setMensaje('');
    setError('');
    try {
      await API.patch('/auth/users/me/', { 
        username: userData.username,
        email: userData.email 
      });
      setMensaje('Datos actualizados correctamente.');
    } catch {
      setError('Error al actualizar los datos.');
    }
  };

  const [currentPassword, setCurrentPassword] = useState('');

  const handleChangePassword = async () => {
    setMensaje('');
    setError('');

    if (!newPassword || !currentPassword) {
      setError('Completa ambos campos de contraseña.');
      return;
    }

    try {
      await API.post('/auth/users/set_password/', {
        new_password: newPassword,
        current_password: currentPassword
      });
      setMensaje('Contraseña cambiada correctamente.');
      setNewPassword('');
      setCurrentPassword('');
    } catch (err) {
      setError('La contraseña actual no es correcta o hubo un error.');
      console.error(err);
    }
  };

  if (loading) return <div className="page-container"><h2>Cargando...</h2></div>;

  return (
    <div className="page-container profile-page">
      <h2>Mi Perfil</h2>
      <div className="form-group">
        <label style={{alignSelf: 'flex-start', fontSize: '0.8rem', opacity: 0.8}}>Nombre de Usuario</label>
        <input
          placeholder="Usuario"
          value={userData.username}
          onChange={(e) => setUserData({ ...userData, username: e.target.value })}
        />
        <label style={{alignSelf: 'flex-start', fontSize: '0.8rem', opacity: 0.8}}>Email</label>
        <input
          placeholder="Email"
          value={userData.email}
          onChange={(e) => setUserData({ ...userData, email: e.target.value })}
        />
        <button onClick={handleUpdateData}>Guardar Cambios</button>

        <hr style={{width: '100%', opacity: 0.2, margin: '1rem 0'}} />

        <h3>Cambiar Contraseña</h3>
        <div className="password-container">
          <input
            type="password"
            placeholder="Contraseña actual"
            value={currentPassword}
            onChange={(e) => setCurrentPassword(e.target.value)}
          />
        </div>
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
            {showPassword ? "" : ""}
          </button>
        </div>
        <button onClick={handleChangePassword}>Actualizar Clave</button>

        <button onClick={() => navigate(-1)} className="decorative-button-prueba">
          <span>Volver</span>
        </button>

        {mensaje && <p className="success-msg" style={{color: '#27ae60'}}>{mensaje}</p>}
        {error && <p className="error-msg" style={{color: '#c0392b'}}>{error}</p>}
      </div>
    </div>
  );
}
