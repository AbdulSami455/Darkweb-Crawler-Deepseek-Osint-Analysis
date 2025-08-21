#!/usr/bin/env python3
"""
LangChain integration for structured dark web content analysis.
"""

import os
import json
from typing import Dict, Optional, Any
from langchain_openai import ChatOpenAI
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, SystemMessage

from .models import DarkWebAnalysis


class LangChainAnalyzer:
    """LangChain-based analyzer for structured dark web content analysis."""
    
    def __init__(self, api_key: Optional[str] = None) -> None:
        """Initialize the LangChain analyzer."""
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY is required for LangChain analysis")
        
        # Initialize LangChain components
        self.llm = ChatOpenAI(
            model="deepseek/deepseek-r1-0528:free",
            openai_api_key=self.api_key,
            openai_api_base="https://openrouter.ai/api/v1",
            temperature=0.3,
            max_tokens=2000,
            headers={
                "HTTP-Referer": "https://github.com/GENAI-RAG",
                "X-Title": "OnionScrap-API",
            }
        )
        
        self.parser = PydanticOutputParser(pydantic_object=DarkWebAnalysis)
        
        # Create the prompt template
        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", self._get_system_prompt()),
            ("human", self._get_human_prompt_template())
        ])
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the analysis."""
        return """You are an OSINT-focused cybersecurity analyst specializing in dark-web (.onion) content analysis. 
Your task is to analyze dark web content and extract structured information according to the provided schema.

Key responsibilities:
1. Extract factual information without speculation
2. Normalize data according to specified rules
3. Provide accurate categorization
4. Assess security implications
5. Maintain analytical objectivity

Output format: Structured JSON that matches the DarkWebAnalysis schema exactly."""

    def _get_human_prompt_template(self) -> str:
        """Get the human prompt template."""
        return """Analyze the following dark-web content captured from a .onion page and extract structured information.

{format_instructions}

Content to analyze:
{content}

Please provide a comprehensive analysis following these guidelines:

1. **Content Summary**: Provide a plain, factual summary of what this page is about
2. **Key Information Extraction**: 
   - Names/aliases mentioned
   - Contact methods (Telegram, Email, Jabber, Tox, etc.)
   - URLs (.onion/.clearnet)
   - PGP keys/fingerprints
   - Crypto wallets (BTC/ETH/XMR/etc.)
   - Product/service listings with prices/currencies
   - Dates/timestamps (normalize to ISO 8601)
   - Target industries/regions
   - Claims of affiliation or reputation

3. **Security Assessment**:
   - Indicators of malware/phishing/scams
   - Escrow claims
   - Operational security practices
   - External links/downloads
   - Signs of law enforcement impersonation

4. **Categorization**: Classify using appropriate categories from the schema

5. **Notable Elements**: Identify unusual or high-signal elements

6. **Recommendations**: Provide safety and handling guidance for analysts

7. **Source Reliability**: Rate 1-5 with explanation

8. **Confidence**: Rate 0-1 with justification

9. **Limitations**: Note any truncation, language barriers, or quality issues

Normalization rules:
- Normalize dates to ISO 8601 format
- For PGP: include 40-character hex fingerprint and key block presence
- For crypto: include type, address, and network/tag information
- For onion links: flag v2 addresses as deprecated
- If non-English content: include detected language and English summary"""

    def analyze_content(self, content: str) -> Dict[str, Any]:
        """Analyze content using LangChain and return structured data."""
        try:
            # Format the prompt with instructions and content
            messages = self.prompt_template.format_messages(
                format_instructions=self.parser.get_format_instructions(),
                content=content[:4000]  # Limit content length
            )
            
            # Get response from LLM
            response = self.llm.invoke(messages)
            
            # Parse the response into structured data
            structured_analysis = self.parser.parse(response.content)
            
            # Convert to dictionary for easier handling
            result = structured_analysis.model_dump()
            
            return {
                "success": True,
                "analysis": result,
                "model": "deepseek/deepseek-r1-0528:free",
                "tokens_used": getattr(response, 'usage', {}).get('total_tokens', 0) if hasattr(response, 'usage') else 0,
                "raw_response": response.content
            }
            
        except Exception as exc:
            return {
                "success": False,
                "error": f"LangChain analysis failed: {str(exc)}",
                "raw_response": getattr(response, 'content', '') if 'response' in locals() else ''
            }
    
    def analyze_content_with_fallback(self, content: str) -> Dict[str, Any]:
        """Analyze content with fallback to JSON parsing if structured parsing fails."""
        # Try structured analysis first
        result = self.analyze_content(content)
        
        if result["success"]:
            return result
        
        # Fallback: try to extract JSON from the response
        try:
            raw_response = result.get("raw_response", "")
            if raw_response:
                # Try to find JSON in the response
                start_idx = raw_response.find('{')
                end_idx = raw_response.rfind('}') + 1
                
                if start_idx != -1 and end_idx > start_idx:
                    json_str = raw_response[start_idx:end_idx]
                    json_data = json.loads(json_str)
                    
                    return {
                        "success": True,
                        "analysis": json_data,
                        "model": "deepseek/deepseek-r1-0528:free",
                        "tokens_used": 0,
                        "raw_response": raw_response,
                        "fallback_used": True
                    }
        except Exception:
            pass
        
        return result
