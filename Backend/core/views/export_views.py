from datetime import datetime
from django.db.models import Sum
from django.db.models.functions import TruncMonth
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from bot.models import Order
from ..models import PayrollPayment
from .general import calculate_recipe_expenses


class ExportFinancialPDFView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        current_month = datetime.now().strftime('%Y-%m')

        monthly_stats = (
            Order.objects.filter(
                fecha__year=datetime.now().year, payment_status='payment_approved'
            )
            .annotate(mes=TruncMonth('fecha'))
            .values('mes')
            .annotate(total=Sum('precio'))
        )

        current_revenue = 0
        for m in monthly_stats:
            if m['mes'].strftime('%Y-%m') == current_month:
                current_revenue = float(m['total'] or 0)
                break

        first_day = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        orders_this_month = Order.objects.filter(
            payment_status='payment_approved', fecha__gte=first_day
        )
        monthly_expenses, shopping_list = calculate_recipe_expenses(orders_this_month)

        estimated_tax = current_revenue * 0.10
        net_profit = current_revenue - monthly_expenses - estimated_tax

        total_orders = Order.objects.count()
        approved_orders = Order.objects.filter(payment_status='payment_approved').count()
        approval_rate = (approved_orders / total_orders * 100) if total_orders > 0 else 0

        response = HttpResponse(content_type='application/pdf')
        filename = f"Reporte_Financiero_{current_month}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        p = canvas.Canvas(response, pagesize=letter)
        w, h = letter

        p.setTitle(f"Reporte Financiero {current_month}")

        p.setFillColor(colors.HexColor("#1f2428"))
        p.rect(0, h - 100, w, 100, fill=1, stroke=0)
        p.setFillColor(colors.white)
        p.setFont("Helvetica-Bold", 24)
        p.drawString(50, h - 60, "Reporte Financiero Mensual")
        p.setFont("Helvetica", 12)
        p.drawString(50, h - 80, f"Generado el: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

        y = h - 150
        p.setFillColor(colors.black)
        p.setFont("Helvetica-Bold", 14)
        p.drawString(50, y, "Dinero Reunido (Ingreso Bruto)")
        p.setFont("Helvetica", 14)
        p.drawString(350, y, f"${current_revenue:,.2f}")
        p.line(50, y - 10, 500, y - 10)

        y -= 50
        p.setFont("Helvetica-Bold", 14)
        p.drawString(50, y, "Gastos de Mercancía (Compras)")
        p.setFillColor(colors.red)
        p.drawString(350, y, f"-${monthly_expenses:,.2f}")
        p.setFillColor(colors.black)
        p.line(50, y - 10, 500, y - 10)

        y -= 50
        p.setFont("Helvetica-Bold", 14)
        p.drawString(50, y, "Impuesto Estimado (10%)")
        p.setFillColor(colors.red)
        p.drawString(350, y, f"-${estimated_tax:,.2f}")
        p.setFillColor(colors.black)
        p.line(50, y - 10, 500, y - 10)

        y -= 50
        p.setFont("Helvetica-Bold", 16)
        p.drawString(50, y, "Utilidad Neta (Libre)")
        p.setFillColor(colors.green)
        p.drawString(350, y, f"${net_profit:,.2f}")
        p.setFillColor(colors.black)
        p.line(50, y - 10, 500, y - 10)

        p.showPage()
        p.setFont("Helvetica-Bold", 18)
        p.drawString(50, h - 50, "Lista de Compras Automática (Recetario)")
        p.setFont("Helvetica", 10)
        p.drawString(50, h - 70, "Generado según ingredientes necesarios para las ventas del mes.")

        y = h - 100
        headers = ["Ingrediente", "Cant. Necesaria", "Unidad", "Costo/U", "Total"]
        x_pos = [50, 200, 320, 380, 480]

        p.setFont("Helvetica-Bold", 10)
        for i, head in enumerate(headers):
            p.drawString(x_pos[i], y, head)
        p.line(50, y - 5, 550, y - 5)
        y -= 25
        p.setFont("Helvetica", 10)

        total_list_cost = 0
        for item in shopping_list:
            if y < 50:
                p.showPage()
                y = h - 50
                p.setFont("Helvetica-Bold", 10)
                for i, head in enumerate(headers):
                    p.drawString(x_pos[i], y, head)
                p.line(50, y - 5, 550, y - 5)
                y -= 25
                p.setFont("Helvetica", 10)

            p.drawString(x_pos[0], y, item['ingredient_name'][:30])
            p.drawString(x_pos[1], y, f"{item['quantity']:.2f}")
            p.drawString(x_pos[2], y, item['unit'])
            p.drawString(x_pos[3], y, f"${item['cost_per_unit']:.2f}")
            p.drawString(x_pos[4], y, f"${item['total_cost']:.2f}")
            total_list_cost += item['total_cost']
            y -= 20

        y -= 10
        p.line(50, y + 15, 550, y + 15)
        p.setFont("Helvetica-Bold", 12)
        p.drawString(350, y, "TOTAL NECESARIO:")
        p.drawString(480, y, f"${total_list_cost:,.2f}")

        y -= 80
        p.setFont("Helvetica-Bold", 12)
        p.drawString(50, y, "Indicadores de Inteligencia Artificial")
        y -= 30
        p.setFont("Helvetica", 12)
        p.drawString(50, y, f"\u2022 Tasa de Aprobación de Pagos: {approval_rate:.1f}%")
        y -= 20
        p.drawString(50, y, "\u2022 Método de Pago Frecuente: Transferencia")

        p.setFont("Helvetica-Oblique", 10)
        p.setFillColor(colors.gray)
        p.drawString(50, 50, "Documento generado automáticamente por Sistema de Gestión AI.")

        p.showPage()
        p.save()
        return response


class ExportPayrollPDFView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        payments = PayrollPayment.objects.all().order_by('-payment_date')
        current_date_str = datetime.now().strftime('%Y-%m-%d')

        response = HttpResponse(content_type='application/pdf')
        filename = f"Reporte_Nomina_{current_date_str}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        p = canvas.Canvas(response, pagesize=letter)
        w, h = letter

        p.setTitle(f"Reporte de Nómina {current_date_str}")
        p.setFillColor(colors.HexColor("#1f2428"))
        p.rect(0, h - 80, w, 80, fill=1, stroke=0)
        p.setFillColor(colors.white)
        p.setFont("Helvetica-Bold", 20)
        p.drawString(50, h - 50, "Reporte de Nómina")
        p.setFont("Helvetica", 10)
        p.drawString(w - 200, h - 50, f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

        y = h - 120
        p.setFillColor(colors.black)
        headers = ["Fecha", "Empleado", "Rol", "Notas", "Monto"]
        x_positions = [50, 150, 270, 350, 500]

        p.setFont("Helvetica-Bold", 10)
        for i, header in enumerate(headers):
            p.drawString(x_positions[i], y, header)
        p.line(50, y - 5, 550, y - 5)
        y -= 25

        p.setFont("Helvetica", 10)
        total_payroll = 0

        for pay in payments:
            if y < 50:
                p.showPage()
                y = h - 50
                p.setFont("Helvetica-Bold", 10)
                for i, header in enumerate(headers):
                    p.drawString(x_positions[i], y, header)
                p.line(50, y - 5, 550, y - 5)
                y -= 25
                p.setFont("Helvetica", 10)

            p.drawString(x_positions[0], y, str(pay.payment_date))
            p.drawString(x_positions[1], y, pay.employee.name[:20])
            p.drawString(x_positions[2], y, pay.employee.get_role_display()[:15])
            p.drawString(x_positions[3], y, (pay.notes or "")[:20])
            p.drawString(x_positions[4], y, f"${pay.amount:,.2f}")
            total_payroll += pay.amount
            y -= 20

        y -= 10
        p.line(50, y + 15, 550, y + 15)
        p.setFont("Helvetica-Bold", 12)
        p.drawString(350, y, "TOTAL PAGADO:")
        p.setFillColor(colors.HexColor("#2ecc71"))
        p.drawString(500, y, f"${total_payroll:,.2f}")

        y -= 80
        if y < 100:
            p.showPage()
            y = h - 150

        p.setFillColor(colors.black)
        p.line(200, y, 400, y)
        p.setFont("Helvetica", 10)
        p.drawCentredString(300, y - 15, "Firma del Empleado / Recibido Conforme")

        p.setFillColor(colors.gray)
        p.setFont("Helvetica-Oblique", 8)
        p.drawString(50, 30, "Documento confidencial de Recursos Humanos.")

        p.showPage()
        p.save()
        return response
