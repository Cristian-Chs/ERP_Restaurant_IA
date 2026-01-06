// src/components/CarritoTelegram.jsx

import React from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import BackButton from './BackButton';
import API from '../api/axios';

// Asegúrate de crear e importar Carrito.css para los estilos
import './Carrito.css'; 

// 🛑 CONFIGURACIÓN: Reemplaza con tus datos reales
const TELEGRAM_USERNAME = 'Sabores4_bot'; 
const CURRENCY_SYMBOL = '$';

const PAYMENT_METHODS = [
    { id: 'pagomovil', name: 'Pago Móvil', icon: '📱', desc: 'Transferencia instantánea nacional', color: '#ff4b2b' },
    { id: 'zelle', name: 'Zelle', icon: '🏦', desc: 'Pagos en divisas USA', color: '#6a1b9a' },
    { id: 'efectivo', name: 'Efectivo', icon: '💵', desc: 'Pago al recibir el pedido', color: '#2e7d32' },
    { id: 'transferencia', name: 'Transferencia', icon: '💳', desc: 'Banesco, Provincial o Mercantil', color: '#1565c0' }
];

function Carrito({ carrito, eliminarDelCarrito, vaciarCarrito, startTracking }) {
    const navigate = useNavigate();
    const [step, setStep] = React.useState('CART'); // CART, SERVICE, DELIVERY_MODE, LOCATION, METHODS, DETAILS
    const [serviceType, setServiceType] = React.useState(null); // 'HERE', 'TOGO'
    const [deliveryMode, setDeliveryMode] = React.useState(null); // 'PICKUP', 'DELIVERY'
    const [location, setLocation] = React.useState(null);
    const [selectedMethod, setSelectedMethod] = React.useState(null);
    const [paymentProof, setPaymentProof] = React.useState(null);
    const [orderStatus, setOrderStatus] = React.useState(null);

    const subtotal = carrito.reduce((acc, item) => acc + (parseFloat(item.price) * item.cantidad), 0);
    const serviceFee = 0.50;
    const [isOptimizing, setIsOptimizing] = React.useState(false);
    const [optimalRoute, setOptimalRoute] = React.useState(null);

    // Mock Dijkstra para simular optimización de ruta IA
    const runAIPathfinding = (userLoc) => {
        setIsOptimizing(true);
        setTimeout(() => {
            // Simulación de nodos y búsqueda del camino más corto
            const restaurantLoc = { lat: 11.411, lng: -69.673 }; 
            // En una App real, aquí usaríamos una Graph Library (como ngraph.path)
            setOptimalRoute({
                distance: "3.2 km",
                time: "12 min",
                path: ["Calle Falcón", "Av. Manaure", "Destino"]
            });
            setIsOptimizing(false);
        }, 1500);
    };

    const total = subtotal + serviceFee;

    const handleFinalize = async () => {
        try {
            // 1. Preparar datos para el Backend
            const formData = new FormData();
            
            // Intentar obtener Telegram ID del usuario logueado (ej: tg_123456)
            const token = localStorage.getItem('token');
            let tgId = 0;
            if (token) {
                try {
                    const payload = JSON.parse(atob(token.split('.')[1]));
                    if (payload.username?.startsWith('tg_')) {
                        tgId = payload.username.replace('tg_', '');
                    }
                } catch (e) { console.error("Error decodificando token", e); }
            }

            // Los items los mandamos como string por ahora para el campo 'item' del modelo Order
            const itemsSummary = carrito.map(i => `${i.cantidad}x ${i.name}`).join(', ');
            
            formData.append('telegram_id', tgId);
            formData.append('item', itemsSummary);
            formData.append('precio', total.toFixed(2));
            formData.append('status', 'pendiente');
            formData.append('service_type', serviceType);
            formData.append('delivery_mode', deliveryMode || '');
            formData.append('location', location || '');
            
            if (paymentProof) {
                formData.append('payment_proof', paymentProof);
            }

            // 2. Guardar en Base de Datos
            const response = await API.post('/bot/orders/', formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });

            if (response.status === 201 || response.status === 200) {
                setOrderStatus('SUCCESS');
                
                // ✅ TRIGGER POLLING IF EATING HERE
                if (serviceType === 'HERE' && response.data && response.data.id) {
                    startTracking(response.data.id);
                }
            } else {
                throw new Error("Fallo al guardar pedido");
            }

        } catch (error) {
            console.error("Error finalizando pedido:", error);
            setOrderStatus('ERROR');
        }
    };

    const StatusOverlay = ({ type, onClose }) => {
        const isHere = serviceType === 'HERE';
        const telegramUrl = `https://t.me/${TELEGRAM_USERNAME}`;

        return (
            <motion.div 
                className="order-status-overlay"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
            >
                <motion.div 
                    className={`status-card ${type.toLowerCase()}`}
                    initial={{ scale: 0.5, y: 20 }}
                    animate={{ scale: 1, y: 0 }}
                    transition={{ type: "spring", damping: 15 }}
                >
                    <div className="status-icon">
                        {type === 'SUCCESS' ? '✅' : '❌'}
                    </div>
                    <h2>{type === 'SUCCESS' ? '¡Pedido Recibido!' : 'Error en el Pedido'}</h2>
                    
                    <div className="status-message">
                        {type === 'SUCCESS' ? (
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
                                        Volver al Menú 🏠
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

    const handleBack = () => {
        if (step === 'SERVICE') setStep('CART');
        else if (step === 'DELIVERY_MODE') setStep('SERVICE');
        else if (step === 'LOCATION') setStep('DELIVERY_MODE');
        else if (step === 'METHODS') {
            if (serviceType === 'HERE') setStep('SERVICE');
            else if (deliveryMode === 'PICKUP') setStep('DELIVERY_MODE');
            else setStep('LOCATION');
        } 
        else if (step === 'DETAILS') setStep('METHODS');
        else navigate('/menu');
    };

    const renderSummary = (buttonText, onAction, disabled = false) => {
        const isProofRequired = selectedMethod && selectedMethod.id !== 'efectivo' && step === 'DETAILS';
        const isButtonDisabled = disabled || (isProofRequired && !paymentProof);

        return (
            <div className="checkout-sidebar">
                <div className="summary-card">
                    <h3>Resumen</h3>
                    <div className="summary-row">
                        <span>{carrito.length} producto(s)</span>
                        <span>{CURRENCY_SYMBOL}{subtotal.toFixed(2)}</span>
                    </div>
                    <div className="summary-row">
                        <span>Tarifa de servicio</span>
                        <span>{CURRENCY_SYMBOL}{serviceFee.toFixed(2)}</span>
                    </div>
                    <div className="summary-total">
                        <div>
                            <strong>Total:</strong>
                            <span className="cashback-text">Ahorras {CURRENCY_SYMBOL}0.30</span>
                        </div>
                        <span className="total-amount">{CURRENCY_SYMBOL}{total.toFixed(2)}</span>
                    </div>

                    {isProofRequired && !paymentProof && (
                        <p className="mandatory-proof-hint">⚠️ Por favor, sube el comprobante para continuar</p>
                    )}

                    <button 
                        className="main-action-btn" 
                        onClick={onAction}
                        disabled={isButtonDisabled}
                    >
                        {buttonText}
                    </button>
                </div>

            </div>
        );
    };

    return (
        <div className="premium-checkout-wrapper">
            <AnimatePresence>
                {orderStatus && (
                    <StatusOverlay type={orderStatus} onClose={() => setOrderStatus(null)} />
                )}
            </AnimatePresence>

            <div className="checkout-header">
                {/* 👈 Ahora la flecha maneja los pasos internos */}
                <button onClick={handleBack} className="decorative-back-button">
                    <svg height="16" width="16" xmlns="http://www.w3.org/2000/svg" version="1.1" viewBox="0 0 1024 1024">
                        <path d="M874.690416 495.52477c0 11.2973-9.168824 20.466124-20.466124 20.466124l-604.773963 0 188.083679 188.083679c7.992021 7.992021 7.992021 20.947078 0 28.939099-4.001127 3.990894-9.240455 5.996574-14.46955 5.996574-5.239328 0-10.478655-1.995447-14.479783-5.996574l-223.00912-223.00912c-3.837398-3.837398-5.996574-9.046027-5.996574-14.46955 0-5.433756 2.159176-10.632151 5.996574-14.46955l223.019353-223.029586c7.992021-7.992021 20.957311-7.992021 28.949332 0 7.992021 8.002254 7.992021 20.957311 0 28.949332l-188.073446 188.073446 604.753497 0C865.521592 475.058646 874.690416 484.217237 874.690416 495.52477z"></path>
                    </svg>
                    <span>Volver</span>
                </button>
            </div>

            <div className="checkout-layout">
                <motion.div 
                    className="checkout-main-content"
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    key={step}
                >
                    {step === 'CART' && (
                        <div className="step-container">
                            <h2 className="step-title">Mi carrito</h2>
                            {carrito.length === 0 ? (
                                <p className="empty-msg">Tu carrito está vacío</p>
                            ) : (
                                <div className="cart-items-list">
                                    {carrito.map(item => (
                                        <div key={item.id} className="checkout-item">
                                            <img src={item.imagen} alt={item.name} />
                                            <div className="item-info">
                                                <h4>{item.name}</h4>
                                                <div className="item-controls">
                                                    <span>Cant: {item.cantidad}</span>
                                                    <button onClick={() => eliminarDelCarrito(item.id)} className="remove-item-btn">✕</button>
                                                </div>
                                            </div>
                                            <div className="item-price">
                                                {CURRENCY_SYMBOL}{(parseFloat(item.price) * item.cantidad).toFixed(2)}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    )}

                    {step === 'SERVICE' && (
                        <div className="step-container">
                            <h2 className="step-title">¿Cómo prefieres tu pedido?</h2>
                            <div className="service-options-grid">
                                <div 
                                    className={`service-card ${serviceType === 'HERE' ? 'active' : ''}`}
                                    onClick={() => setServiceType('HERE')}
                                >
                                    <div className="service-icon">🍽️</div>
                                    <h3>Comer aquí</h3>
                                    <p>Disfruta de nuestros sabores en el restaurante.</p>
                                </div>
                                <div 
                                    className={`service-card ${serviceType === 'TOGO' ? 'active' : ''}`}
                                    onClick={() => setServiceType('TOGO')}
                                >
                                    <div className="service-icon">🛍️</div>
                                    <h3>Para llevar</h3>
                                    <p>Lo preparamos para que lo disfrutes donde quieras.</p>
                                </div>
                            </div>
                        </div>
                    )}

                    {step === 'DELIVERY_MODE' && (
                        <div className="step-container">
                            <h2 className="step-title">Elige el método de entrega</h2>
                            <div className="service-options-grid">
                                <div 
                                    className={`service-card ${deliveryMode === 'PICKUP' ? 'active' : ''}`}
                                    onClick={() => setDeliveryMode('PICKUP')}
                                >
                                    <div className="service-icon">🏪</div>
                                    <h3>Pick up</h3>
                                    <p>Tú vienes por el pedido al local.</p>
                                </div>
                                <div 
                                    className={`service-card ${deliveryMode === 'DELIVERY' ? 'active' : ''}`}
                                    onClick={() => setDeliveryMode('DELIVERY')}
                                >
                                    <div className="service-icon">🛵</div>
                                    <h3>Delivery</h3>
                                    <p>Te lo llevamos a la puerta de tu casa.</p>
                                </div>
                            </div>
                        </div>
                    )}

                    {step === 'LOCATION' && (
                        <div className="step-container">
                            <h2 className="step-title">¿Dónde entregamos?</h2>
                            <div className="location-selection-card">
                                <div className="location-icon">📍</div>
                                <p>Necesitamos tu ubicación para calcular la mejor ruta (AI Dijkstra).</p>
                                
                                <button 
                                    className="use-location-btn"
                                    onClick={() => {
                                        if (navigator.geolocation) {
                                            navigator.geolocation.getCurrentPosition((pos) => {
                                                const locStr = `${pos.coords.latitude}, ${pos.coords.longitude}`;
                                                setLocation(locStr);
                                                runAIPathfinding(locStr);
                                            }, (err) => {
                                                alert("No pudimos obtener tu ubicación. Por favor, ingrésala manualmente.");
                                            });
                                        }
                                    }}
                                >
                                    {location ? '✅ Ubicación Lista' : '🌐 Compartir Ubicación Actual'}
                                </button>

                                {isOptimizing && (
                                    <motion.div className="routing-loader" initial={{opacity:0}} animate={{opacity:1}}>
                                        <div className="ai-spinner"></div>
                                        <span>IA Analizando Rutas (Dijkstra)...</span>
                                    </motion.div>
                                )}

                                {optimalRoute && !isOptimizing && (
                                    <motion.div className="route-result-card" initial={{scale:0.9, opacity:0}} animate={{scale:1, opacity:1}}>
                                        <div className="route-badge">Ruta Óptima de Entrega</div>
                                        <div className="route-stats">
                                            <span>⏱️ {optimalRoute.time}</span>
                                            <span>🛣️ {optimalRoute.distance}</span>
                                        </div>
                                        <p><strong>Camino:</strong> {optimalRoute.path.join(' ➔ ')}</p>
                                    </motion.div>
                                )}

                                <div className="manual-location">
                                    <span>O ingresa tu dirección manualmente:</span>
                                    <textarea 
                                        placeholder="Calle, número de casa, punto de referencia..."
                                        value={location || ''}
                                        onChange={(e) => {
                                            setLocation(e.target.value);
                                            if (e.target.value.length > 5) runAIPathfinding(e.target.value);
                                        }}
                                    />
                                </div>
                            </div>
                        </div>
                    )}

                    {step === 'METHODS' && (
                        <div className="methods-step">
                            <h2 className="step-title">Selecciona un método de pago</h2>
                            <div className="payment-grid">
                                {PAYMENT_METHODS.map(m => (
                                    <div 
                                        key={m.id} 
                                        className={`payment-card ${selectedMethod?.id === m.id ? 'active' : ''}`}
                                        onClick={() => setSelectedMethod(m)}
                                    >
                                        <div className="method-icon" style={{ backgroundColor: m.color }}>{m.icon}</div>
                                        <div className="method-text">
                                            <strong>{m.name}</strong>
                                            <span>{m.desc}</span>
                                        </div>
                                        <div className="radio-circle"></div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {step === 'DETAILS' && (
                        <div className="details-step">
                            <h2 className="step-title">Finalizar Pago</h2>
                            <div className="binance-details-card">
                                <div className="p2p-badge">Pago Directo Seguro</div>
                                <h3>{selectedMethod?.name}</h3>
                                <div className="data-rows">
                                    <div className="data-row"><span>Banco</span> <strong>Banesco</strong></div>
                                    <div className="data-row"><span>Cédula</span> <strong>20.123.456</strong></div>
                                    <div className="data-row"><span>Teléfono</span> <strong>0412-5556677</strong></div>
                                </div>
                                <div className="upload-section">
                                    <p>Sube tu captura de pantalla para confirmar</p>
                                    <label className="custom-file-upload">
                                        <input 
                                            type="file" 
                                            accept="image/*"
                                            onChange={(e) => {
                                                const file = e.target.files[0];
                                                if (file) {
                                                    setPaymentProof(file);
                                                    console.log("Archivo seleccionado para envío:", file.name, file.size, file.type);
                                                }
                                            }} 
                                        />
                                        {paymentProof ? '✅ Captura Lista' : '📁 Seleccionar Imagen'}
                                    </label>
                                    
                                    {paymentProof && (
                                        <motion.div 
                                            className="proof-preview"
                                            initial={{ opacity: 0, scale: 0.8 }}
                                            animate={{ opacity: 1, scale: 1 }}
                                        >
                                            <img src={URL.createObjectURL(paymentProof)} alt="Preview" />
                                            <button onClick={() => setPaymentProof(null)} className="remove-proof">✕</button>
                                        </motion.div>
                                    )}
                                </div>
                            </div>
                        </div>
                    )}
                </motion.div>

                {step === 'CART' && renderSummary('Siguiente', () => setStep('SERVICE'), carrito.length === 0)}
                
                {step === 'SERVICE' && renderSummary('Siguiente', () => {
                    if (serviceType === 'HERE') setStep('METHODS');
                    else setStep('DELIVERY_MODE');
                }, !serviceType)}

                {step === 'DELIVERY_MODE' && renderSummary('Siguiente', () => {
                    if (deliveryMode === 'PICKUP') setStep('METHODS');
                    else setStep('LOCATION');
                }, !deliveryMode)}

                {step === 'LOCATION' && renderSummary('Siguiente', () => setStep('METHODS'), !location)}

                {step === 'METHODS' && renderSummary('Siguiente', () => setStep('DETAILS'), !selectedMethod)}
                
                {step === 'DETAILS' && renderSummary('Confirmar Pedido', handleFinalize)}
            </div>
        </div>
    );
}

export default Carrito;