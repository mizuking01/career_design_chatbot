from langchain.document_loaders import PyMuPDFLoader
from langchain.document_loaders import TextLoader  
from docx import Document

def load_docx(docx_path):
    document = Document(docx_path)
    return "\n".join([para.text for para in document.paragraphs])

def load_pdf(pdf_path):
    loader = PyMuPDFLoader(pdf_path)
    return loader.load()

def load_text(text_path):
    loader = TextLoader(text_path)
    return loader.load()
