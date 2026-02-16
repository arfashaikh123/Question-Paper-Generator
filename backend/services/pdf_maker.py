from fpdf import FPDF

def create_pdf(text):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    # Title
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Generated Question Paper", ln=True, align='C')
    pdf.ln(10)
    
    # Body
    pdf.set_font("Arial", size=11)
    
    # Improve text wrapping and encoding
    # FPDF has trouble with some utf-8 characters if not using a unicode font.
    # We'll use latin-1 encoding for simplicity or a replacement logic.
    
    normalized_text = text.encode('latin-1', 'replace').decode('latin-1')
    
    for line in normalized_text.split("\n"):
        pdf.multi_cell(0, 8, line)
        
    return pdf.output(dest="S").encode("latin-1")
