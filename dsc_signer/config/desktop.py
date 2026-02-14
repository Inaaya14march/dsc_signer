from frappe import _

def get_data():
    return [
        {
            "module_name": "DSC Signer",
            "category": "Tools",
            "color": "blue",
            "icon": "fa fa-pencil-square-o",
            "type": "module",
            "label": _("DSC Signer"),
            "link": "modules/dsc_signer"
        }
    ]
