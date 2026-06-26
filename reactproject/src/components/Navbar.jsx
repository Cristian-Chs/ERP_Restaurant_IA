// src/components/Navbar.jsx
import React from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import logo from '../assets/images/logo.jpeg';
import { ShoppingCart, LogOut, UtensilsCrossed } from 'lucide-react'; // Import icons
import './Navbar.css';

const Navbar = () => {
    const location = useLocation();
    const navigate = useNavigate();
    const [isMenuOpen, setIsMenuOpen] = React.useState(false);
    
    const token = localStorage.getItem('token');
    const rol = localStorage.getItem('rol');
    const isAdmin = rol === 'admin';
    const isChef = rol === 'chef';

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
    const hideOnRoutes = ['/', '/Login', '/login', '/register', '/forgot-password'];
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
                {/* Logo Section */}
                <Link to="/menu" className="navbar-logo">
                    {/* Use Icon if logo image fails/not desired, or keep exact logo */}
                    <div className="logo-img" style={{display:'flex', alignItems:'center', justifyContent:'center', background:'white', padding:'2px'}}>
                         <UtensilsCrossed size={24} color="#ef4444" />
                    </div>
                    {/* <img src={logo} alt="4 Sabores" className="logo-img" /> */}
                    <span className="brand-name">Sabor Venezolano</span>
                </Link>

                {/* Right Actions */}
                <div className="navbar-links">
                    <span className="nav-greeting">¡Hola, cliente!</span>

                    {/* Cart Button (Icon) */}
                    <button className="nav-icon-btn" onClick={() => navigate('/carrito')}>
                         <ShoppingCart size={20} />
                    </button>

                    {/* Logout/Menu Button (Icon) */}
                    <div className="dropdown-wrapper">
                        <button 
                            className="nav-icon-btn"
                            onClick={() => setIsMenuOpen(!isMenuOpen)}
                        >
                            <LogOut size={20} style={{transform: isMenuOpen ? 'rotate(180deg)' : 'none'}}/> 
                            {/* Or use <MenuIcon /> and put Logout inside dropdown. Source has Logout icon directly? 
                                Screenshot shows Logout icon. Let's assume it logs out or opens menu. 
                                For now, let's keep the dropdown functionality but use the icon trigger.
                            */}
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
                                    {(isAdmin || isChef) && (
                                        <>
                                            <Link to="/kitchen-panel" className="dropdown-item">Cocina</Link>
                                            <Link to="/admin" className="dropdown-item">Admin</Link>
                                        </>
                                    )}
                                    <Link to="/profile" className="dropdown-item">
                                         Editar Perfil
                                    </Link>
                                    <button onClick={handleLogout} className="dropdown-item logout">
                                         Cerrar Sesión
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

