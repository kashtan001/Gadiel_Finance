#!/usr/bin/env python3
"""
PDF Constructor API для генерации документов Intesa Sanpaolo
Поддерживает: contratto, garanzia, carta, compensacion
"""

from io import BytesIO
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP


def format_money(amount: float) -> str:
    """Форматирование суммы БЕЗ знака € (он уже есть в HTML)"""
    return f"{amount:,.2f}".replace(',', ' ')


def format_date() -> str:
    """Получение текущей даты в итальянском формате"""
    return datetime.now().strftime("%d/%m/%Y")


def format_date_es() -> str:
    """Дата для испаноязычных писем (dd.mm.yyyy)"""
    return datetime.now().strftime("%d.%m.%Y")


def monthly_payment(amount: float, months: int, annual_rate: float) -> float:
    """Аннуитетный расчёт ежемесячного платежа"""
    r = (annual_rate / 100) / 12
    if r == 0:
        return round(amount / months, 2)
    num = amount * r * (1 + r) ** months
    den = (1 + r) ** months - 1
    return round(num / den, 2)


def generate_payment_schedule_table(amount: float, months: int, annual_rate: float, payment: float) -> str:
    """
    Генерирует HTML таблицу графика платежей (амортизационную таблицу) для пункта 6.
    Вставляется в HTML на место <!-- PAYMENT_SCHEDULE_TABLE_PLACEHOLDER -->.
    """
    monthly_rate = (annual_rate / 100) / 12

    table_html = """
<table class="c18" style="width: 100%; border-collapse: collapse; margin: 10pt 0;">
<tr class="c7">
<td class="c4" style="border: 1pt solid #666666; padding: 5pt; text-align: center; font-weight: 700;"><span class="c3">Mes</span></td>
<td class="c4" style="border: 1pt solid #666666; padding: 5pt; text-align: center; font-weight: 700;"><span class="c3">Pago</span></td>
<td class="c4" style="border: 1pt solid #666666; padding: 5pt; text-align: center; font-weight: 700;"><span class="c3">Intereses</span></td>
<td class="c4" style="border: 1pt solid #666666; padding: 5pt; text-align: center; font-weight: 700;"><span class="c3">Importe del préstamo</span></td>
<td class="c4" style="border: 1pt solid #666666; padding: 5pt; text-align: center; font-weight: 700;"><span class="c3">Saldo pendiente</span></td>
</tr>
"""

    remaining = float(amount)
    for month in range(1, months + 1):
        interest = remaining * monthly_rate
        principal = payment - interest

        # Последний платёж — корректируем, чтобы остаток стал 0
        if month == months:
            principal = remaining
            interest = payment - principal
            remaining = 0.0
        else:
            remaining = remaining - principal

        interest = round(interest, 2)
        principal = round(principal, 2)
        remaining = round(remaining, 2)

        payment_str = format_money(payment)
        interest_str = format_money(interest)
        principal_str = format_money(principal)
        balance_str = format_money(remaining) if remaining > 0 else "0,00"

        table_html += f"""
<tr class="c7">
<td class="c5" style="border: 1pt solid #666666; padding: 3pt; text-align: center;"><span class="c3">{month}</span></td>
<td class="c5" style="border: 1pt solid #666666; padding: 3pt; text-align: right;"><span class="c9 c8">&euro; {payment_str}</span></td>
<td class="c5" style="border: 1pt solid #666666; padding: 3pt; text-align: right;"><span class="c9 c8">&euro; {interest_str}</span></td>
<td class="c5" style="border: 1pt solid #666666; padding: 3pt; text-align: right;"><span class="c9 c8">&euro; {principal_str}</span></td>
<td class="c5" style="border: 1pt solid #666666; padding: 3pt; text-align: right;"><span class="c9 c8">&euro; {balance_str}</span></td>
</tr>
"""

    table_html += "</table>"
    return table_html


def generate_signatures_table() -> str:
    """
    Генерирует две наложенные друг на друга таблицы:
    1) Таблица с подписями (sing_1.png и sing_2.png)
    2) Таблица с печатью (seal.png), наложенная со смещением
    Изображения встраиваются как base64 для гарантированной загрузки в weasyprint.
    """
    import os
    import base64

    base_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()

    def image_to_base64(filename: str) -> str | None:
        img_path = os.path.join(base_dir, filename)
        if os.path.exists(img_path):
            with open(img_path, 'rb') as f:
                img_base64 = base64.b64encode(f.read()).decode('utf-8')
            mime_type = 'image/png' if filename.lower().endswith('.png') else 'image/jpeg'
            return f"data:{mime_type};base64,{img_base64}"
        return None

    sing_1_data = image_to_base64('sing_1.png')
    sing_2_data = image_to_base64('sing_2.png')
    seal_data = image_to_base64('seal.png')

    if not all([sing_1_data, sing_2_data, seal_data]):
        print("⚠️  Не все изображения найдены для таблицы подписей/печати (sing_1.png, sing_2.png, seal.png)")
        return ''

    signatures_table = f'''
<table class="signatures-table-base">
<tr>
<td style="width: 33.33%;">
<img src="{sing_1_data}" alt="Подпись 1" style="display: block; width: auto; height: auto; max-width: 100mm; max-height: 40mm; margin: 0 auto;" />
</td>
<td style="width: 33.33%;">
<img src="{sing_2_data}" alt="Подпись 2" style="display: block; width: auto; height: auto; max-width: 100mm; max-height: 40mm; margin: 0 auto;" />
</td>
<td style="width: 33.33%;">
</td>
</tr>
</table>
'''

    seal_table = f'''
<table class="signatures-table-overlay">
<tr>
<td style="width: 33.33%;">
<img src="{seal_data}" alt="Печать" style="display: block; width: auto; height: auto; max-width: 150mm; max-height: 65mm; margin: 0 auto;" />
</td>
<td style="width: 33.33%;">
</td>
<td style="width: 33.33%;">
</td>
</tr>
</table>
'''

    return f'''
<div class="signatures-tables-wrapper">
{signatures_table}
{seal_table}
</div>
'''


def generate_contratto_pdf(data: dict) -> BytesIO:
    """
    API функция для генерации PDF договора
    
    Args:
        data (dict): Словарь с данными {
            'name': str - ФИО клиента,
            'amount': float - Сумма кредита,
            'duration': int - Срок в месяцах, 
            'tan': float - TAN процентная ставка,
            'taeg': float - TAEG эффективная ставка,
            'payment': float - Ежемесячный платеж (опционально, будет рассчитан)
        }
    
    Returns:
        BytesIO: PDF файл в памяти
    """
    # Рассчитываем платеж если не задан
    if 'payment' not in data:
        data['payment'] = monthly_payment(data['amount'], data['duration'], data['tan'])
    
    html = fix_html_layout('contratto')
    return _generate_pdf_with_images(html, 'contratto', data)


def generate_garanzia_pdf(name: str) -> BytesIO:
    """
    API функция для генерации PDF гарантийного письма
    
    Args:
        name (str): ФИО клиента
        
    Returns:
        BytesIO: PDF файл в памяти
    """
    html = fix_html_layout('garanzia')
    return _generate_pdf_with_images(html, 'garanzia', {'name': name})


def generate_carta_pdf(data: dict) -> BytesIO:
    """
    API функция для генерации PDF письма о карте
    
    Args:
        data (dict): Словарь с данными {
            'name': str - ФИО клиента,
            'amount': float - Сумма кредита,
            'duration': int - Срок в месяцах,
            'tan': float - TAN процентная ставка,
            'payment': float - Ежемесячный платеж (опционально, будет рассчитан)
        }
    
    Returns:
        BytesIO: PDF файл в памяти
    """
    # Рассчитываем платеж если не задан
    if 'payment' not in data:
        data['payment'] = monthly_payment(data['amount'], data['duration'], data['tan'])
    
    html = fix_html_layout('carta')
    return _generate_pdf_with_images(html, 'carta', data)


