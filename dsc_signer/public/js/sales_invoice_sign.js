frappe.ui.form.on('Sales Invoice', {
    refresh(frm) {
        frm.add_custom_button('Digital Sign', () => {
            open_signature_dialog(frm);
        });
    }
});


function open_signature_dialog(frm) {
    frappe.call({
        method: "dsc_signer.api.get_profiles",
        args: {
            doctype: frm.doc.doctype
        },
        callback: function(r) {
            let profiles = r.message || [];

            let d = new frappe.ui.Dialog({
                title: "Select Signature Profile",
                fields: [
                    {
                        label: "Profile",
                        fieldname: "profile",
                        fieldtype: "Select",
                        options: profiles,
                        reqd: 1
                    }
                ],
                primary_action_label: "Sign",
                primary_action() {
                    let values = d.get_values();
                    sign_document(frm, values.profile);
                    d.hide();
                },
                secondary_action_label: "Preview",
                secondary_action() {
                    let values = d.get_values();
                    preview_document(frm, values.profile);
                }
            });

            d.show();
        }
    });
}


function preview_document(frm, profile) {
    frappe.call({
        method: "dsc_signer.api.preview_with_profile",
        args: {
            docname: frm.doc.name,
            profile: profile
        },
        freeze: true,
        freeze_message: "Generating preview...",
        callback: function(r) {
            if (r.message) {
                window.open(r.message);
            }
        }
    });
}
function sign_document(frm, profile) {
    frappe.call({
        method: "dsc_signer.api.sign_with_profile",
        args: {
            docname: frm.doc.name,
            profile: profile
        },
        freeze: true,
        freeze_message: "Signing document...",
        callback: function() {
            frappe.msgprint("Document signed successfully");
            frm.reload_doc();
        }
    });
}