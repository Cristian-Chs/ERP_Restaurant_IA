from django.urls import path
from .coupon_admin import coupon_admin_site
from .models import Coupon, RedeemedCoupon, LoyaltyPoints
from .admin import CouponAdmin, RedeemedCouponAdmin

# Registrar modelos en el sitio de cupones
coupon_admin_site.register(Coupon, CouponAdmin)
coupon_admin_site.register(RedeemedCoupon, RedeemedCouponAdmin)

# Opcional: También registrar LoyaltyPoints para gestión de puntos
from django.contrib import admin

class LoyaltyPointsAdminForCoupons(admin.ModelAdmin):
    list_display = ("telegram_id", "puntos", "nivel", "total_gastado", "ultima_actualizacion")
    search_fields = ("telegram_id",)
    list_filter = ("nivel", "ultima_actualizacion")
    readonly_fields = ("ultima_actualizacion",)
    
    fieldsets = (
        (' Usuario', {
            'fields': ('telegram_id',)
        }),
        (' Puntos y Nivel', {
            'fields': ('puntos', 'nivel', 'total_gastado')
        }),
        (' Información', {
            'fields': ('ultima_actualizacion',)
        }),
    )

coupon_admin_site.register(LoyaltyPoints, LoyaltyPointsAdminForCoupons)

urlpatterns = [
    path('', coupon_admin_site.urls),
]