def generate_approvazione_pdf(data: dict) -> BytesIO:
    """
    API функция для генерации PDF письма об одобрении кредита
    
    Args:
        data (dict): Словарь с данными {
            'name': str - ФИО клиента,
            'amount': float - Сумма кредита,
            'tan': float - TAN процентная ставка
        }
    
    Returns:
        BytesIO: PDF файл в памяти
    """
    html = fix_html_layout('approvazione')
    return _generate_pdf_with_images(html, 'approvazione', data)


def generate_compensacion_pdf(data: dict) -> BytesIO:
    """Письмо GARANTÍA (ES): name, commission, indemnity; дата — format_date_es()."""
    html = fix_html_layout('compensacion')
    return _generate_pdf_with_images(html, 'compensacion', data)


def _generate_pdf_with_images(html: str, template_name: str, data: dict) -> BytesIO:
    """Внутренняя функция для генерации PDF с изображениями"""
    try:
        from weasyprint import HTML
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        from PyPDF2 import PdfReader, PdfWriter
        from PIL import Image
        
        # Заменяем XXX на реальные данные для contratto, carta, garanzia, compensacion и approvazione
        if template_name in ['contratto', 'carta', 'garanzia', 'compensacion', 'approvazione']:
            replacements = []
            if template_name == 'contratto':
                replacements = [
                    ('XXX', data['name']),  # имя клиента (первое)
                    ('XXX', format_money(data['amount'])),  # сумма кредита
                    ('XXX', f"{data['tan']:.2f}%"),  # TAN
                    ('XXX', f"{data['taeg']:.2f}%"),  # TAEG  
                    ('XXX', f"{data['duration']} mesi"),  # срок
                    ('XXX', format_money(data['payment'])),  # платеж
                    ('11/10/2025', format_date()),  # дата
                    ('XXX', data['name']),  # имя в подписи
                ]

                # Пункт 6: Plan de pagos — подстановка плейсхолдеров и таблицы
                monthly_rate = (data['tan'] / 100) / 12
                total_payments = data['payment'] * data['duration']
                overpayment = total_payments - data['amount']

                html = html.replace('PAYMENT_SCHEDULE_MONTHLY_RATE', f"{monthly_rate:.12f}")
                html = html.replace('PAYMENT_SCHEDULE_MONTHLY_PAYMENT', f"&euro; {format_money(data['payment'])}")
                html = html.replace('PAYMENT_SCHEDULE_TOTAL_PAYMENTS', f"&euro; {format_money(total_payments)}")
                html = html.replace('PAYMENT_SCHEDULE_OVERPAYMENT', f"&euro; {format_money(overpayment)}")

                payment_schedule_table = generate_payment_schedule_table(
                    data['amount'],
                    data['duration'],
                    data['tan'],
                    data['payment'],
                )
                
                html = html.replace('<!-- PAYMENT_SCHEDULE_TABLE_PLACEHOLDER -->', payment_schedule_table)

                # Добавляем класс к разделу 7 для принудительного разрыва страницы
                import re
                # Ищем параграф с "7. Firmas" и ПРЕДЫДУЩУЮ пунктирную линию
                # Добавляем класс разрыва страницы к пунктирной линии
                html = re.sub(
                    r'(<p class="c2">\s*<span class="c1">-{10,}</span>\s*</p>)(\s*<p class="c2">\s*<span class="c12 c6">7\. Firmas</span>\s*</p>)',
                    r'<p class="c2 section-7-firme"><span class="c1">------------------------------------------</span></p>\2',
                    html
                )

                # Таблица с подписями и печатью
                signatures_table = generate_signatures_table()
                html = html.replace('<!-- SIGNATURES_TABLE_PLACEHOLDER -->', signatures_table)
            elif template_name == 'carta':
                replacements = [
                    ('XXX', data['name']),  # имя клиента
                    ('XXX', format_money(data['amount'])),  # сумма кредита
                    ('XXX', f"{data['tan']:.2f}%"),  # TAN
                    ('XXX', f"{data['duration']} mesi"),  # срок
                    ('XXX', format_money(data['payment'])),  # платеж
                ]
            elif template_name == 'garanzia':
                replacements = [
                    ('XXX', data['name']),  # имя клиента
                ]
            elif template_name == 'approvazione':
                replacements = [
                    ('XXX', data['name']),  # имя клиента в Asunto
                    ('XXX', data['name']),  # имя клиента в тексте (второй раз)
                    ('XXX', format_money(data['amount'])),  # сумма кредита
                    ('XXX', f"{data['tan']:.2f}%"),  # TAN
                    ('XXX', str(data['duration'])),  # срок в месяцах
                ]
            elif template_name == 'compensacion':
                n = data['name'].strip()
                if not n.endswith(','):
                    n = n + ','
                replacements = [
                    ('XXX', format_date_es()),
                    ('XXX', n),
                    ('XXX', format_money(data['commission'])),
                    ('XXX', format_money(data['indemnity'])),
                ]

            for old, new in replacements:
                html = html.replace(old, new, 1)  # заменяем по одному
        
        # Универсальная подстановка актуальной даты: заменяем первую дату формата dd/mm/yyyy на текущую
        try:
            import re
            html = re.sub(r'\b\d{2}/\d{2}/\d{4}\b', format_date(), html, count=1)
        except Exception:
            pass
        
        # Конвертируем HTML в PDF
        pdf_bytes = HTML(string=html).write_pdf()
        
        # НАКЛАДЫВАЕМ ИЗОБРАЖЕНИЯ ЧЕРЕЗ REPORTLAB
        return _add_images_to_pdf(pdf_bytes, template_name)
            
    except Exception as e:
        print(f"Ошибка генерации PDF: {e}")
        raise

