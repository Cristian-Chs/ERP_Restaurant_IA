import logging
from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from ..models import Order
from ..serializers import OrderSerializer
from ..inventory_service import deduct_inventory_for_order

logger = logging.getLogger(__name__)


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        user = self.request.user
        customer_name = user.username if user.is_authenticated else None

        order = serializer.save(customer_name=customer_name)

        self._handle_coupon(order, customer_name)
        self._handle_payment(order)
        self._handle_local_invoice(order)

    def _handle_coupon(self, order, customer_name):
        if not (order.payment_data and 'coupon_code' in order.payment_data):
            return
        try:
            from ..models import Coupon, RedeemedCoupon
            code = order.payment_data['coupon_code']
            discount = order.payment_data.get('discount_applied', 0)

            coupon = Coupon.objects.get(code=code)

            RedeemedCoupon.objects.create(
                telegram_id=order.telegram_id,
                coupon=coupon,
                order=order,
                discount_applied=discount,
                customer_name=customer_name or f"Cliente {order.telegram_id}"
            )

            coupon.current_uses += 1
            coupon.save()
            logger.info(f"Cupón {code} canjeado en orden #{order.id}")
        except Exception as e:
            logger.error(f"Error registrando cupón: {e}")

    def _handle_payment(self, order):
        payment_method = None
        if order.payment_data:
            payment_method = order.payment_data.get('payment_method')

        if payment_method == 'cash':
            self._approve_cash_payment(order)
        elif order.payment_proof:
            self._handle_proof_payment(order)
        elif order.service_type != 'AQUI' and order.status not in ['pendiente', 'esperando_pago']:
            self._notify_external_order(order)

    def _approve_cash_payment(self, order):
        order.payment_status = 'payment_approved'
        order.status = 'pendiente'
        order.save()

        try:
            from ..utils import notificar_nuevo_pedido_externo
            notificar_nuevo_pedido_externo(order)
            deduct_inventory_for_order(order)
            logger.info(f"Pedido en efectivo {order.id} auto-aprobado y notificado")
        except Exception as e:
            logger.error(f"Error notificando pedido efectivo: {e}")

    def _handle_proof_payment(self, order):
        order.payment_status = 'payment_submitted'
        order.save()

        from ..security import verify_payment_authenticity
        try:
            security_results = verify_payment_authenticity(order, order.payment_proof.path)

            if security_results["is_duplicate"]:
                order.status = 'fraude_sospecha'
                order.payment_data = order.payment_data or {}
                order.payment_data['fraud_error'] = (
                    f"Duplicado de orden #{security_results['duplicate_order_id']}"
                )
                order.save()
                logger.warning(
                    f"FRAUDE DETECTADO: Comprobante ya usado en orden "
                    f"#{security_results['duplicate_order_id']}"
                )
        except Exception as e:
            logger.error(f"Error en verificación de seguridad: {e}")

        try:
            from ..utils import notificar_nuevo_pedido_externo
            notificar_nuevo_pedido_externo(order)
            logger.info(f"Notificación enviada para pedido web {order.id}")
        except Exception as e:
            logger.error(f"Error notificando pedido web: {e}")

    def _notify_external_order(self, order):
        try:
            from ..utils import notificar_nuevo_pedido_externo
            notificar_nuevo_pedido_externo(order)
        except Exception as e:
            logger.error(f"Error notificando pedido externo: {e}")

    def _handle_local_invoice(self, order):
        if order.service_type != 'AQUI':
            return
        try:
            from ..factura import InvoiceGenerator
            generator = InvoiceGenerator()
            invoice_path = generator.generate(order)
            order.invoice_path = invoice_path
            order.save()
            logger.info(f"Factura local generada: {invoice_path}")
        except Exception as e:
            logger.error(f"Error generando factura local: {e}")
