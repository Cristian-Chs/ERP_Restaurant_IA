// src/components/TelegramButton.jsx
import React from 'react';
import { FaTelegramPlane } from 'react-icons/fa';

function TelegramButton() {
  // ----------------------------------------------------
  //  Configuración de Telegram
  // ----------------------------------------------------
  // Nombre del bot SIN el @
  const telegramUsername = 'Sabores4_bot';

  // Recuperar el nombre del usuario desde localStorage (guardado en Login.jsx)
  const nombreUsuario = localStorage.getItem('username') || 'Cliente';

  // Mensaje prellenado con saludo y opciones
  const prefilledMessage = encodeURIComponent(
    `¡Hola ${nombreUsuario}! Me gustaría hacer un pedido.`
  );

  // Enlace directo al bot con mensaje prellenado
  const telegramLink = `https://t.me/${telegramUsername}?text=${prefilledMessage}`;

  return (
    <a
      href={telegramLink}
      target="_blank"
      rel="noopener noreferrer"
      style={{
        position: 'fixed',
        bottom: '20px',
        right: '20px',
        zIndex: 1000,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        width: '60px',
        height: '60px',
        backgroundColor: '#0088cc', // Azul Telegram
        borderRadius: '50%',
        boxShadow: '0 4px 8px rgba(0, 0, 0, 0.4)',
        transition: 'transform 0.2s',
        cursor: 'pointer',
      }}
    >
      <FaTelegramPlane size={32} color="white" />
    </a>
  );
}

export default TelegramButton;