def _add_images_to_pdf(pdf_bytes: bytes, template_name: str) -> BytesIO:
    """Добавляет изображения на PDF через ReportLab"""
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        from PyPDF2 import PdfReader, PdfWriter
        from PIL import Image
        
        # Создаем overlay с изображениями
        overlay_buffer = BytesIO()
        overlay_canvas = canvas.Canvas(overlay_buffer, pagesize=A4)
        
        # Размер ячейки для расчета сдвигов
        cell_width_mm = 210/25  # 8.4mm
        cell_height_mm = 297/35  # 8.49mm
        
        if template_name == 'garanzia':
            # Добавляем company.png в центр 27-й клетки с уменьшением в 1.92 раза + сдвиг вправо на 5 клеток
            company_img = Image.open("company.png")
            company_width_mm = company_img.width * 0.264583  # пиксели в мм (96 DPI)
            company_height_mm = company_img.height * 0.264583
            
            # Уменьшаем в 1.33 раза (было 1.6, увеличиваем еще на 20%)
            company_scaled_width = company_width_mm / 1.33
            company_scaled_height = company_height_mm / 1.33
            
            # Клетка 27 = строка 1, колонка 1 + сдвиг на 5 клеток вправо
            row_27 = (27 - 1) // 25  # строка 1
            col_27 = (27 - 1) % 25   # колонка 1
            
            # Центр клетки 27 + смещение на 5 клеток вправо + 1.25 клетки правее + 1 клетка вправо + 1/3 клетки вправо - 3 клетки влево - 0.5 клетки влево
            x_27_center = (col_27 + 5 + 0.5 + 1.25 + 1 + 1/3 - 3 - 0.5) * cell_width_mm * mm
            y_27_center = (297 - (row_27 + 0.5 + 1 + 0.5) * cell_height_mm) * mm  # на 1.5 клетки вниз
            
            # Смещаем на половину размера изображения для центрирования
            x_27 = x_27_center - (company_scaled_width * mm / 2)
            y_27 = y_27_center - (company_scaled_height * mm / 2)
            
            # Рисуем company.png
            overlay_canvas.drawImage("company.png", x_27, y_27, 
                                   width=company_scaled_width*mm, height=company_scaled_height*mm,
                                   mask='auto', preserveAspectRatio=True)
            
            # Добавляем seal.png в центр 590-й клетки с уменьшением в 5 раз
            seal_img = Image.open("seal.png")
            seal_width_mm = seal_img.width * 0.264583
            seal_height_mm = seal_img.height * 0.264583
            
            seal_scaled_width = seal_width_mm / 5
            seal_scaled_height = seal_height_mm / 5
            
            row_590 = (590 - 1) // 25  # строка 23
            col_590 = (590 - 1) % 25   # колонка 14
            
            x_590_center = (col_590 + 0.5) * cell_width_mm * mm
            y_590_center = (297 - (row_590 + 0.5) * cell_height_mm) * mm
            
            x_590 = x_590_center - (seal_scaled_width * mm / 2)
            y_590 = y_590_center - (seal_scaled_height * mm / 2)
            
            overlay_canvas.drawImage("seal.png", x_590, y_590, 
                                   width=seal_scaled_width*mm, height=seal_scaled_height*mm,
                                   mask='auto', preserveAspectRatio=True)
            
            # Добавляем sing_1.png в центр 593-й клетки с уменьшением в 5 раз
            sing1_img = Image.open("sing_1.png")
            sing1_width_mm = sing1_img.width * 0.264583
            sing1_height_mm = sing1_img.height * 0.264583
            
            sing1_scaled_width = sing1_width_mm / 5
            sing1_scaled_height = sing1_height_mm / 5
            
            row_593 = (593 - 1) // 25  # строка 23
            col_593 = (593 - 1) % 25   # колонка 17
            
            x_593_center = (col_593 + 0.5) * cell_width_mm * mm
            y_593_center = (297 - (row_593 + 0.5) * cell_height_mm) * mm
            
            x_593 = x_593_center - (sing1_scaled_width * mm / 2)
            y_593 = y_593_center - (sing1_scaled_height * mm / 2)
            
            overlay_canvas.drawImage("sing_1.png", x_593, y_593, 
                                   width=sing1_scaled_width*mm, height=sing1_scaled_height*mm,
                                   mask='auto', preserveAspectRatio=True)
            
            overlay_canvas.save()
            print("🖼️ Добавлены изображения для garanzia через ReportLab API")
        
        elif template_name in ('carta', 'compensacion'):
            # Добавляем company.png как в contratto
            img = Image.open("company.png")
            img_width_mm = img.width * 0.264583
            img_height_mm = img.height * 0.264583

            scaled_width = (img_width_mm / 2) * 1.44  # +44% как в contratto
            scaled_height = (img_height_mm / 2) * 1.44

            row_52 = (52 - 1) // 25 + 1  # строка 3
            col_52 = (52 - 1) % 25 + 1   # колонка 2

            x_52 = (col_52 * cell_width_mm - 0.5 * cell_width_mm - (1/6) * cell_width_mm + 0.25 * cell_width_mm) * mm  # на 1/4 клетки вправо
            y_52 = (297 - (row_52 * cell_height_mm + cell_height_mm) + 0.5 * cell_height_mm + 0.25 * cell_height_mm - 1 * cell_height_mm) * mm  # на 1 клетку вниз

            overlay_canvas.drawImage("company.png", x_52, y_52,
                                   width=scaled_width*mm, height=scaled_height*mm,
                                   mask='auto', preserveAspectRatio=True)

            # Добавляем seal.png в центр 590-й клетки со смещением +7 вниз +2 вправо
            seal_img = Image.open("seal.png")
            seal_width_mm = seal_img.width * 0.264583
            seal_height_mm = seal_img.height * 0.264583

            seal_scaled_width = seal_width_mm / 5
            seal_scaled_height = seal_height_mm / 5

            row_590 = (590 - 1) // 25
            col_590 = (590 - 1) % 25

            x_590_center = (col_590 + 0.5) * cell_width_mm * mm
            y_590_center = (297 - (row_590 + 0.5) * cell_height_mm) * mm

            x_590 = x_590_center - (seal_scaled_width * mm / 2) + 2 * cell_width_mm * mm  # +2 клетки вправо
            y_590 = y_590_center - (seal_scaled_height * mm / 2) - 7 * cell_height_mm * mm  # +12 клеток вниз

            overlay_canvas.drawImage("seal.png", x_590, y_590,
                                   width=seal_scaled_width*mm, height=seal_scaled_height*mm,
                                   mask='auto', preserveAspectRatio=True)

            # Добавляем sing_1.png в центр 593-й клетки со смещением +7 вниз +2 вправо
            sing1_img = Image.open("sing_1.png")
            sing1_width_mm = sing1_img.width * 0.264583
            sing1_height_mm = sing1_img.height * 0.264583

            sing1_scaled_width = sing1_width_mm / 5
            sing1_scaled_height = sing1_height_mm / 5

            row_593 = (593 - 1) // 25
            col_593 = (593 - 1) % 25

            x_593_center = (col_593 + 0.5) * cell_width_mm * mm
            y_593_center = (297 - (row_593 + 0.5) * cell_height_mm) * mm

            x_593 = x_593_center - (sing1_scaled_width * mm / 2) + 2 * cell_width_mm * mm  # +2 клетки вправо
            y_593 = y_593_center - (sing1_scaled_height * mm / 2) - 7 * cell_height_mm * mm  # +12 клеток вниз
            
            overlay_canvas.drawImage("sing_1.png", x_593, y_593, 
                                   width=sing1_scaled_width*mm, height=sing1_scaled_height*mm,
                                   mask='auto', preserveAspectRatio=True)
            
            overlay_canvas.save()
            print(f"🖼️ Добавлены изображения для {template_name} через ReportLab API")
        
        elif template_name == 'approvazione':
            # Страница 1 - только company.png
            img = Image.open("company.png")
            img_width_mm = img.width * 0.264583
            img_height_mm = img.height * 0.264583
            
            scaled_width = (img_width_mm / 2) * 1.44
            scaled_height = (img_height_mm / 2) * 1.44
            
            row_52 = (52 - 1) // 25 + 1
            col_52 = (52 - 1) % 25 + 1
            
            x_52 = (col_52 * cell_width_mm - 0.5 * cell_width_mm - (1/6) * cell_width_mm + 0.25 * cell_width_mm) * mm
            y_52 = (297 - (row_52 * cell_height_mm + cell_height_mm) + 0.5 * cell_height_mm + 0.25 * cell_height_mm - 1 * cell_height_mm) * mm
            
            overlay_canvas.drawImage("company.png", x_52, y_52, 
                                   width=scaled_width*mm, height=scaled_height*mm, 
                                   mask='auto', preserveAspectRatio=True)
            
            overlay_canvas.showPage()
            
            # Страница 2 - печать и подпись
            # Добавляем seal.png в центр 590-й клетки
            seal_img = Image.open("seal.png")
            seal_width_mm = seal_img.width * 0.264583
            seal_height_mm = seal_img.height * 0.264583
            
            seal_scaled_width = seal_width_mm / 5
            seal_scaled_height = seal_height_mm / 5
            
            row_590 = (590 - 1) // 25
            col_590 = (590 - 1) % 25
            
            x_590_center = (col_590 + 0.5) * cell_width_mm * mm
            y_590_center = (297 - (row_590 + 0.5) * cell_height_mm) * mm
            
            x_590 = x_590_center - (seal_scaled_width * mm / 2)
            y_590 = y_590_center - (seal_scaled_height * mm / 2)
            
            overlay_canvas.drawImage("seal.png", x_590, y_590, 
                                   width=seal_scaled_width*mm, height=seal_scaled_height*mm,
                                   mask='auto', preserveAspectRatio=True)
            
            # Добавляем sing_1.png в центр 593-й клетки
            sing1_img = Image.open("sing_1.png")
            sing1_width_mm = sing1_img.width * 0.264583
            sing1_height_mm = sing1_img.height * 0.264583
            
            sing1_scaled_width = sing1_width_mm / 5
            sing1_scaled_height = sing1_height_mm / 5
            
            row_593 = (593 - 1) // 25
            col_593 = (593 - 1) % 25
            
            x_593_center = (col_593 + 0.5) * cell_width_mm * mm
            y_593_center = (297 - (row_593 + 0.5) * cell_height_mm) * mm
            
            x_593 = x_593_center - (sing1_scaled_width * mm / 2)
            y_593 = y_593_center - (sing1_scaled_height * mm / 2)
            
            overlay_canvas.drawImage("sing_1.png", x_593, y_593, 
                                   width=sing1_scaled_width*mm, height=sing1_scaled_height*mm,
                                   mask='auto', preserveAspectRatio=True)
            
            overlay_canvas.save()
            print(f"🖼️ Добавлены изображения для approvazione через ReportLab API (печать и подпись на странице 2)")
        
        elif template_name == 'contratto':
            # Страница 1 - добавляем company.png и logo.png
            img = Image.open("company.png")
            img_width_mm = img.width * 0.264583
            img_height_mm = img.height * 0.264583
            
            scaled_width = (img_width_mm / 2) * 1.44  # +44% (было +20%, теперь еще +20%)
            scaled_height = (img_height_mm / 2) * 1.44
            
            row_52 = (52 - 1) // 25 + 1  # строка 3
            col_52 = (52 - 1) % 25 + 1   # колонка 2
            
            x_52 = (col_52 * cell_width_mm - 0.5 * cell_width_mm - (1/6) * cell_width_mm + 0.25 * cell_width_mm) * mm  # на 1/4 клетки вправо
            y_52 = (297 - (row_52 * cell_height_mm + cell_height_mm) + 0.5 * cell_height_mm + 0.25 * cell_height_mm - 1 * cell_height_mm) * mm  # на 1 клетку вниз
            
            overlay_canvas.drawImage("company.png", x_52, y_52, 
                                   width=scaled_width*mm, height=scaled_height*mm, 
                                   mask='auto', preserveAspectRatio=True)
            
            # Добавляем logo.png
            logo_img = Image.open("logo.png")
            logo_width_mm = logo_img.width * 0.264583
            logo_height_mm = logo_img.height * 0.264583
            
            logo_scaled_width = logo_width_mm / 9
            logo_scaled_height = logo_height_mm / 9
            
            row_71 = (71 - 1) // 25
            col_71 = (71 - 1) % 25
            
            x_71 = (col_71 - 2 + 4 - 1.5 - 1) * cell_width_mm * mm  # на 2.5 клетки влево (было 1.5, добавили еще 1)
            y_71 = (297 - (row_71 * cell_height_mm + cell_height_mm) - 0.25 * cell_height_mm - 1 * cell_height_mm) * mm  # на 1 клетку вниз
            
            overlay_canvas.drawImage("logo.png", x_71, y_71, 
                                   width=logo_scaled_width*mm, height=logo_scaled_height*mm,
                                   mask='auto', preserveAspectRatio=True)
            
            # Нумерация страницы 1
            row_862_p1 = (862 - 1) // 25
            col_862_p1 = (862 - 1) % 25
            
            x_page_num_p1 = (col_862_p1 + 1 + 0.5) * cell_width_mm * mm
            y_page_num_p1 = (297 - (row_862_p1 * cell_height_mm + cell_height_mm/2) - 0.25 * cell_height_mm + 0.25 * cell_height_mm) * mm  # на 1/4 клетки вверх
            
            overlay_canvas.setFillColorRGB(0, 0, 0)
            overlay_canvas.setFont("Helvetica", 10)
            overlay_canvas.drawString(x_page_num_p1-2, y_page_num_p1-2, "1")
            
            overlay_canvas.showPage()
            
            # Страница 2 - добавляем только logo.png (подписи/печать теперь в HTML-таблице после пункта 7)
            overlay_canvas.drawImage("logo.png", x_71, y_71, 
                                   width=logo_scaled_width*mm, height=logo_scaled_height*mm,
                                   mask='auto', preserveAspectRatio=True)
            
            # Нумерация страницы 2
            row_862 = (862 - 1) // 25
            col_862 = (862 - 1) % 25
            
            x_page_num = (col_862 + 1 + 0.5) * cell_width_mm * mm
            y_page_num = (297 - (row_862 * cell_height_mm + cell_height_mm/2) - 0.25 * cell_height_mm + 0.25 * cell_height_mm) * mm  # на 1/4 клетки вверх
            
            overlay_canvas.setFillColorRGB(0, 0, 0)
            overlay_canvas.setFont("Helvetica", 10)
            overlay_canvas.drawString(x_page_num-2, y_page_num-2, "2")
            
            overlay_canvas.save()
            print("🖼️ Добавлены изображения для contratto через ReportLab API")
        
        # Объединяем PDF с overlay
        overlay_buffer.seek(0)
        base_pdf = PdfReader(BytesIO(pdf_bytes))
        overlay_pdf = PdfReader(overlay_buffer)
        
        writer = PdfWriter()
        
        # Накладываем изображения на каждую страницу
        for i, page in enumerate(base_pdf.pages):
            if i < len(overlay_pdf.pages):
                page.merge_page(overlay_pdf.pages[i])
            writer.add_page(page)
        
        # Создаем финальный PDF с изображениями
        final_buffer = BytesIO()
        writer.write(final_buffer)
        final_buffer.seek(0)
        
        print(f"✅ PDF с изображениями создан через API! Размер: {len(final_buffer.getvalue())} байт")
        return final_buffer
        
    except Exception as e:
        print(f"❌ Ошибка наложения изображений через API: {e}")
        # Возвращаем обычный PDF без изображений
        buf = BytesIO(pdf_bytes)
        buf.seek(0)
        return buf


