#!/usr/bin/env python3
"""
P16 Corpus Generator — Creates realistic test documents with known ground truth.

Generates PDFs and images for:
  - purchase_agreements/
  - window_stickers/
  - registrations/
  - wechat/
  - vin_photos/
  - dealer_worksheets/

All documents contain realistic auto insurance intake fields.
Ground truth is embedded in the CORPUS_GROUND_TRUTH dict at the bottom.

Usage:
    python3 scripts/generate_p16_corpus.py
"""

import json
import sys
from pathlib import Path
from datetime import date

# ── PDF generation via reportlab ────────────────────────────────────────────
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch
from reportlab.lib import colors

# ── Image generation via Pillow ─────────────────────────────────────────────
from PIL import Image, ImageDraw, ImageFont

REPO_ROOT = Path(__file__).resolve().parent.parent
CORPUS_ROOT = REPO_ROOT / "test_data" / "p16_real_docs"

# ── Ground truth data for each document ─────────────────────────────────────
# These values are what we embed into the documents.
# The evaluation runner compares extracted values to these.

CORPUS_GROUND_TRUTH = {
    # ── Purchase Agreements ──────────────────────────────────────────────────
    "purchase_agreements/pa_001_toyota_camry.pdf": {
        "doc_type": "purchase_agreement",
        "customer_name": "Wei Zhang",
        "vin": "4T1BF1FK5CU512345",
        "year": "2023",
        "make_model": "Toyota Camry",
        "garaging_zip": "91801",
        "lienholder": "Toyota Financial Services",
        "ocr_difficulty": "easy",
        "notes": "Standard dealer PDF, clean text, single page",
    },
    "purchase_agreements/pa_002_honda_civic.pdf": {
        "doc_type": "purchase_agreement",
        "customer_name": "Mei Lin Chen",
        "vin": "2HGFC2F69MH123456",
        "year": "2021",
        "make_model": "Honda Civic",
        "garaging_zip": "91776",
        "lienholder": "Honda Financial Services",
        "ocr_difficulty": "easy",
        "notes": "Multi-page contract, key fields on page 1",
    },
    "purchase_agreements/pa_003_bmw_x5.pdf": {
        "doc_type": "purchase_agreement",
        "customer_name": "Jianming Liu",
        "vin": "5UXCR6C06L9B12345",
        "year": "2020",
        "make_model": "BMW X5",
        "garaging_zip": "91011",
        "lienholder": "BMW Financial Services",
        "ocr_difficulty": "medium",
        "notes": "Dense two-column layout, VIN in header box",
    },
    "purchase_agreements/pa_004_tesla_model3.jpg": {
        "doc_type": "purchase_agreement",
        "customer_name": "Xiaohui Wang",
        "vin": "5YJ3E1EA8MF123456",
        "year": "2021",
        "make_model": "Tesla Model 3",
        "garaging_zip": "91030",
        "lienholder": "",
        "ocr_difficulty": "medium",
        "notes": "Image scan of Tesla order agreement, no lienholder (cash purchase)",
    },
    "purchase_agreements/pa_005_lexus_rx350.pdf": {
        "doc_type": "purchase_agreement",
        "customer_name": "Hongying Zhao",
        "vin": "2T2BZMCA8KC123456",
        "year": "2019",
        "make_model": "Lexus RX 350",
        "garaging_zip": "91801",
        "lienholder": "Lexus Financial Services",
        "ocr_difficulty": "hard",
        "notes": "Scanned fax copy, slightly rotated, low contrast",
    },
    "purchase_agreements/pa_006_nissan_altima.jpg": {
        "doc_type": "purchase_agreement",
        "customer_name": "Fang Xu",
        "vin": "1N4BL4BV2KC123456",
        "year": "2019",
        "make_model": "Nissan Altima",
        "garaging_zip": "91702",
        "lienholder": "Nissan Motor Acceptance",
        "ocr_difficulty": "easy",
        "notes": "Phone photo of dealer printout, straight shot",
    },
    "purchase_agreements/pa_007_hyundai_elantra.pdf": {
        "doc_type": "purchase_agreement",
        "customer_name": "Yong Kim",
        "vin": "KMHD84LF8KU123456",
        "year": "2019",
        "make_model": "Hyundai Elantra",
        "garaging_zip": "91754",
        "lienholder": "Hyundai Motor Finance",
        "ocr_difficulty": "medium",
        "notes": "Bilingual English/Korean document, fields clear",
    },
    # ── Window Stickers ──────────────────────────────────────────────────────
    "window_stickers/ws_001_toyota_rav4.pdf": {
        "doc_type": "window_sticker",
        "customer_name": "",
        "vin": "4T3P6RFV5MU123456",
        "year": "2021",
        "make_model": "Toyota RAV4",
        "garaging_zip": "",
        "lienholder": "",
        "ocr_difficulty": "easy",
        "notes": "Standard Monroney label PDF, all fields in structured grid",
    },
    "window_stickers/ws_002_ford_f150.jpg": {
        "doc_type": "window_sticker",
        "customer_name": "",
        "vin": "1FTFW1ET5MKD12345",
        "year": "2021",
        "make_model": "Ford F-150",
        "garaging_zip": "",
        "lienholder": "",
        "ocr_difficulty": "easy",
        "notes": "Window sticker photo, slight glare on top third",
    },
    "window_stickers/ws_003_honda_crv.jpg": {
        "doc_type": "window_sticker",
        "customer_name": "",
        "vin": "7FARW2H57ME123456",
        "year": "2021",
        "make_model": "Honda CR-V",
        "garaging_zip": "",
        "lienholder": "",
        "ocr_difficulty": "medium",
        "notes": "Photo of sticker through car window, slight distortion",
    },
    "window_stickers/ws_004_chevy_equinox.png": {
        "doc_type": "window_sticker",
        "customer_name": "",
        "vin": "2GNAXKEV4M6123456",
        "year": "2021",
        "make_model": "Chevrolet Equinox",
        "garaging_zip": "",
        "lienholder": "",
        "ocr_difficulty": "easy",
        "notes": "Screenshot from dealer inventory system",
    },
    "window_stickers/ws_005_bmw_330i.pdf": {
        "doc_type": "window_sticker",
        "customer_name": "",
        "vin": "3MW5R7J07N8C12345",
        "year": "2022",
        "make_model": "BMW 330i",
        "garaging_zip": "",
        "lienholder": "",
        "ocr_difficulty": "medium",
        "notes": "BMW Monroney label, dense feature list, VIN at bottom",
    },
    # ── Registrations ────────────────────────────────────────────────────────
    "registrations/reg_001_ca_dmv.jpg": {
        "doc_type": "registration",
        "customer_name": "Wei Zhang",
        "vin": "4T1BF1FK5CU512345",
        "year": "2023",
        "make_model": "Toyota Camry",
        "garaging_zip": "91801",
        "lienholder": "",
        "ocr_difficulty": "easy",
        "notes": "California DMV registration card, standard format",
    },
    "registrations/reg_002_ca_dmv.pdf": {
        "doc_type": "registration",
        "customer_name": "Mei Lin Chen",
        "vin": "2HGFC2F69MH123456",
        "year": "2021",
        "make_model": "Honda Civic",
        "garaging_zip": "91776",
        "lienholder": "",
        "ocr_difficulty": "medium",
        "notes": "PDF of CA temp registration, lighter text",
    },
    "registrations/reg_003_ca_temp.jpg": {
        "doc_type": "registration",
        "customer_name": "Jianming Liu",
        "vin": "5UXCR6C06L9B12345",
        "year": "2020",
        "make_model": "BMW X5",
        "garaging_zip": "91011",
        "lienholder": "",
        "ocr_difficulty": "hard",
        "notes": "Temporary operating permit, partial fields, blurry photo",
    },
    # ── WeChat Screenshots ───────────────────────────────────────────────────
    "wechat/wechat_001_vin_message.jpg": {
        "doc_type": "wechat_screenshot",
        "customer_name": "Xiaohui Wang",
        "vin": "5YJ3E1EA8MF123456",
        "year": "2021",
        "make_model": "Tesla Model 3",
        "garaging_zip": "91030",
        "lienholder": "",
        "ocr_difficulty": "medium",
        "notes": "WeChat message thread, customer typed VIN in chat",
    },
    "wechat/wechat_002_delivery_date.png": {
        "doc_type": "wechat_screenshot",
        "customer_name": "Fang Xu",
        "vin": "",
        "year": "2019",
        "make_model": "Nissan Altima",
        "garaging_zip": "91702",
        "lienholder": "",
        "ocr_difficulty": "medium",
        "notes": "WeChat screenshot with delivery date confirmation, no VIN visible",
    },
    "wechat/wechat_003_zip_confirmation.jpg": {
        "doc_type": "wechat_screenshot",
        "customer_name": "Hongying Zhao",
        "vin": "",
        "year": "",
        "make_model": "",
        "garaging_zip": "91801",
        "lienholder": "",
        "ocr_difficulty": "easy",
        "notes": "Simple WeChat message: customer confirms garaging ZIP only",
    },
    # ── VIN Photos ───────────────────────────────────────────────────────────
    "vin_photos/vin_001_dashboard.jpg": {
        "doc_type": "vin_photo",
        "customer_name": "",
        "vin": "4T1BF1FK5CU512345",
        "year": "",
        "make_model": "",
        "garaging_zip": "",
        "lienholder": "",
        "ocr_difficulty": "medium",
        "notes": "Photo of dashboard VIN plate through windshield, typical iPhone shot",
    },
    "vin_photos/vin_002_door_jamb.jpg": {
        "doc_type": "vin_photo",
        "customer_name": "",
        "vin": "5UXCR6C06L9B12345",
        "year": "",
        "make_model": "",
        "garaging_zip": "",
        "lienholder": "",
        "ocr_difficulty": "hard",
        "notes": "Door jamb sticker photo, dark lighting, VIN partially obscured",
    },
    # ── Dealer Worksheets ────────────────────────────────────────────────────
    "dealer_worksheets/dw_001_finance_worksheet.pdf": {
        "doc_type": "dealer_worksheet",
        "customer_name": "Yong Kim",
        "vin": "KMHD84LF8KU123456",
        "year": "2019",
        "make_model": "Hyundai Elantra",
        "garaging_zip": "91754",
        "lienholder": "Hyundai Motor Finance",
        "ocr_difficulty": "easy",
        "notes": "Finance department worksheet with all fields, good quality",
    },
    "dealer_worksheets/dw_002_buyers_order.pdf": {
        "doc_type": "dealer_worksheet",
        "customer_name": "Wei Zhang",
        "vin": "4T1BF1FK5CU512345",
        "year": "2023",
        "make_model": "Toyota Camry",
        "garaging_zip": "91801",
        "lienholder": "Toyota Financial Services",
        "ocr_difficulty": "medium",
        "notes": "Buyer's order with trade-in section (second vehicle flagged)",
    },
}


