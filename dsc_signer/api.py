import frappe
from frappe import _
from frappe.utils.pdf import get_pdf
from frappe.utils.file_manager import save_file
from dsc_signer.pdf_signer import sign_pdf
from dsc_signer.pdf_signer import add_signature_box


@frappe.whitelist()
def get_profiles(doctype=None):
    if not doctype:
        return []

    profiles = frappe.get_all(
        "DSC Signature Profile",
        filters={
            "document_type": doctype,
            "active": 1
        },
        pluck="name"
    )
    return profiles

@frappe.whitelist()
def sign_with_profile(docname=None, profile=None):
    if not docname or not profile:
        frappe.throw("Missing document or profile")

    prof = frappe.get_doc("DSC Signature Profile", profile)

    doc = frappe.get_doc(prof.document_type, docname)

    if not prof.allow_re_sign and is_document_signed(doc.doctype, doc.name):
        frappe.throw("Document already signed. Re-signing is disabled in profile.")

    settings = frappe.get_single("DSC Settings")
    pfx_file = settings.attach_vmcx
    pfx_password = settings.get_password("certificate_password")

    if not pfx_file:
        frappe.throw("Certificate not configured in DSC Settings")

    pfx_file_path = frappe.get_site_path(
        "private", "files", pfx_file.split("/")[-1]
    )

    html = frappe.get_print(
        doc.doctype,
        doc.name,
        print_format=prof.print_format
    )

    pdf_data = get_pdf(html)

    safe_name = docname.replace("/", "_")

    unsigned_pdf = f"/tmp/{safe_name}_unsigned.pdf"
    signed_pdf = f"/tmp/{safe_name}_signed.pdf"

    with open(unsigned_pdf, "wb") as f:
        f.write(pdf_data)

    sign_pdf(unsigned_pdf, signed_pdf, pfx_file_path, pfx_password,prof)

    with open(signed_pdf, "rb") as f:
        save_file(
            f"{safe_name}_SIGNED.pdf",
            f.read(),
            doc.doctype,
            doc.name,
            is_private=1
        )

    return _("Document signed and attached successfully")

def is_document_signed(doctype, docname):
    return frappe.db.exists(
        "File",
        {
            "attached_to_doctype": doctype,
            "attached_to_name": docname,
            "file_name": ["like", "%SIGNED%"]
        }
    )

def auto_sign_on_submit(doc, method):
    profiles = frappe.get_all(
        "DSC Signature Profile",
        filters={
            "document_type": doc.doctype,
            "active": 1,
            "auto_sign_on_submit": 1
        },
        pluck="name"
    )

    if not profiles:
        return

    profile = profiles[0]

    sign_with_profile(doc.name, profile)

@frappe.whitelist()
def batch_sign(doctype=None, names=None, profile=None):
    if not doctype or not names or not profile:
        frappe.throw("Missing parameters")

    names = frappe.parse_json(names)

    results = []
    profiles = frappe.get_all(
        "DSC Signature Profile",
        filters={
            "document_type": doctype,
            "active": 1
        },
        pluck="name"
    )

    if not profiles:
        return

    profiledt = profiles[0]
    
    #sign_with_profile(doc.name, profile)

    for name in names:
        try:
            sign_with_profile(name, profiledt)
            results.append({"doc": name, "status": "Signed"})
        except Exception as e:
            results.append({"doc": name, "status": str(e)})

    return results

@frappe.whitelist()
def preview_with_profile(docname=None, profile=None):
    if not docname or not profile:
        frappe.throw("Missing document or profile")

    prof = frappe.get_doc("DSC Signature Profile", profile)
    doc = frappe.get_doc(prof.document_type, docname)

    html = frappe.get_print(
        doc.doctype,
        doc.name,
        print_format=prof.print_format
    )

    pdf_data = get_pdf(html)

    safe_name = docname.replace("/", "_")

    unsigned_pdf = f"/tmp/{safe_name}_preview.pdf"
    preview_pdf = f"/tmp/{safe_name}_preview_box.pdf"

    with open(unsigned_pdf, "wb") as f:
        f.write(pdf_data)
    signer_name = prof.default_signer_label or "Preview Signature"

    x = prof.x_positionpoints or 350
    y = prof.y_positionpoints or 60
    width = prof.box_widthponts or 200
    height = prof.box_hieghtponts or 50

    add_signature_box(
        unsigned_pdf,
        preview_pdf,
        signer_name,
        x=x,
        y=y,
        box_width=width,
        box_height=height,
        page_number=prof.page_number or 1,
        mode=prof.signature_mode or "Single Page"
    )

    with open(preview_pdf, "rb") as f:
        file_doc = save_file(
            f"{safe_name}_preview.pdf",
            f.read(),
            doc.doctype,
            doc.name,
            is_private=1
        )

    return file_doc.file_url