def fix_html_layout(template_name='contratto'):
    """Исправляем HTML для корректного отображения"""
    
    # Читаем оригинальный HTML
    import os
    html_file = f'{template_name}.html'
    # Fallback на испанские имена файлов
    fallback_map = {
        'contratto': 'contrato.html',
        'carta': 'tarjeta.html',
        'garanzia': 'garantía.html',
    }
    if not os.path.exists(html_file) and template_name in fallback_map:
        html_file = fallback_map[template_name]
    
    with open(html_file, 'r', encoding='utf-8') as f:
        html = f.read()
    
    # Для garanzia - МИНИМАЛЬНАЯ обработка, только @page рамка
    if template_name == 'garanzia':
        # СНАЧАЛА удаляем все изображения из HTML, но добавляем пробел
        import re
        html = re.sub(r'<img[^>]*>', '', html)  # Удаляем все img теги
        html = re.sub(r'<span[^>]*overflow:[^>]*>[^<]*</span>', '<br><br>', html)  # Заменяем span с overflow на пробел
        print("🗑️ Удалены все изображения из HTML, добавлен пробел вместо изображения")
        
        css_fixes = """
    <style>
    @page {
        size: A4;
        margin: 1cm;           /* 1cm отступ от края страницы до текста */
        border: 4pt solid #5985db;  /* Синяя рамка вокруг текста (увеличена на 1pt) */
        padding: 0;            /* Никаких дополнительных отступов */
    }
    
    /* ИСПРАВЛЯЕМ ОТСТУПЫ BODY - ставим 2см слева и справа */
    .c8 {
        padding: 0 2cm !important;  /* 2см слева и справа для текста */
        max-width: none !important;  /* Убираем ограничение ширины */
    }
    
    /* ТОЛЬКО контроль количества страниц */
    * {
        page-break-after: avoid !important;
        page-break-inside: avoid !important;
        page-break-before: avoid !important;
    }
    
    @page:nth(2) {
        display: none !important;
    }
    </style>
    """
        # Вставляем CSS ПЕРЕД закрывающим </head>
        html = html.replace('</head>', f'{css_fixes}</head>')
        print("✅ Для garanzia добавлена только @page рамка - исходная структура сохранена")
        return html
    
    # Добавляем CSS для правильной разметки (НЕ для garanzia - уже обработана выше)
    elif template_name in ['carta', 'approvazione', 'compensacion']:
        # Для carta - СТРОГО 1 СТРАНИЦА с компактной версткой
        css_fixes = """
    <style>
    @page {
        size: A4;
        margin: 1cm;  /* Отступ как в garanzia */
        border: 2pt solid #5985db;  /* Синяя рамка (на 2pt тоньше чем garanzia) */
        padding: 0;  /* Отступ как в garanzia */
    }
    
    body {
        font-family: "Roboto Mono", monospace;
        font-size: 9pt;  /* Уменьшаем размер шрифта для компактности */
        line-height: 1.0;  /* Компактная высота строки */
        margin: 0;
        padding: 0 2cm;  /* 2см отступы слева и справа как в garanzia */
        overflow: hidden;  /* Предотвращаем выход за границы */
    }
    
    /* СТРОГИЙ КОНТРОЛЬ: ТОЛЬКО 1 СТРАНИЦА для carta */
    * {
        page-break-after: avoid !important;
        page-break-inside: avoid !important;
        page-break-before: avoid !important;
        overflow: hidden !important;  /* Обрезаем контент если он не помещается */
    }
    
    /* Запрещаем создание страниц после 1-й */
    @page:nth(2) {
        display: none !important;
    }
    
    /* УБИРАЕМ ВСЕ рамки элементов - используем только @page рамку КАК В ДРУГИХ ШАБЛОНАХ */
    .c12, .c9, .c20, .c22, .c8 {
        border: none !important;
        padding: 2pt !important;
        margin: 0 !important;
        width: 100% !important;
        max-width: none !important;
    }
    
    /* Основной контейнер документа - компактный */
    .c12 {
        max-width: none !important;
        padding: 0 !important;
        margin: 0 !important;
        width: 100% !important;
        height: auto !important;
        overflow: hidden !important;
        border: none !important;  /* Убираем только лишние рамки, НЕ .c8 */
    }
    
    /* Параграфы с минимальными отступами */
    .c6, .c0, .c2, .c3 {
        margin: 1pt 0 !important;  /* Минимальные отступы */
        padding: 0 !important;
        text-align: left !important;
        width: 100% !important;
        line-height: 1.0 !important;
        overflow: hidden !important;
    }
    
    /* Таблицы компактные */
    table {
        margin: 1pt 0 !important;
        padding: 0 !important;
        width: 100% !important;
        font-size: 9pt !important;
        border-collapse: collapse !important;
    }
    
    td, th {
        padding: 1pt !important;
        margin: 0 !important;
        font-size: 9pt !important;
        line-height: 1.0 !important;
    }
    
    /* Убираем красное выделение и фоны */
    .c15, .c1, .c16, .c6 {
        background-color: transparent !important;
        background: none !important;
    }
    
    /* Списки компактные */
    ul, ol, li {
        margin: 0 !important;
        padding: 0 !important;
        line-height: 1.0 !important;
    }
    
    /* Заголовки компактные */
    h1, h2, h3, h4, h5, h6 {
        margin: 2pt 0 !important;
        padding: 0 !important;
        font-size: 10pt !important;
        line-height: 1.0 !important;
    }
    
    /* СЕТКА ДЛЯ ПОЗИЦИОНИРОВАНИЯ ИЗОБРАЖЕНИЙ 25x35 - КАК В ДРУГИХ ШАБЛОНАХ */
    .grid-overlay {
        position: absolute;
        top: 0;
        left: 0;
        width: 210mm;  /* Полная ширина A4 */
        height: 297mm; /* Полная высота A4 */
        pointer-events: none;
        z-index: 1000;
        opacity: 0; /* 0% прозрачности - невидимая */
    }
    
    .grid-cell {
        position: absolute;
        border: none;
        background-color: transparent;
        display: none;
        font-size: 6pt;
        font-weight: bold;
        color: transparent;
        font-family: Arial, sans-serif;
        box-sizing: border-box;
    }
    
    </style>
    """
        if template_name == 'compensacion':
            css_fixes += """
    <style>
    body.c9.doc-content {
        padding-top: 5em !important;
        font-family: "Courier New", Courier, monospace !important;
        font-size: 9pt !important;
        line-height: 1.12 !important;
    }
    body.c9.doc-content td.c8 {
        overflow: visible !important;
    }
    body.c9.doc-content td.c8 p,
    body.c9.doc-content td.c8 span {
        overflow: visible !important;
    }
    body.c9.doc-content td.c8 span.comp-title {
        font-family: Arial, Helvetica, sans-serif !important;
        font-weight: 700 !important;
        font-size: 12pt !important;
    }
    body.c9.doc-content td.c8 span:not(.comp-title) {
        font-family: "Courier New", Courier, monospace !important;
        font-size: 9pt !important;
        line-height: 1.12 !important;
    }
    body.c9.doc-content span.c4 {
        font-weight: 700 !important;
    }
    body.c9.doc-content span.c5 {
        font-weight: 400 !important;
    }
    body.c9.doc-content p.comp-bullet {
        margin: 4pt 0 5pt 0 !important;
        padding-left: 1.35em !important;
        text-indent: -1.35em !important;
    }
    body.c9.doc-content p.comp-quote {
        margin: 0 0 6pt 0 !important;
        padding-left: 2em !important;
        text-indent: 0 !important;
    }
    body.c9.doc-content p.comp-line-data {
        margin-bottom: 2pt !important;
    }
    body.c9.doc-content p.comp-line-gentile {
        margin-bottom: 4pt !important;
    }
    body.c9.doc-content p.comp-saluti {
        margin-top: 8pt !important;
    }
    </style>
    """
    else:
        # Для contratto и carta - 2 СТРАНИЦЫ
        css_fixes = """
    <style>
    @page {
        size: A4;
        margin: 1cm;  /* Отступ как в garanzia */
        border: 4pt solid #5985db;  /* Синяя рамка как в garanzia (4pt) */
        padding: 0;  /* Отступ как в garanzia */
    }
    
    body {
        font-family: "Roboto Mono", monospace;
        font-size: 10pt;  /* Возвращаем нормальный размер шрифта */
        line-height: 1.0;  /* Нормальная высота строки */
        margin: 0;
        padding: 0 2cm;  /* 2см отступы слева и справа как в garanzia */
    }
    
    /* КРИТИЧНО: Убираем ВСЕ рамки из элементов, оставляем только @page */
    .c20 {
        border: none !important;
        padding: 3mm !important;  /* Нормальные отступы */
        margin: 0 !important;
    }
    
    /* СТРОГИЙ КОНТРОЛЬ: МАКСИМУМ 2 СТРАНИЦЫ */
    * {
        page-break-after: avoid !important;
        page-break-inside: avoid !important;
    }
    
    .page-break {
        page-break-before: always !important;
        page-break-after: avoid !important;
        height: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    
    /* ВОССТАНАВЛИВАЕМ НОРМАЛЬНЫЕ ОТСТУПЫ В ТЕКСТЕ */
    p {
        margin: 2pt 0 !important;  /* Нормальные отступы между параграфами */
        padding: 0 !important;
        line-height: 1.0 !important;
    }
    
    div {
        margin: 0 !important;
        padding: 0 !important;
    }
    
    table {
        margin: 3pt 0 !important;  /* Нормальные отступы для таблиц */
        font-size: 10pt !important;  /* Нормальный размер шрифта */
    }
    
    /* Убираем Google Docs стили */
    .c22 {
        max-width: none !important;
        padding: 0 !important;
        margin: 0 !important;
        border: none !important;
    }
    
    .c14, .c25 {
        margin-left: 0 !important;
    }
    
    /* НОРМАЛЬНЫЕ ЗАГОЛОВКИ С ОТСТУПАМИ */
    .c15 {
        font-size: 14pt !important;  /* Возвращаем нормальный размер */
        margin: 4pt 0 !important;    /* Нормальные отступы */
        font-weight: 700 !important;
    }
    
    .c10 {
        font-size: 12pt !important;  /* Возвращаем нормальный размер */
        margin: 3pt 0 !important;    /* Нормальные отступы */
        font-weight: 700 !important;
    }
    
    /* ТОЛЬКО пустые элементы делаем невидимыми - НЕ ТРОГАЕМ текстовые! */
    .c6:empty {
        height: 0pt !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    
    /* Нормальные отступы для списков */
    .c3 {
        margin: 1pt 0 !important;
    }
    
    /* Запрещаем создание страниц после 2-й */
    @page:nth(3) {
        display: none !important;
    }
    
    /* УБИРАЕМ КРАСНОЕ ВЫДЕЛЕНИЕ ТЕКСТА */
    .c1, .c16 {
        background-color: transparent !important;
        background: none !important;
    }
    
    /* СЕТКА ДЛЯ ПОЗИЦИОНИРОВАНИЯ ИЗОБРАЖЕНИЙ 25x35 - НА КАЖДОЙ СТРАНИЦЕ */
    .grid-overlay {
        position: absolute;
        top: 0;
        left: 0;
        width: 210mm;  /* Полная ширина A4 */
        height: 297mm; /* Полная высота A4 */
        pointer-events: none;
        z-index: 1000;
        opacity: 0; /* 0% прозрачности - невидимая */
    }
    
    /* Сетка для каждой страницы отдельно */
    .page-grid {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100vh;
        pointer-events: none;
        z-index: 1000;
        opacity: 0.3;
    }
    
    .grid-cell {
        position: absolute;
        border: none;
        background-color: transparent;
        display: none;
        font-size: 6pt;
        font-weight: bold;
        color: transparent;
        font-family: Arial, sans-serif;
        box-sizing: border-box;
    }
    
    /* Позиционирование относительно сетки */
    .positioned-image {
        position: absolute;
        z-index: 500;
    }

    /* Разрыв страницы перед пунктом 7. Firmas */
    .section-7-firme {
        page-break-before: always !important;
        margin-top: 0 !important;
    }

    /* ТАБЛИЦА С ПОДПИСЯМИ И ПЕЧАТЬЮ */
    .signatures-tables-wrapper {
        position: relative !important;
        width: 100% !important;
        margin-top: 15pt !important;
        margin-bottom: 10pt !important;
        page-break-inside: avoid !important;
    }

    .signatures-table-base {
        width: 100% !important;
        border-collapse: collapse !important;
        border: none !important;
        background: transparent !important;
        position: relative !important;
    }

    .signatures-table-base td {
        border: none !important;
        padding: 10pt !important;
        background: transparent !important;
        vertical-align: bottom !important;
        text-align: center !important;
    }

    .signatures-table-base td img[alt="Подпись 1"],
    .signatures-table-base td img[alt="Подпись 2"] {
        display: block !important;
        margin: 0 auto !important;
        max-width: 100mm !important;
        max-height: 40mm !important;
        width: auto !important;
        height: auto !important;
    }

    .signatures-table-overlay {
        width: 100% !important;
        border-collapse: collapse !important;
        border: none !important;
        background: transparent !important;
        position: absolute !important;
        top: -25.47mm !important;  /* 3 клетки вверх (3 * 8.49mm) */
        left: 25.2mm !important;  /* 3 клетки вправо (3 * 8.4mm) */
        z-index: 10 !important;
    }

    .signatures-table-overlay td {
        border: none !important;
        padding: 10pt !important;
        background: transparent !important;
        vertical-align: bottom !important;
        text-align: center !important;
    }

    .signatures-table-overlay td img[alt="Печать"] {
        display: block !important;
        margin: 0 auto !important;
        max-width: 150mm !important;
        max-height: 65mm !important;
        width: auto !important;
        height: auto !important;
    }
    
    </style>
    """
    
    # Вставляем CSS ПЕРЕД закрывающим </head>, чтобы наши правила шли ПОСЛЕ исходных
    # и имели приоритет каскада (last-wins)
    html = html.replace('</head>', f'{css_fixes}</head>')
    
    # НЕ НУЖНО - используем @page рамку как в других шаблонах
    
    # КРИТИЧНО: СНАЧАЛА убираем старые изображения, ПОТОМ добавляем новые!
    import re
    
    # Очистка HTML в зависимости от шаблона
    if template_name == 'contratto':
        # 1. ПОЛНОСТЬЮ убираем блок с 3 изображениями между разделами
        middle_images_pattern = r'<p class="c3"><span style="overflow: hidden[^>]*><img alt="" src="images/image1\.png"[^>]*></span><span style="overflow: hidden[^>]*><img alt="" src="images/image2\.png"[^>]*></span><span style="overflow: hidden[^>]*><img alt="" src="images/image4\.png"[^>]*></span></p>'
        html = re.sub(middle_images_pattern, '', html)
    
        # 2. Убираем ВСЕ пустые div и параграфы в конце
        html = re.sub(r'<div><p class="c6 c18"><span class="c7 c23"></span></p></div>$', '', html)
        html = re.sub(r'<p class="c3 c6"><span class="c7 c12"></span></p>$', '', html)
        html = re.sub(r'<p class="c6 c24"><span class="c7 c12"></span></p>$', '', html)
        
        # 3. Убираем избыточные пустые строки между разделами (НЕ в тексте!)
        html = re.sub(r'(<p class="c3 c6"><span class="c7 c12"></span></p>\s*){2,}', '<p class="c3 c6"><span class="c7 c12"></span></p>', html)
        html = re.sub(r'(<p class="c24 c6"><span class="c7 c12"></span></p>\s*)+', '', html)
        
        # 4. Убираем лишние высоты из таблиц
        html = html.replace('class="c13"', 'class="c13" style="height: auto !important;"')
        html = html.replace('class="c19"', 'class="c19" style="height: auto !important;"')
        
        # 5. Принудительно разбиваем на 2 страницы: после раздела 2 (Agevolazioni)
        agevolazioni_end = html.find('• Bonifici SEPA e SDD gratuiti, senza spese aggiuntive')
        if agevolazioni_end != -1:
            # Находим конец этого раздела
            next_section_start = html.find('</td></tr></table>', agevolazioni_end)
            if next_section_start != -1:
                # Вставляем разрыв страницы
                html = html[:next_section_start] + '</td></tr></table><div class="page-break"></div>' + html[next_section_start+len('</td></tr></table>'):]
    
    elif template_name == 'garanzia':
        # Для garanzia НЕ УДАЛЯЕМ НИЧЕГО - сохраняем исходную структуру
        print("✅ Для garanzia сохранена исходная HTML структура без изменений")
    elif template_name in ['carta', 'approvazione', 'compensacion']:
        # Убираем ВСЕ изображения из carta - они создают лишние страницы
        # Убираем логотип в начале
        logo_pattern = r'<p class="c12"><span style="overflow: hidden[^>]*><img alt="" src="images/image1\.png"[^>]*></span></p>'
        html = re.sub(logo_pattern, '', html)
        
        # Убираем изображения в тексте (печать и подпись)
        seal_pattern = r'<span style="overflow: hidden[^>]*><img alt="" src="images/image2\.png"[^>]*></span>'
        html = re.sub(seal_pattern, '', html)
        
        signature_pattern = r'<span style="overflow: hidden[^>]*><img alt="" src="images/image3\.png"[^>]*></span>'
        html = re.sub(signature_pattern, '', html)
        
        # Убираем ВСЕ пустые div и параграфы которые создают лишние страницы
        html = re.sub(r'<div><p class="c6 c18"><span class="c7 c23"></span></p></div>', '', html)
        html = re.sub(r'<p class="c3 c6"><span class="c7 c12"></span></p>', '', html)
        html = re.sub(r'<p class="c6 c24"><span class="c7 c12"></span></p>', '', html)
        html = re.sub(r'<p class="c6"><span class="c7"></span></p>', '', html)
        
        # Убираем избыточные пустые строки между разделами
        html = re.sub(r'(<p class="c3 c6"><span class="c7 c12"></span></p>\s*){2,}', '', html)
        html = re.sub(r'(<p class="c24 c6"><span class="c7 c12"></span></p>\s*)+', '', html)
        
        # Убираем лишние высоты из таблиц - принудительно делаем auto
        html = html.replace('class="c13"', 'class="c13" style="height: auto !important;"')
        html = html.replace('class="c19"', 'class="c19" style="height: auto !important;"')
        html = html.replace('class="c5"', 'class="c5" style="height: auto !important;"')
        html = html.replace('class="c9"', 'class="c9" style="height: auto !important;"')
        
        # КРИТИЧНО: Убираем всё что может создать вторую страницу в конце документа
        # Ищем закрывающий тег body и убираем всё лишнее перед ним
        body_end = html.rfind('</body>')
        if body_end != -1:
            # Находим последний значимый контент перед </body>
            content_before_body = html[:body_end].rstrip()
            # Убираем trailing пустые параграфы и divs
            content_before_body = re.sub(r'(<p[^>]*><span[^>]*></span></p>\s*)+$', '', content_before_body)
            content_before_body = re.sub(r'(<div[^>]*></div>\s*)+$', '', content_before_body)
            html = content_before_body + '\n</body></html>'
        
        print(f"🗑️ Удалены все изображения из {template_name} для предотвращения лишних страниц")
        print("🗑️ Убраны пустые элементы в конце документа для строгого контроля 1 страницы")

    
    # Общая очистка ТОЛЬКО для contratto и carta
    if template_name != 'garanzia':
        # Убираем лишние высоты из таблиц
        html = html.replace('class="c5"', 'class="c5" style="height: auto !important;"')
        html = html.replace('class="c9"', 'class="c9" style="height: auto !important;"')
    else:
        print("🚫 Для garanzia пропускаем общую очистку таблиц - сохраняем исходные стили")
    
    # УНИВЕРСАЛЬНЫЙ АНАЛИЗАТОР И УДАЛИТЕЛЬ ПРОБЛЕМНЫХ ЭЛЕМЕНТОВ
    def analyze_and_fix_problematic_elements(html_content):
        """
        Универсальный анализатор, находящий и исправляющий элементы, создающие лишние страницы:
        1. Элементы с огромными высотами (>500pt)
        2. Элементы с красными/оранжевыми рамками
        3. Таблицы с фиксированными высотами строк
        """
        print("🔍 Анализируем HTML на предмет проблемных элементов...")
        
        # 1. НАХОДИМ И ИСПРАВЛЯЕМ ОГРОМНЫЕ ВЫСОТЫ (>500pt)
        height_pattern = r'\.([a-zA-Z0-9_-]+)\{[^}]*height:\s*([0-9]+(?:\.[0-9]+)?)pt[^}]*\}'
        matches = re.findall(height_pattern, html_content)
        
        fixed_heights = []
        for class_name, height_value in matches:
            height_pt = float(height_value)
            if height_pt > 500:  # Больше 500pt = проблема
                old_pattern = f'.{class_name}{{height:{height_value}pt}}'
                new_pattern = f'.{class_name}{{height:auto;}}'
                html_content = html_content.replace(old_pattern, new_pattern)
                fixed_heights.append(f"{class_name}({height_value}pt)")
        
        if fixed_heights:
            print(f"📏 Исправлены огромные высоты: {', '.join(fixed_heights)}")
        
        # 2. НАХОДИМ И УБИРАЕМ СТАРЫЕ РАМКИ #a52b4c и #5985db (встроенные из HTML)
        # Это нужно чтобы избежать двойных рамок с @page
        border_pattern = r'\.([a-zA-Z0-9_-]+)\{[^}]*border[^}]*#(?:a52b4c|5985db)[^}]*\}'
        border_matches = re.findall(border_pattern, html_content, re.IGNORECASE)
        
        removed_borders = []
        for class_name in border_matches:
            # Заменяем весь CSS класса на простой без рамки
            old_class_pattern = rf'\.{re.escape(class_name)}\{{[^}}]+\}}'
            new_class_css = f'.{class_name}{{border:none !important; padding:5pt;}}'
            html_content = re.sub(old_class_pattern, new_class_css, html_content)
            removed_borders.append(class_name)
        
        if removed_borders:
            print(f"🎨 Убраны встроенные рамки: {', '.join(removed_borders)}")
        # 3. НАХОДИМ И ИСПРАВЛЯЕМ ТАБЛИЦЫ С ФИКСИРОВАННЫМИ ВЫСОТАМИ СТРОК
        # Ищем tr с классами, имеющими большие высоты
        tr_pattern = r'<tr\s+class="([^"]*)"[^>]*>'
        tr_matches = re.findall(tr_pattern, html_content)
        
        fixed_rows = []
        for tr_class in set(tr_matches):  # Убираем дубли
            # Проверяем, есть ли у этого класса большая высота в CSS
            css_pattern = rf'\.{re.escape(tr_class)}\{{[^}}]*height:\s*([0-9]+(?:\.[0-9]+)?)pt[^}}]*\}}'
            css_match = re.search(css_pattern, html_content)
            if css_match:
                height_value = float(css_match.group(1))
                if height_value > 300:  # Строки таблиц больше 300pt = проблема
                    old_css = css_match.group(0)
                    new_css = f'.{tr_class}{{height:auto;}}'
                    html_content = html_content.replace(old_css, new_css)
                    fixed_rows.append(f"{tr_class}({height_value}pt)")
        
        if fixed_rows:
            print(f"📋 Исправлены высоты строк таблиц: {', '.join(fixed_rows)}")
        
        if not fixed_heights and not removed_borders and not fixed_rows:
            print("✅ Проблемных элементов не найдено")
        
        return html_content
    
    # Применяем универсальный анализатор ТОЛЬКО для contratto и carta
    if template_name != 'garanzia':
        html = analyze_and_fix_problematic_elements(html)
    else:
        print("🚫 Для garanzia пропускаем универсальный анализатор - сохраняем исходный HTML")
    
    # ТЕСТИРУЕМ ОЧИСТКУ ПО ЧАСТЯМ - ШАГ 4: ОТКЛЮЧАЕМ ВСЮ АГРЕССИВНУЮ ОЧИСТКУ
    # html = re.sub(r'<p[^>]*>\s*<span[^>]*>\s*</span>\s*</p>', '', html)  # ОТКЛЮЧЕНО - убивает пробелы
    # html = re.sub(r'<div[^>]*>\s*</div>', '', html)  # ОТКЛЮЧЕНО - не влияет на страницы
    # html = re.sub(r'\n\s*\n\s*\n+', '\n\n', html)  # ОТКЛЮЧЕНО - не влияет на лишние страницы
    # html = re.sub(r'<table[^>]*>\s*<tbody[^>]*>\s*<tr[^>]*>\s*<td[^>]*>\s*</td>\s*</tr>\s*</tbody>\s*</table>', '', html)  # ОТКЛЮЧЕНО - тестируем
    
    if template_name != 'garanzia':
        print("🗑️ Удалены: блок изображений между разделами")
        print("📄 Установлен принудительный разрыв после раздела 'Agevolazioni'")
        print("🤖 ПРИМЕНЕН: Универсальный анализатор проблемных элементов")
        print("✅ Агрессивная очистка отключена - сохранены пробелы и структура")
    else:
        print("🚫 Для garanzia все модификации отключены - используется исходный HTML")
    
    # ГЕНЕРИРУЕМ СЕТКУ 25x35 ДЛЯ ПОЗИЦИОНИРОВАНИЯ
    def generate_grid():
        """Генерирует HTML сетку 25x35 с нумерацией для A4"""
        grid_html = '<div class="grid-overlay">\n'
        
        # Размеры страницы A4 в миллиметрах
        page_width_mm = 210  # A4 ширина
        page_height_mm = 297  # A4 высота
        
        cell_width_mm = page_width_mm / 25  # 8.4mm на ячейку
        cell_height_mm = page_height_mm / 35  # 8.49mm на ячейку
        
        cell_number = 1
        
        for row in range(35):
            for col in range(25):
                x_mm = col * cell_width_mm
                y_mm = row * cell_height_mm
                
                grid_html += f'''    <div class="grid-cell" style="
                    left: {x_mm:.1f}mm; 
                    top: {y_mm:.1f}mm; 
                    width: {cell_width_mm:.1f}mm; 
                    height: {cell_height_mm:.1f}mm;">
                    {cell_number}
                </div>\n'''
                
                cell_number += 1
        
        grid_html += '</div>\n'
        return grid_html
    
    
    # Функция для размещения изображения по номеру квадрата
    def place_image_at_cell(cell_number, image_path):
        """Размещает изображение с левой гранью в указанном квадрате"""
        page_width_mm = 210
        page_height_mm = 297
        cell_width_mm = page_width_mm / 25  # 8.4mm
        cell_height_mm = page_height_mm / 35  # 8.49mm
        
        row = (cell_number - 1) // 25
        col = (cell_number - 1) % 25
        x = col * cell_width_mm  # Левая грань квадрата
        y = row * cell_height_mm  # Верхняя грань квадрата
        
        return f'''<img src="{image_path}" style="
            position: absolute;
            left: {x:.1f}mm;
            top: {y:.1f}mm;
            z-index: 600;
        " />\n'''
    
    # Добавляем сетку в body (для contratto, carta, compensacion и approvazione)
    if template_name in ['contratto', 'carta', 'compensacion', 'approvazione']:
        grid_overlay = generate_grid()
        if template_name == 'contratto':
            html = html.replace('<body class="c22 doc-content">', f'<body class="c22 doc-content">\n{grid_overlay}')
        elif template_name in ['carta', 'approvazione', 'compensacion']:
            # Для carta, compensacion и approvazione ищем правильный body тег
            if '<body class="c9 doc-content">' in html:
                html = html.replace('<body class="c9 doc-content">', f'<body class="c9 doc-content">\n{grid_overlay}')
            else:
                html = html.replace('<body class="c6 doc-content">', f'<body class="c6 doc-content">\n{grid_overlay}')
        print("🔢 Добавлена сетка позиционирования 25x35")
        print("📋 Изображения будут добавлены через ReportLab поверх PDF")
    elif template_name == 'garanzia':
        print("🚫 Для garanzia НЕ добавляем сетку - сохраняем чистый HTML")
        print("📋 Изображения будут добавлены ТОЛЬКО через ReportLab поверх PDF")
    else:
        print("📋 Простой PDF без сетки и изображений")
    
    # НЕ СОХРАНЯЕМ исправленный HTML - не нужен
    
    print(f"✅ HTML обработан в памяти (файл не сохраняется)")
    print("🔧 Рамка зафиксирована через @page - будет на каждой странице!")
    if template_name != 'garanzia':
        print("📄 Удалены изображения между разделами - главная причина лишних страниц")
    else:
        print("📄 Для garanzia сохранена исходная структура HTML без удаления изображений")
    
    # Тестовые данные удалены - используем только данные из API
    
    return html