# ── Helpers ──────────────────────────────────────────────────────────────────

def pil_font(size: int):
    """Return a PIL font, falling back to default if truetype not available."""
    try:
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size)
    except (IOError, OSError):
        try:
            return ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", size)
        except (IOError, OSError):
            return ImageFont.load_default()


def pil_font_bold(size: int):
    try:
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size)
    except (IOError, OSError):
        try:
            return ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", size)
        except (IOError, OSError):
            return ImageFont.load_default()


# ── PDF generators ───────────────────────────────────────────────────────────

def make_purchase_agreement_pdf(path: Path, gt: dict):
    """Generate a realistic purchase agreement PDF."""
    c = canvas.Canvas(str(path), pagesize=letter)
    w, h = letter

    # Header
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(w / 2, h - 60, "VEHICLE PURCHASE AGREEMENT")
    c.setFont("Helvetica", 10)
    c.drawCentredString(w / 2, h - 80, "California Dealer Agreement — Retain for Records")

    # Horizontal rule
    c.setStrokeColor(colors.black)
    c.setLineWidth(1)
    c.line(72, h - 90, w - 72, h - 90)

    y = h - 120

    def label_value(label, value, y, x=72, label_w=160):
        c.setFont("Helvetica-Bold", 10)
        c.drawString(x, y, label + ":")
        c.setFont("Helvetica", 10)
        c.drawString(x + label_w, y, str(value))
        return y - 22

    c.setFont("Helvetica-Bold", 12)
    c.drawString(72, y, "VEHICLE INFORMATION")
    y -= 20

    y = label_value("Year / Make / Model", f"{gt['year']} {gt['make_model']}", y)
    y = label_value("Vehicle Identification Number (VIN)", gt["vin"], y)
    if gt.get("lienholder"):
        y = label_value("Lienholder / Lender", gt["lienholder"], y)
    y -= 10

    c.setFont("Helvetica-Bold", 12)
    c.drawString(72, y, "BUYER INFORMATION")
    y -= 20

    y = label_value("Buyer Name", gt["customer_name"], y)
    y = label_value("Garaging Address ZIP", gt["garaging_zip"], y)
    y = label_value("Date", date.today().strftime("%m/%d/%Y"), y)

    y -= 20
    c.setFont("Helvetica-Bold", 12)
    c.drawString(72, y, "FINANCE INFORMATION")
    y -= 20

    if gt.get("lienholder"):
        y = label_value("Financing Institution", gt["lienholder"], y)
    y = label_value("Purchase Price", "$32,450.00", y)
    y = label_value("Down Payment", "$5,000.00", y)
    y = label_value("Monthly Payment", "$589.00", y)
    y = label_value("Loan Term", "60 months", y)

    y -= 30
    c.setFont("Helvetica", 8)
    c.drawString(72, y, "This agreement is subject to the terms and conditions on the reverse side.")
    y -= 14
    c.drawString(72, y, "California Vehicle Code section 11736 governs all vehicle sale agreements.")

    c.save()


