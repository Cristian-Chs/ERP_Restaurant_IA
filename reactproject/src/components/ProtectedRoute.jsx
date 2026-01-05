import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';

const ProtectedRoute = ({ children, requiredRole }) => {
    const token = localStorage.getItem('token');
    const location = useLocation();

    if (!token) {
        return <Navigate to="/Login" state={{ from: location }} replace />;
    }

    try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        const userRole = payload.rol;

        if (requiredRole && userRole !== requiredRole) {
            // Si el rol no coincide, redirigir al menú (o página permitida)
            return <Navigate to="/menu" replace />;
        }
    } catch (e) {
        console.error("Error validando token en ProtectedRoute", e);
        return <Navigate to="/Login" replace />;
    }

    return children;
};

export default ProtectedRoute;