import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def generate_inspection_pdf():
    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "corpus")
    os.makedirs(output_dir, exist_ok=True)
    pdf_path = os.path.join(output_dir, "site_inspection_report.pdf")
    
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=16,
        leading=20,
        textColor=colors.HexColor("#1A365D"),
        alignment=1
    )
    heading_style = ParagraphStyle(
        'HeadingStyle',
        parent=styles['Heading2'],
        fontSize=12,
        leading=15,
        textColor=colors.HexColor("#2B6CB0"),
        spaceBefore=10,
        spaceAfter=5
    )
    normal_style = ParagraphStyle(
        'NormalStyle',
        parent=styles['Normal'],
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#2D3748")
    )
    bold_style = ParagraphStyle(
        'BoldStyle',
        parent=normal_style,
        fontName='Helvetica-Bold'
    )
    
    story = []
    
    # Header
    story.append(Paragraph("AMPERIA CHARGING NETWORKS - FIELD AUDIT DIVISION", title_style))
    story.append(Paragraph("ANNUAL COMPREHENSIVE SITE & HARDWARE INSPECTION AUDIT REPORT", ParagraphStyle('Sub', parent=title_style, fontSize=11, leading=14, textColor=colors.HexColor("#4A5568"))))
    story.append(Spacer(1, 12))
    
    # Meta Table
    meta_data = [
        [Paragraph("<b>Audit Report ID:</b> AUD-2026-PUN-088", normal_style), Paragraph("<b>Site Location ID:</b> MH-PUN-EXP-04", normal_style)],
        [Paragraph("<b>Site Name:</b> Pune Expressway Super-Hub Plaza", normal_style), Paragraph("<b>Inspection Date:</b> April 28, 2026", normal_style)],
        [Paragraph("<b>Lead Inspector:</b> Vikram Shinde (Cert #INSP-882)", normal_style), Paragraph("<b>Site Tier:</b> Tier-1 Critical Highway Hub", normal_style)],
        [Paragraph("<b>Installed Assets:</b> 3x DC-150 Fast Chargers", normal_style), Paragraph("<b>Grid Substation Feed:</b> 11kV / 415V, 750 kVA", normal_style)]
    ]
    meta_table = Table(meta_data, colWidths=[260, 260])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F7FAFC")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#CBD5E0")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 12))
    
    # Section 1
    story.append(Paragraph("1. Environmental & Utility Feed Measurements", heading_style))
    story.append(Paragraph("Field ambient temperature measured at 38.5 deg C at 14:00 hours under direct sun exposure. Grid 3-phase line-to-line voltage measured at 418.2 V AC RMS with phase imbalance at 1.2% (well within 8% threshold). Dedicated copper earthing pit loop impedance tested at 2.14 Ohms using 3-point fall-of-potential test (fully compliant with < 5.0 Ohms spec).", normal_style))
    story.append(Spacer(1, 10))
    
    # Section 2: Physical Insulation Resistance Testing Table
    story.append(Paragraph("2. Physical High-Voltage Insulation Resistance Test Results (Megohmmeter 1000V DC)", heading_style))
    story.append(Paragraph("Insulation resistance measurements taken across DC Bus to Protective Earth and Charging Cable Conductors to Earth after complete de-energization:", normal_style))
    story.append(Spacer(1, 6))
    
    table_data = [
        ["Asset Tag", "Serial Number", "Cable Length / Type", "Insulation Reading", "Test Status", "Inspector Notes"],
        ["Unit DC150-01", "AMP-DC150-2025-0104", "8.5m Liquid-Cooled Dual Gun", "620 Megaohms (MΩ)", "PASS (Nominal)", "Internal insulation integrity excellent."],
        ["Unit DC150-02", "AMP-DC150-2025-0105", "8.5m Liquid-Cooled Dual Gun", "580 Megaohms (MΩ)", "PASS (Nominal)", "Zero dielectric leakage detected."],
        ["Unit DC150-03", "AMP-DC150-2025-0106", "8.5m Liquid-Cooled Dual Gun", "410 Megaohms (MΩ)", "PASS (Compliant)", "Insulation reading 410 Megaohms, well above 100 Megaohms limit."],
    ]
    
    t = Table(table_data, colWidths=[65, 85, 110, 85, 75, 100])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#2B6CB0")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 8),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E0")),
        ('BACKGROUND', (0,1), (-1,-1), colors.white),
        ('FONTSIZE', (0,1), (-1,-1), 7.5),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t)
    story.append(Spacer(1, 10))
    
    # Section 3: Physical Cable Wear & Mechanical Observations
    story.append(Paragraph("3. Cable Physical Wear, Strain Relief & Connector Inspection", heading_style))
    story.append(Paragraph("Detailed mechanical audit of charging guns, cables, and coolant conduits:", normal_style))
    story.append(Paragraph("• <b>Unit DC150-01 & DC150-02:</b> Cables, handles, and CCS2 latches in good mechanical condition. Coolant flow measured at 3.8 L/min (above 2.5 L/min minimum threshold).", normal_style))
    story.append(Paragraph("• <b>Unit DC150-03 (Specific Field Finding):</b> On Gun B, physical scuffing and outer jacket abrasion observed on the liquid-cooled cable at the lower strain relief boot. Measured jacket wear depth is <b>1.8 mm</b> into outer protective sheath. Dielectric core remains unexposed, but cable is scheduled for preemptive replacement during next 6-month maintenance window.", normal_style))
    story.append(Paragraph("• <b>Cabinet Filter & Fans:</b> Intake dust filters replaced on all three units. Radiator fans tested at 100% duty cycle without bearing vibration.", normal_style))
    story.append(Spacer(1, 12))
    
    # Section 4: Sign-off
    story.append(Paragraph("4. Auditor Certification & Compliance Sign-off", heading_style))
    story.append(Paragraph("All 3 units at Pune Expressway Super-Hub (MH-PUN-EXP-04) passed high-voltage electrical safety and earthing compliance audits. Next mandatory annual inspection scheduled for April 2027.", normal_style))
    story.append(Spacer(1, 15))
    
    sig_data = [
        [Paragraph("<b>Lead Auditor Signature:</b> <i>Vikram Shinde</i>", normal_style), Paragraph("<b>Site Representative:</b> <i>Amperia Operations Center</i>", normal_style)],
        [Paragraph("<b>Date Signed:</b> April 28, 2026", normal_style), Paragraph("<b>Audit Status:</b> APPROVED & ARCHIVED", normal_style)]
    ]
    sig_table = Table(sig_data, colWidths=[260, 260])
    sig_table.setStyle(TableStyle([
        ('LINEABOVE', (0,0), (-1,-1), 0.5, colors.HexColor("#A0AEC0")),
        ('TOPPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(sig_table)
    
    doc.build(story)
    print(f"[Done] Generated official site inspection PDF: {pdf_path}")

if __name__ == "__main__":
    generate_inspection_pdf()
