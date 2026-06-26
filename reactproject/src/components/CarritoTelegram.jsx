import React from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion'; // eslint-disable-line no-unused-vars
import BackButton from './BackButton';
import API from '../api/axios';
import StatusOverlay from './StatusOverlay';
import config from '../config';
import './Carrito.css'; 

const { TELEGRAM_USERNAME, CURRENCY_SYMBOL, GOOGLE_MAPS_API_KEY } = config;

const PAYMENT_METHODS = [
    { id: 'pagomovil', name: 'Pago Móvil', icon: '', desc: 'Transferencia instantánea nacional', color: '#ff4b2b' },
    { id: 'zelle', name: 'Zelle', icon: '', desc: '4restaurant@gmail.com', color: '#6a1b9a' },
    { id: 'efectivo', name: 'Efectivo', icon: '', desc: '', color: '#2e7d32' },
    { id: 'transferencia', name: 'Transferencia', icon: '', desc: 'Banco Banesco', color: '#1565c0' }
];

const SUPPORTED_LOCATIONS = [
    "Puerta Maraven",
    "Comunidad Cardón",
    "Maraven",
    "Centro de Punto Fijo",
    "Banco Obrero",
    "Caja de Agua",
    "Santa Irene",
    "Santa Fe",
    "Las Margaritas",
    "Judibana",
    "Los Taques",
    "Villa Marina",
    "El Cayude"
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
    const currency = 'USD';
    const [exchangeRate, setExchangeRate] = React.useState(1);
    
    // Coupon states
    const [couponCode, setCouponCode] = React.useState('');
    const [appliedCoupon, setAppliedCoupon] = React.useState(null);
    const [couponError, setCouponError] = React.useState('');
    const [validatingCoupon, setValidatingCoupon] = React.useState(false);
    const [lastOrderId, setLastOrderId] = React.useState(null);

    // Google Maps Script Loader
    React.useEffect(() => {
        if (step === 'LOCATION' && deliveryMode === 'DELIVERY' && !window.google) {
            const script = document.createElement('script');
            script.src = `https://maps.googleapis.com/maps/api/js?key=${GOOGLE_MAPS_API_KEY}&libraries=places`;
            script.async = true;
            script.defer = true;
            script.onload = () => initAutocomplete(); // Call init when loaded
            document.head.appendChild(script);
        } else if (step === 'LOCATION' && window.google) {
            initAutocomplete(); // Call immediately if already loaded
        }
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [step, deliveryMode]);

    const initAutocomplete = () => {
        try {
            const input = document.getElementById("google-maps-input");
            if (input && window.google) {
                const autocomplete = new window.google.maps.places.Autocomplete(input, {
                    types: ['geocode'], // or 'address'
                    componentRestrictions: { country: "ve" } // Limit to Venezuela
                });

                autocomplete.addListener("place_changed", () => {
                    const place = autocomplete.getPlace();
                    if (place.geometry) {
                        const address = place.formatted_address;
                        const lat = place.geometry.location.lat();
                        const lng = place.geometry.location.lng();
                        
                        console.log(" Lugar seleccionado:", address, lat, lng);
                        setLocation(address); // Save full address
                        
                        // Optional: Save coordinates separately if needed
                        // setCoordinates({ lat, lng });
                        
                        runAIPathfinding(address);
                    }
                });
            }
        } catch (e) {
            console.error("Error initializing Google Maps:", e);
        }
    };


    // Check Table Availability on Mount
    React.useEffect(() => {
        const checkAvailability = async () => {
            try {
                const res = await API.get('/tables/availability/');
                if (res.data && res.data.can_order === false) {
                    alert(res.data.message); // Simple alert or custom overlay
                    // Optional: Navigate away or disable checkout
                    setOrderStatus('BLOCKED'); // Reuse status overlay with custom type?
                    // Or just set a state to disable
                }
            } catch (e) { console.error("Error checking availability", e); }
        };
        checkAvailability();
    }, []);

    React.useEffect(() => {
        const fetchRates = async () => {
            try {
                const res = await API.get('/currency/rates/');
                if (res.data && res.data.VES) {
                    setExchangeRate(res.data.VES);
                }
            } catch (e) { console.error("Error fetching rates", e); }
        };
        fetchRates();
    }, []);

    const subtotal = carrito.reduce((acc, item) => acc + (parseFloat(item.price) * item.cantidad), 0);
    const serviceFee = 0.50;
    const discount = appliedCoupon ? appliedCoupon.discount : 0;
    const [isOptimizing, setIsOptimizing] = React.useState(false);
    const [optimalRoute, setOptimalRoute] = React.useState(null);

    // Autocomplete State
    const [filteredLocations, setFilteredLocations] = React.useState([]);
    const [showSuggestions, setShowSuggestions] = React.useState(false);

    const handleLocationSearch = (query) => {
        setLocation(query);
        if (query.length > 0) {
            const matches = SUPPORTED_LOCATIONS.filter(loc => 
                loc.toLowerCase().includes(query.toLowerCase())
            );
            setFilteredLocations(matches);
            setShowSuggestions(true);
        } else {
            setFilteredLocations([]);
            setShowSuggestions(false);
        }
    };

    const selectLocation = (loc) => {
        setLocation(loc);
        setShowSuggestions(false);
        runAIPathfinding(loc);
    };

    // Real AI Pathfinding using Backend API
    const runAIPathfinding = async (userLoc) => {
        setIsOptimizing(true);
        setOptimalRoute(null);
        
        try {
            const response = await API.post('/bot/route/calculate/', {
                location: userLoc
            });
            
            if (response.data && response.data.distance) {
                setOptimalRoute({
                    distance: response.data.distance,
                    time: response.data.time,
                    path: response.data.path.map(p => `[${p.join(', ')}]`) // Simple representation of path points
                });
            } else {
                 console.warn("No route data returned", response.data);
            }
        } catch (error) {
            console.error("Error calculating route:", error);
            // Optional: fallback or error state
        } finally {
            setIsOptimizing(false);
        }
    };

    const total = Math.max(0, subtotal + serviceFee - discount);
    
    // Validate coupon
    const validateCoupon = async () => {
        if (!couponCode.trim()) {
            setCouponError('Ingresa un código de cupón');
            return;
        }
        
        setValidatingCoupon(true);
        setCouponError('');
        
        try {
            const response = await API.post('/bot/coupons/validate/', {
                code: couponCode,
                order_amount: subtotal + serviceFee
            });
            
            setAppliedCoupon(response.data);
            setCouponError('');
        } catch (error) {
            setCouponError(error.response?.data?.error || 'Cupón no válido');
            setAppliedCoupon(null);
        } finally {
            setValidatingCoupon(false);
        }
    };
    
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
            
            // Mapeo de valores para el Backend
            const serviceTypeMap = { 'HERE': 'AQUI', 'TOGO': 'LLEVAR' };
            const deliveryModeMap = { 'PICKUP': 'RETIRO', 'DELIVERY': 'DELIVERY' };

            formData.append('telegram_id', tgId);
            formData.append('item', itemsSummary);
            formData.append('precio', total.toFixed(2));
            formData.append('status', 'pendiente');
            formData.append('service_type', serviceTypeMap[serviceType] || 'AQUI');
            formData.append('delivery_mode', deliveryMode ? deliveryModeMap[deliveryMode] : '');
            formData.append('location', location || '');
            formData.append('currency', currency);
            formData.append('exchange_rate', exchangeRate);
            
            if (paymentProof) {
                formData.append('payment_proof', paymentProof);
            }

            // 3. Datos de Pago (JSON)
            let methodId = selectedMethod ? selectedMethod.id : '';
            if (methodId === 'efectivo') methodId = 'cash';

            const paymentData = {
                payment_method: methodId,
                ...((appliedCoupon) && {
                    coupon_code: appliedCoupon.code,
                    discount_applied: appliedCoupon.discount,
                    discount_type: appliedCoupon.discount_type
                })
            };
            formData.append('payment_data', JSON.stringify(paymentData));

            // 4. Guardar en Base de Datos
            const response = await API.post('/bot/orders/', formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });

            if (response.status === 201 || response.status === 200) {
                setOrderStatus('SUCCESS');
                if (response.data && response.data.id) {
                    setLastOrderId(response.data.id);
                }
                
                //  TRIGGER POLLING IF EATING HERE
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
                    
                    {/* Coupon Section */}
                    {!appliedCoupon ? (
                        <div className="coupon-input-section" style={{ marginTop: '1rem', paddingTop: '1rem', borderTop: '1px solid rgba(255,255,255,0.1)' }}>
                            <label style={{ fontSize: '0.9rem', color: '#8b949e', marginBottom: '0.5rem', display: 'block' }}>¿Tienes un cupón?</label>
                            <div style={{ display: 'flex', gap: '8px' }}>
                                <input 
                                    type="text" 
                                    placeholder="Código de cupón"
                                    value={couponCode}
                                    onChange={(e) => setCouponCode(e.target.value.toUpperCase())}
                                    onKeyPress={(e) => e.key === 'Enter' && validateCoupon()}
                                    style={{
                                        flex: 1,
                                        padding: '8px 12px',
                                        background: '#0d1117',
                                        border: '1px solid #30363d',
                                        borderRadius: '6px',
                                        color: '#fff',
                                        fontSize: '0.9rem'
                                    }}
                                />
                                <button 
                                    onClick={validateCoupon}
                                    disabled={validatingCoupon}
                                    style={{
                                        padding: '8px 16px',
                                        background: '#238636',
                                        border: 'none',
                                        borderRadius: '6px',
                                        color: '#fff',
                                        cursor: 'pointer',
                                        fontSize: '0.9rem',
                                        fontWeight: 600
                                    }}
                                >
                                    {validatingCoupon ? '...' : 'Aplicar'}
                                </button>
                            </div>
                            {couponError && (
                                <p style={{ color: '#ff4d4d', fontSize: '0.85rem', marginTop: '0.5rem', marginBottom: 0 }}>
                                     {couponError}
                                </p>
                            )}
                        </div>
                    ) : (
                        <div className="summary-row" style={{ color: '#2ecc71' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                                <span>Descuento ({appliedCoupon.code})</span>

                            </div>
                            <span>-{CURRENCY_SYMBOL}{discount.toFixed(2)}</span>
                        </div>
                    )}
                    
                    <div className="summary-total">
                        <div className="total-labels">
                            <strong>Total:</strong>
                        </div>
                        <div className="total-display">
                            <span className="total-amount">${total.toFixed(2)}</span>
                            <span className="total-amount-ves">Bs. {(total * exchangeRate).toFixed(2)}</span>
                        </div>
                    </div>

                    {isProofRequired && !paymentProof && (
                        <p className="mandatory-proof-hint"> Por favor, sube el comprobante para continuar</p>
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
                    <StatusOverlay
                        type={orderStatus}
                        onClose={() => setOrderStatus(null)}
                        serviceType={serviceType}
                        lastOrderId={lastOrderId}
                        vaciarCarrito={vaciarCarrito}
                        navigate={navigate}
                    />
                )}
            </AnimatePresence>

            <div className="checkout-header">
                {/*  Ahora la flecha maneja los pasos internos */}
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
                                                    <button onClick={() => eliminarDelCarrito(item.id)} className="remove-item-btn">
                                                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                                            <path d="M18 6L6 18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                                                            <path d="M6 6L18 18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                                                        </svg>
                                                    </button>
                                                </div>
                                            </div>
                                            <div className="item-price">
                                                <div className="price-primary">${(parseFloat(item.price) * item.cantidad).toFixed(2)}</div>
                                                <div className="price-secondary">Bs. {(parseFloat(item.price) * item.cantidad * exchangeRate).toFixed(2)}</div>
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
                                    <div className="service-icon"></div>
                                    <h3>Comer aquí</h3>
                                    <p>Disfruta de nuestros sabores en el restaurante.</p>
                                </div>
                                <div 
                                    className={`service-card ${serviceType === 'TOGO' ? 'active' : ''}`}
                                    onClick={() => setServiceType('TOGO')}
                                >
                                    <div className="service-icon"></div>
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
                                    <div className="service-icon"></div>
                                    <h3>Pick up</h3>
                                    <p>Tú vienes por el pedido al local.</p>
                                </div>
                                <div 
                                    className={`service-card ${deliveryMode === 'DELIVERY' ? 'active' : ''}`}
                                    onClick={() => setDeliveryMode('DELIVERY')}
                                >
                                    <div className="service-icon"></div>
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
                                <div className="location-icon"></div>
                                <p>Ingresa tu dirección exacta para calcular el delivery.</p>
                                
                                <button 
                                    className="use-location-btn"
                                    onClick={() => {
                                        if (navigator.geolocation) {
                                            navigator.geolocation.getCurrentPosition((pos) => {
                                                const locStr = `${pos.coords.latitude}, ${pos.coords.longitude}`;
                                                setLocation(locStr);
                                                runAIPathfinding(locStr);
                                            }, () => {
                                                alert("No pudimos obtener tu ubicación. Por favor, ingrésala manualmente.");
                                            });
                                        }
                                    }}
                                >
                                    {location && location.includes(',') && !isNaN(parseFloat(location.split(',')[0])) 
                                        ? ' Ubicación GPS Lista' 
                                        : ' Usar GPS Actual'}
                                </button>

                                <div className="manual-location" style={{ marginTop: '1.5rem', position: 'relative' }}>
                                    <label style={{display:'block', marginBottom:'8px', color:'#8b949e'}}>Selecciona tu sector:</label>
                                    <input 
                                        type="text"
                                        placeholder="Ej: Puerta Maraven..."
                                        value={location || ''}
                                        onChange={(e) => handleLocationSearch(e.target.value)}
                                        onFocus={() => {
                                            if(location) handleLocationSearch(location);
                                        }}
                                        style={{
                                            width: '100%',
                                            padding: '12px',
                                            borderRadius: '8px',
                                            border: '1px solid #30363d',
                                            backgroundColor: '#0d1117',
                                            color: '#fff',
                                            marginBottom: '10px'
                                        }}
                                    />
                                    
                                    {/* Autocomplete Dropdown */}
                                    {showSuggestions && filteredLocations.length > 0 && (
                                        <ul style={{
                                            position: 'absolute',
                                            top: '100%',
                                            left: 0,
                                            right: 0,
                                            background: '#161b22',
                                            border: '1px solid #30363d',
                                            borderRadius: '6px',
                                            listStyle: 'none',
                                            padding: '5px 0',
                                            margin: 0,
                                            zIndex: 10,
                                            maxHeight: '200px',
                                            overflowY: 'auto',
                                            boxShadow: '0 4px 12px rgba(0,0,0,0.5)'
                                        }}>
                                            {filteredLocations.map((loc, index) => (
                                                <li 
                                                    key={index}
                                                    onClick={() => selectLocation(loc)}
                                                    style={{
                                                        padding: '10px 15px',
                                                        cursor: 'pointer',
                                                        color: '#c9d1d9',
                                                        borderBottom: index < filteredLocations.length - 1 ? '1px solid #21262d' : 'none'
                                                    }}
                                                    onMouseEnter={(e) => e.target.style.background = '#1f6feb'}
                                                    onMouseLeave={(e) => e.target.style.background = 'transparent'}
                                                >
                                                     {loc}
                                                </li>
                                            ))}
                                        </ul>
                                    )}
                                </div>

                                {isOptimizing && (
                                    <motion.div className="routing-loader" initial={{opacity:0}} animate={{opacity:1}}>
                                        <div className="ai-spinner"></div>
                                        <span>Calculando ruta...</span>
                                    </motion.div>
                                )}

                                {optimalRoute && !isOptimizing && (
                                    <motion.div className="route-result-card" initial={{scale:0.9, opacity:0}} animate={{scale:1, opacity:1}}>
                                        <div className="route-badge">Ruta Estimada</div>
                                        <div className="route-stats">
                                            <span>⏱ {optimalRoute.time}</span>
                                            <span> {optimalRoute.distance}</span>
                                        </div>
                                    </motion.div>
                                )}
                            </div>
                        </div>
                    )}

                    {step === 'METHODS' && (
                        <div className="methods-step">
                            <h2 className="step-title">Selecciona un método de pago</h2>
                            <div className="payment-grid">
                                {PAYMENT_METHODS.filter(m => !(deliveryMode === 'DELIVERY' && m.id === 'efectivo')).map(m => (
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
                                {selectedMethod?.id === 'pagomovil' && (
                                    <div className="data-rows">
                                        <div className="data-row"><span>Banco</span> <strong>Banesco</strong></div>
                                        <div className="data-row"><span>Cédula</span> <strong>20.123.456</strong></div>
                                        <div className="data-row"><span>Teléfono</span> <strong>0412-5556677</strong></div>
                                    </div>
                                )}

                                {selectedMethod?.id === 'zelle' && (
                                    <div className="data-rows">
                                        <div className="data-row"><span>Correo</span> <strong>4restaurant@gmail.com</strong></div>
                                        <div className="data-row"><span>Titular</span> <strong>4 Sabores Restaurant</strong></div>
                                    </div>
                                )}

                                {selectedMethod?.id === 'transferencia' && (
                                     <div className="data-rows">
                                        <div className="data-row"><span>Banco</span> <strong>Banesco</strong></div>
                                        <div className="data-row"><span>Cuenta</span> <strong>0134-0000-00-0000000000</strong></div>
                                        <div className="data-row"><span>Titular</span> <strong>4 Sabores Restaurant</strong></div>
                                    </div>
                                )}
                                
                                {selectedMethod?.id === 'efectivo' && (
                                    <div className="data-rows">
                                        <p style={{color:'#c9d1d9', textAlign:'center', width:'100%'}}>El pago se realizará al momento de la entrega.</p>
                                    </div>
                                )}
                                {selectedMethod?.id !== 'efectivo' && (
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
                                            {paymentProof ? ' Captura Lista' : ' Seleccionar Imagen'}
                                        </label>
                                        
                                        {paymentProof && (
                                            <motion.div 
                                                className="proof-preview"
                                                initial={{ opacity: 0, scale: 0.8 }}
                                                animate={{ opacity: 1, scale: 1 }}
                                            >
                                                <img src={URL.createObjectURL(paymentProof)} alt="Preview" />
                                                <button onClick={() => setPaymentProof(null)} className="remove-proof"></button>
                                            </motion.div>
                                        )}
                                    </div>
                                )}
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