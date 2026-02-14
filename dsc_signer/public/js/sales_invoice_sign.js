frappe.ui.form.on('Sales Invoice', {
    refresh: function(frm) {
        if (frm.doc.docstatus == 1) {
            frm.add_custom_button(__('Sign Invoice'), function() {
               
                frappe.call({
                    method: 'dsc_signer.api.sign_invoice',
                    args: {
                        docname: frm.doc.name
                    },
                    callback: function(response) {
                        if (response.message == "Signed Successfully") {
                            frappe.msgprint(__('Invoice Signed Successfully!'));
                        }
                    }
                });
            });
        }
    }
});
