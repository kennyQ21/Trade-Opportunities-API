"""
PDF Generator Utility
Converts markdown reports to professional PDF documents with citations
"""
from weasyprint import HTML
from markdown2 import markdown
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def generate_pdf(
    markdown_body: str,
    sector: str,
    sources: list = None,
    data_summary: dict = None
) -> bytes:
    """
    Generate PDF from markdown report with citations
    
    Args:
        markdown_body: Markdown formatted report
        sector: Sector name
        sources: List of source citations
        data_summary: Extracted data summary
        
    Returns:
        PDF file as bytes
    """
    try:
        # Convert markdown to HTML
        html_content = markdown(
            markdown_body,
            extras=[
                'fenced-code-blocks',
                'tables',
                'header-ids',
                'metadata',
                'code-friendly'
            ]
        )
        
        # Build sources section HTML
        sources_html = ""
        if sources:
            sources_html = '<div class="sources"><h2>📚 Sources & Citations</h2><ol>'
            for idx, source in enumerate(sources, 1):
                sources_html += f'''
                <li class="source-item">
                    <strong>{source.get('title', 'No Title')}</strong><br>
                    <span class="source-meta">{source.get('source', 'Unknown Source')}</span><br>
                    <a href="{source.get('url', '#')}" class="source-link">{source.get('url', '#')}</a>
                </li>
                '''
            sources_html += '</ol></div>'
        
        # Build complete HTML document
        html_document = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>{sector.title()} - Trade Opportunities Analysis</title>
            <style>
                @page {{
                    size: A4;
                    margin: 2cm;
                    @bottom-right {{
                        content: "Page " counter(page) " of " counter(pages);
                        font-size: 9pt;
                        color: #666;
                    }}
                }}
                
                body {{
                    font-family: 'Helvetica', 'Arial', sans-serif;
                    line-height: 1.6;
                    color: #333;
                    font-size: 11pt;
                }}
                
                h1 {{
                    color: #1e3a8a;
                    font-size: 24pt;
                    margin-top: 0;
                    padding-bottom: 10px;
                    border-bottom: 3px solid #3b82f6;
                }}
                
                h2 {{
                    color: #1e40af;
                    font-size: 16pt;
                    margin-top: 20px;
                    margin-bottom: 10px;
                    border-left: 4px solid #3b82f6;
                    padding-left: 10px;
                }}
                
                h3 {{
                    color: #1e40af;
                    font-size: 13pt;
                    margin-top: 15px;
                }}
                
                ul, ol {{
                    margin: 10px 0;
                    padding-left: 25px;
                }}
                
                li {{
                    margin: 5px 0;
                }}
                
                strong {{
                    color: #1e40af;
                }}
                
                code {{
                    background: #f3f4f6;
                    padding: 2px 6px;
                    border-radius: 3px;
                    font-family: 'Courier New', monospace;
                    font-size: 10pt;
                }}
                
                .cover {{
                    text-align: center;
                    padding: 50px 0;
                    page-break-after: always;
                }}
                
                .cover h1 {{
                    font-size: 32pt;
                    border: none;
                    margin-bottom: 30px;
                }}
                
                .metadata {{
                    background: #f8fafc;
                    padding: 15px;
                    border-radius: 8px;
                    margin: 20px 0;
                    border-left: 4px solid #3b82f6;
                }}
                
                .metadata-item {{
                    margin: 5px 0;
                    font-size: 10pt;
                }}
                
                .sources {{
                    page-break-before: always;
                    margin-top: 30px;
                }}
                
                .source-item {{
                    margin: 15px 0;
                    padding: 10px;
                    background: #f8fafc;
                    border-radius: 5px;
                    border-left: 3px solid #3b82f6;
                }}
                
                .source-meta {{
                    color: #64748b;
                    font-size: 9pt;
                    font-style: italic;
                }}
                
                .source-link {{
                    color: #3b82f6;
                    text-decoration: none;
                    font-size: 9pt;
                    word-break: break-all;
                }}
                
                .summary-box {{
                    background: #eff6ff;
                    padding: 15px;
                    border-radius: 8px;
                    margin: 20px 0;
                    border: 2px solid #3b82f6;
                }}
                
                .summary-box h3 {{
                    margin-top: 0;
                    color: #1e40af;
                }}
            </style>
        </head>
        <body>
            <div class="cover">
                <h1>📊 {sector.title()} Sector</h1>
                <h2>Trade Opportunities Analysis Report</h2>
                <div class="metadata">
                    <div class="metadata-item"><strong>Generated:</strong> {datetime.utcnow().strftime('%B %d, %Y')}</div>
                    <div class="metadata-item"><strong>Market Focus:</strong> India</div>
                    <div class="metadata-item"><strong>Report Type:</strong> Comprehensive Market Analysis</div>
                </div>
            </div>
            
            {f"""
            <div class="summary-box">
                <h3>📈 Key Metrics</h3>
                <ul>
                    <li><strong>Market Size:</strong> {data_summary.get('market_size', 'Not Available')}</li>
                    <li><strong>Growth Rate:</strong> {data_summary.get('growth_cagr', 'Not Available')}</li>
                    <li><strong>Top Recommendations:</strong> {len(data_summary.get('top_recommendations', []))} actionable steps</li>
                </ul>
            </div>
            """ if data_summary else ""}
            
            <div class="content">
                {html_content}
            </div>
            
            {sources_html}
            
            <div style="margin-top: 30px; padding-top: 20px; border-top: 2px solid #e5e7eb; text-align: center; font-size: 9pt; color: #64748b;">
                <p>Trade Opportunities Analysis System | © 2025 | Confidential & Proprietary</p>
            </div>
        </body>
        </html>
        '''
        
        # Generate PDF
        logger.info(f"[PDF] Generating: {sector}")
        pdf_bytes = HTML(string=html_document).write_pdf()
        logger.info(f"[PDF] Done ({len(pdf_bytes)} bytes)")
        return pdf_bytes
        
    except Exception as e:
        logger.error(f"[PDF] {e}")
        raise
