import React from 'react';
import { motion } from 'framer-motion'; // eslint-disable-line no-unused-vars

const StatusOverlay = ({ type, onClose, serviceType, lastOrderId, vaciarCarrito, navigate }) => {
  const isHere = serviceType === 'HERE';

  return (
    <motion.div
      className="order-status-overlay"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
    >
      <motion.div
        className={`status-card status-theme-${type.toLowerCase()}`}
        initial={{ scale: 0.5, y: 20 }}
        animate={{ scale: 1, y: 0 }}
        transition={{ type: "spring", damping: 15 }}
      >
        <div className="status-icon-container">
          {type === 'SUCCESS' ? '' : ''}
        </div>
        <h2 className="status-heading">
          {type === 'SUCCESS' ? '¡Pedido Recibido!' :
           type === 'BLOCKED' ? 'No Disponible' : 'Error en el Pedido'}
        </h2>

        <div className="status-message">
          {type === 'BLOCKED' ? (
            <>
              <p style={{fontSize: '1.1rem', marginBottom: '10px'}}>Lo siento pero en estos momento no hay lugares disponible.</p>
              <p style={{opacity: 0.8}}>Por favor interntelo más tarde.</p>
              <button onClick={() => navigate('/menu')} className="main-action-btn" style={{marginTop: '20px'}}>
                Volver al Menú
              </button>
            </>
          ) : type === 'SUCCESS' ? (
            isHere ? (
              <>
                <p style={{fontSize: '1.1rem', marginBottom: '10px'}}>Su pedido se está procesando en cocina.</p>
                <p style={{opacity: 0.8}}>Por favor, espere en su mesa.</p>

                <button
                  onClick={() => {
                    vaciarCarrito();
                    navigate('/menu');
                  }}
                  className="main-action-btn"
                  style={{marginTop: '15px'}}
                >
                  Volver al Menú
                </button>
                {lastOrderId && (
                  <a
                    href={`http://localhost:8000/api/bot/invoices/${lastOrderId}/`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="main-action-btn"
                    style={{ marginTop: '10px', background: '#2ecc71', display: 'flex', alignItems: 'center', justifyContent: 'center', textDecoration: 'none' }}
                  >
                     Ver Factura Local
                  </a>
                )}
              </>
            ) : (
              <>
                <p style={{fontSize: '1.1rem', marginBottom: '10px'}}>¡Gracias por su compra!</p>
                <p style={{opacity: 0.8}}>Estamos verificando su pago. Le avisaremos por Telegram cuando su pedido sea aprobado.</p>

                <button
                  onClick={() => {
                    vaciarCarrito();
                    navigate('/menu');
                  }}
                  className="main-action-btn"
                  style={{marginTop: '20px'}}
                >
                  Volver al Menú
                </button>
              </>
            )
          ) : (
            <p>Hubo un problema procesando tu solicitud. Reintenta.</p>
          )}
        </div>

        {type === 'ERROR' && (
          <button onClick={onClose} className="status-close-btn">Cerrar</button>
        )}
      </motion.div>
    </motion.div>
  );
};

export default StatusOverlay;
