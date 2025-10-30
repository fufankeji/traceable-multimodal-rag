import pdfplumber

pdf_path = "/home/data/nongwa/workspace/data/阿里开发手册-泰山版.pdf"
with pdfplumber.open(pdf_path) as pdf:
    for i in range(5):
        page = pdf.pages[i]
        text = page.extract_text()
        print(f"PDFPlumber提取字符数: {len(text)}")
        print(text[:500])