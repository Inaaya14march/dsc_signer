frappe.listview_settings['Sales Invoice'] = {
    onload(listview) {
        listview.page.add_action_item('Batch Digital Sign', () => {
            let selected = listview.get_checked_items();

            if (!selected.length) {
                frappe.msgprint("Select documents first");
                return;
            }

            let docs = selected.map(d => d.name);

            let d = new frappe.ui.Dialog({
                title: "Batch Sign",
                fields: [
                    {
                        label: "Profile",
                        fieldname: "profile",
                        fieldtype: "Link",
                        options: "DSC Signature Profile",
                        reqd: 1
                    }
                ],
                primary_action_label: "Sign All",
                primary_action(values) {
                    frappe.call({
                        method: "dsc_signer.api.batch_sign",
                        args: {
                            doctype: "Sales Invoice",
                            names: docs,
                            profile: values.profile
                        },
                        freeze: true,
                        freeze_message: "Batch signing documents...",
                        callback(r) {
                            show_batch_result(r.message);
                            listview.refresh();
                        }
                    });

                    d.hide();
                }
            });

            d.show();
        });
    }
};

function show_batch_result(results) {
    let html = `<div style="max-height:300px;overflow:auto">`;

    results.forEach(r => {
        let icon = r.status === "Signed"
            ? "✅"
            : "❌";

        html += `<p>${icon} <b>${r.doc}</b> — ${r.status}</p>`;
    });

    html += `</div>`;

    frappe.msgprint({
        title: "Batch Signing Result",
        message: html,
        wide: true
    });
}