def make_window_sticker_pdf(path: Path, gt: dict):
    """Generate a Monroney label style PDF."""
    c = canvas.Canvas(str(path), pagesize=letter)
    w, h = letter

    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(w / 2, h - 50, f"{gt['year']} {gt['make_model'].upper()}")
    c.setFont("Helvetica", 11)
    c.drawCentredString(w / 2, h - 70, "MANUFACTURER'S SUGGESTED RETAIL PRICE")

    c.setStrokeColor(colors.black)
    c.setLineWidth(2)
    c.line(72, h - 80, w - 72, h - 80)

    y = h - 110

    def row(label, value, y, bold_label=False):
        if bold_label:
            c.setFont("Helvetica-Bold", 10)
        else:
            c.setFont("Helvetica", 10)
        c.drawString(72, y, label)
        c.setFont("Helvetica", 10)
        c.drawRightString(w - 72, y, str(value))
        c.setLineWidth(0.5)
        c.setStrokeColor(colors.lightgrey)
        c.line(72, y - 4, w - 72, y - 4)
        return y - 20

    c.setFont("Helvetica-Bold", 11)
    c.drawString(72, y, "VEHICLE IDENTIFICATION")
    y -= 20

    y = row("Vehicle Identification Number (VIN):", gt["vin"], y, bold_label=True)
    y = row("Model Year:", gt["year"], y)
    y = row("Make / Model:", gt["make_model"], y)
    y = row("Body Style:", "4-Door Sedan", y)
    y = row("Drive Type:", "Front-Wheel Drive", y)
    y = row("Engine:", "2.5L 4-Cylinder DOHC", y)
    y = row("Transmission:", "8-Speed Automatic", y)
    y -= 10

    c.setFont("Helvetica-Bold", 11)
    c.drawString(72, y, "STANDARD FEATURES")
    y -= 20
    features = [
        "Apple CarPlay / Android Auto",
        "Dual-Zone Automatic Climate Control",
        "Keyless Entry with Push-Button Start",
        "Toyota Safety Sense 2.5+",
        "8-inch Touchscreen Display",
    ]
    c.setFont("Helvetica", 9)
    for feat in features:
        c.drawString(90, y, f"• {feat}")
        y -= 14

    y -= 15
    c.setFont("Helvetica-Bold", 11)
    c.drawString(72, y, "PRICING")
    y -= 20
    y = row("Base Vehicle Price:", "$29,995", y)
    y = row("Destination & Delivery:", "$1,025", y)
    y = row("TOTAL MSRP:", "$31,020", y)

    y -= 20
    c.setFont("Helvetica", 8)
    c.drawCentredString(w / 2, y, "This label is required by federal law.")

    c.save()


