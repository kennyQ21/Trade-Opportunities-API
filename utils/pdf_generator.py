"""
PDF Generator Utility
Converts markdown reports to professional PDF documents with citations
Uses fpdf2 (pure Python - no system dependencies)
"""
from fpdf import FPDF
from markdown2 import markdown
from datetime import datetime
import logging
import re

logger = logging.getLogger(__name__)


class PDFReport(FPDF):
    """Custom PDF class with header and footer"""
    
    def __init__(self, title, sector):
        super().__init__()
        self.title_text = title
        self.sector = sector
        
    def header(self):
        """Page header"""
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, self.title_text, 0, 1, 'C')
        self.set_font('Arial', 'I', 10)
        self.cell(0, 5, f'Sector: {self.sector}', 0, 1, 'C')
        self.ln(5)
        
    def footer(self):
        """Page footer"""
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')


def generate_pdf(markdown_body: str, sector: str, sources: list, data_summary: dict) -> bytes:
    """
    Generate PDF from markdown report
    
    Args:
        markdown_body: Markdown formatted report
        sector: Sector name
        sources: List of source dictionaries
        data_summary: Summary data dictionary
        
    Returns:
        PDF file as bytes
    """
    try:
        # Create PDF
        pdf = PDFReport(
            title='Trade Opportunities Analysis',
            sector=sector.title()
        )
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        
        # Add key metrics
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, 'Key Metrics', 0, 1)
        pdf.set_font('Arial', '', 11)
        
        if data_summary.get('market_size'):
            pdf.multi_cell(0, 8, f"Market Size: {data_summary['market_size']}")
        if data_summary.get('growth_cagr'):
            pdf.multi_cell(0, 8, f"Growth Rate: {data_summary['growth_cagr']}")
        
        pdf.ln(5)
        
        # Add main content (convert markdown to plain text for PDF)
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, 'Analysis Report', 0, 1)
        pdf.set_font('Arial', '', 10)
        
        # Simple markdown to text conversion
        text_content = markdown_body
        # Remove markdown headers
        text_content = re.sub(r'^#{1,6}\s+', '', text_content, flags=re.MULTILINE)
        # Remove markdown bold/italic
        text_content = re.sub(r'\*\*([^*]+)\*\*', r'\1', text_content)
        text_content = re.sub(r'\*([^*]+)\*', r'\1', text_content)
        # Remove markdown links but keep text
        text_content = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text_content)
        
        # Split into paragraphs and add to PDF
        paragraphs = text_content.split('\n\n')
        for para in paragraphs:
            if para.strip():
                # Handle bullet points
                if para.strip().startswith('-'):
                    lines = para.split('\n')
                    for line in lines:
                        if line.strip():
                            pdf.multi_cell(0, 6, line.strip())
                else:
                    pdf.multi_cell(0, 6, para.strip())
                pdf.ln(3)
        
        # Add sources
        if sources:
            pdf.add_page()
            pdf.set_font('Arial', 'B', 14)
            pdf.cell(0, 10, 'Sources & Citations', 0, 1)
            pdf.set_font('Arial', '', 9)
            
            for idx, source in enumerate(sources[:10], 1):
                pdf.set_font('Arial', 'B', 9)
                pdf.multi_cell(0, 5, f"{idx}. {source.get('title', 'No Title')}")
                pdf.set_font('Arial', '', 8)
                pdf.multi_cell(0, 4, f"Source: {source.get('source', 'Unknown')}")
                pdf.multi_cell(0, 4, f"URL: {source.get('url', 'No URL')}")
                pdf.ln(2)
        
        # Generate timestamp
        pdf.set_font('Arial', 'I', 8)
        pdf.ln(5)
        pdf.cell(0, 5, f'Generated on: {datetime.utcnow().strftime("%B %d, %Y at %H:%M UTC")}', 0, 1, 'C')
        
        # Return PDF as bytes
        return bytes(pdf.output())
        
    except Exception as e:
        logger.error(f"PDF generation error: {e}")
        raise
