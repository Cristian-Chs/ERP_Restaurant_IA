
from PIL import Image, ImageDraw, ImageFont
import datetime
import os

class InvoiceGenerator:
    """
    Generates a fiscal-style receipt image.
    """
    
    # Configuration
    WIDTH = 550
    BG_COLOR = (255, 255, 255) # White
    TEXT_COLOR = (0, 0, 0) # Black
    FONT_SIZE_HEADER = 24
    FONT_SIZE_BODY = 18
    FONT_SIZE_SMALL = 14
    LINE_HEIGHT = 22
    MARGIN = 20
    
    # Mock Fiscal Info
    COMPANY_NAME = "LOS CUATROS SABORES C.A."
    COMPANY_RIF = "J-12345678-9"
    COMPANY_ADDRESS = "Av. Principal, Sector Puerta Maraven,\nPunto Fijo, Falcón, Venezuela"
    FISCAL_SERIAL = "Z1B8560355" # Serial impresora fiscal mock

    def generate(self, order, output_path=None):
        """
        Generates invoice image for an Order object.
        Returns the path to the generated image.
        """
        
        # 1. Calculate Dynamic Height
        # Header (approx 150) + Client Info (100) + Items (30 per item) + Totals (150) + Footer (50)
        items_count = 1 # Default if no list
        if hasattr(order, 'items_detalle') and order.items_detalle.exists():
            items_count = order.items_detalle.count()
        
        est_height = 550 + (items_count * 30)
        
        img = Image.new('RGB', (self.WIDTH, est_height), self.BG_COLOR)
        d = ImageDraw.Draw(img)
        
        # Load Fonts (Fallback to default if not found)
        try:
            # Try to use a monospace font for fiscal look
            font_header = ImageFont.truetype("arialbd.ttf", self.FONT_SIZE_HEADER) # Bold
            font_body = ImageFont.truetype("arial.ttf", self.FONT_SIZE_BODY)
            font_bold = ImageFont.truetype("arialbd.ttf", self.FONT_SIZE_BODY)
            font_small = ImageFont.truetype("arial.ttf", self.FONT_SIZE_SMALL)
        except IOError:
            # Linux/Server fallback
            font_header = ImageFont.load_default()
            font_body = ImageFont.load_default()
            font_bold = ImageFont.load_default()
            font_small = ImageFont.load_default()

        y = self.MARGIN
        
        # --- HEADER ---
        # Centered Text
        self._draw_centered_text(d, "SENIAT", self.WIDTH, y, font_bold); y += 25
        self._draw_centered_text(d, f"RIF {self.COMPANY_RIF}", self.WIDTH, y, font_bold); y += 25
        self._draw_centered_text(d, self.COMPANY_NAME, self.WIDTH, y, font_bold); y += 25
        
        # Address (Multiline)
        for line in self.COMPANY_ADDRESS.split('\n'):
            self._draw_centered_text(d, line, self.WIDTH, y, font_small); y += 18
            
        y += 20
        d.line([(self.MARGIN, y), (self.WIDTH - self.MARGIN, y)], fill=self.TEXT_COLOR, width=2)
        y += 10

        # --- CLIENT INFO ---
        # Fetch client info (simulated or from order if available)
        client_name = f"Cliente Telegram ({order.telegram_id})"
        client_doc = "V-00000000"
        
        d.text((self.MARGIN, y), f"Cliente: {client_name}", font=font_body, fill=self.TEXT_COLOR); y += self.LINE_HEIGHT
        d.text((self.MARGIN, y), f"RIF/C.I.: {client_doc}", font=font_body, fill=self.TEXT_COLOR); y += self.LINE_HEIGHT
        d.text((self.MARGIN, y), f"Fecha: {datetime.datetime.now().strftime('%d-%m-%Y')}", font=font_body, fill=self.TEXT_COLOR)
        d.text((self.WIDTH - 200, y), f"Hora: {datetime.datetime.now().strftime('%H:%M')}", font=font_body, fill=self.TEXT_COLOR); y += self.LINE_HEIGHT
        
        text_w = d.textlength("FACTURA", font=font_bold)
        d.text(((self.WIDTH - text_w) / 2, y + 10), "FACTURA", font=font_bold, fill=self.TEXT_COLOR)
        d.text((self.WIDTH - 150, y + 10), f"N° {str(order.id).zfill(8)}", font=font_bold, fill=self.TEXT_COLOR)
        y += 40

        # --- ITEMS HEADER ---
        # Cols: QTY (50px), DESC (300px), TOTAL (100px)
        col_qty_x = self.MARGIN
        col_desc_x = self.MARGIN + 60
        col_total_x = self.WIDTH - self.MARGIN 
        
        d.rectangle([(self.MARGIN, y), (self.WIDTH - self.MARGIN, y+25)], fill="#f0f0f0")
        d.text((col_qty_x, y+2), "CANT", font=font_small, fill=self.TEXT_COLOR)
        d.text((col_desc_x, y+2), "DESCRIPCIÓN", font=font_small, fill=self.TEXT_COLOR)
        d.text((col_total_x - 80, y+2), "TOTAL", font=font_small, fill=self.TEXT_COLOR)
        y += 30

        # --- ITEMS BODY ---
        total_monto = float(order.precio)
        
        # If we have detailed items in DB, iterate
        if hasattr(order, 'items_detalle') and order.items_detalle.exists():
            for item in order.items_detalle.all():
                qty = str(item.cantidad)
                desc = item.product.name[:30] # Truncate
                price = f"{float(item.precio_unitario * item.cantidad):.2f}"
                
                d.text((col_qty_x, y), qty, font=font_body, fill=self.TEXT_COLOR)
                d.text((col_desc_x, y), desc, font=font_body, fill=self.TEXT_COLOR)
                
                # Right align price
                p_width = d.textlength(price, font=font_body)
                d.text((col_total_x - p_width, y), price, font=font_body, fill=self.TEXT_COLOR)
                y += self.LINE_HEIGHT
        else:
            # Fallback to single item order string
            qty = "1"
            desc = order.item[:30]
            price = f"{total_monto:.2f}"
            
            d.text((col_qty_x, y), qty, font=font_body, fill=self.TEXT_COLOR)
            d.text((col_desc_x, y), desc, font=font_body, fill=self.TEXT_COLOR)
            
            p_width = d.textlength(price, font=font_body)
            d.text((col_total_x - p_width, y), price, font=font_body, fill=self.TEXT_COLOR)
            y += self.LINE_HEIGHT

        y += 10
        d.line([(self.MARGIN, y), (self.WIDTH - self.MARGIN, y)], fill=self.TEXT_COLOR, width=1)
        y += 10

        # --- TOTALS ---
        # Fiscal calculation (mock)
        # Base = Total / 1.16
        base = total_monto / 1.16
        iva = total_monto - base
        
        self._draw_total_line(d, "BI G (16.00%)", f"{base:.2f}", y, font_body); y += self.LINE_HEIGHT
        self._draw_total_line(d, "IVA G (16.00%)", f"{iva:.2f}", y, font_body); y += self.LINE_HEIGHT + 10
        
        d.line([(self.MARGIN + 200, y), (self.WIDTH - self.MARGIN, y)], fill=self.TEXT_COLOR, width=2)
        y += 10
        self._draw_total_line(d, "TOTAL A PAGAR", f"{total_monto:.2f}", y, font_bold, is_total=True); y += 40

        # --- FOOTER ---
        self._draw_centered_text(d, "GRACIAS POR SU COMPRA", self.WIDTH, y, font_body); y += 25
        
        # Barcode (Fake)
        # Draw bars
        bar_x = (self.WIDTH - 200) / 2
        d.rectangle([(bar_x, y), (bar_x + 200, y + 50)], fill=self.TEXT_COLOR) 
        # Just a black box for now to simulate barcode visually or load a barcode font if available
        # Better: draw vertical lines
        import random
        random.seed(order.id)
        current_x = bar_x
        for _ in range(40):
            w = random.choice([2, 4, 6])
            d.rectangle([(current_x, y), (current_x + w, y + 50)], fill=self.TEXT_COLOR)
            current_x += w + 2
        
        y += 60
        self._draw_centered_text(d, self.FISCAL_SERIAL, self.WIDTH, y, font_body); y += 20

        # Save
        filename = f"factura_{order.id}.jpg"
        if output_path is None:
             output_path = os.path.join(os.path.dirname(__file__), "invoices")
             
        if not os.path.exists(output_path):
            os.makedirs(output_path)
            
        full_path = os.path.join(output_path, filename)
        img.save(full_path)
        print(f"✅ Factura generada: {full_path}")
        return full_path

    def _draw_centered_text(self, draw, text, width, y, font):
        text_w = draw.textlength(text, font=font)
        x = (width - text_w) / 2
        draw.text((x, y), text, font=font, fill=self.TEXT_COLOR)

    def _draw_total_line(self, draw, label, value, y, font, is_total=False):
        draw.text((self.WIDTH - 250, y), label, font=font, fill=self.TEXT_COLOR)
        val_w = draw.textlength(value, font=font)
        draw.text((self.WIDTH - self.MARGIN - val_w, y), value, font=font, fill=self.TEXT_COLOR)

