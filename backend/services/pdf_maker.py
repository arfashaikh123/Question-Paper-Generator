from fpdf import FPDF
import re

class PDF(FPDF):
    def __init__(self, college_name="COLLEGE OF ENGINEERING", header_image_path=None, header_text=None):
        super().__init__()
        self.college_name = college_name
        self.header_image_path = header_image_path
        self.header_text = header_text

    def header(self):
        # Render Header Image if provided
        if self.header_image_path:
            try:
                # Top center, 40mm wide
                self.image(self.header_image_path, x=85, y=5, w=40)
                self.ln(35) # Move down below image
            except Exception as e:
                print(f"Error loading image: {e}")
        else:
            self.ln(10) # Default spacing if no image

        # Render Text Header
        if self.header_text:
            lines = self.header_text.split('\n')
            for i, line in enumerate(lines):
                if i == 0:
                    self.set_font('Arial', 'B', 16) # Primary Title
                    self.cell(0, 8, line.strip(), 0, 1, 'C')
                elif i == 1:
                    self.set_font('Arial', 'B', 14) # Secondary Title
                    self.cell(0, 7, line.strip(), 0, 1, 'C')
                else:
                    self.set_font('Arial', 'B', 12) # Details
                    self.cell(0, 6, line.strip(), 0, 1, 'C')
        else:
            # Fallback to old simple header
            self.set_font('Arial', 'B', 16)
            self.cell(0, 10, self.college_name.upper(), 0, 1, 'C')
            self.set_font('Arial', 'B', 12)
            self.cell(0, 8, "EXAMINATION - 202X", 0, 1, 'C')
        
        # Line break
        self.set_line_width(0.5)
        self.line(10, self.get_y()+5, 200, self.get_y()+5) # Dynamic Line position
        self.ln(8)

    def footer(self):
        # Position at 1.5 cm from bottom
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        # Page number
        self.cell(0, 10, 'Page ' + str(self.page_no()) + '/{nb}', 0, 0, 'C')

def create_pdf(text, college_name="COLLEGE OF ENGINEERING", header_image_path=None, header_text=None):
    pdf = PDF(college_name=college_name, header_image_path=header_image_path, header_text=header_text)
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    # Body Font
    pdf.set_font("Arial", size=11)
    
    # Improve text wrapping and encoding
    # FPDF has trouble with some utf-8 characters if not using a unicode font.
    # We'll use latin-1 encoding for simplicity or a replacement logic.
    
    # Simple cleanup to fix common encoding issues
    replacements = {
        '\u2013': '-', '\u2014': '-', '\u2018': "'", '\u2019': "'",
        '\u201c': '"', '\u201d': '"', '\u2022': '*'
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    
    normalized_text = text.encode('latin-1', 'replace').decode('latin-1')
    
    # Processing Markdown-like headers for bolding
    # e.g. ## Section A
    
    lines = normalized_text.split("\n")
    for line in lines:
        if line.startswith("##"):
            pdf.set_font("Arial", "B", 13)
            pdf.cell(0, 10, line.replace("#", "").strip(), 0, 1, 'L')
            pdf.set_font("Arial", size=11)
        elif line.startswith("**") and line.endswith("**"):
             # Bold line
            pdf.set_font("Arial", "B", 11)
            pdf.multi_cell(0, 6, line.replace("*", "").strip())
            pdf.set_font("Arial", size=11)
        else:
            pdf.multi_cell(0, 6, line)
            pdf.ln(1) # Extra spacing
        
    return pdf.output(dest="S").encode("latin-1")
