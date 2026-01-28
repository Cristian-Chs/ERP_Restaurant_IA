from django.contrib.admin import AdminSite


class CouponAdminSite(AdminSite):
    """
    Panel de administración dedicado para la gestión de cupones y promociones
    """
    site_header = " Panel de Cupones y Promociones"
    site_title = "Gestión de Cupones"
    index_title = "Administración de Cupones"
    
    def get_app_list(self, request):
        """
        Personaliza la lista de aplicaciones mostradas
        """
        app_list = super().get_app_list(request)
        
        # Reordenar para mostrar primero los cupones
        for app in app_list:
            if app['app_label'] == 'bot':
                # Filtrar solo modelos relacionados con cupones
                app['models'] = [
                    model for model in app['models']
                    if model['object_name'] in ['Coupon', 'RedeemedCoupon', 'LoyaltyPoints']
                ]
        
        return app_list


# Instancia del sitio de cupones
coupon_admin_site = CouponAdminSite(name='coupon_admin')
