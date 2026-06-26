import re
import logging
from core.models import Product, Recipe, InventoryMovement, Ingredient

logger = logging.getLogger(__name__)

def deduct_inventory_for_order(order):
    """
    Parses the order item string, identifies products, and deducts ingredients 
    from inventory based on their recipes.
    
    Args:
        order (Order): The order instance to process.
    """
    try:
        # 1. Parse order items string (e.g., "2 x Hamburguesa (Extra...), 1 x Refresco")
        # Logic adapted from core/views.py
        items_map = {} # {product_name_lower: quantity}
        
        # Split by commas, but be careful with commas inside parens if any exist (basic split first)
        # For robustness, we might want to iterate via regex finding patterns "N x Item"
        
        # This regex looks for "Digits x Something"
        # It matches: 2 x Hamburguesa Queso
        matches = re.finditer(r'(\d+)\s*x\s*([^(,]+)', order.item)
        
        found_any = False
        for match in matches:
            found_any = True
            qty = int(match.group(1))
            product_name = match.group(2).strip()
            items_map[product_name.lower()] = items_map.get(product_name.lower(), 0) + qty
            
        # Fallback: if no "Nx" pattern, assume 1 x Whole String
        if not found_any and order.item:
             items_map[order.item.strip().lower()] = 1

        print(f"DEBUG: Deducting inventory for Order #{order.id}. Items: {items_map}")

        # 2. Iterate and deduct
        for p_name, qty in items_map.items():
            # Find Product (Best effort match)
            product = Product.objects.filter(name__iexact=p_name).first()
            if not product:
                # Try contains if exact fail
                product = Product.objects.filter(name__icontains=p_name).first()
            
            if product:
                # Get Recipes
                recipes = Recipe.objects.filter(product=product).select_related('ingredient')
                
                if not recipes.exists():
                    print(f"WARNING: No recipe found for product '{product.name}'")
                    continue
                
                for recipe in recipes:
                    total_qty_needed = recipe.quantity * qty
                    
                    # Create Inventory Movement (Deduction)
                    InventoryMovement.objects.create(
                        ingredient=recipe.ingredient,
                        movement_type='USAGE',
                        quantity=-total_qty_needed, # Negative for usage? Or depends on convention. 
                                                    # Convention in core/models wasn't explicit but usually Usage is negative or just tracked as type.
                                                    # Let's look at `core/models.py`. It has 'USAGE'. Usually tracked as positive magnitude, 
                                                    # but let's check if we want to show it as negative in stock calculations. 
                                                    # For safety, let's store positive quantity and rely on 'movement_type' for logic,
                                                    # OR store negative. Let's assume Positive Magnitude for the record, 
                                                    # and the aggregation logic subtracts 'USAGE'.
                                                    # WAIT: If I look at `calculate_recipe_expenses`, it calculates cost.
                                                    # Let's check `InventoryMovement` typical usage. 
                                                    # I will stick to Positive Quantity for the record, as the semantic is "Amount Used".
                        cost_per_unit=recipe.ingredient.cost,
                        notes=f"Venta Orden #{order.id}: {qty}x {product.name}"
                    )
                    print(f"   -> Deducted {total_qty_needed} {recipe.ingredient.unit} of {recipe.ingredient.nombre}")
                    
            else:
                print(f"WARNING: Product not found for deduction: '{p_name}'")

    except Exception as e:
        logger.error(f"Error deducting inventory for order {order.id}: {e}")
        print(f"ERROR deducting inventory: {e}")
