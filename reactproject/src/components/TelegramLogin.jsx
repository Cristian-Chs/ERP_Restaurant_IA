import React, { useEffect, useRef } from 'react';

const TelegramLogin = ({ onAuth }) => {
  const containerRef = useRef(null);

  useEffect(() => {
    // 💡 Definir el callback globalmente para que el widget de Telegram lo encuentre
    window.onTelegramAuth = (user) => {
      onAuth(user);
    };

    const script = document.createElement('script');
    script.src = 'https://telegram.org/js/telegram-widget.js?22';
    script.setAttribute('data-telegram-login', 'Sabores4_bot'); // Reemplaza con tu bot username real
    script.setAttribute('data-size', 'large');
    script.setAttribute('data-radius', '12');
    script.setAttribute('data-onauth', 'onTelegramAuth(user)');
    script.setAttribute('data-request-access', 'write');
    script.async = true;

    if (containerRef.current) {
        containerRef.current.appendChild(script);
    }

    return () => {
      if (containerRef.current) {
        containerRef.current.innerHTML = '';
      }
      delete window.onTelegramAuth;
    };
  }, [onAuth]);

  return <div ref={containerRef} className="telegram-login-container" />;
};

export default TelegramLogin;
