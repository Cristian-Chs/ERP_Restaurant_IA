import React from 'react';
import { Navigate } from 'react-router-dom';

/**
 * Componente Wrapper para proteger rutas.
 * Redirige a /Login si el usuario no está autenticado.
 * @param {object} children - El componente que se quiere proteger (e.g., <AdminPanel />)
 * @param {boolean} isAuthenticated - El estado de autenticación del usuario.
 */
function ProtectedRoute({ children, isAuthenticated }) {
    // Si el usuario NO está autenticado, lo redirige a la página de Login.
    if (!isAuthenticated) {
        return <Navigate to="/Login" replace />;
    }

    // Si está autenticado, permite el acceso al componente.
    return children;
}

export default ProtectedRoute;  