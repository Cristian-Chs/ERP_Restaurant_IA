import React from 'react';

const ProductForm = ({ newItem, setNewItem, ingredients, flavors, onSave, onCancel, isEditing }) => (
  <div className="form-container inline">
    <h2 className="form-title">{isEditing ? ' Editar Platillo' : ' Nuevo Platillo'}</h2>

    <div className="form-group-inline">
      <label>Nombre:</label>
      <input className="form-input" placeholder="Ej: Hamburguesa Especial" value={newItem.name} onChange={e => setNewItem({...newItem, name: e.target.value})} />
    </div>

    <div className="form-group-inline">
      <label>Precio ($):</label>
      <input className="form-input" type="number" placeholder="0.00" value={newItem.price} onChange={e => setNewItem({...newItem, price: e.target.value})} />
    </div>

    <div className="form-group-inline">
      <label>Costo ($):</label>
      <input className="form-input" type="number" placeholder="0.00" value={newItem.cost_price || ''} onChange={e => setNewItem({...newItem, cost_price: e.target.value})} />
    </div>

    <div className="form-group-inline">
      <label>Imagen:</label>
      <div style={{ flex: 1 }}>
        <input className="form-input" placeholder="Nombre de la imagen (ej: pizza.png)" value={newItem.imagen || ''} onChange={e => setNewItem({...newItem, imagen: e.target.value})} />
        <small className="help-text">Ej: burguer.png</small>
      </div>
    </div>

    <div className="form-group-inline">
      <label>Categoría:</label>
      <select className="form-input" value={newItem.category} onChange={e => setNewItem({...newItem, category: e.target.value})}>
        <option value="entradas">Entradas</option>
        <option value="principales">Principales</option>
        <option value="postres">Postres</option>
        <option value="bebidas">Bebidas</option>
        <option value="promociones">Promociones</option>
      </select>
    </div>

    <div className="form-group-inline">
      <label>Descripción:</label>
      <textarea className="form-input" placeholder="Descripción breve..." value={newItem.description} onChange={e => setNewItem({...newItem, description: e.target.value})} />
    </div>

    <div className="form-group">
      <label>Ingredientes:</label>
      <div className="tag-list clickable">
        {ingredients.map(ing => (
          <button
            key={ing.id}
            className={`tag-mini ${newItem.ingredientes?.includes(ing.id) ? 'active' : ''}`}
            onClick={(e) => {
              e.preventDefault();
              const updated = newItem.ingredientes?.includes(ing.id)
                ? newItem.ingredientes.filter(i => i !== ing.id)
                : [...(newItem.ingredientes || []), ing.id];
              setNewItem({...newItem, ingredientes: updated});
            }}
          >
            {ing.nombre}
          </button>
        ))}
      </div>
    </div>

    <div className="form-group">
      <label>Sabores:</label>
      <div className="tag-list clickable">
        {flavors.map(flav => (
          <button
            key={flav.id}
            className={`tag-mini ${newItem.sabores?.includes(flav.id) ? 'active' : ''}`}
            onClick={(e) => {
              e.preventDefault();
              const updated = newItem.sabores?.includes(flav.id)
                ? newItem.sabores.filter(i => i !== flav.id)
                : [...(newItem.sabores || []), flav.id];
              setNewItem({...newItem, sabores: updated});
            }}
          >
            {flav.nombre}
          </button>
        ))}
      </div>
    </div>

    <div className="form-actions">
      <button className="btn-secondary" onClick={onCancel}>Cancelar</button>
      <button className="btn-primary" onClick={onSave}>Guardar</button>
    </div>
  </div>
);

export default ProductForm;
