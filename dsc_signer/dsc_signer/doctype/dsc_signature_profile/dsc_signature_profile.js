// Copyright (c) 2026, AITS and contributors
// For license information, please see license.txt

// frappe.ui.form.on("DSC Signature Profile", {
// 	refresh(frm) {

// 	},
// });
frappe.ui.form.on("DSC Signature Profile", {
    signature_mode(frm) {
        toggle_page_field(frm);
    },
    refresh(frm) {
        toggle_page_field(frm);
    }
});

function toggle_page_field(frm) {
    frm.toggle_display(
        "page_number",
        frm.doc.signature_mode === "Single Page"
    );
}