def main():
    """Функция для тестирования PDF конструктора"""
    import sys
    
    # Определяем какой шаблон обрабатывать
    template = sys.argv[1] if len(sys.argv) > 1 else 'contratto'
    
    # Mapping Spanish names to internal Italian names
    alias_map = {
        'contrato': 'contratto',
        'tarjeta': 'carta',
        'garantía': 'garanzia',
        'garantia': 'garanzia',
        'aprobación': 'approvazione',
        'aprobacion': 'approvazione',
        'compensazione': 'compensacion',
    }
    
    internal_template = alias_map.get(template, template)
    
    print(f"🧪 Тестируем PDF конструктор для {template} ({internal_template}) через API...")
    
    # Тестовые данные
    test_data = {
        'name': 'Mario Rossi',
        'amount': 15000.0,
        'tan': 7.15 if internal_template == 'approvazione' else 7.24,  # Фиксированный TAN для approvazione
        'taeg': 8.10, 
        'duration': 36,
        'payment': monthly_payment(15000.0, 36, 7.15 if internal_template == 'approvazione' else 7.24)
    }
    
    try:
        if internal_template == 'contratto':
            buf = generate_contratto_pdf(test_data)
            filename = f'test_contratto.pdf'
        elif internal_template == 'garanzia':
            buf = generate_garanzia_pdf(test_data['name'])
            filename = f'test_garanzia.pdf'
        elif internal_template == 'carta':
            buf = generate_carta_pdf(test_data)
            filename = f'test_carta.pdf'
        elif internal_template == 'approvazione':
            buf = generate_approvazione_pdf(test_data)
            filename = f'test_approvazione.pdf'
        elif internal_template == 'compensacion':
            buf = generate_compensacion_pdf({
                'name': test_data['name'],
                'commission': 360.0,
                'indemnity': 1180.0,
            })
            filename = 'test_compensacion.pdf'
        else:
            print(f"❌ Неизвестный тип документа: {template}")
            return
        
        # Сохраняем тестовый PDF
        with open(filename, 'wb') as f:
            f.write(buf.read())
            
        print(f"✅ PDF создан через API! Файл сохранен как {filename}")
        print(f"📊 Данные: {test_data}")
        
    except Exception as e:
        print(f"❌ Ошибка тестирования API: {e}")


if __name__ == '__main__':
    main()
