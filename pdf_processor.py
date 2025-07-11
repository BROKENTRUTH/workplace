import re
import pandas as pd
from pathlib import Path

# Install required packages
try:
    import pdfplumber
except ImportError:
    import sys
    # The following line is problematic for non-interactive environments
    # Consider removing it and instructing users to install dependencies manually
    # !{sys.executable} -m pip install pdfplumber
    print("Attempting to install pdfplumber. If this fails, please install it manually: pip install pdfplumber")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pdfplumber"])
    import pdfplumber

try:
    from fpdf import FPDF
except ImportError:
    import sys
    # The following line is problematic for non-interactive environments
    # Consider removing it and instructing users to install dependencies manually
    # !{sys.executable} -m pip install fpdf
    print("Attempting to install fpdf. If this fails, please install it manually: pip install fpdf2 (fpdf is deprecated)")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "fpdf2"]) # fpdf is deprecated, suggest fpdf2
    from fpdf import FPDF

# Generic PDF text extraction
def extract_pages(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        return [(i + 1, page.extract_text()) for i, page in enumerate(pdf.pages) if page.extract_text()] # ensure text is not None

# Try to detect material sections generically with fallback patterns
def parse_material_sections(pages):
    data = []
    current_material = None
    buffer = []
    last_pg = 0 # Initialize last_pg

    material_patterns = [
        re.compile(r'^(\d+(\.\d+)*)\s+([A-Z][A-Za-z0-9 ,/\-()]+(?:(?:\s+[A-Z][A-Za-z0-9 ,/\-()]+)*))$'), # Improved for multi-word capitalized names
        re.compile(r'^(Material:?\s*[A-Z][A-Za-z0-9 ,/\-()]+(?:(?:\s+[A-Z][A-Za-z0-9 ,/\-()]+)*))$', re.IGNORECASE),
        re.compile(r'^(Specification for\s*[A-Z][A-Za-z0-9 ,/\-()]+(?:(?:\s+[A-Z][A-Za-z0-9 ,/\-()]+)*))$', re.IGNORECASE),
        re.compile(r'^([A-Z][A-Z0-9 \-/]+)$')  # fallback: all-caps headings (allow numbers)
    ]

    print("\nDetected Material Sections:")
    for pg_num, text in pages:
        if not text: # Should be handled by extract_pages, but good to double check
            continue
        lines = text.split('\n')
        for ln in lines:
            ln_stripped = ln.strip()
            if not ln_stripped: # Skip empty lines
                continue

            match_text = None
            for pattern in material_patterns:
                match = pattern.match(ln_stripped)
                if match:
                    # Prefer longer matches or more specific patterns if multiple could match
                    match_text = ln_stripped
                    break

            if match_text:
                if current_material and buffer: # Ensure buffer is not empty before appending
                    data.append((current_material, buffer, last_pg))
                current_material = match_text
                buffer = []
                last_pg = pg_num
                print(f"  → {current_material} (Page {last_pg})")
            else:
                buffer.append((ln_stripped, pg_num))

    if current_material and buffer: # Ensure buffer is not empty for the last material
        data.append((current_material, buffer, last_pg))
    elif current_material and not buffer: # If a material header was found but no content followed before EOF or next header
        print(f"  → Found material '{current_material}' (Page {last_pg}) with no subsequent content before next section or EOF.")
        # Optionally append with empty content: data.append((current_material, [], last_pg))

    return data

# Extract test names, definitions, and other technical info robustly
def extract_fields(material, buffer, material_start_pg):
    tests = []
    defs = []
    other_info = []

    # Regex to check if page number is already in the line (e.g., "... (Page X)", "... - Page X")
    page_ref_pattern = re.compile(r'([Pp]age\s*\d+|\(?[Pp][Gg]\.?\s*\d+\)?)$')

    for line, specific_page_num in buffer:
        line_with_page = line
        # Add page number if not already present and it's different from material start page, or for clarity
        if not page_ref_pattern.search(line):
             line_with_page = f"{line.strip()} (Page {specific_page_num})"
        else:
            line_with_page = line.strip() # Already has page, just strip

        # Test identification: look for IS codes, or keywords related to tests
        if re.search(r"\bIS\s*\d+", line, re.IGNORECASE) or \
           re.search(r"\b(?:ASTM|BS|EN|DIN)\s*[\w\d-]+", line, re.IGNORECASE) or \
           re.search(r"\b(test|strength|resistance|absorption|durability|conductivity|analysis|permeability|hardness|tolerance|classification|compliance|specimen|method|procedure|requirement)", line, re.IGNORECASE):
            tests.append(line_with_page)
        # Definition identification: keywords related to material properties, types, composition
        elif re.search(r"\b(definition|type|grade|class|size|shape|form|composition|description|material|specification|appearance|finish|color|density|weight|component)", line, re.IGNORECASE):
            defs.append(line_with_page)
        # Other relevant info: lines that don't fit above but are not empty
        else:
            if len(line.strip()) > 0: # Ensure line is not just whitespace
                other_info.append(line_with_page)

    return {
        'Material Name': material.strip(),
        'Test Name/Reference Code/Standard as per the given document (with reference page number)': tests if tests else ["No Information Available"],
        'Specific Material Type/Material Definition': defs if defs else ["No Information Available"],
        'Any other relevant information': other_info if other_info else ["No Information Available"]
        # 'Reference Page' for the material section start is implicitly material_start_pg, but not directly in this dict as per new reqs.
        # The page numbers are now part of the strings in the lists above.
    }

# Clean text for PDF output to remove non-latin1 characters
def clean_text(text):
    if isinstance(text, list):
        return [t.encode('latin-1', 'replace').decode('latin-1') for t in text]
    return text.encode('latin-1', 'replace').decode('latin-1')

# Export the structured data to a readable PDF format
def export_to_pdf(df, filename='extracted_report.pdf'):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=10) # Smaller base font for more info
    pdf.set_auto_page_break(auto=True, margin=15)

    for index, row in df.iterrows():
        pdf.set_font("Arial", 'B', 12)
        # Using Sl. No. from DataFrame for material numbering
        pdf.cell(0, 10, clean_text(f"Sl. No. {row['Sl. No.']}: {row['Material Name']}"), ln=True)

        pdf.set_font("Arial", 'B', 10) # Bold for field names

        # Test Name/Reference
        pdf.multi_cell(0, 5, clean_text("Test Name/Reference Code/Standard as per the given document (with reference page number):"))
        pdf.set_font("Arial", '', 10)
        for item in row['Test Name/Reference Code/Standard as per the given document (with reference page number)']:
            pdf.multi_cell(0, 5, clean_text(f"  - {item}"))
        pdf.ln(2) # Small space

        # Specific Material Type/Definition
        pdf.set_font("Arial", 'B', 10)
        pdf.multi_cell(0, 5, clean_text("Specific Material Type/Material Definition:"))
        pdf.set_font("Arial", '', 10)
        for item in row['Specific Material Type/Material Definition']:
            pdf.multi_cell(0, 5, clean_text(f"  - {item}"))
        pdf.ln(2)

        # Any other relevant information
        pdf.set_font("Arial", 'B', 10)
        pdf.multi_cell(0, 5, clean_text("Any other relevant information:"))
        pdf.set_font("Arial", '', 10)
        for item in row['Any other relevant information']:
            pdf.multi_cell(0, 5, clean_text(f"  - {item}"))
        pdf.ln(5) # Larger space before next material

    try:
        pdf.output(filename)
        print(f"\nPDF report saved as: {filename}")
    except Exception as e:
        print(f"Error saving PDF: {e}. Ensure the path is valid and you have write permissions.")
        print("Consider installing fpdf2 if you are using an older fpdf: pip install fpdf2")


