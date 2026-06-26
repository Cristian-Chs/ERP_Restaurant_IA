import logging
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework import status as http_status
from ..models import Coupon, RedeemedCoupon

logger = logging.getLogger(__name__)


@api_view(['GET', 'POST'])
@permission_classes([IsAdminUser])
def coupon_list_create(request):
    if request.method == 'GET':
        coupons = Coupon.objects.all().order_by('-fecha_creacion')
        data = [
            {
                'id': c.id,
                'code': c.code,
                'discount_type': c.discount_type,
                'discount_amount': float(c.discount_amount),
                'points_cost': c.points_cost,
                'is_active': c.is_active,
                'valid_from': c.valid_from.isoformat() if c.valid_from else None,
                'valid_until': c.valid_until.isoformat() if c.valid_until else None,
                'max_uses': c.max_uses,
                'current_uses': c.current_uses,
                'min_order_amount': float(c.min_order_amount),
                'fecha_creacion': c.fecha_creacion.isoformat(),
            }
            for c in coupons
        ]
        return Response(data)

    elif request.method == 'POST':
        data = request.data
        try:
            valid_from = data.get('valid_from')
            valid_until = data.get('valid_until')

            if valid_from and len(valid_from) == 10:
                valid_from += "T00:00:00Z"
            if valid_until and len(valid_until) == 10:
                valid_until += "T23:59:59Z"

            coupon = Coupon.objects.create(
                code=data['code'].upper(),
                discount_type=data.get('discount_type', 'fixed'),
                discount_amount=data['discount_amount'],
                points_cost=data.get('points_cost', 0),
                is_active=data.get('is_active', True),
                valid_from=valid_from,
                valid_until=valid_until,
                max_uses=data.get('max_uses', 0),
                min_order_amount=data.get('min_order_amount', 0),
            )
            return Response({
                'id': coupon.id,
                'code': coupon.code,
                'message': 'Cupón creado exitosamente',
            }, status=http_status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=http_status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAdminUser])
def coupon_detail(request, coupon_id):
    try:
        coupon = Coupon.objects.get(id=coupon_id)
    except Coupon.DoesNotExist:
        return Response({'error': 'Cupón no encontrado'}, status=http_status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        data = {
            'id': coupon.id,
            'code': coupon.code,
            'discount_type': coupon.discount_type,
            'discount_amount': float(coupon.discount_amount),
            'points_cost': coupon.points_cost,
            'is_active': coupon.is_active,
            'valid_from': coupon.valid_from.isoformat() if coupon.valid_from else None,
            'valid_until': coupon.valid_until.isoformat() if coupon.valid_until else None,
            'max_uses': coupon.max_uses,
            'current_uses': coupon.current_uses,
            'min_order_amount': float(coupon.min_order_amount),
            'fecha_creacion': coupon.fecha_creacion.isoformat(),
        }
        return Response(data)

    elif request.method == 'PUT':
        data = request.data
        try:
            coupon.code = data.get('code', coupon.code).upper()
            coupon.discount_type = data.get('discount_type', coupon.discount_type)
            coupon.discount_amount = data.get('discount_amount', coupon.discount_amount)
            coupon.points_cost = data.get('points_cost', coupon.points_cost)
            coupon.is_active = data.get('is_active', coupon.is_active)

            updated_valid_from = data.get('valid_from', coupon.valid_from)
            updated_valid_until = data.get('valid_until', coupon.valid_until)

            if isinstance(updated_valid_from, str) and len(updated_valid_from) == 10:
                updated_valid_from += "T00:00:00Z"
            if isinstance(updated_valid_until, str) and len(updated_valid_until) == 10:
                updated_valid_until += "T23:59:59Z"

            coupon.valid_from = updated_valid_from
            coupon.valid_until = updated_valid_until
            coupon.max_uses = data.get('max_uses', coupon.max_uses)
            coupon.min_order_amount = data.get('min_order_amount', coupon.min_order_amount)
            coupon.save()
            return Response({'message': 'Cupón actualizado exitosamente'})
        except Exception as e:
            return Response({'error': str(e)}, status=http_status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        coupon.delete()
        return Response({'message': 'Cupón eliminado exitosamente'}, status=http_status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def coupon_redemptions(request):
    redemptions = RedeemedCoupon.objects.all().select_related('coupon', 'order').order_by('-fecha_canje')
    data = [
        {
            'id': r.id,
            'telegram_id': r.telegram_id,
            'customer_name': (
                r.customer_name
                or (r.order.customer_name if r.order else None)
                or f"ID: {r.telegram_id}"
            ),
            'coupon_code': r.coupon.code,
            'discount_applied': float(r.discount_applied),
            'fecha_canje': r.fecha_canje.isoformat(),
            'order_id': r.order.id if r.order else None,
        }
        for r in redemptions
    ]
    return Response(data)


@api_view(['POST'])
def validate_coupon(request):
    coupon_code = request.data.get('code', '').upper()
    order_amount = float(request.data.get('order_amount', 0))

    if not coupon_code:
        return Response({'error': 'Código de cupón requerido'}, status=http_status.HTTP_400_BAD_REQUEST)

    try:
        coupon = Coupon.objects.get(code=coupon_code)
    except Coupon.DoesNotExist:
        return Response({'error': 'Cupón no válido'}, status=http_status.HTTP_404_NOT_FOUND)

    if not coupon.is_valid():
        return Response({'error': 'Cupón expirado o inactivo'}, status=http_status.HTTP_400_BAD_REQUEST)

    discount = coupon.apply_discount(order_amount)

    if discount == 0:
        return Response({
            'error': f'Monto mínimo requerido: ${coupon.min_order_amount}'
        }, status=http_status.HTTP_400_BAD_REQUEST)

    return Response({
        'valid': True,
        'code': coupon.code,
        'discount': float(discount),
        'discount_type': coupon.discount_type,
        'discount_amount': float(coupon.discount_amount),
        'message': f'Cupón aplicado: -{discount:.2f}',
    })
