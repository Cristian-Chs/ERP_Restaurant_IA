from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from .utils import notificar_pedido_listo
from core.models import Product #  Importamos productos para análisis ML


#  Modelo principal de pedidos
class Order(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('pending_payment', 'Esperando Pago'),
        ('payment_submitted', 'Pago Enviado'),
        ('payment_approved', 'Pago Aprobado'),
        ('payment_rejected', 'Pago Rechazado'),
    ]
    
    telegram_id = models.BigIntegerField()
    item = models.CharField(max_length=255)
    precio = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    status = models.CharField(max_length=50, default="pendiente")
    fecha = models.DateTimeField(auto_now_add=True)
    
    #  Nuevos campos de logística
    service_type = models.CharField(max_length=20, choices=[('AQUI', 'Comer Aquí'), ('LLEVAR', 'Para Llevar')], default='AQUI')
    delivery_mode = models.CharField(max_length=20, choices=[('RETIRO', 'Retiro en Local'), ('DELIVERY', 'Delivery')], blank=True, null=True)
    location = models.TextField(blank=True, null=True) # Dirección manual o coordenadas
    
    #  Campos de verificación de pago
    payment_status = models.CharField(
        max_length=20, 
        choices=PAYMENT_STATUS_CHOICES, 
        default='pending_payment'
    )
    payment_receipt_file_id = models.CharField(max_length=255, blank=True, null=True)
    payment_proof = models.ImageField(upload_to='payments/', blank=True, null=True) # Captura subida desde web
    payment_verified_at = models.DateTimeField(blank=True, null=True)
    payment_verified_by = models.BigIntegerField(blank=True, null=True)
    payment_data = models.JSONField(blank=True, null=True)
    payment_hash = models.CharField(max_length=64, blank=True, null=True, db_index=True) # Hash perceptual para evitar duplicados
    
    #  Ruta de la factura generada
    invoice_path = models.CharField(max_length=500, blank=True, null=True)

    # Identificación del cliente (Web/Telegram)
    customer_name = models.CharField(max_length=255, blank=True, null=True)

    #  Finanzas Multi-moneda
    currency = models.CharField(max_length=5, default='USD')
    exchange_rate = models.DecimalField(max_digits=10, decimal_places=2, default=1.0)

    def __str__(self):
        return f"{self.item} - Cliente {self.telegram_id}"


#  Rating de platos (para IA)
class Rating(models.Model):
    telegram_id = models.BigIntegerField()
    plato = models.CharField(max_length=255)
    estrellas = models.IntegerField(choices=[(i, f"{i} ") for i in range(1, 6)])
    comentario = models.TextField(blank=True, null=True) #  Feedback textual
    sentimiento = models.CharField(max_length=20, blank=True, null=True) #  Positivo, Neutral, Negativo
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.plato} - {self.estrellas} - {self.telegram_id}"


#  Gustos del cliente (para IA personalizada)
class GustoCliente(models.Model):
    telegram_id = models.BigIntegerField(unique=True)
    gustos = models.JSONField(default=list)  # Ej: ["pollo", "queso", "pasta"]

    def __str__(self):
        return f"Gustos de {self.telegram_id}"


#  Notificación automática cuando un pedido cambia a "listo"
@receiver(post_save, sender=Order)
def enviar_notificacion(sender, instance, **kwargs):
    if instance.status == "listo":
        #  Generar factura si no existe
        if not instance.invoice_path:
            try:
                from bot.factura import InvoiceGenerator
                generator = InvoiceGenerator()
                invoice_path = generator.generate(instance)
                instance.invoice_path = invoice_path
                instance.save(update_fields=['invoice_path'])
                print(f"✅ Factura generada: {invoice_path}")
            except Exception as e:
                print(f"❌ Error generando factura: {e}")
        
        #  Notificar al cliente con factura
        notificar_pedido_listo(instance.telegram_id, instance.item, instance.invoice_path)
        
        #  Agregar Puntos de Fidelización (Fase 9)
        loyalty, created = LoyaltyPoints.objects.get_or_create(telegram_id=instance.telegram_id)
        puntos_ganados = loyalty.agregar_puntos(instance.precio)

class PedidoPersonalizado(models.Model):
    telegram_id = models.BigIntegerField()
    producto = models.CharField(max_length=255)
    removidos = models.JSONField(default=list)   # ["Tomate", "Mostaza"]
    agregados = models.JSONField(default=list)   # ["Cebolla extra"]
    pedido_final = models.CharField(max_length=255)
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.producto} ({self.telegram_id})"
    
