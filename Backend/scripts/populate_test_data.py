import random
from datetime import timedelta
from django.utils import timezone
from bot.models import Order, OrderItem
from core.models import Product

def populate_test_data():
    print("Iniciando población de datos de prueba...")
    
    # Clientes de prueba
    customers = [
        {'id': 1001, 'name': 'Juan Perez'},
        {'id': 1002, 'name': 'Maria Garcia'},
        {'id': 1003, 'name': 'Carlos Rodriguez'},
        {'id': 1004, 'name': 'Ana Martinez'},
        {'id': 1005, 'name': 'Luis Hernandez'},
    ]
    
    # Obtener productos existentes
    products = list(Product.objects.filter(is_active=True))
    if not products:
        print("Error: No hay productos activos en la base de datos.")
        return

    # Limpiar datos previos si es necesario (opcional)
    # Order.objects.filter(telegram_id__in=[c['id'] for c in customers]).delete()

    now = timezone.now()
    
    # Generar entre 20 y 30 pedidos
    num_orders = random.randint(20, 30)
    
    for _ in range(num_orders):
        customer = random.choice(customers)
        # Fecha aleatoria en los últimos 7 días
        days_ago = random.randint(0, 6)
        hours_ago = random.randint(0, 23)
        minutes_ago = random.randint(0, 59)
        order_date = now - timedelta(days=days_ago, hours=hours_ago, minutes=minutes_ago)
        
        # Crear la orden
        status = random.choice(['listo', 'pendiente', 'entregado'])
        payment_status = random.choice(['payment_approved', 'payment_submitted', 'pending_payment'])
        
        # Si el pago está aprobado, la orden suele estar en un estado más avanzado
        if payment_status == 'payment_approved':
            status = random.choice(['listo', 'entregado'])
        
        order = Order.objects.create(
            telegram_id=customer['id'],
            customer_name=customer['name'],
            item="Pedido de Prueba", # Se actualizará después o se usa como resumen
            precio=0, # Se calculará sumando los items
            status=status,
            payment_status=payment_status,
            currency='USD',
            exchange_rate=1.0,
            service_type=random.choice(['HERE', 'TOGO']),
            delivery_mode=random.choice(['PICKUP', 'DELIVERY']) if random.random() > 0.5 else None,
        )
        
        # Forzar la fecha de creación (auto_now_add=True no permite setearla en el create)
        order.fecha = order_date
        order.save()
        
        # Añadir items a la orden (1 a 4 items)
        num_items = random.randint(1, 4)
        total_price = 0
        items_summary = []
        
        selected_products = random.sample(products, min(num_items, len(products)))
        
        for product in selected_products:
            qty = random.randint(1, 2)
            item_price = product.price
            
            OrderItem.objects.create(
                order=order,
                product=product,
                cantidad=qty,
                precio_unitario=item_price,
                fecha=order_date # También forzamos la fecha para que coincida
            )
            
            total_price += item_price * qty
            items_summary.append(f"{qty}x {product.name}")
            
        # Actualizar el resumen del pedido y el precio total
        order.item = ", ".join(items_summary)[:255]
        order.precio = total_price
        order.save()
        
        # Forzar fecha de creación de los items después de guardarlos
        OrderItem.objects.filter(order=order).update(fecha=order_date)

    print(f"Población completada. Se crearon {num_orders} pedidos.")

if __name__ == "__main__":
    populate_test_data()
