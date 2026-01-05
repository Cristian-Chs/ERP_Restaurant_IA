// src/components/Navbar.jsx
import React from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import logo from '../assets/images/logo.jpeg';
import './Navbar.css';

const Navbar = () => {
    const location = useLocation();
    const navigate = useNavigate();
    const [isMenuOpen, setIsMenuOpen] = React.useState(false);
    
    const token = localStorage.getItem('token');
    const rol = localStorage.getItem('rol');

    // Cerrar el menú al cambiar de ruta
    React.useEffect(() => {
        setIsMenuOpen(false);
    }, [location.pathname]);

    const handleLogout = () => {
        localStorage.removeItem('token');
        localStorage.removeItem('rol');
        navigate('/Login');
    };
    
    // Lista de rutas donde NO debe aparecer el Navbar (autenticación y landing)
    const hideOnRoutes = ['/', '/Login', '/login', '/register', '/forgot-password','/kitchen-panel','/admin'];
    const isAuthRoute = hideOnRoutes.includes(location.pathname) || location.pathname.startsWith('/reset-password');
    
    // El Navbar SOLO aparece si hay un token Y no estamos en páginas de autenticación
    if (!token || isAuthRoute) return null;

    return (
        <motion.nav 
            className="global-navbar"
            initial={{ y: -100 }}
            animate={{ y: 0 }}
            transition={{ duration: 0.5 }}
        >
            <div className="navbar-container">
                <Link to="/menu" className="navbar-logo">
                    <img src={logo} alt="4 Sabores" className="logo-img" />
                    <span className="brand-name">4 SABORES</span>
                </Link>

                <div className="navbar-links">
                    <Link 
                        to="/menu" 
                        className={`nav-link ${location.pathname === '/menu' ? 'active' : ''}`}
                    >
                        Menú
                    </Link>
                    

                    {/* Menú Desplegable ::: */}
                    <div className="dropdown-wrapper">
                        <button 
                            className={`dropdown-trigger ${isMenuOpen ? 'open' : ''}`}
                            onClick={() => setIsMenuOpen(!isMenuOpen)}
                        >...
                        </button>

                        <AnimatePresence>
                            {isMenuOpen && (
                                <motion.div 
                                    className="nav-dropdown-menu"
                                    initial={{ opacity: 0, y: 10, scale: 0.95 }}
                                    animate={{ opacity: 1, y: 0, scale: 1 }}
                                    exit={{ opacity: 0, y: 10, scale: 0.95 }}
                                    transition={{ duration: 0.2 }}
                                >
                                    <Link to="/profile" className="dropdown-item">
                                        👤 Editar Perfil
                                    </Link>
                                    <button onClick={handleLogout} className="dropdown-item logout">
                                        🚪 Cerrar Sesión
                                    </button>
                                </motion.div>
                            )}
                        </AnimatePresence>
                    </div>
                </div>
            </div>
        </motion.nav>
    );
};

export default Navbar;
