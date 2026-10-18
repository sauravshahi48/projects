"""Rebuild the fictional sample PDFs. Requires the optional [samples] dependencies."""

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docassist" / "samples"
BLUE = colors.HexColor("#345ef1")
INK = colors.HexColor("#202a3a")
MUTED = colors.HexColor("#758298")

HANDBOOK = [
    (
        "Working at Northstar",
        [
            (
                "Working hours",
                "The standard working week is Monday to Friday. Normal working hours are 09:30 to 18:00, including a one-hour lunch break. Teams may agree flexible starting times with their manager.",
            ),
            (
                "Hybrid working",
                "Employees attend the office two days each week. The team manager selects the office days. Remote work from another city requires advance manager approval.",
            ),
            (
                "Probation",
                "The standard probation period is three months. A manager reviews performance at the end of probation and confirms the outcome in writing.",
            ),
        ],
    ),
    (
        "Leave and time off",
        [
            (
                "Annual leave",
                "Full-time employees receive 18 days of paid annual leave per financial year. Employees submit annual leave requests through the HR portal at least five working days before the planned leave. The reporting manager approves the request.",
            ),
            (
                "Sick leave",
                "Employees receive 10 days of sick leave per financial year. A medical certificate is required when sick leave exceeds three consecutive working days.",
            ),
            (
                "Carrying leave forward",
                "Employees may carry forward up to five unused annual leave days into the next financial year. Carried leave must be used by 30 June. Sick leave cannot be carried forward.",
            ),
        ],
    ),
    (
        "Security and onboarding",
        [
            (
                "Security incident reporting",
                "Employees must report a suspected security incident within 30 minutes of discovery. Contact security@northstar.example and the reporting manager. Record the time, affected systems, and a short description. Do not delete potentially relevant evidence.",
            ),
            (
                "Account access",
                "Multi-factor authentication is required for company accounts. Passwords must not be shared. Access requests require approval from the system owner.",
            ),
            (
                "New joiners",
                "New employees attend an orientation session on their first working day. The HR team explains leave, payroll and workplace policies. The IT team provides approved accounts and device setup instructions.",
            ),
        ],
    ),
]

EXPENSES = [
    (
        "Equipment and learning",
        [
            (
                "Laptop reimbursement",
                "The laptop reimbursement limit is INR 60,000 per employee, once every 36 months. Employees must obtain manager approval before purchase. An itemized invoice in the employee's name is required. Company-issued laptops are not eligible for a second reimbursement.",
            ),
            (
                "Monitor allowance",
                "The external monitor allowance is INR 15,000 once every 36 months. Manager approval is required before purchase. Accessories are covered only when explicitly approved.",
            ),
            (
                "Learning budget",
                "The annual learning budget is INR 12,000 per employee per financial year. It covers approved job-related courses, books and certification exam fees. Obtain manager approval before enrolling. Unused learning budget does not carry forward.",
            ),
        ],
    ),
    (
        "Travel and claims",
        [
            (
                "Submitting a claim",
                "Employees must submit reimbursement claims within 30 calendar days of the expense date. Upload an itemized receipt and the manager's approval to the expense portal. Finance may return incomplete claims for correction.",
            ),
            (
                "Domestic travel",
                "The domestic hotel reimbursement cap is INR 3,500 per night, excluding applicable taxes. The domestic meal allowance is INR 800 per day. Expenses above these caps need written approval before travel.",
            ),
            (
                "Payment timeline",
                "Approved reimbursement claims are paid within 10 working days after final finance approval. The payment is made to the employee's registered bank account.",
            ),
        ],
    ),
]


def build(filename: str, title: str, pages):
    path = OUTPUT / filename
    pdf = canvas.Canvas(str(path), pagesize=A4, invariant=1)
    pdf.setTitle(f"Northstar Works - {title}")
    pdf.setAuthor("SourceDesk sample dataset")
    width, height = A4
    body = ParagraphStyle("body", fontName="Helvetica", fontSize=11, leading=18, textColor=INK)
    for page_number, (section, blocks) in enumerate(pages, 1):
        pdf.setFillColor(BLUE)
        pdf.rect(0, height - 9, width, 9, fill=1, stroke=0)
        pdf.setFont("Helvetica-Bold", 10)
        pdf.drawString(50, height - 55, "NORTHSTAR WORKS")
        pdf.setFillColor(MUTED)
        pdf.setFont("Helvetica", 9)
        pdf.drawRightString(width - 50, height - 55, "FICTIONAL SAMPLE DOCUMENT")
        pdf.setFillColor(INK)
        pdf.setFont("Helvetica-Bold", 25)
        pdf.drawString(50, height - 110, title)
        pdf.setFillColor(MUTED)
        pdf.setFont("Helvetica", 11)
        pdf.drawString(50, height - 136, section)
        pdf.setStrokeColor(colors.HexColor("#e3e8f0"))
        pdf.line(50, height - 159, width - 50, height - 159)
        y = height - 196
        for heading, text in blocks:
            pdf.setFont("Helvetica-Bold", 12)
            pdf.setFillColor(BLUE)
            pdf.drawString(50, y, heading)
            paragraph = Paragraph(text, body)
            _, paragraph_height = paragraph.wrap(width - 100, height)
            paragraph.drawOn(pdf, 50, y - 18 - paragraph_height)
            y -= paragraph_height + 57
        if y < 90:
            raise ValueError(f"Content overflows {filename}, page {page_number}")
        pdf.setStrokeColor(colors.HexColor("#e3e8f0"))
        pdf.line(50, 63, width - 50, 63)
        pdf.setFont("Helvetica", 8)
        pdf.setFillColor(MUTED)
        pdf.drawString(
            50, 46, "For portfolio demonstrations only. These are not real company policies."
        )
        pdf.drawRightString(width - 50, 46, f"Page {page_number} of {len(pages)}")
        pdf.showPage()
    pdf.save()
    print(path)


if __name__ == "__main__":
    OUTPUT.mkdir(parents=True, exist_ok=True)
    build("Employee_Handbook.pdf", "Employee Handbook", HANDBOOK)
    build("Expense_Policy.pdf", "Expense Policy", EXPENSES)
