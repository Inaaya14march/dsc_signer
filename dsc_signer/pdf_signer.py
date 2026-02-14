from pyhanko.sign import signers
from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
from reportlab.pdfgen import canvas
from reportlab.lib.colors import black
from io import BytesIO
from PyPDF2 import PdfReader, PdfWriter
from datetime import datetime


def add_signature_box(input_pdf, temp_pdf, signer_name):
    packet = BytesIO()
    overlay_reader = PdfReader(input_pdf)
    first_page = overlay_reader.pages[0]

    # Get actual page width/height
    page_width = float(first_page.mediabox.width)
    page_height = float(first_page.mediabox.height)

    packet = BytesIO()
    c = canvas.Canvas(packet, pagesize=(page_width, page_height))

    # 🔹 Box dimensions (right side)
    box_width = 200
    box_height = 50
    x = page_width - box_width - 40
    y = 60

    # Draw rectangle
    c.setStrokeColor(black)
    c.rect(x, y, box_width, box_height, fill=0)

    # 🔹 Bold Text
    c.setFont("Helvetica-Bold", 10)
    c.drawString(x + 10, y + 30, f"For : {signer_name}")

    # 🔹 Timestamp
    timestamp = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    c.setFont("Helvetica", 10)
    c.drawString(x + 10, y + 15, f"Date: {timestamp}")

    c.save()
    packet.seek(0)

    overlay_pdf = PdfReader(packet)
    writer = PdfWriter()

    for i in range(len(overlay_reader.pages)):
        page = overlay_reader.pages[i]
        if i == 0:
            page.merge_page(overlay_pdf.pages[0])
        writer.add_page(page)

    with open(temp_pdf, "wb") as f:
        writer.write(f)


def sign_pdf(input_pdf, output_pdf, pfx_path, pfx_password):
    temp_pdf = "temp_with_box.pdf"

    # 🔹 Load signer
    signer = signers.SimpleSigner.load_pkcs12(
        pfx_file=pfx_path,
        passphrase=pfx_password.encode() if pfx_password else None
    )

    # 🔹 Extract signer name from certificate
    cert = signer.signing_cert
    organization_name = cert.subject.native.get("common_name", "")
    signer_name = organization_name # cert.subject.human_friendly.replace("Common Name:","")

    # ✅ STEP 1: Add box + name + timestamp
    add_signature_box(input_pdf, temp_pdf, signer_name)

    # ✅ STEP 2: Sign AFTER adding box
    meta = signers.PdfSignatureMetadata(
        field_name="Signature1",
        md_algorithm="sha256"
    )

    #signature_field_spec = fields.SigFieldSpec( 
       # 'Signature1', 
      #  on_page=0, # 0 is the first page 
     #   box=(300, 50, 500, 110) # (left, bottom, right, top) - shifted to the right 
    #)

    with open(temp_pdf, "rb") as inf:
        writer = IncrementalPdfFileWriter(inf)

        pdf_signer = signers.PdfSigner(
            signature_meta=meta,
            signer=signer
            #new_field_spec=signature_field_spec
        )

        with open(output_pdf, "wb") as outf:
            pdf_signer.sign_pdf(writer, output=outf)

    print("✅ PDF signed successfully with box, signer name and timestamp.")
