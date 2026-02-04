from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from io import BytesIO
from datetime import datetime


def generate_attendance_pdf(title, columns, data):
    """
    Generate a PDF attendance report and return bytes
    """

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=30,
        leftMargin=30,
        topMargin=40,
        bottomMargin=30
    )

    styles = getSampleStyleSheet()
    elements = []

    # Title
    elements.append(Paragraph(f"<b>{title}</b>", styles["Title"]))
    elements.append(Paragraph(
        f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        styles["Normal"]
    ))

    elements.append(Paragraph("<br/>", styles["Normal"]))

    # Table
    table_data = [columns] + data

    table = Table(table_data, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2563EB")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONT", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
        ("BACKGROUND", (0, 1), (-1, -1), colors.whitesmoke),
    ]))

    elements.append(table)

    doc.build(elements)
    buffer.seek(0)

    return buffer.getvalue()