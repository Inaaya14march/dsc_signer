import fitz
from pyhanko.sign import signers
from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
from reportlab.pdfgen import canvas
from reportlab.lib.colors import black
from io import BytesIO
from PyPDF2 import PdfReader, PdfWriter
from datetime import datetime
import os
import pdfplumber

from PyPDF2 import PdfReader, PdfWriter
from reportlab.lib.pagesizes import letter

from PyPDF2 import PdfReader, PdfWriter
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO
from datetime import datetime
from reportlab.lib.colors import black

def get_last_text_y_position(pdf_path, page_index):
    doc = fitz.open(pdf_path)
    page = doc[page_index]

    blocks = page.get_text("blocks")

    if not blocks:
        return 100  # fallback if page has no text

    
    
    lowest_y = max(block[3] for block in blocks)

    doc.close()
    return lowest_y

def get_gstin_line_y(pdf_path, page_index):
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[page_index]

        words = page.extract_words()

        for w in words:
            if w["text"].startswith("GSTIN"):
                return page.height - w["top"]

    return None
def add_signature_box(input_pdf, temp_pdf, signer_name,
                      x=350, y=60, box_width=200, box_height=50,
                      page_number=1, mode="Single Page"):

    overlay_reader = PdfReader(input_pdf)
    total_pages = len(overlay_reader.pages)

    def draw_box(page, px, py):
        page_width = float(page.mediabox.width)
        page_height = float(page.mediabox.height)

        packet = BytesIO()
        c = canvas.Canvas(packet, pagesize=(page_width, page_height))

        c.setStrokeColor(black)
        if py < 5:
            py = 5  # keep minimum bottom margin

        if py + box_height > page_height:
            top_margin = 5
            py = page_height - box_height - top_margin

        c.rect(px, py, box_width, box_height, fill=0)

        c.setFont("Helvetica-Bold", 10)
        c.drawString(px + 10, py + 30, f"For : {signer_name}")

        timestamp = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        c.setFont("Helvetica", 10)
        c.drawString(px + 10, py + 15, f"Date: {timestamp}")

        c.save()
        packet.seek(0)

        overlay_pdf = PdfReader(packet)
        page.merge_page(overlay_pdf.pages[0])

        return page

    writer = PdfWriter()

    for i in range(total_pages):

        page = overlay_reader.pages[i]
        apply_box = False

        px = x
        py = y

        if mode == "All Pages":
            apply_box = True

        elif mode == "Last Page":

            if i == total_pages - 1:

                page_width = float(page.mediabox.width)
                page_height = float(page.mediabox.height)

                gstin_y = get_gstin_line_y(input_pdf, i)

                margin = 20
                gap = 30

                px = page_width - box_width - margin

                if gstin_y:

                    py = gstin_y - box_height - gap

                    # If box goes outside page
                    if py < 60:

                        writer.add_page(page)

                        from PyPDF2._page import PageObject
                        new_page = PageObject.create_blank_page(
                            width=page_width,
                            height=page_height
                        )

                        # place box on top-right of new page
                        top_margin = 20
                        px = page_width - box_width - 40
                        new_py = page_height - top_margin

                        new_page = draw_box(new_page, px, new_py)


                        writer.add_page(new_page)
                        continue

                apply_box = True

        else:

            target = max(0, min(page_number - 1, total_pages - 1))

            if i == target:
                apply_box = True

        if apply_box:

            if mode == "Last Page" and i == total_pages - 1:
                page = draw_box(page, px, py)
            else:
                page = draw_box(page, x, py)

        writer.add_page(page)

    with open(temp_pdf, "wb") as f:
        writer.write(f)

def sign_pdf(input_pdf, output_pdf, pfx_path, pfx_password, profile):
    temp_pdf = "temp_with_box.pdf"
    
    signer = signers.SimpleSigner.load_pkcs12(
        pfx_file=pfx_path,
        passphrase=pfx_password.encode() if pfx_password else None
    )
    cert = signer.signing_cert
    organization_name = cert.subject.native.get("common_name", "")
    signer_name = organization_name # cert.subject.human_friendly.replace("Common Name:","")
    x = profile.x_positionpoints or 350
    y = profile.y_positionpoints or 60
    width = profile.box_widthponts or 200
    height = profile.box_hieghtponts or 50

    add_signature_box(
        input_pdf,
        temp_pdf,
        signer_name,
        x=x,
        y=y,
        box_width=width,
        box_height=height,
        page_number=profile.page_number or 1,
        mode=profile.signature_mode or "Single Page"
    )
    #add_signature_box(input_pdf, temp_pdf, signer_name)
    meta = signers.PdfSignatureMetadata(
        field_name="Signature1",
        md_algorithm="sha256"
    )

    with open(temp_pdf, "rb") as inf:
        writer = IncrementalPdfFileWriter(inf)

        pdf_signer = signers.PdfSigner(
            signature_meta=meta,
            signer=signer
        )

        with open(output_pdf, "wb") as outf:
            pdf_signer.sign_pdf(writer, output=outf)

