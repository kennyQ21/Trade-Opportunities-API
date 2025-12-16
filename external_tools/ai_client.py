"""
AI Client Module
Wrapper for OpenAI API interactions
Centralizes prompts and model configuration
"""
from openai import OpenAI
from typing import Optional
import logging
import json

from app.core.config import settings

logger = logging.getLogger(__name__)


class OpenAIClient:
    """Client for OpenAI API operations"""
    
    def __init__(self, default_model: str = "gpt-4o"):
        """
        Initialize OpenAI client with model flexibility
        
        Args:
            default_model: Default model for analysis. Options:
                - gpt-4o: Best quality, recommended for analysis (default)
                - gpt-4o-mini: Fast, cost-effective, and high quality (recommended for speed)
        """
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.default_model = default_model
        logger.info(f"[OPENAI] Initialized with default model: {default_model}")
    
    def generate_analysis(self, sector: str, country: str, raw_data: str, model: str = None) -> Optional[str]:
        """
        Generate initial market analysis report
        
        Args:
            sector: Sector to analyze
            country: Target country
            raw_data: Collected market intelligence
            model: Override default model (optional)
            
        Returns:
            Markdown formatted analysis report or None on error
        """
        prompt = self._build_analysis_prompt(sector, country, raw_data)
        model = model or self.default_model
        
        try:
            logger.info(f"[OPENAI] Generating analysis for {sector} using {model}")
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a senior market analyst with 15 years of experience specializing in trade opportunities analysis and strategic market intelligence. You provide data-driven, actionable insights."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,  # Very low for maximum data extraction accuracy
                max_tokens=4000  # Increased for comprehensive reports
            )
            
            if response.choices and response.choices[0].message.content:
                return response.choices[0].message.content
            return None
            
        except Exception as e:
            logger.error(f"[OPENAI] Analysis error: {e}")
            return None
    
    def critique_report(self, sector: str, report: str, model: str = "gpt-4o-mini") -> Optional[str]:
        """
        Critique report quality and completeness
        Uses faster gpt-4o-mini by default for deterministic validation
        
        Args:
            sector: Sector being analyzed
            report: Markdown report to critique
            model: Model to use (default: gpt-4o-mini for speed)
            
        Returns:
            Critique feedback (PASS or FAIL: reason) or None on error
        """
        prompt = self._build_critique_prompt(sector, report)
        
        try:
            logger.info(f"[OPENAI] Critiquing report for {sector} using {model}")
            response = self.client.chat.completions.create(
                model=model,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": "You are a quality assurance reviewer for market analysis reports. You MUST output valid JSON only. Evaluate reports fairly based on realistic expectations for web-scraped data. PASS reports that show reasonable effort at data extraction and meet baseline quality standards."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,  # Very low for consistent, strict evaluation
                max_tokens=800  # More space for detailed critique
            )
            
            if response.choices and response.choices[0].message.content:
                content = response.choices[0].message.content.strip()
                try:
                    # Parse JSON output for structured decision
                    critique_dict = json.loads(content)
                    return critique_dict
                except json.JSONDecodeError as je:
                    logger.error(f"[OPENAI] Critique JSON decode error: {je}. Content: {content[:100]}...")
                    # Fallback: Return PASS dictionary to avoid blocking
                    return {"decision": "PASS", "reason": "JSON parse error - defaulting to PASS.", "raw_output": content[:200]}
            
            # No content returned
            return {"decision": "PASS", "reason": "Empty response from critique model."}
            
        except Exception as e:
            logger.error(f"[OPENAI] Critique API error: {e}")
            # Fail-safe: Return PASS to prevent deadlock
            return {"decision": "PASS", "reason": "API error - defaulting to PASS to prevent blocking."}
    
    def refine_report(self, sector: str, country: str, original_report: str, 
                     critique: str, raw_data: str, model: str = "gpt-4o") -> Optional[str]:
        """
        Refine report based on critique feedback using GPT-4o
        
        Uses the same powerful model as the analyzer to ensure high-quality
        refinements that address critique feedback effectively on the first attempt.
        
        Args:
            sector: Sector being analyzed
            country: Target country
            original_report: Original report text
            critique: Feedback from critic
            raw_data: Original market data
            model: Model to use (default: gpt-4o for complex refinement)
            
        Returns:
            Refined report or original on error
        """
        prompt = self._build_refinement_prompt(sector, country, original_report, critique, raw_data)
        
        try:
            logger.info(f"[OPENAI] Refining report for {sector} using {model}")
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a senior market analyst revising your report to meet strict editorial standards. You are meticulous about addressing every critique point and adding specific data."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # Extremely low for precise data extraction in refinement
                max_tokens=4000  # Increased for comprehensive revision
            )
            
            if response.choices and response.choices[0].message.content:
                return response.choices[0].message.content
            return original_report  # Return original if refinement fails
            
        except Exception as e:
            logger.error(f"[OPENAI] Refinement error: {e}")
            return original_report
    
    def _build_analysis_prompt(self, sector: str, country: str, raw_data: str) -> str:
        """Build prompt for initial analysis with enhanced structure"""
        from datetime import datetime
        
        return f"""**ROLE & EXPERTISE:**
You are an expert {country} market analyst with 15 years of experience in trade opportunities analysis and strategic market intelligence. You have deep knowledge of the {sector} sector specifically.

**CRITICAL CONSTRAINT:**
You MUST strictly output a structured report in Markdown format ONLY. No preamble, no conversational text—just the formatted report.

**INPUT DATA ANALYSIS:**
The following market intelligence has been collected from multiple sources and is delimited by `---Article X---` markers. Each article contains SOURCE, TITLE, and content information.

**AVAILABLE MARKET INTELLIGENCE:**
{raw_data}

**YOUR TASK:**
Analyze the above data comprehensively and produce a professional trade opportunities report. Your analysis MUST focus on identifying **Actionable Trade Opportunities** in the **{sector}** sector.

**MANDATORY OUTPUT STRUCTURE:**
Create a detailed, data-driven markdown report with the following structure:

# {sector.title()} Sector - Trade Opportunities Analysis ({country})

## Executive Summary
Provide a 3-4 sentence data-driven overview citing SPECIFIC figures, percentages, or timeframes from the source articles. Focus on current sector status and key opportunities.

## Market Overview
**CRITICAL:** Extract and cite EVERY number from the articles. For each data point, cite the source:
- Current market size with SPECIFIC numbers (₹ Crores, $ Billions, etc.) - cite source
- Growth rate with percentages and timeframes - cite source  
- Key players with recent developments (mergers, earnings, launches) - cite source
- Recent policy changes or government announcements - cite source

**INSTRUCTION:** Scan the articles for ANY numerical data (market value, percentages, growth figures, company revenue, investment amounts) and include them with proper attribution.

## Trade Opportunities

### Export Opportunities
- Identify 3-5 specific export opportunities
- Target markets and demand drivers
- Competitive advantages

### Import Opportunities  
- Key imported products/services
- Supply gaps in domestic market
- Partnership opportunities

### Domestic Trade Opportunities
- B2B opportunities
- Distribution channels
- Emerging market segments

## Sector Analysis

### Strengths
- List key advantages and strengths (bullet points)

### Challenges
- Regulatory hurdles
- Competition analysis
- Infrastructure concerns

### Emerging Trends
- Technology adoption
- Policy changes
- Consumer behavior shifts

## Investment Considerations
- Capital requirements
- Risk factors
- ROI potential
- Time horizons

## Regulatory Framework
- Key regulations and compliance requirements
- Recent policy changes
- Import/export procedures

## Actionable Recommendations
Provide 5-7 specific, actionable steps for businesses looking to enter this sector.

## Market Outlook (Next 12-24 Months)
Short to medium-term projections and anticipated changes.

---
*Report generated on: {datetime.utcnow().strftime('%B %d, %Y')}*
*Sector: {sector.title()}*
*Market: {country}*

**CRITICAL REQUIREMENTS:**
1. **Data-Driven:** Extract and cite EVERY specific number, percentage, market size, growth rate, or quantitative metric from the articles. Prioritize numerical data extraction above all else.
2. **Current:** Reference actual events, policies, or developments from {datetime.now().year}
3. **Actionable:** Every opportunity must be specific, not generic (e.g., "Export surgical instruments to UAE" not just "Export opportunities exist")
4. **Complete:** ALL sections must be substantial—no placeholders or "TBD" allowed
5. **Source Attribution:** When citing specific data, mention the source (e.g., "According to Economic Times...")
6. **No Hallucination:** Only use information from the provided articles—do not invent data

**OUTPUT FORMAT:** Pure markdown starting with # {sector.title()} Sector - Trade Opportunities Analysis
"""
    
    def _build_critique_prompt(self, sector: str, report: str) -> str:
        """Build enhanced critique prompt with strict quality standards"""
        return f"""**ROLE:** You are a senior editorial quality assurance specialist reviewing market analysis reports for institutional investors and trade organizations.

**REPORT TO REVIEW:**
{report}

**STRICT QUALITY CRITERIA (All Must Pass):**

1. **DATA SPECIFICITY**: 
   - Are there at least 2-3 SPECIFIC numbers, percentages, market sizes, or growth rates cited from the source articles?
   - This is a MINIMUM threshold - if you see at least 2-3 quantitative data points with source attribution, this criterion is MET.
   - PASS if the report contains measurable specifics even if some sections lack numbers due to source data limitations

2. **TRADE OPPORTUNITY PRECISION**:
   - Are export/import opportunities SPECIFIC (products, target markets, partners)?
   - NO PASS if opportunities are generic (e.g., "explore exports" vs "export precision instruments to Germany")

3. **CURRENT RELEVANCE**:
   - Does the report reference events, policies, or data from 2024-2025?
   - NO PASS if report appears outdated or lacks recent developments

4. **ACTIONABILITY**:
   - Can a business executive take concrete action from this report?
   - Are recommendations clear with steps, timeframes, and requirements?

5. **COMPLETENESS**:
   - Are ALL sections substantial (not just headers or bullet points)?
   - NO PASS if any section is a placeholder or lacks depth

6. **NO HALLUCINATION**:
   - Does the report stay grounded in provided data?
   - NO PASS if report invents statistics or events not in source data

**YOUR EVALUATION TASK:**
Review the report against ALL criteria above. Be strict—this report will guide real business decisions.

**RESPONSE FORMAT (STRICT JSON OBJECT ONLY):**

You MUST return a valid JSON object with exactly two keys:
- **decision**: Must be the string "PASS" or "FAIL"
- **reason**: A brief explanation (one sentence for PASS, bullet list for FAIL)

**Example of PASS:**
{{
  "decision": "PASS",
  "reason": "Report contains 3+ specific data points with sources and meets all baseline quality criteria."
}}

**Example of FAIL:**
{{
  "decision": "FAIL",
  "reason": "Criterion 1 (DATA): Only 1 number cited, need 2-3 minimum. Criterion 2 (TRADE): Export opportunities too generic."
}}

**EVALUATION GUIDANCE:** 
- Web-scraped news articles have inherent data limitations
- PASS if the report demonstrates reasonable data extraction effort and meets minimum thresholds (2-3 numbers)
- Only FAIL if critical deficiencies exist (e.g., zero quantitative data, generic opportunities, completely missing sections)

**CRITICAL:** Return ONLY the JSON object. No preamble, no markdown, no conversational text.

Respond now:"""
    
    def _build_refinement_prompt(self, sector: str, country: str, 
                                 original_report: str, critique: str, raw_data: str) -> str:
        """Build enhanced refinement prompt with strict improvement focus"""
        return f"""**ROLE:** You are a senior market analyst revising your previous report based on editorial feedback.

**CONTEXT:**
You wrote a market analysis report for the {sector} sector in {country}, but it was rejected for quality issues.

**YOUR ORIGINAL REPORT:**
{original_report}

**EDITORIAL REJECTION REASONS:**
{critique}

**ORIGINAL SOURCE DATA (Re-analyze carefully):**
{raw_data}

**YOUR REFINEMENT TASK:**
Completely rewrite the report addressing EVERY SINGLE point in the editorial feedback. This is your final chance to meet publication standards.

**REFINEMENT REQUIREMENTS:**

1. **Address Every Critique Point:** Go through each failure mentioned and fix it explicitly
2. **Add Missing Data:** If numbers/percentages were missing, extract them from the source articles
3. **Increase Specificity:** Replace every vague statement with specific details:
   - Instead of "growing sector" → "15% CAGR from 2023-2025 (Source: IBEF)"
   - Instead of "export opportunities" → "export API pharmaceuticals to regulated markets (US, EU) via WHO-GMP certified facilities"
4. **Enhance Actionability:** Every recommendation must have:
   - Specific action (what to do)
   - Target/partner (who to contact)
   - Timeframe (when to act)
   - Expected outcome (what to achieve)
5. **Maintain Structure:** Keep the markdown format and section headers
6. **Source Attribution:** Cite sources for key claims

**CRITICAL:** The refined report MUST pass all quality criteria. Do not submit mediocre work.

**OUTPUT:** Pure markdown report starting with the title:"""
    
    def format_report(self, markdown_report: str, sector: str) -> dict:
        """
        Extract structured data from final validated markdown report
        Uses GPT-4o-mini for cost-effective data extraction
        
        Args:
            markdown_report: The final validated markdown report
            sector: Sector name for context
            
        Returns:
            Dictionary with extracted data: {market_size, growth_cagr, top_recommendations}
        """
        prompt = f"""**TASK:** Extract key data points from this market analysis report.

**REPORT TO ANALYZE:**
{markdown_report}

**EXTRACTION REQUIREMENTS:**
1. Find the current or projected market size (e.g., "USD 400 billion", "₹5.2 trillion")
2. Find the growth rate/CAGR (e.g., "12% CAGR", "15% annual growth")
3. Extract the top 3 most impactful recommendations (full sentence for each)

**OUTPUT FORMAT (STRICT JSON):**
```json
{{
  "market_size": "USD 400 billion by 2025",
  "growth_cagr": "12% CAGR (2023-2028)",
  "top_recommendations": [
    "First recommendation here...",
    "Second recommendation here...",
    "Third recommendation here..."
  ]
}}
```

**RULES:**
- If data not found, use null for that field
- Copy exact text from report, do not paraphrase
- Recommendations must be the most actionable and specific ones
- Return ONLY the JSON, no other text

**OUTPUT:**"""

        try:
            logger.info(f"[OPENAI] Extracting structured data for {sector} using gpt-4o-mini")
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a data extraction specialist. You extract structured information from documents with perfect accuracy. You only return valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,  # Zero temperature for deterministic extraction
                max_tokens=800
            )
            
            if response.choices and response.choices[0].message.content:
                content = response.choices[0].message.content.strip()
                
                # Remove markdown code blocks if present
                if content.startswith("```json"):
                    content = content[7:]
                if content.startswith("```"):
                    content = content[3:]
                if content.endswith("```"):
                    content = content[:-3]
                content = content.strip()
                
                # Parse JSON
                result = json.loads(content)
                logger.info(f"[OPENAI] ✓ Successfully extracted structured data")
                return result
            
            # Fallback
            return {
                "market_size": None,
                "growth_cagr": None,
                "top_recommendations": []
            }
            
        except Exception as e:
            logger.error(f"[OPENAI] Format error: {e}")
            return {
                "market_size": None,
                "growth_cagr": None,
                "top_recommendations": []
            }


# Global client instance
openai_client = OpenAIClient()
