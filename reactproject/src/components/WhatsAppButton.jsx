import React from 'react';
import { FaWhatsapp } from 'react-icons/fa'; 

function WhatsAppButton() {
  // Reemplaza '1234567890' con el número de teléfono, incluyendo el código de país.
  const phoneNumber = '+5804246188448'; 
  
  
  // Opcional: Para incluir un mensaje predefinido:
  const prefilledMessage = encodeURIComponent('Hola, me gustaría más información.');
  const whatsappLink = `https://wa.me/${phoneNumber}?text=${prefilledMessage}`;


  return (
    <a 
      href={whatsappLink}
      target="_blank" 
      rel="noopener noreferrer"
      style={{
        //  Estilos Clave para el Posicionamiento Fijo
        position: 'fixed', // Hace que el elemento se quede quieto en la ventana
        bottom: '20px',    // Distancia desde el borde inferior
        right: '20px',     // Distancia desde el borde derecho
        zIndex: 1000,      // Asegura que esté por encima de otros elementos
        
        // Estilos de Apariencia del Botón
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center',
        width: '60px',       // Ajusta el tamaño si solo es el icono
        height: '60px',
        backgroundColor: '#25D366', // Verde de WhatsApp
        borderRadius: '50%', // Forma circular
        boxShadow: '0 4px 8px rgba(0, 0, 0, 0.4)', // Sombra para que destaque
        transition: 'transform 0.2s', // Transición suave al pasar el ratón (hover)
        cursor: 'pointer',
      }}
      // Aquí puedes añadir estilos de hover si usas styled-components o un archivo CSS
      // En este ejemplo, te muestro solo los estilos inline esenciales.
    >
      <FaWhatsapp 
        size={32}       // Tamaño grande para el icono central
        color="white"   // Color blanco para el icono
      />
    </a>
  );
}

export default WhatsAppButton;