class PreferenciaIngrediente(models.Model):
    telegram_id = models.BigIntegerField()
    ingrediente = models.CharField(max_length=100)
    gusta = models.BooleanField()  # True = le gusta, False = no le gusta
    contador = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.ingrediente} ({'gusta' if self.gusta else 'no gusta'})"




#  Sesión de Telegram para Máquina de Estados
class TelegramSession(models.Model):
    telegram_id = models.BigIntegerField(unique=True)
    state = models.CharField(max_length=50, default="IDLE")
    current_product_id = models.IntegerField(null=True, blank=True)
    temp_data = models.JSONField(default=dict, blank=True)
    last_interaction = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Session {self.telegram_id} - {self.state}"


#  Modelo para detectar fraude por duplicados visuales
class PaymentHash(models.Model):
    hash_value = models.CharField(max_length=64, unique=True, db_index=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='hashes')
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Hash {self.hash_value[:10]}... (Orden {self.order_id})"


#  Sistema de Fidelización
class LoyaltyPoints(models.Model):
    telegram_id = models.BigIntegerField(unique=True)
    puntos = models.IntegerField(default=0)
    nivel = models.CharField(max_length=50, default="Bronce")
    total_gastado = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    ultima_actualizacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cliente {self.telegram_id} - {self.puntos} pts ({self.nivel})"

    def agregar_puntos(self, monto):
        """
        Agrega 1 punto por cada $1 gastado.
        """
        puntos_nuevos = int(float(monto))
        self.puntos += puntos_nuevos
        self.total_gastado += monto
        
        # Lógica de niveles (ejemplo)
        if self.total_gastado > 500:
            self.nivel = "Diamante"
        elif self.total_gastado > 200:
            self.nivel = "Oro"
        elif self.total_gastado > 100:
            self.nivel = "Plata"
            
        self.save()
        return puntos_nuevos
    
    def redeem_points(self, points_to_redeem):
        """
        Canjea puntos por descuento. 
        Retorna el monto de descuento en USD o None si no tiene suficientes puntos.
        Conversión: 10 puntos = $1 de descuento
        """
        if self.puntos >= points_to_redeem:
            self.puntos -= points_to_redeem
            self.save()
            discount_amount = points_to_redeem / 25.0  # 10 puntos = $1
            return discount_amount
        return None


#  Modelo para desglosar ítems de un pedido (Estructura para ML)
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items_detalle')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='ventas')
    cantidad = models.IntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2) # Precio capturado en el momento de la venta
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.cantidad}x {self.product.name} (Orden {self.order.id})"


#  Sistema de Cupones
class Coupon(models.Model):
    COUPON_TYPE_CHOICES = [
        ('fixed', 'Descuento Fijo'),
        ('percentage', 'Porcentaje'),
    ]
    
    code = models.CharField(max_length=50, unique=True, db_index=True)  # Ej: "PROMO2026"
    discount_type = models.CharField(max_length=20, choices=COUPON_TYPE_CHOICES, default='fixed')
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2)  # $5 o 10 (para 10%)
    points_cost = models.IntegerField(default=0, help_text="Puntos necesarios para canjear (0 = cupón manual)")
    
    # Validez
    is_active = models.BooleanField(default=True)
    valid_from = models.DateTimeField(blank=True, null=True)
    valid_until = models.DateTimeField(blank=True, null=True)
    max_uses = models.IntegerField(default=0, help_text="0 = ilimitado")
    current_uses = models.IntegerField(default=0)
    
    # Restricciones
    min_order_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.code} (-${self.discount_amount})"
    
    def is_valid(self):
        """Verifica si el cupón está activo y dentro del período de validez"""
        from django.utils import timezone
        now = timezone.now()
        
        if not self.is_active:
            return False
        
        if self.valid_from and now < self.valid_from:
            return False
            
        if self.valid_until and now > self.valid_until:
            return False
        
        if self.max_uses > 0 and self.current_uses >= self.max_uses:
            return False
            
        return True
    
    def apply_discount(self, order_amount):
        """Calcula el descuento aplicable al monto del pedido"""
        if not self.is_valid():
            return 0
        
        if order_amount < self.min_order_amount:
            return 0
        
        if self.discount_type == 'fixed':
            return min(float(self.discount_amount), float(order_amount))
        else:  # percentage
            return float(order_amount) * (float(self.discount_amount) / 100.0)


class RedeemedCoupon(models.Model):
    """Registro de cupones canjeados por usuarios"""
    telegram_id = models.BigIntegerField()
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE, related_name='redemptions')
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True, related_name='coupons_used')
    discount_applied = models.DecimalField(max_digits=10, decimal_places=2)
    customer_name = models.CharField(max_length=255, blank=True, null=True)
    fecha_canje = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.coupon.code} - Usuario {self.telegram_id}"