def main():
    fallback_mode = False
    pdf_path_input = input("Enter the path to the technical specification PDF: ").strip()
    pdf_path = Path(pdf_path_input) # Use Path object earlier

    if not pdf_path.exists():
        print(f"File not found: {pdf_path}")
        return

    print(f"\nProcessing: {pdf_path}\n")

    try:
        pages = extract_pages(pdf_path)
    except Exception as e:
        print(f"Error extracting pages from PDF: {e}")
        return

    if not pages:
        print("Could not extract any text from the PDF. The document might be image-based or empty.")
        return

    sections = parse_material_sections(pages)

    if not sections:
        print("⚠️ No clear material sections detected using primary patterns. Fallback mode activated.")
        fallback_mode = True
        sections = []
        block_size = 20  # lines per block fallback
        material_counter = 1
        for pg_num, text in pages:
            if not text: # Should be handled by extract_pages
                continue
            lines = text.split('\n')
            for i in range(0, len(lines), block_size):
                chunk = lines[i:i+block_size]
                # Ensure chunk_buffer only contains non-empty lines
                chunk_buffer = [(line.strip(), pg_num) for line in chunk if line.strip()]
                if chunk_buffer: # Only add if there's actual content
                    label = f"Material Block {material_counter} (Source Page {pg_num})"
                    sections.append((label, chunk_buffer, pg_num)) # pg_num here is the page the block started on
                    material_counter += 1

    if not sections:
        print("No material sections or blocks detected. This could be due to PDF formatting or an empty document after text extraction.")
        return

    rows = [extract_fields(material_name, buffer_content, material_page) for material_name, buffer_content, material_page in sections]

    if not rows:
        print("No information could be extracted into structured fields.")
        return

    df = pd.DataFrame(rows)

    # Add 'Sl. No.' column
    df.insert(0, 'Sl. No.', range(1, len(df) + 1))

    # Define column order for CSV as per new requirements
    column_order = [
        'Sl. No.',
        'Material Name',
        'Test Name/Reference Code/Standard as per the given document (with reference page number)',
        'Specific Material Type/Material Definition',
        'Any other relevant information'
    ]
    df = df[column_order]

    csv_filename = 'extracted_table.csv'
    try:
        df.to_csv(csv_filename, index=False, encoding='utf-8') # Specify encoding
        print(f"\nExtraction complete. CSV saved to {csv_filename}\n")
        print("First 5 rows of extracted data:")
        print(df.head().to_string())
    except Exception as e:
        print(f"Error saving CSV: {e}")


    export_to_pdf(df) # df already has Sl. No.

if __name__ == "__main__":
    main()