def make_registration_pdf(path: Path, gt: dict):
    """Generate a CA DMV registration certificate style PDF."""
    c = canvas.Canvas(str(path), pagesize=letter)
    w, h = letter

    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(w / 2, h - 50, "STATE OF CALIFORNIA")
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(w / 2, h - 68, "DEPARTMENT OF MOTOR VEHICLES")
    c.setFont("Helvetica", 10)
    c.drawCentredString(w / 2, h - 84, "CERTIFICATE OF OWNERSHIP / REGISTRATION")

    c.setLineWidth(2)
    c.rect(50, h - 380, w - 100, 270)

    y = h - 110

    def dmv_row(label, value, y):
        c.setFont("Helvetica-Bold", 9)
        c.drawString(72, y, label.upper() + ":")
        c.setFont("Helvetica", 10)
        c.drawString(72, y - 14, str(value))
        return y - 32

    y = dmv_row("Registered Owner", gt["customer_name"], y)
    y = dmv_row("Address / City / ZIP", f"[ADDRESS REDACTED] {gt['garaging_zip']}", y)
    y = dmv_row("License Plate", "7ABC234", y)
    y = dmv_row("Vehicle Identification Number", gt["vin"], y)
    y = dmv_row("Year / Make / Model", f"{gt['year']} {gt['make_model']}", y)
    y = dmv_row("Registration Expiration", "12/2025", y)

    y = h - 400
    c.setFont("Helvetica", 8)
    c.drawString(72, y, "Keep this document in the vehicle at all times. DMV.CA.GOV")

    c.save()


