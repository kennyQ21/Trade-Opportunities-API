"""
Trade Opportunities Analysis - Streamlit Frontend
User-friendly interface for sector analysis with citations and PDF export
"""
import streamlit as st
import requests
import json
from datetime import datetime
from pathlib import Path
from utils.pdf_generator import generate_pdf

# Page configuration
st.set_page_config(
    page_title="Trade Opportunities Analysis",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1e3a8a;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #64748b;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        margin: 0.5rem 0;
    }
    .metric-label {
        font-size: 0.9rem;
        opacity: 0.9;
        margin-bottom: 0.5rem;
    }
    .metric-value {
        font-size: 1.5rem;
        font-weight: 700;
    }
    .source-card {
        background: #f8fafc;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #3b82f6;
        margin: 0.5rem 0;
    }
    .source-title {
        font-weight: 600;
        color: #1e40af;
        margin-bottom: 0.3rem;
    }
    .source-meta {
        font-size: 0.85rem;
        color: #64748b;
        margin-bottom: 0.3rem;
    }
    .recommendation-item {
        background: #eff6ff;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border-left: 3px solid #3b82f6;
        color: #1e293b;
    }
    .stButton>button {
        width: 100%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.75rem;
        font-weight: 600;
        border-radius: 8px;
    }
    .success-box {
        background: #d1fae5;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #10b981;
        margin: 1rem 0;
    }
    .error-box {
        background: #fee2e2;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #ef4444;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'analysis_data' not in st.session_state:
    st.session_state.analysis_data = None
if 'pdf_bytes' not in st.session_state:
    st.session_state.pdf_bytes = None

# Sidebar configuration
with st.sidebar:
    st.markdown("### ⚙️ Configuration")
    
    api_url = st.text_input(
        "API Endpoint",
        value="http://localhost:8000",
        help="Base URL of the Trade Opportunities API"
    )
    
    api_key = st.text_input(
        "API Key",
        value="demo-key-12345",
        type="password",
        help="Your API authentication key"
    )
    
    st.markdown("---")
    st.markdown("### 📖 About")
    st.markdown("""
    This tool analyzes trade opportunities for Indian sectors using:
    - Real-time news data
    - AI-powered analysis
    - Expert recommendations
    - Cited sources
    """)
    
    st.markdown("---")
    st.markdown("### 🎯 Features")
    st.markdown("""
    ✅ Comprehensive analysis  
    ✅ Live citations  
    ✅ PDF export  
    ✅ Source links  
    ✅ Key metrics
    """)

# Main content
st.markdown('<div class="main-header">📊 Trade Opportunities Analysis</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">AI-Powered Market Intelligence for Indian Sectors</div>', unsafe_allow_html=True)

# Input section
col1, col2 = st.columns([3, 1])

with col1:
    sector = st.text_input(
        "Enter Sector to Analyze",
        placeholder="e.g., pharmaceuticals, textiles, agriculture, technology",
        help="Enter the name of the sector you want to analyze"
    )

with col2:
    st.markdown("<br>", unsafe_allow_html=True)
    analyze_button = st.button("🚀 Analyze Sector", use_container_width=True)

# Analysis execution
if analyze_button and sector:
    with st.spinner(f"🔍 Analyzing {sector} sector... This may take 60-90 seconds."):
        try:
            # Make API request
            response = requests.get(
                f"{api_url}/v1/analyze/{sector}",
                headers={"X-API-Key": api_key},
                timeout=180
            )
            
            if response.status_code == 200:
                st.session_state.analysis_data = response.json()
                st.markdown('<div class="success-box">✅ Analysis completed successfully!</div>', unsafe_allow_html=True)
            elif response.status_code == 429:
                st.markdown('<div class="error-box">⚠️ Rate limit exceeded. Please wait and try again.</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="error-box">❌ Error: {response.status_code} - {response.text}</div>', unsafe_allow_html=True)
                
        except requests.exceptions.Timeout:
            st.markdown('<div class="error-box">⏱️ Request timeout. The analysis is taking longer than expected. Please try again.</div>', unsafe_allow_html=True)
        except Exception as e:
            st.markdown(f'<div class="error-box">❌ Error: {str(e)}</div>', unsafe_allow_html=True)

elif analyze_button:
    st.warning("⚠️ Please enter a sector name")

# Display results
if st.session_state.analysis_data:
    data = st.session_state.analysis_data
    
    # Tabs for organized display
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "📝 Full Report", "📚 Sources", "💾 Export"])
    
    # Tab 1: Overview
    with tab1:
        st.markdown("### 📈 Key Metrics")
        
        # Display metrics in cards
        col1, col2, col3 = st.columns(3)
        
        data_summary = data.get('data_summary', {})
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Market Size</div>
                <div class="metric-value">{data_summary.get('market_size', 'Not Available')}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Growth Rate</div>
                <div class="metric-value">{data_summary.get('growth_cagr', 'Not Available')}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Recommendations</div>
                <div class="metric-value">{len(data_summary.get('top_recommendations', []))} Actions</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Top Recommendations
        st.markdown("### 🎯 Top Actionable Recommendations")
        recommendations = data_summary.get('top_recommendations', [])
        
        if recommendations:
            for idx, rec in enumerate(recommendations, 1):
                st.markdown(f"""
                <div class="recommendation-item">
                    <strong>{idx}.</strong> {rec}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No specific recommendations extracted.")
        
        # Metadata
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"**Report ID:** `{data.get('report_id', 'N/A')}`")
        with col2:
            st.markdown(f"**Sector:** {data.get('sector', 'N/A').title()}")
        with col3:
            timestamp = data.get('timestamp', '')
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    st.markdown(f"**Generated:** {dt.strftime('%B %d, %Y %H:%M UTC')}")
                except:
                    st.markdown(f"**Generated:** {timestamp}")
    
    # Tab 2: Full Report
    with tab2:
        st.markdown("### 📄 Complete Analysis Report")
        markdown_body = data.get('markdown_body', '')
        
        if markdown_body:
            st.markdown(markdown_body)
        else:
            st.warning("No report content available.")
    
    # Tab 3: Sources
    with tab3:
        st.markdown("### 📚 Sources & Citations")
        sources = data.get('sources', [])
        
        if sources:
            st.info(f"📊 Total sources cited: **{len(sources)}**")
            
            for idx, source in enumerate(sources, 1):
                st.markdown(f"""
                <div class="source-card">
                    <div class="source-title">{idx}. {source.get('title', 'No Title')}</div>
                    <div class="source-meta">📰 {source.get('source', 'Unknown Source')}</div>
                    <a href="{source.get('url', '#')}" target="_blank" style="color: #3b82f6; text-decoration: none;">
                        🔗 {source.get('url', 'No URL')}
                    </a>
                    {f'<p style="margin-top: 0.5rem; font-size: 0.9rem; color: #475569;">{source.get("snippet", "")}</p>' if source.get('snippet') else ''}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.warning("No sources available for this analysis.")
    
    # Tab 4: Export
    with tab4:
        st.markdown("### 💾 Export Options")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📄 Download as PDF")
            st.markdown("Generate a professional PDF report with full analysis and citations.")
            
            if st.button("📥 Generate & Download PDF", use_container_width=True):
                with st.spinner("Generating PDF..."):
                    try:
                        pdf_bytes = generate_pdf(
                            markdown_body=data.get('markdown_body', ''),
                            sector=data.get('sector', 'Unknown'),
                            sources=data.get('sources', []),
                            data_summary=data.get('data_summary', {})
                        )
                        st.session_state.pdf_bytes = pdf_bytes
                        st.success("✅ PDF generated successfully!")
                    except Exception as e:
                        st.error(f"❌ PDF generation failed: {str(e)}")
            
            if st.session_state.pdf_bytes:
                date_suffix = datetime.now().strftime('%Y%m%d')
                sector_name = data.get('sector', 'analysis')
                st.download_button(
                    label="📥 Download PDF File",
                    data=st.session_state.pdf_bytes,
                    file_name=f"{sector_name}_{date_suffix}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
        
        with col2:
            st.markdown("#### 📋 Download as Markdown")
            st.markdown("Get the raw markdown file for custom processing.")
            
            if markdown_content := data.get('markdown_body'):
                date_suffix = datetime.now().strftime('%Y%m%d')
                sector_name = data.get('sector', 'analysis')
                st.download_button(
                    label="📥 Download Markdown File",
                    data=markdown_content,
                    file_name=f"{sector_name}_{date_suffix}.md",
                    mime="text/markdown",
                    use_container_width=True
                )
        
        st.markdown("---")
        st.markdown("#### 📊 Raw JSON Data")
        st.markdown("Access the complete API response in JSON format.")
        
        with st.expander("View JSON Response"):
            st.json(data)
        
        date_suffix = datetime.now().strftime('%Y%m%d')
        sector_name = data.get('sector', 'analysis')
        st.download_button(
            label="📥 Download JSON File",
            data=json.dumps(data, indent=2),
            file_name=f"{sector_name}_{date_suffix}.json",
            mime="application/json",
            use_container_width=True
        )

else:
    # Welcome message when no analysis
    st.info("👆 Enter a sector name above and click 'Analyze Sector' to get started!")
    
    st.markdown("### 🌟 Sample Sectors")
    col1, col2, col3, col4 = st.columns(4)
    
    sample_sectors = [
        ("💊", "Pharmaceuticals"),
        ("🧵", "Textiles"),
        ("🌾", "Agriculture"),
        ("💻", "Technology"),
        ("🏗️", "Construction"),
        ("⚡", "Energy"),
        ("🚗", "Automotive"),
        ("🏭", "Manufacturing")
    ]
    
    for idx, (icon, name) in enumerate(sample_sectors):
        col = [col1, col2, col3, col4][idx % 4]
        with col:
            st.markdown(f"""
            <div style="background: #f8fafc; padding: 1rem; border-radius: 8px; text-align: center; margin: 0.5rem 0;">
                <div style="font-size: 2rem;">{icon}</div>
                <div style="font-weight: 600; color: #1e40af;">{name}</div>
            </div>
            """, unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #64748b; font-size: 0.9rem;">
    <p>Trade Opportunities Analysis System | Powered by AI & Real-time Data</p>
    <p>© 2025 | Built with Streamlit & FastAPI</p>
</div>
""", unsafe_allow_html=True)
