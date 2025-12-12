// src/components/CarritoTelegram.jsx

import React from 'react';
import { motion } from 'framer-motion';
import BackButton from './BackButton';

// Asegúrate de crear e importar Carrito.css para los estilos
import './Carrito.css'; 

// 🛑 CONFIGURACIÓN: Reemplaza con tus datos reales
const TELEGRAM_USERNAME = 'Sabores4_bot'; 
const CURRENCY_SYMBOL = '$';

function Carrito({ carrito, eliminarDelCarrito }) {
  
    // Calcular el total del carrito (usando parseFloat para asegurar que el precio es un número)
    const totalPedido = carrito.reduce((acc, item) => 
        acc + (parseFloat(item.price) * item.cantidad), 0); 
  
    // Función para generar el enlace de Telegram
    const handleCheckout = () => {
        if (carrito.length === 0) return;

        // 1. INICIO CLAVE: Frase de inicio que el bot de Python puede reconocer fácilmente
        // Usamos una frase simple para que el bot la detecte sin ambigüedad.
        let message = `Quiero pedir. Aquí está mi resumen:\n\n*🛒 Resumen del Pedido:*\n`;

        carrito.forEach((item, index) => {
            const price = parseFloat(item.price);
            const subtotal = (price * item.cantidad).toFixed(2);
            
            // Formato del ítem (se mantienen los * para la visualización en Telegram)
            message += `${index + 1}. *${item.name}* (${item.cantidad} x ${CURRENCY_SYMBOL}${price.toFixed(2)})\n`;
            message += `   Subtotal: ${CURRENCY_SYMBOL}${subtotal}\n`;
        });

        message += `\n--------------------------------\n`;
        message += `*💰 TOTAL FINAL: ${CURRENCY_SYMBOL}${totalPedido.toFixed(2)}*\n`;
        message += `--------------------------------\n`;
        message += `\nPor favor, confirma mi pedido.`;

        // 2. Codificación
        const encodedMessage = encodeURIComponent(message);
        
        // 3. Generación del enlace
        const telegramUrl = `https://t.me/${TELEGRAM_USERNAME}?text=${encodedMessage}`;
        
        window.open(telegramUrl, '_blank');
    };

    return (
        <motion.div 
            className="carrito-container"
            initial={{ opacity: 0, y: -50 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 50 }}
        >
            <BackButton to="/menu"/>
            <h2>🛍️ Tu Pedido ({carrito.length} Items)</h2>
            
            {carrito.length === 0 ? (
                <p className="carrito-vacio">El carrito está vacío. ¡Añade algo delicioso del menú!</p>
            ) : (
                <div className="carrito-list"> 
                    {carrito.map(item => (
                        <div key={item.id} className="carrito-item"> {/* Clase CSS para el ítem */}
                            <img 
                                src={item.imagen} 
                                alt={item.name} 
                                className="carrito-item-img"
                            />
                            <div className="carrito-item-details">
                                <h4>{item.name}</h4>
                                {/* Usamos parseFloat para el precio */}
                                <p>Precio: ${parseFloat(item.price).toFixed(2)}</p>
                                <p>Cantidad: {item.cantidad}</p>
                                <p className="carrito-item-subtotal">Subtotal: ${(parseFloat(item.price) * item.cantidad).toFixed(2)}</p>
                            </div>
                            <button 
                                className="eliminar-btn"
                                onClick={() => eliminarDelCarrito(item.id)}
                            >
                            X
                            </button>
                        </div>
                    ))}
                    
                    <div className="carrito-summary">
                        <h3>Total: **${totalPedido.toFixed(2)}**</h3>
                        
                        <button 
                            className="checkout-btn"
                            onClick={handleCheckout} 
                        >
                            Finalizar Pedido por Telegram
                        </button>
                    </div>
                </div>
            )}
        </motion.div>
    );
}

export default Carrito;