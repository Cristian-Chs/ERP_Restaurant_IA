from django.contrib import admin
from telegram import Bot
from .models import Order, Rating, GustoCliente, Coupon, RedeemedCoupon

#  Configuración
BOT_TOKEN_CLIENTE = "537597604:AAFyajyokOXKShw5Zx9UNh5likds4FUmUHU"
CHEF_CHAT_ID = 1234567890
ADMIN_CHAT_ID = 5719602467


def notificar_cliente(order):
    bot = Bot(token=BOT_TOKEN_CLIENTE)
    bot.send_message(
        chat_id=order.telegram_id,
        text=f" Tu pedido '{order.item}' está listo. ¡Buen provecho!"
    )


def notificar_chef(order):
    bot = Bot(token=BOT_TOKEN_CLIENTE)
    mensaje = (
        f"‍ Pedido LISTO:\n\n"
        f"{order.item}\n\n"
        f" Cliente: {order.telegram_id}\n"
        f" Hora: {order.fecha.strftime('%d/%m/%Y %H:%M')}"
    )
    bot.send_message(chat_id=CHEF_CHAT_ID, text=mensaje)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id", 
        "item", 
        "telegram_id", 
        "status", 
        "payment_status_display",
        "payment_verified_at",
        "fecha"
    )
    list_filter = (
        "status", 
        "payment_status",
        "fecha",
        "payment_verified_at"
    )
    search_fields = (
        "item", 
        "telegram_id",
        "payment_receipt_file_id",
        "id"
    )
    actions = ["marcar_listo", "aprobar_pago_admin", "rechazar_pago_admin"]
    
    readonly_fields = (
        "payment_receipt_file_id",
        "payment_verified_at",
        "payment_verified_by",
        "payment_data_display",
        "fecha"
    )
    
    fieldsets = (
        ('Información del Pedido', {
            'fields': ('telegram_id', 'item', 'status', 'fecha')
        }),
        ('Información de Pago', {
            'fields': (
                'payment_status',
                'payment_receipt_file_id',
                'payment_verified_at',
                'payment_verified_by',
                'payment_data_display'
            )
        }),
    )

    def payment_status_display(self, obj):
        """Mostrar estado de pago con colores"""
        colors = {
            'pending_payment': '🟡',
            'payment_submitted': '',
            'payment_approved': '🟢',
            'payment_rejected': '',
        }
        icon = colors.get(obj.payment_status, '')
        return f"{icon} {obj.get_payment_status_display()}"
    payment_status_display.short_description = "Estado de Pago"
    
    def payment_data_display(self, obj):
        """Mostrar datos extraídos del comprobante"""
        if obj.payment_data:
            import json
            data = json.dumps(obj.payment_data, indent=2, ensure_ascii=False)
            return f"<pre>{data}</pre>"
        return "Sin datos"
    payment_data_display.short_description = "Datos del Comprobante"
    payment_data_display.allow_tags = True

    def marcar_listo(self, request, queryset):
        for order in queryset:
            order.status = "listo"
            order.save()
            notificar_cliente(order)
            notificar_chef(order)
        self.message_user(request, "Pedidos marcados como listos.")
    marcar_listo.short_description = "Marcar pedidos seleccionados como listos"
    
    def aprobar_pago_admin(self, request, queryset):
        """Aprobar pagos desde el admin"""
        from django.utils import timezone
        count = 0
        for order in queryset.filter(payment_status='payment_submitted'):
            order.payment_status = 'payment_approved'
            order.payment_verified_at = timezone.now()
            order.payment_verified_by = request.user.id if hasattr(request.user, 'id') else None
            order.status = 'confirmado'
            order.save()
            count += 1
        self.message_user(request, f"{count} pago(s) aprobado(s).")
    aprobar_pago_admin.short_description = " Aprobar pagos seleccionados"
    
    def rechazar_pago_admin(self, request, queryset):
        """Rechazar pagos desde el admin"""
        from django.utils import timezone
        count = 0
        for order in queryset.filter(payment_status='payment_submitted'):
            order.payment_status = 'payment_rejected'
            order.payment_verified_at = timezone.now()
            order.payment_verified_by = request.user.id if hasattr(request.user, 'id') else None
            order.status = 'cancelado'
            order.save()
            count += 1
        self.message_user(request, f"{count} pago(s) rechazado(s).")
    rechazar_pago_admin.short_description = " Rechazar pagos seleccionados"


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ("plato", "telegram_id", "estrellas", "fecha")
    list_filter = ("estrellas", "fecha")
    search_fields = ("plato", "telegram_id")


