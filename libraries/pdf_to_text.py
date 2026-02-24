import os
path_results = "files/results/output.txt"

import pdfplumber
def extract_text_from_pdf_plumber(file_path, output_path): # Texto totalmente lineal
    filename = os.path.basename(file_path)
    filename = filename+'_pdfplumber.txt'
    output_path = os.path.join("files/results", filename)
    with pdfplumber.open(file_path) as pdf, open(output_path, "w", encoding="utf-8") as f:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                f.write(text + '\n')

def extract_text_from_pdfminer(file_path, output_path): # Texto dividido en columnas y saltos de linea
    filename = os.path.basename(file_path)
    filename = filename+'_pdfminer.txt'
    output_path = os.path.join("files/results", filename)
    from pdfminer.high_level import extract_text
    text = extract_text(file_path)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(text)
def extract_text_from_pypdf2(file_path, output_path): # Funciona raro
    filename = os.path.basename(file_path)
    filename = filename+'_pypdf2.txt'
    output_path = os.path.join("files/results", filename)
    from PyPDF2 import PdfReader
    reader = PdfReader(file_path)
    with open(output_path, "w", encoding="utf-8") as f:
        for page in reader.pages:
            text = page.extract_text()
        if text:
            f.write(text + '\n')

def extract_text_from_pymupdf(file_path, output_path): # funciona bien, con saltos de linea y columnas // EL MEJOR
    import fitz # PyMuPDF
    filename = os.path.basename(file_path)
    filename = filename+'_pymupdf.txt'
    output_path = os.path.join("files/results", filename)
    doc = fitz.open(file_path)
    with open(output_path, "w", encoding="utf-8") as f:
        for page in doc:
            f.write(page.get_text() + '\n')

def extract_text_from_epub(file_path, output_path):
    from ebooklib import epub
    from bs4 import BeautifulSoup

    book = epub.read_epub(file_path)
    with open(output_path, "w", encoding="utf-8") as f:
        for item in book.get_items():
            if item.get_type() == epub.EpubHtml:
                soup = BeautifulSoup(item.get_content(), 'html.parser')
                text = soup.get_text()
                f.write(text + '\n')

# import pdftotext
# with open("file.pdf", "rb") as f:
#    pdf = pdftotext.PDF(f)
#    with open("output.txt", "w", encoding="utf-8") as out:
#        out.write("\n\n".join(pdf))

def extract_text_from_pdf(file_path, output_path=path_results, method="pdfplumber"):
    if method == "pdfplumber":
        extract_text_from_pdf_plumber(file_path, output_path)
    elif method == "pdfminer":
        extract_text_from_pdfminer(file_path, output_path)
    elif method == "pypdf2":
        extract_text_from_pypdf2(file_path, output_path)
    elif method == "pymupdf":
        extract_text_from_pymupdf(file_path, output_path)
    else:
        raise ValueError(f"Unknown method: {method}")
    
# Example usage:
extract_text_from_pdf("files/source/Clean Code in Python.pdf", method="pymupdf")
extract_text_from_epub("files/source/CleanCodePython.epub", "files/results/sample_epub.txt")