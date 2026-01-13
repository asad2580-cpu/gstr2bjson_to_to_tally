import json
import xml.etree.ElementTree as ET
from xml.dom import minidom

def create_ledger_element(parent_node, name, group, is_gst=False, tax_type=None):
    tally_msg = ET.SubElement(parent_node, 'TALLYMESSAGE', {'xmlns:UDF': 'TallyUDF'})
    ledger = ET.SubElement(tally_msg, 'LEDGER', {'NAME': name, 'ACTION': 'Create'})
    ET.SubElement(ledger, 'NAME').text = name
    ET.SubElement(ledger, 'PARENT').text = group
    # Tally essentials
    ET.SubElement(ledger, 'ISBILLWISEON').text = 'Yes' if group == "Sundry Creditors" else 'No'
    ET.SubElement(ledger, 'ISUPDATINGTARGETID').text = "No"
    ET.SubElement(ledger, 'ASORIGINAL').text = "Yes"
    
    if is_gst:
        ET.SubElement(ledger, 'TAXTYPE').text = 'GST'
        if tax_type:
            ET.SubElement(ledger, 'GSTDUTYHEAD').text = tax_type

def generate_masters_from_json(json_file, output_file):
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            invoices = json.load(f)
    except Exception as e:
        print(f"Error loading JSON: {e}")
        return

    created_ledgers = set()
    # Add Version 1.0 to Envelope
    envelope = ET.Element('ENVELOPE', {'VERSION': '1.0'})
    header = ET.SubElement(envelope, 'HEADER')
    ET.SubElement(header, 'TALLYREQUEST').text = 'Import Data'
    
    body = ET.SubElement(envelope, 'BODY')
    import_data = ET.SubElement(body, 'IMPORTDATA')
    request_desc = ET.SubElement(import_data, 'REQUESTDESC')
    ET.SubElement(request_desc, 'REPORTNAME').text = 'All Masters'
    
    # Crucial: Target the correct company
    static_vars = ET.SubElement(request_desc, 'STATICVARIABLES')
    ET.SubElement(static_vars, 'SVCURRENTCOMPANY').text = 'test company'
    
    request_data = ET.SubElement(import_data, 'REQUESTDATA')

    # 1. Round Off Ledger
    create_ledger_element(request_data, "Round Off", "Indirect Expenses")
    created_ledgers.add("Round Off")

    for inv in invoices:
        # 2. Party Ledgers
        party = inv.get('supplier_name')
        if party and party not in created_ledgers:
            create_ledger_element(request_data, party, "Sundry Creditors")
            created_ledgers.add(party)

        # 3. Tax and Purchase Ledgers (Assuming 12% based on previous context)
        # Check IGST
        if float(inv.get('igst_amount', 0)) > 0:
            if "Interstate Purchase 12%" not in created_ledgers:
                create_ledger_element(request_data, "Interstate Purchase 12%", "Purchase Accounts")
                created_ledgers.add("Interstate Purchase 12%")
            if "Input IGST 12%" not in created_ledgers:
                create_ledger_element(request_data, "Input IGST 12%", "Duties & Taxes", True, "Integrated Tax")
                created_ledgers.add("Input IGST 12%")
        
        # Check Local (CGST/SGST)
        if float(inv.get('cgst_amount', 0)) > 0:
            if "Local Purchase 12%" not in created_ledgers:
                create_ledger_element(request_data, "Local Purchase 12%", "Purchase Accounts")
                created_ledgers.add("Local Purchase 12%")
            for tax in ["Input CGST 6%", "Input SGST 6%"]:
                if tax not in created_ledgers:
                    head = "Central Tax" if "CGST" in tax else "State Tax"
                    create_ledger_element(request_data, tax, "Duties & Taxes", True, head)
                    created_ledgers.add(tax)

    # Use encoding="utf-8" and xml_declaration
    xml_str = ET.tostring(envelope, encoding='utf-8')
    parsed = minidom.parseString(xml_str)
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(parsed.toprettyxml(indent="    "))
    print(f"DONE: Masters XML created. Import this into Tally first.")

if __name__ == "__main__":
    generate_masters_from_json('cleaned_invoices.json', 'masters_import.xml')