def make_dealer_worksheet_pdf(path: Path, gt: dict):
    """Generate a dealer finance worksheet PDF."""
    c = canvas.Canvas(str(path), pagesize=letter)
    w, h = letter

    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(w / 2, h - 50, "DEALER FINANCE WORKSHEET")
    c.setFont("Helvetica", 10)
    c.drawCentredString(w / 2, h - 68, "INTERNAL DOCUMENT — NOT FOR CUSTOMER DISTRIBUTION")

    c.setLineWidth(1.5)
    c.line(72, h - 78, w - 72, h - 78)

    y = h - 110

    def ws_row(label, value, y):
        c.setFont("Helvetica-Bold", 9)
        c.drawString(72, y, label + ":")
        c.setFont("Courier", 10)
        c.drawString(280, y, str(value))
        c.setLineWidth(0.3)
        c.setStrokeColor(colors.lightgrey)
        c.line(72, y - 3, w - 72, y - 3)
        c.setStrokeColor(colors.black)
        return y - 20

    c.setFont("Helvetica-Bold", 11)
    c.drawString(72, y, "CUSTOMER")
    y -= 18
    y = ws_row("Buyer Name", gt["customer_name"], y)
    y = ws_row("Garaging ZIP", gt["garaging_zip"], y)

    y -= 5
    c.setFont("Helvetica-Bold", 11)
    c.drawString(72, y, "VEHICLE")
    y -= 18
    y = ws_row("VIN", gt["vin"], y)
    y = ws_row("Year", gt["year"], y)
    y = ws_row("Make / Model", gt["make_model"], y)

    if gt.get("lienholder"):
        y -= 5
        c.setFont("Helvetica-Bold", 11)
        c.drawString(72, y, "FINANCE")
        y -= 18
        y = ws_row("Lender / Lienholder", gt["lienholder"], y)
        y = ws_row("Loan Amount", "$27,450.00", y)
        y = ws_row("APR", "4.99%", y)
        y = ws_row("Term (months)", "60", y)

    c.save()


# ── Image generators ─────────────────────────────────────────────────────────

def make_purchase_agreement_jpg(path: Path, gt: dict):
    """Generate a purchase agreement as a scanned-photo style image."""
    img = Image.new("RGB", (1200, 1600), color=(252, 252, 248))
    draw = ImageDraw.Draw(img)

    font_title = pil_font_bold(36)
    font_h2 = pil_font_bold(24)
    font_label = pil_font_bold(20)
    font_val = pil_font(20)
    font_small = pil_font(16)

    y = 60
    draw.text((600, y), "VEHICLE PURCHASE AGREEMENT", font=font_title, fill=(20, 20, 20), anchor="mt")
    y += 60
    draw.line([(80, y), (1120, y)], fill=(100, 100, 100), width=2)
    y += 20

    draw.text((80, y), "VEHICLE INFORMATION", font=font_h2, fill=(40, 40, 120))
    y += 40

    def row(label, val, y):
        draw.text((80, y), label + ":", font=font_label, fill=(60, 60, 60))
        draw.text((400, y), str(val), font=font_val, fill=(20, 20, 20))
        return y + 36

    y = row("Year / Make / Model", f"{gt['year']} {gt['make_model']}", y)
    y = row("VIN", gt["vin"], y)
    if gt.get("lienholder"):
        y = row("Lienholder", gt["lienholder"], y)
    y += 20

    draw.text((80, y), "BUYER INFORMATION", font=font_h2, fill=(40, 40, 120))
    y += 40
    y = row("Buyer Name", gt["customer_name"], y)
    y = row("Garaging ZIP", gt["garaging_zip"], y)
    y = row("Date", date.today().strftime("%m/%d/%Y"), y)
    y += 30

    draw.text((80, y), "AGREEMENT TERMS", font=font_h2, fill=(40, 40, 120))
    y += 40
    draw.text((80, y), "Buyer agrees to purchase the above vehicle subject to terms", font=font_small, fill=(80, 80, 80))
    y += 26
    draw.text((80, y), "and conditions as outlined in this agreement. California DMV", font=font_small, fill=(80, 80, 80))
    y += 26
    draw.text((80, y), "transfer fees and all applicable taxes are buyer's responsibility.", font=font_small, fill=(80, 80, 80))

    # Slight noise to simulate scan
    import random
    rng = random.Random(42)
    for _ in range(800):
        x = rng.randint(0, 1199)
        yp = rng.randint(0, 1599)
        c_val = rng.randint(200, 240)
        draw.point((x, yp), fill=(c_val, c_val, c_val))

    img.save(str(path), quality=88)


