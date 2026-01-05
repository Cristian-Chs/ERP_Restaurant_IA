// src/components/PlatilloOpciones.jsx

/**
 * Componente selector de opciones (ej. sabores dinámicos).
 * @param {string} id - ID único del producto.
 * @param {string} selectedOption - El sabor seleccionado.
 * @param {function} onOptionChange - Función para cambiar el sabor.
 * @param {array} opciones - Lista de strings con los nombres de los sabores.
 */
export default function PlatilloOpciones({ id, selectedOption, onOptionChange, opciones = [] }) {
    
    // Estilos para los radio buttons
    const optionStyle = {
        margin: '10px 0',
        fontSize: '14px',
        color: '#333', // Cambiado a negro para mejor visibilidad
    };

    const labelStyle = {
        display: 'inline-block',
        marginRight: '10px',
        cursor: 'pointer',
    };

    return (
        <div className="platillo-opciones-selector" style={optionStyle}>
            <p style={{ margin: '5px 0 10px 0', fontSize: '14px', color: '#555' }}>
                ¿Qué tipo deseas?
            </p>
            
            {opciones.map((opcion) => (
                <label key={`${id}-${opcion}`} style={labelStyle}>
                    <input
                        type="checkbox"
                        checked={selectedOption === opcion}
                        onChange={() => {
                            const nextValue = selectedOption === opcion ? '' : opcion;
                            onOptionChange(nextValue);
                        }}
                        style={{ marginRight: '5px' }}
                    />
                    {opcion}
                </label>
            ))}
        </div>
    );
}