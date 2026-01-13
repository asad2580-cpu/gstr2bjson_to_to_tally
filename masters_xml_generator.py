import json
import xml.etree.ElementTree as ET
from xml.dom import minidom


def create_ledger(parent, name, group, is_gst=False, gst_head=None):
    msg = ET.SubElement(parent, "TALLYMESSAGE", {"xmlns:UDF": "TallyUDF"})
    ledger = ET.SubElement(msg, "LEDGER", {"NAME": name, "ACTION": "Create"})

    ET.SubElement(ledger, "NAME").text = name
    ET.SubElement(ledger, "PARENT").text = group
    ET.SubElement(ledger, "ISBILLWISEON").text = "Yes" if group == "Sundry Creditors" else "No"
    ET.SubElement(ledger, "ISUPDATINGTARGETID").text = "No"
    ET.SubElement(ledger, "ASORIGINAL").text = "Yes"

    if is_gst:
        ET.SubElement(ledger, "TAXTYPE").text = "GST"
        ET.SubElement(ledger, "GSTDUTYHEAD").text = gst_head


def generate_masters_from_json(json_file, output_file):
    with open(json_file, "r", encoding="utf-8") as f:
        invoices = json.load(f)

    created = set()

    envelope = ET.Element("ENVELOPE", {"VERSION": "1.0"})
    header = ET.SubElement(envelope, "HEADER")
    ET.SubElement(header, "TALLYREQUEST").text = "Import Data"

    body = ET.SubElement(envelope, "BODY")
    import_data = ET.SubElement(body, "IMPORTDATA")
    req_desc = ET.SubElement(import_data, "REQUESTDESC")
    ET.SubElement(req_desc, "REPORTNAME").text = "All Masters"

    static_vars = ET.SubElement(req_desc, "STATICVARIABLES")
    ET.SubElement(static_vars, "SVCURRENTCOMPANY").text = "test company"

    req_data = ET.SubElement(import_data, "REQUESTDATA")

    # --- Round Off Ledger ---
    create_ledger(req_data, "Round Off", "Indirect Expenses")
    created.add("Round Off")

    for inv in invoices:
        taxable = float(inv["taxable_value"])
        igst = float(inv.get("igst_amount", 0))
        cgst = float(inv.get("cgst_amount", 0))
        sgst = float(inv.get("sgst_amount", 0))

        # --- Party Ledger ---
        party = inv["supplier_name"]
        if party not in created:
            create_ledger(req_data, party, "Sundry Creditors")
            created.add(party)

        # --- Interstate Purchase ---
        if igst > 0 and taxable > 0:
            rate = round((igst / taxable) * 100)

            purchase_ledger = f"Interstate Purchase {rate}%"
            igst_ledger = f"Input IGST {rate}%"

            if purchase_ledger not in created:
                create_ledger(req_data, purchase_ledger, "Purchase Accounts")
                created.add(purchase_ledger)

            if igst_ledger not in created:
                create_ledger(req_data, igst_ledger, "Duties & Taxes", True, "Integrated Tax")
                created.add(igst_ledger)

        # --- Local Purchase ---
        if cgst > 0 and sgst > 0 and taxable > 0:
            rate = round(((cgst + sgst) / taxable) * 100)
            half = rate // 2

            purchase_ledger = f"Local Purchase {rate}%"
            cgst_ledger = f"Input CGST {half}%"
            sgst_ledger = f"Input SGST {half}%"

            if purchase_ledger not in created:
                create_ledger(req_data, purchase_ledger, "Purchase Accounts")
                created.add(purchase_ledger)

            if cgst_ledger not in created:
                create_ledger(req_data, cgst_ledger, "Duties & Taxes", True, "Central Tax")
                created.add(cgst_ledger)

            if sgst_ledger not in created:
                create_ledger(req_data, sgst_ledger, "Duties & Taxes", True, "State Tax")
                created.add(sgst_ledger)

    xml_bytes = ET.tostring(envelope, encoding="utf-8")
    pretty = minidom.parseString(xml_bytes)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(pretty.toprettyxml(indent="    "))

    print("DONE: Robust Masters XML generated.")


if __name__ == "__main__":
    generate_masters_from_json("cleaned_invoices1.json", "masters_import.xml")