def make_wechat_screenshot(path: Path, gt: dict, suffix: str = ".jpg"):
    """Generate a WeChat chat screenshot with automotive data."""
    img = Image.new("RGB", (750, 1334), color=(237, 237, 237))
    draw = ImageDraw.Draw(img)

    font_header = pil_font_bold(28)
    font_name = pil_font_bold(22)
    font_msg = pil_font(20)
    font_time = pil_font(16)
    font_small = pil_font(15)

    # Status bar
    draw.rectangle([(0, 0), (750, 44)], fill=(50, 50, 50))
    draw.text((375, 22), "9:41 AM", font=font_small, fill=(255, 255, 255), anchor="mm")

    # Header bar
    draw.rectangle([(0, 44), (750, 100)], fill=(237, 237, 237))
    draw.line([(0, 100), (750, 100)], fill=(200, 200, 200), width=1)
    draw.text((375, 72), "WeChat", font=font_header, fill=(30, 30, 30), anchor="mm")

    y = 120

    def bubble_right(text_lines, y):
        """Caller bubble (right side, green)."""
        max_w = max(draw.textlength(t, font=font_msg) for t in text_lines)
        bw = int(max_w) + 30
        bh = len(text_lines) * 30 + 16
        x1 = 750 - bw - 20
        draw.rounded_rectangle([(x1, y), (750 - 20, y + bh)], radius=12, fill=(149, 236, 105))
        for i, line in enumerate(text_lines):
            draw.text((x1 + 14, y + 8 + i * 30), line, font=font_msg, fill=(20, 20, 20))
        return y + bh + 16

    def bubble_left(text_lines, sender, y):
        """Contact bubble (left side, white)."""
        max_w = max(draw.textlength(t, font=font_msg) for t in text_lines)
        bw = int(max_w) + 30
        bh = len(text_lines) * 30 + 16
        draw.text((80, y), sender, font=font_name, fill=(80, 80, 180))
        y += 28
        draw.rounded_rectangle([(80, y), (80 + bw, y + bh)], radius=12, fill=(255, 255, 255))
        for i, line in enumerate(text_lines):
            draw.text((94, y + 8 + i * 30), line, font=font_msg, fill=(20, 20, 20))
        return y + bh + 20

    # Scenario varies by content
    if gt.get("vin"):
        y = bubble_left([f"My car VIN is:", gt["vin"]], gt["customer_name"].split()[0] if gt.get("customer_name") else "Customer", y)
        y = bubble_right(["Thank you! Received."], y)
        if gt.get("year") and gt.get("make_model"):
            y = bubble_left([f"{gt['year']} {gt['make_model']}"], gt["customer_name"].split()[0] if gt.get("customer_name") else "Customer", y)
    elif gt.get("garaging_zip") and not gt.get("vin"):
        y = bubble_left([f"My garaging address ZIP is {gt['garaging_zip']}"], gt["customer_name"].split()[0] if gt.get("customer_name") else "Customer", y)
        y = bubble_right(["Got it, thanks!"], y)
        y = bubble_left(["Will the car be garaged there?"], gt["customer_name"].split()[0] if gt.get("customer_name") else "Customer", y)
        y = bubble_right(["Yes, it will be at that address."], y)
    else:
        y = bubble_left([f"Delivery confirmed for next Tuesday."], gt["customer_name"].split()[0] if gt.get("customer_name") else "Customer", y)
        if gt.get("make_model"):
            y = bubble_left([f"For the {gt['year']} {gt['make_model']}"], gt["customer_name"].split()[0] if gt.get("customer_name") else "Customer", y)
        y = bubble_right(["Perfect, I'll update the file."], y)

    if suffix == ".png":
        img.save(str(path), format="PNG")
    else:
        img.save(str(path), quality=92)


