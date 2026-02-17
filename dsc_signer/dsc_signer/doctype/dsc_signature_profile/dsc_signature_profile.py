import frappe
from frappe.model.document import Document


class DSCSignatureProfile(Document):

    def validate(self):
        self.validate_slot_limit()
        self.validate_unique_active_profile()

    def validate_slot_limit(self):
        if self.signature_slot and self.signature_slot > 1:
            frappe.throw("Slot value can't be more than 1")

    def validate_unique_active_profile(self):
        if not self.active:
            return

        existing = frappe.db.exists(
            "DSC Signature Profile",
            {
                "document_type": self.document_type,
                "print_format": self.print_format,
                "signature_slot": self.signature_slot,
                "active": 1,
                "name": ["!=", self.name],
            },
        )

        if existing:
            frappe.throw(
                f"Another active profile already exists for "
                f"{self.document_type} + {self.print_format} "
                f"(Slot {self.signature_slot}). "
                f"Deactivate it first."
            )