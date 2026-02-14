import frappe
from frappe.utils.pdf import get_pdf
from frappe.utils.file_manager import save_file
from .pdf_signer import sign_pdf
from frappe import _

@frappe.whitelist()
def sign_invoice(docname):
    # Get the Sales Invoice doc
    doc = frappe.get_doc("Sales Invoice", docname)
    
    # Generate the PDF for the Sales Invoice
    html = frappe.render_template("templates/pdf/sales_invoice.html", {"doc": doc})
    pdf_data = get_pdf(html)

    unsigned_pdf_path = f"/tmp/{docname}_unsigned.pdf"
    signed_pdf_path = f"/tmp/{docname}_signed.pdf"

    # Save the unsigned PDF temporarily
    with open(unsigned_pdf_path, "wb") as f:
        f.write(pdf_data)

    # Get DSC settings (PFX file and password from settings)
    
    #pfx_file_path ="/home/frappe/frappe-bench/apps/dsc_signer/dsc_signer/config/DSC.pfx"  # Example path
    import frappe

pfx_file_path = frappe.get_app_path(
    "dsc_signer",
    "dsc_signer",
    "config",
    "DSC.pfx"
)
    pfx_password = "ABCD@1234"; #frappe.conf.dsc_pfx_password  # Stored in site config

    # Sign the PDF
    sign_pdf(unsigned_pdf_path, signed_pdf_path, pfx_file_path, pfx_password)

    # Save the signed PDF as an attachment
    with open(signed_pdf_path, "rb") as f:
        file_doc = save_file(
            f"{docname}_Signed.pdf",
            f.read(),
            "Sales Invoice",
            docname,
            is_private=1
        )

    return _("Signed Successfully")