def make_vin_photo(path: Path, gt: dict):
    """Generate a VIN plate photo."""
    img = Image.new("RGB", (800, 300), color=(40, 40, 40))
    draw = ImageDraw.Draw(img)

    font_label = pil_font(18)
    font_vin = pil_font_bold(38)
    font_small = pil_font(16)

    # Simulate aluminum VIN plate
    draw.rectangle([(20, 20), (780, 280)], fill=(220, 215, 200), outline=(180, 170, 150), width=3)

    draw.text((400, 50), "VEHICLE IDENTIFICATION NUMBER", font=font_label, fill=(80, 80, 80), anchor="mt")
    draw.line([(40, 72), (760, 72)], fill=(150, 140, 130), width=1)

    # VIN in large monospace style
    draw.text((400, 140), gt["vin"], font=font_vin, fill=(20, 20, 20), anchor="mm")

    draw.text((400, 190), "U.S. Federal Motor Vehicle Safety Standard No. 115", font=font_small, fill=(100, 100, 100), anchor="mt")

    # Simulate slight photo noise/blur
    import random
    rng = random.Random(7)
    for _ in range(300):
        x = rng.randint(0, 799)
        y = rng.randint(0, 299)
        c_val = rng.randint(0, 40)
        a = rng.randint(80, 160)
        draw.point((x, y), fill=(c_val, c_val, c_val + 10))

    img.save(str(path), quality=82)


def make_window_sticker_image(path: Path, gt: dict, suffix: str = ".jpg"):
    """Generate a window sticker image."""
    img = Image.new("RGB", (850, 1100), color=(255, 255, 245))
    draw = ImageDraw.Draw(img)

    font_title = pil_font_bold(28)
    font_h2 = pil_font_bold(20)
    font_label = pil_font_bold(16)
    font_val = pil_font(16)

    y = 40
    draw.rectangle([(30, 30), (820, 1070)], outline=(0, 0, 0), width=2)

    draw.text((425, y + 10), f"{gt['year']} {gt['make_model'].upper()}", font=font_title, fill=(10, 10, 10), anchor="mt")
    y += 60
    draw.text((425, y), "MANUFACTURER'S SUGGESTED RETAIL PRICE", font=font_h2, fill=(40, 40, 40), anchor="mt")
    y += 40
    draw.line([(50, y), (800, y)], fill=(0, 0, 0), width=1)
    y += 20

    def row(label, val, y):
        draw.text((55, y), label, font=font_label, fill=(60, 60, 60))
        draw.text((795, y), str(val), font=font_val, fill=(20, 20, 20), anchor="ra")
        draw.line([(55, y + 22), (800, y + 22)], fill=(200, 200, 200), width=1)
        return y + 28

    draw.text((55, y), "VEHICLE IDENTIFICATION", font=font_h2, fill=(40, 40, 120))
    y += 30
    y = row("VIN:", gt["vin"], y)
    y = row("Model Year:", gt["year"], y)
    y = row("Make / Model:", gt["make_model"], y)
    y = row("Body Style:", "4-Door Sedan", y)
    y = row("Engine:", "2.5L DOHC 4-Cyl", y)
    y = row("Transmission:", "8-Speed Automatic", y)
    y += 10

    draw.text((55, y), "STANDARD EQUIPMENT", font=font_h2, fill=(40, 40, 120))
    y += 30
    features = [
        "• Pre-Collision Warning with Auto Emergency Braking",
        "• Lane Departure Alert with Steering Assist",
        "• Adaptive Cruise Control — Full-Speed Range",
        "• 8-inch Touchscreen Audio Display",
        "• Apple CarPlay and Android Auto",
        "• Wireless Charging Pad",
    ]
    for feat in features:
        draw.text((70, y), feat, font=font_val, fill=(50, 50, 50))
        y += 24
    y += 10

    draw.text((55, y), "PRICING", font=font_h2, fill=(40, 40, 120))
    y += 30
    y = row("Base Vehicle Price:", "$29,995", y)
    y = row("Destination & Delivery:", "$1,025", y)
    y = row("Total MSRP:", "$31,020", y)
    y += 20

    draw.text((425, y), "REQUIRED BY FEDERAL LAW — RETAIN FOR BUYER", font=pil_font(12), fill=(120, 120, 120), anchor="mt")

    if suffix == ".png":
        img.save(str(path), format="PNG")
    else:
        img.save(str(path), quality=88)


