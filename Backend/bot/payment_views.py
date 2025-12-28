from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse
from django.db.models import Count, Q, Avg
from django.utils import timezone
from datetime import timedelta
import pandas as pd
import json
from .models import Order


@staff_member_required
def payment_dashboard(request):
    """
    Dashboard de análisis de pagos con pandas
    """
    # Obtener todas las órdenes
    orders = Order.objects.all().values(
        'id',
        'telegram_id',
        'item',
        'status',
        'payment_status',
        'fecha',
        'payment_verified_at',
        'payment_verified_by',
        'payment_data'
    )
    
    # Convertir a DataFrame de pandas
    df = pd.DataFrame(list(orders))
    
    if df.empty:
        context = {
            'total_orders': 0,
            'stats': {},
            'recent_payments': [],
            'error': 'No hay datos de órdenes disponibles'
        }
        return render(request, 'bot/payment_dashboard.html', context)
    
    # Convertir fechas
    df['fecha'] = pd.to_datetime(df['fecha'])
    if 'payment_verified_at' in df.columns:
        df['payment_verified_at'] = pd.to_datetime(df['payment_verified_at'])
    
    # Estadísticas generales
    total_orders = len(df)
    
    # Estadísticas por estado de pago
    payment_stats = df['payment_status'].value_counts().to_dict()
    
    # Órdenes por estado
    status_stats = df['status'].value_counts().to_dict()
    
    # Análisis temporal
    today = timezone.now().date()
    df['fecha_date'] = df['fecha'].dt.date
    
    # Pagos de hoy
    today_payments = len(df[df['fecha_date'] == today])
    
    # Pagos de esta semana
    week_ago = today - timedelta(days=7)
    week_payments = len(df[df['fecha_date'] >= week_ago])
    
    # Pagos de este mes
    month_ago = today - timedelta(days=30)
    month_payments = len(df[df['fecha_date'] >= month_ago])
    
    # Pagos aprobados vs rechazados
    approved = len(df[df['payment_status'] == 'payment_approved'])
    rejected = len(df[df['payment_status'] == 'payment_rejected'])
    pending = len(df[df['payment_status'] == 'payment_submitted'])
    waiting = len(df[df['payment_status'] == 'pending_payment'])
    
    # Tasa de aprobación
    total_verified = approved + rejected
    approval_rate = (approved / total_verified * 100) if total_verified > 0 else 0
    
    # Tiempo promedio de verificación
    verified_df = df[df['payment_verified_at'].notna()].copy()
    if not verified_df.empty:
        verified_df['verification_time'] = (
            verified_df['payment_verified_at'] - verified_df['fecha']
        ).dt.total_seconds() / 60  # en minutos
        avg_verification_time = verified_df['verification_time'].mean()
    else:
        avg_verification_time = 0
    
    # Pagos recientes (últimos 20)
    recent_payments = df.sort_values('fecha', ascending=False).head(20).to_dict('records')
    
    # Extraer montos de payment_data si están disponibles
    montos = []
    for _, row in df.iterrows():
        if row.get('payment_data') and isinstance(row['payment_data'], dict):
            monto_str = row['payment_data'].get('monto', '')
            # Intentar extraer número del monto
            import re
            match = re.search(r'[\d,\.]+', str(monto_str))
            if match:
                try:
                    monto = float(match.group().replace(',', '').replace('.', ''))
                    montos.append(monto)
                except:
                    pass
    
    total_revenue = sum(montos) if montos else 0
    avg_order_value = (total_revenue / len(montos)) if montos else 0
    
    # Análisis por día de la semana
    df['day_of_week'] = df['fecha'].dt.day_name()
    orders_by_day = df['day_of_week'].value_counts().to_dict()
    
    # Top clientes
    top_customers = df['telegram_id'].value_counts().head(10).to_dict()
    
    context = {
        'total_orders': total_orders,
        'today_payments': today_payments,
        'week_payments': week_payments,
        'month_payments': month_payments,
        'approved': approved,
        'rejected': rejected,
        'pending': pending,
        'waiting': waiting,
        'approval_rate': round(approval_rate, 2),
        'avg_verification_time': round(avg_verification_time, 2),
        'total_revenue': round(total_revenue, 2),
        'avg_order_value': round(avg_order_value, 2),
        'payment_stats': payment_stats,
        'status_stats': status_stats,
        'orders_by_day': orders_by_day,
        'top_customers': top_customers,
        'recent_payments': recent_payments,
    }
    
    return render(request, 'bot/payment_dashboard.html', context)


@staff_member_required
def export_payments_csv(request):
    """
    Exportar historial de pagos a CSV
    """
    orders = Order.objects.all().values(
        'id',
        'telegram_id',
        'item',
        'status',
        'payment_status',
        'fecha',
        'payment_verified_at',
        'payment_verified_by'
    )
    
    df = pd.DataFrame(list(orders))
    
    if df.empty:
        return HttpResponse("No hay datos para exportar", status=404)
    
    # Convertir a CSV
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="historial_pagos.csv"'
    
    df.to_csv(response, index=False, encoding='utf-8-sig')
    
    return response


@staff_member_required
def export_payments_excel(request):
    """
    Exportar historial de pagos a Excel con múltiples hojas
    """
    import io
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill
    
    # Obtener datos
    orders = Order.objects.all().values(
        'id',
        'telegram_id',
        'item',
        'status',
        'payment_status',
        'fecha',
        'payment_verified_at',
        'payment_verified_by',
        'payment_data'
    )
    
    df = pd.DataFrame(list(orders))
    
    if df.empty:
        return HttpResponse("No hay datos para exportar", status=404)
    
    # Crear archivo Excel
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Hoja 1: Todos los pagos
        df.to_excel(writer, sheet_name='Todos los Pagos', index=False)
        
        # Hoja 2: Pagos aprobados
        approved_df = df[df['payment_status'] == 'payment_approved']
        approved_df.to_excel(writer, sheet_name='Pagos Aprobados', index=False)
        
        # Hoja 3: Pagos rechazados
        rejected_df = df[df['payment_status'] == 'payment_rejected']
        rejected_df.to_excel(writer, sheet_name='Pagos Rechazados', index=False)
        
        # Hoja 4: Pagos pendientes
        pending_df = df[df['payment_status'] == 'payment_submitted']
        pending_df.to_excel(writer, sheet_name='Pagos Pendientes', index=False)
    
    output.seek(0)
    
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="historial_pagos.xlsx"'
    
    return response