@admin.register(GustoCliente)
class GustoClienteAdmin(admin.ModelAdmin):
    list_display = ("telegram_id",)
    search_fields = ("telegram_id",)


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "discount_display",
        "discount_type",
        "points_cost",
        "is_active_display",
        "usage_display",
        "valid_until"
    )
    list_filter = ("is_active", "discount_type", "fecha_creacion", "valid_until")
    search_fields = ("code",)
    readonly_fields = ("current_uses", "fecha_creacion")
    actions = ["activate_coupons", "deactivate_coupons", "reset_usage"]
    
    fieldsets = (
        (' Información del Cupón', {
            'fields': ('code', 'discount_type', 'discount_amount', 'points_cost')
        }),
        ('⏰ Validez y Límites', {
            'fields': ('is_active', 'valid_from', 'valid_until', 'max_uses', 'current_uses')
        }),
        (' Restricciones', {
            'fields': ('min_order_amount',)
        }),
        (' Información del Sistema', {
            'fields': ('fecha_creacion',),
            'classes': ('collapse',)
        }),
    )
    
    def discount_display(self, obj):
        """Muestra el descuento de forma visual"""
        if obj.discount_type == 'fixed':
            return f" ${obj.discount_amount}"
        else:
            return f" {obj.discount_amount}%"
    discount_display.short_description = "Descuento"
    
    def is_active_display(self, obj):
        """Muestra estado activo con íconos"""
        if obj.is_active:
            return " Activo"
        return " Inactivo"
    is_active_display.short_description = "Estado"
    
    def usage_display(self, obj):
        """Muestra uso actual vs máximo"""
        if obj.max_uses == 0:
            return f"{obj.current_uses} / ∞"
        
        percentage = (obj.current_uses / obj.max_uses * 100) if obj.max_uses > 0 else 0
        if percentage >= 100:
            icon = ""
        elif percentage >= 75:
            icon = "🟡"
        else:
            icon = "🟢"
        
        return f"{icon} {obj.current_uses} / {obj.max_uses}"
    usage_display.short_description = "Uso"
    
    def activate_coupons(self, request, queryset):
        """Activa los cupones seleccionados"""
        count = queryset.update(is_active=True)
        self.message_user(request, f"{count} cupón(es) activado(s).")
    activate_coupons.short_description = " Activar cupones seleccionados"
    
    def deactivate_coupons(self, request, queryset):
        """Desactiva los cupones seleccionados"""
        count = queryset.update(is_active=False)
        self.message_user(request, f"{count} cupón(es) desactivado(s).")
    deactivate_coupons.short_description = " Desactivar cupones seleccionados"
    
    def reset_usage(self, request, queryset):
        """Reinicia el contador de usos"""
        count = queryset.update(current_uses=0)
        self.message_user(request, f"Contador de usos reiniciado para {count} cupón(es).")
    reset_usage.short_description = " Reiniciar contador de usos"


@admin.register(RedeemedCoupon)
class RedeemedCouponAdmin(admin.ModelAdmin):
    list_display = (
        "coupon_code_display",
        "telegram_id",
        "discount_display",
        "fecha_canje",
        "order_link"
    )
    list_filter = ("fecha_canje", "coupon")
    search_fields = ("telegram_id", "coupon__code")
    readonly_fields = ("fecha_canje", "discount_applied")
    date_hierarchy = "fecha_canje"
    
    def coupon_code_display(self, obj):
        """Muestra el código del cupón"""
        return f" {obj.coupon.code}"
    coupon_code_display.short_description = "Cupón"
    
    def discount_display(self, obj):
        """Muestra el descuento aplicado"""
        return f" ${obj.discount_applied}"
    discount_display.short_description = "Descuento Aplicado"
    
    def order_link(self, obj):
        """Link a la orden si existe"""
        if obj.order:
            from django.urls import reverse
            from django.utils.html import format_html
            url = reverse("admin:bot_order_change", args=[obj.order.id])
            return format_html('<a href="{}">Orden #{}</a>', url, obj.order.id)
        return "-"
    order_link.short_description = "Orden"
    order_link.allow_tags = True
