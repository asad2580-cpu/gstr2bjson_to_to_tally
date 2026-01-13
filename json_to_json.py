import json
import os

def process_gstr2b():
    # File configuration
    input_filename = 'returns_R2B_07ADLPF8341H1ZH_102025.json'
    output_filename = 'cleaned_invoices1.json'

    # Check if input file exists in root
    if not os.path.exists(input_filename):
        print(f"Error: {input_filename} not found in the root directory.")
        return

    try:
        with open(input_filename, 'r') as f:
            raw_data = json.load(f)

        # Accessing the core data structure from your JSON
        data_root = raw_data.get("data", {})
        return_period = data_root.get("rtnprd", "N/A")
        b2b_sections = data_root.get("docdata", {}).get("b2b", [])
        
        extracted_invoices = []

        # Iterate through each supplier
        for supplier in b2b_sections:
            supplier_name = supplier.get("trdnm")
            supplier_gstin = supplier.get("ctin")
            
            # Iterate through each invoice under that supplier
            for invoice_entry in supplier.get("inv", []):
                # Flatten the data for Tally-ready structure
                clean_inv = {
                    "supplier_name": supplier_name,
                    "supplier_gstin": supplier_gstin,
                    "date": invoice_entry.get("dt"),
                    "invoice_number": invoice_entry.get("inum"),
                    "return_period": return_period,
                    "taxable_value": invoice_entry.get("txval", 0),
                    "igst_amount": invoice_entry.get("igst", 0),
                    "cgst_amount": invoice_entry.get("cgst", 0),
                    "sgst_amount": invoice_entry.get("sgst", 0),
                    "total_invoice_value": invoice_entry.get("val", 0)
                }
                extracted_invoices.append(clean_inv)
        
        # Save to a new JSON file in the root directory
        with open(output_filename, 'w') as f:
            json.dump(extracted_invoices, f, indent=4)
            
        print("-" * 30)
        print(f"SUCCESS!")
        print(f"Total Invoices Processed: {len(extracted_invoices)}")
        print(f"Output saved to: {output_filename}")
        print("-" * 30)

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    process_gstr2b()