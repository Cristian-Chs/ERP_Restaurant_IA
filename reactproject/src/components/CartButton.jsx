// src/components/CartButton.jsx

import React from 'react';
import { useNavigate } from 'react-router-dom';
import './CartButton.css'; // Asegúrate de crear este CSS

const CartButton = ({ totalItems }) => {
    const navigate = useNavigate();

    return (
        <button 
            className="cart-float-button" 
            onClick={() => navigate('/carrito')}
        >
            
            <div className='icono'>🛒</div> 
            {/* Solo muestra el contador si hay ítems */}
            {totalItems > 0 && (
                <span className="cart-item-count">{totalItems}</span>
            )}
        </button>
    );
};

export default CartButton;