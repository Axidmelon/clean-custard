# File: backend/services/ai_routing_agent.py
# Real AI Agent with LLM power for intelligent routing decisions

import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import json

from langchain_openai import ChatOpenAI
from core.config import settings

logger = logging.getLogger(__name__)

class RecommendedService(Enum):
    """Recommended services for different analysis types."""
    CSV_SQL = "csv_sql"           # SQL queries on CSV data
    CSV_PANDAS = "csv"            # Pandas operations on CSV data
    DATABASE = "database"         # External database queries

@dataclass
class AnalysisContext:
    """Context information for analysis routing."""
    question: str
    file_size: Optional[int] = None
    file_type: Optional[str] = None
    data_source: Optional[str] = None
    user_preference: Optional[str] = None

class AIRoutingAgent:
    """
    Real AI Agent powered by LLM that intelligently routes data analysis requests.
    
    This agent uses OpenAI's GPT models to understand the user's question and context,
    then makes intelligent decisions about which service to use for optimal results.
    """
    
    def __init__(self):
        """Initialize the AI routing agent with LLM."""
        self.logger = logging.getLogger(__name__)
        
        # Initialize the LLM
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=0.1,  # Low temperature for consistent routing decisions
            max_tokens=500,
            timeout=10  # Fast response for routing decisions
        )
        
        self.logger.info("AI Routing Agent initialized with LLM")
    
    async def analyze_and_route(self, question: str, context: Optional[AnalysisContext] = None) -> Dict[str, Any]:
        """
        Use AI to analyze the question and determine the best service to use.
        
        Args:
            question: The user's question
            context: Additional context about the data and user preferences
            
        Returns:
            Analysis result with recommended service and AI reasoning
        """
        try:
            self.logger.info(f"AI Agent analyzing question: {question[:100]}...")
            
            # Create context if not provided
            if context is None:
                context = AnalysisContext(question=question)
            
            # Build the AI prompt
            prompt = self._build_routing_prompt(question, context)
            
            # Get AI decision
            ai_response = await self.llm.ainvoke(prompt)
            
            # Parse AI response
            result = self._parse_ai_response(ai_response.content, context)
            
            self.logger.info(f"AI Agent recommendation: {result['recommended_service']} (confidence: {result['confidence']:.2f})")
            return result
            
        except Exception as e:
            self.logger.error(f"Error in AI routing: {e}")
            # Fallback to safe default
            return {
                "recommended_service": RecommendedService.CSV_SQL.value,
                "reasoning": f"AI routing failed: {str(e)}. Using safe default.",
                "confidence": 0.3,
                "ai_analysis": "Error occurred during AI analysis",
                "context": {
                    "question": question,
                    "file_size": context.file_size if context else None,
                    "data_source": context.data_source if context else None
                }
            }
    
    def _build_routing_prompt(self, question: str, context: AnalysisContext) -> str:
        """Build the AI prompt for routing decisions."""
        
        # Context information
        context_info = []
        if context.file_size:
            context_info.append(f"File size: {context.file_size / (1024*1024):.1f}MB")
        if context.data_source:
            context_info.append(f"Data source: {context.data_source}")
        if context.user_preference:
            context_info.append(f"User preference: {context.user_preference}")
        
        context_str = "\n".join(context_info) if context_info else "No additional context"
        
        # Determine available services based on context
        if context.data_source == "csv":
            # CSV file selected - only choose between CSV services
            available_services = """AVAILABLE SERVICES (CSV FILE SELECTED):
1. csv_sql: SQL queries on CSV data (fast, familiar SQL syntax, good for simple queries)
2. csv: Pandas operations on CSV data (powerful, good for complex statistical analysis and data transformation)

IMPORTANT: You can ONLY choose between csv_sql and csv. Do NOT recommend database service."""
            
            analysis_guidelines = """ANALYSIS GUIDELINES (CSV FILE CONTEXT):
- For simple queries (SELECT, WHERE, GROUP BY, COUNT, SUM, AVG): recommend csv_sql
- For complex statistical analysis (correlation, regression, ML, clustering): recommend csv
- For data transformation (pivot, reshape, merge, clean): recommend csv
- For large CSV files (>100MB): prefer csv over csv_sql for complex operations
- For user preferences: respect sql preference → csv_sql, python preference → csv
- For ambiguous cases: choose csv_sql for simplicity
- NEVER recommend database service when CSV file is selected"""
            
            response_format = """RESPONSE FORMAT (JSON only):
{{
    "recommended_service": "csv_sql|csv",
    "reasoning": "Brief explanation of why this service was chosen",
    "confidence": 0.85,
    "analysis_type": "simple_query|complex_statistical|data_transformation|large_dataset",
    "key_factors": ["factor1", "factor2", "factor3"]
}}"""
        else:
            # Database context - can choose all services
            available_services = """AVAILABLE SERVICES (DATABASE CONTEXT):
1. csv_sql: SQL queries on CSV data (fast, familiar SQL syntax, good for simple queries)
2. csv: Pandas operations on CSV data (powerful, good for complex statistical analysis and data transformation)
3. database: External database queries (real-time data, large datasets, production data)"""
            
            analysis_guidelines = """ANALYSIS GUIDELINES (DATABASE CONTEXT):
- For simple queries (SELECT, WHERE, GROUP BY, COUNT, SUM, AVG): recommend csv_sql
- For complex statistical analysis (correlation, regression, ML, clustering): recommend csv
- For data transformation (pivot, reshape, merge, clean): recommend csv
- For real-time data queries: recommend database
- For large datasets (>100MB): prefer csv or database over csv_sql
- For user preferences: respect sql preference → csv_sql, python preference → csv
- For ambiguous cases: choose csv_sql for simplicity"""
            
            response_format = """RESPONSE FORMAT (JSON only):
{{
    "recommended_service": "csv_sql|csv|database",
    "reasoning": "Brief explanation of why this service was chosen",
    "confidence": 0.85,
    "analysis_type": "simple_query|complex_statistical|data_transformation|real_time|large_dataset",
    "key_factors": ["factor1", "factor2", "factor3"]
}}"""
        
        prompt = f"""You are an expert data analysis routing agent. Your job is to analyze user questions and recommend the best service for data analysis.

{available_services}

USER QUESTION: {question}

CONTEXT:
{context_str}

{analysis_guidelines}

{response_format}

Respond with ONLY the JSON, no other text:"""

        return prompt
    
    def _parse_ai_response(self, ai_response: str, context: AnalysisContext) -> Dict[str, Any]:
        """Parse the AI response and extract routing decision."""
        try:
            # Clean the response (remove any markdown formatting)
            clean_response = ai_response.strip()
            if clean_response.startswith("```json"):
                clean_response = clean_response[7:]
            if clean_response.endswith("```"):
                clean_response = clean_response[:-3]
            clean_response = clean_response.strip()
            
            # Parse JSON response
            ai_data = json.loads(clean_response)
            
            # Validate the response
            recommended_service = ai_data.get("recommended_service", "csv_sql")
            
            # Additional validation: Prevent database recommendation when CSV file is selected
            if context.data_source == "csv" and recommended_service == "database":
                self.logger.warning("AI recommended database service for CSV file - overriding to csv_sql")
                recommended_service = "csv_sql"
            
            # Validate service is in allowed list
            if recommended_service not in ["csv_sql", "csv", "database"]:
                recommended_service = "csv_sql"  # Safe default
            
            return {
                "recommended_service": recommended_service,
                "reasoning": ai_data.get("reasoning", "AI analysis completed"),
                "confidence": float(ai_data.get("confidence", 0.7)),
                "ai_analysis": ai_data.get("analysis_type", "unknown"),
                "key_factors": ai_data.get("key_factors", []),
                "context": {
                    "question": context.question,
                    "file_size": context.file_size,
                    "data_source": context.data_source,
                    "user_preference": context.user_preference
                }
            }
            
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            self.logger.warning(f"Failed to parse AI response: {e}")
            # Fallback parsing
            return {
                "recommended_service": RecommendedService.CSV_SQL.value,
                "reasoning": f"AI response parsing failed: {str(e)}. Using safe default.",
                "confidence": 0.4,
                "ai_analysis": "parsing_error",
                "key_factors": ["fallback"],
                "context": {
                    "question": context.question,
                    "file_size": context.file_size,
                    "data_source": context.data_source,
                    "user_preference": context.user_preference
                }
            }
    
    async def get_service_recommendation(self, question: str, file_id: Optional[str] = None, 
                                       data_source: Optional[str] = None, 
                                       user_preference: Optional[str] = None) -> str:
        """
        Get a simple service recommendation for the question.
        
        Args:
            question: The user's question
            file_id: Optional file ID for context
            data_source: Optional data source hint
            user_preference: Optional user preference ("sql" or "python")
            
        Returns:
            Recommended service name ("csv_sql", "csv", or "database")
        """
        context = AnalysisContext(
            question=question,
            data_source=data_source,
            user_preference=user_preference
        )
        
        result = await self.analyze_and_route(question, context)
        return result["recommended_service"]
    
    async def explain_decision(self, question: str, context: Optional[AnalysisContext] = None) -> str:
        """
        Get a detailed explanation of why a particular service was recommended.
        
        Args:
            question: The user's question
            context: Additional context
            
        Returns:
            Detailed explanation of the routing decision
        """
        result = await self.analyze_and_route(question, context)
        
        explanation = f"""
🤖 AI Agent Decision Analysis:

📝 Question: {question}
🎯 Recommended Service: {result['recommended_service']}
🧠 Analysis Type: {result.get('ai_analysis', 'unknown')}
💭 Reasoning: {result['reasoning']}
🎯 Confidence: {result['confidence']:.2f}

🔍 Key Factors:
{chr(10).join(f"• {factor}" for factor in result.get('key_factors', []))}

📊 Context Considered:
• File Size: {result['context'].get('file_size', 'Unknown')}
• Data Source: {result['context'].get('data_source', 'Unknown')}
• User Preference: {result['context'].get('user_preference', 'None')}
        """
        
        return explanation.strip()

# Global instance
ai_routing_agent = AIRoutingAgent()