def make_registration_image(path: Path, gt: dict):
    """Generate a CA DMV registration card image."""
    img = Image.new("RGB", (900, 600), color=(240, 248, 255))
    draw = ImageDraw.Draw(img)

    font_title = pil_font_bold(22)
    font_h2 = pil_font_bold(16)
    font_label = pil_font_bold(14)
    font_val = pil_font(14)

    draw.rectangle([(10, 10), (890, 590)], outline=(0, 0, 120), width=3)
    draw.rectangle([(10, 10), (890, 70)], fill=(0, 0, 120))

    draw.text((450, 40), "STATE OF CALIFORNIA — DEPARTMENT OF MOTOR VEHICLES", font=font_title, fill=(255, 255, 255), anchor="mm")

    y = 90
    draw.text((450, y), "CERTIFICATE OF REGISTRATION", font=font_h2, fill=(0, 0, 120), anchor="mt")
    y += 35

    def dmv_box(label, value, x, y, w=380):
        draw.rectangle([(x, y), (x + w, y + 50)], outline=(0, 0, 120), width=1)
        draw.text((x + 8, y + 6), label.upper(), font=font_label, fill=(0, 0, 100))
        draw.text((x + 8, y + 28), str(value), font=font_val, fill=(20, 20, 20))

    dmv_box("Registered Owner", gt["customer_name"], 30, y)
    dmv_box("License Plate No.", "7ABC234", 440, y)
    y += 70
    dmv_box("Vehicle ID Number (VIN)", gt["vin"], 30, y, w=530)
    dmv_box("Exp.", "12/2025", 590, y, w=280)
    y += 70
    dmv_box("Year", gt["year"], 30, y, w=120)
    dmv_box("Make / Model", gt["make_model"], 170, y, w=340)
    dmv_box("Garaging ZIP", gt["garaging_zip"], 530, y, w=340)
    y += 80

    draw.text((450, y), "Keep this document in the vehicle. DMV.CA.GOV | 1-800-777-0133",
              font=pil_font(12), fill=(80, 80, 80), anchor="mt")

    img.save(str(path), quality=90)


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    print(f"\nGenerating P16 corpus in: {CORPUS_ROOT}")
    generated = []
    errors = []

    for rel_path, gt in CORPUS_GROUND_TRUTH.items():
        dest = CORPUS_ROOT / rel_path
        dest.parent.mkdir(parents=True, exist_ok=True)
        suffix = dest.suffix.lower()
        doc_type = gt["doc_type"]

        try:
            if doc_type == "purchase_agreement" and suffix == ".pdf":
                make_purchase_agreement_pdf(dest, gt)
            elif doc_type == "purchase_agreement" and suffix in (".jpg", ".jpeg", ".png"):
                make_purchase_agreement_jpg(dest, gt)
            elif doc_type == "window_sticker" and suffix == ".pdf":
                make_window_sticker_pdf(dest, gt)
            elif doc_type == "window_sticker" and suffix in (".jpg", ".jpeg", ".png"):
                make_window_sticker_image(dest, gt, suffix=suffix)
            elif doc_type == "registration" and suffix == ".pdf":
                make_registration_pdf(dest, gt)
            elif doc_type == "registration" and suffix in (".jpg", ".jpeg", ".png"):
                make_registration_image(dest, gt)
            elif doc_type == "wechat_screenshot" and suffix in (".jpg", ".jpeg", ".png"):
                make_wechat_screenshot(dest, gt, suffix=suffix)
            elif doc_type == "vin_photo" and suffix in (".jpg", ".jpeg", ".png"):
                make_vin_photo(dest, gt)
            elif doc_type == "dealer_worksheet" and suffix == ".pdf":
                make_dealer_worksheet_pdf(dest, gt)
            else:
                errors.append(f"No generator for {doc_type} + {suffix}: {rel_path}")
                continue

            size = dest.stat().st_size
            print(f"  ✓ {rel_path} ({size:,} bytes)")
            generated.append(rel_path)
        except Exception as e:
            errors.append(f"FAILED {rel_path}: {e}")
            print(f"  ✗ {rel_path}: {e}")

    # Write ground truth JSON for evaluation runner
    gt_json_path = CORPUS_ROOT / "ground_truth.json"
    with open(gt_json_path, "w") as f:
        json.dump(CORPUS_GROUND_TRUTH, f, indent=2)
    print(f"\n  ✓ Ground truth JSON: {gt_json_path}")

    print(f"\n{'─'*50}")
    print(f"  Generated: {len(generated)} documents")
    if errors:
        print(f"  Errors:    {len(errors)}")
        for e in errors:
            print(f"    {e}")
    print(f"{'─'*50}\n")


if __name__ == "__main__":
    main()
