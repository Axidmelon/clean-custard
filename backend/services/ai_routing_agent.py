# File: backend/services/ai_routing_agent.py
# Real AI Agent with LLM power for intelligent routing decisions

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
import json
import uuid
import time

from langchain_openai import ChatOpenAI
from core.config import settings
from core.langsmith_service import langsmith_service
from core.working_memory import working_memory_service

logger = logging.getLogger(__name__)

class RecommendedService(Enum):
    """Recommended services for different analysis types."""
    CSV_SQL = "csv_to_sql_converter"    # SQL queries on CSV data
    CSV_PANDAS = "data_analysis_service" # Pandas operations on CSV data

@dataclass
class AnalysisContext:
    """Context information for analysis routing."""
    question: str
    file_size: Optional[int] = None
    file_type: Optional[str] = None
    data_source: Optional[str] = None
    user_preference: Optional[str] = None
    user_id: Optional[str] = None

class AIRoutingAgent:
    """
    Real AI Agent powered by LLM that intelligently routes CSV data analysis requests.
    
    This agent uses OpenAI's GPT models to understand the user's question and context,
    then makes intelligent decisions between csv_to_sql_converter and data_analysis_service
    for optimal CSV data analysis results.
    
    Note: This agent only handles CSV data routing. Database queries are handled directly
    by agent-postgresql without AI routing.
    """
    
    def __init__(self):
        """Initialize the AI routing agent with LLM."""
        self.logger = logging.getLogger(__name__)
        
        # Initialize the LLM with LangSmith tracing
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=0.1,  # Low temperature for consistent routing decisions
            max_tokens=500,
            timeout=10,  # Fast response for routing decisions
            callbacks=[langsmith_service.get_tracer()] if langsmith_service.is_enabled else None
        )
        
        # Cache for schema analysis results to avoid repeated calls
        self._schema_cache = {}
        self._cache_ttl = 300  # 5 minutes cache TTL
        
        self.logger.info("AI Routing Agent initialized with LLM")
    
    def _get_cached_schema_analysis(self, file_ids: List[str], user_id: str) -> Optional[Dict[str, Any]]:
        """Get cached schema analysis if available and not expired."""
        import time
        
        cache_key = f"{user_id}:{':'.join(sorted(file_ids))}"
        if cache_key in self._schema_cache:
            cached_data, timestamp = self._schema_cache[cache_key]
            if time.time() - timestamp < self._cache_ttl:
                self.logger.debug(f"Using cached schema analysis for {len(file_ids)} files")
                return cached_data
            else:
                # Remove expired cache entry
                del self._schema_cache[cache_key]
        
        return None
    
    def _cache_schema_analysis(self, file_ids: List[str], user_id: str, analysis_data: Dict[str, Any]):
        """Cache schema analysis results."""
        import time
        
        cache_key = f"{user_id}:{':'.join(sorted(file_ids))}"
        self._schema_cache[cache_key] = (analysis_data, time.time())
        self.logger.debug(f"Cached schema analysis for {len(file_ids)} files")
    
    async def analyze_and_route(self, question: str, context: Optional[AnalysisContext] = None) -> Dict[str, Any]:
        """
        Use AI to analyze the question and determine the best service to use.
        
        Args:
            question: The user's question
            context: Additional context about the data and user preferences
            
        Returns:
            Analysis result with recommended service and AI reasoning
        """
        with langsmith_service.create_trace("ai_routing_decision") as trace_obj:
            # Add initial metadata
            trace_obj.metadata = {
                "question_type": "routing_decision",
                "question_length": len(question),
                "file_size": context.file_size if context else None,
                "user_preference": context.user_preference if context else None,
                "data_source": context.data_source if context else None,
                "model": settings.openai_model,
                "temperature": 0.1
            }

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
                
                # Add success metadata
                langsmith_service.add_metadata(trace_obj, {
                    "recommended_service": result["recommended_service"],
                    "confidence": result["confidence"],
                    "ai_analysis": result.get("ai_analysis", "unknown"),
                    "success": True,
                    "response_time_ms": "calculated_by_langsmith"
                })
                
                self.logger.info(f"AI Agent recommendation: {result['recommended_service']} (confidence: {result['confidence']:.2f})")
                langsmith_service.log_trace_event("ai_routing_decision", f"Successfully routed to {result['recommended_service']} with confidence {result['confidence']:.2f}")
                
                return result
                
            except Exception as e:
                self.logger.error(f"Error in AI routing: {e}")
                
                # Smart fallback based on question complexity
                question_lower = question.lower()
                if any(keyword in question_lower for keyword in ['correlation', 'trend', 'analysis', 'regression', 'statistical', 'machine learning', 'ml']):
                    fallback_service = "data_analysis_service"
                    fallback_reasoning = "Complex analysis detected, using pandas service"
                else:
                    fallback_service = "csv_to_sql_converter"
                    fallback_reasoning = "Simple query detected, using SQL service"
                
                # Add fallback metadata
                langsmith_service.add_metadata(trace_obj, {
                    "recommended_service": fallback_service,
                    "confidence": 0.3,
                    "ai_analysis": "fallback_decision",
                    "success": False,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "fallback_reasoning": fallback_reasoning
                })
                
                langsmith_service.log_trace_event("ai_routing_fallback", f"AI routing failed, using fallback: {fallback_service}")
                
                return {
                    "recommended_service": fallback_service,
                    "reasoning": f"AI routing failed: {str(e)}. {fallback_reasoning}.",
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
            try:
                file_size_mb = float(context.file_size) / (1024*1024)
                context_info.append(f"File size: {file_size_mb:.1f}MB")
            except (ValueError, TypeError):
                context_info.append(f"File size: {context.file_size} bytes")
        if context.data_source:
            context_info.append(f"Data source: {context.data_source}")
        if context.user_preference:
            context_info.append(f"User preference: {context.user_preference}")
        
        context_str = "\n".join(context_info) if context_info else "No additional context"
        
        return f"""You are an expert data analysis routing agent. Your job is to analyze user questions and recommend the best service for data analysis.

AVAILABLE SERVICES (CSV DATA ONLY):
1. csv_to_sql_converter: SQL queries on CSV data (fast, familiar SQL syntax, good for simple queries)
2. data_analysis_service: Pandas operations on CSV data (powerful, good for complex statistical analysis and data transformation)

IMPORTANT: You can ONLY choose between csv_to_sql_converter and data_analysis_service.

USER QUESTION: {question}

CONTEXT:
{context_str}

ANALYSIS GUIDELINES:
- For simple queries (SELECT, WHERE, GROUP BY, COUNT, SUM, AVG): recommend csv_to_sql_converter
- For complex statistical analysis (correlation, regression, ML, clustering): recommend data_analysis_service
- For data transformation (pivot, reshape, merge, clean): recommend data_analysis_service
- For large CSV files (>100MB): prefer data_analysis_service over csv_to_sql_converter for complex operations
- For user preferences: respect sql preference → csv_to_sql_converter, python preference → data_analysis_service
- For ambiguous cases: choose csv_to_sql_converter for simplicity

RESPONSE FORMAT (JSON only):
{{
    "recommended_service": "csv_to_sql_converter|data_analysis_service",
    "reasoning": "Brief explanation of why this service was chosen",
    "confidence": 0.85,
    "analysis_type": "simple_query|complex_statistical|data_transformation|large_dataset",
    "key_factors": ["factor1", "factor2", "factor3"]
}}

CRITICAL: Return ONLY the JSON object above, without any markdown formatting, code blocks, or additional text. Do not wrap in ```json``` or any other formatting."""

    def _parse_ai_response(self, ai_response: str, context: AnalysisContext) -> Dict[str, Any]:
        """Parse the AI response and extract routing decision."""
        try:
            # Clean the response (remove any markdown formatting)
            clean_response = ai_response.strip()
            
            # Remove various markdown formatting patterns
            if clean_response.startswith("```json"):
                clean_response = clean_response[7:]
            elif clean_response.startswith("```"):
                clean_response = clean_response[3:]
            
            if clean_response.endswith("```"):
                clean_response = clean_response[:-3]
            
            # Remove any leading/trailing whitespace and newlines
            clean_response = clean_response.strip()
            
            # Try to find JSON object boundaries
            start_idx = clean_response.find('{')
            end_idx = clean_response.rfind('}')
            
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                clean_response = clean_response[start_idx:end_idx + 1]
            
            # Parse JSON response
            ai_data = json.loads(clean_response)
            
            # Validate the response
            recommended_service = ai_data.get("recommended_service", "csv_to_sql_converter")
            
            # Validate service is in allowed list (only CSV services)
            if recommended_service not in ["csv_to_sql_converter", "data_analysis_service"]:
                recommended_service = "csv_to_sql_converter"  # Safe default
            
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
                "recommended_service": "csv_to_sql_converter",
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
        Get a simple service recommendation for CSV data analysis.
        
        Args:
            question: The user's question
            file_id: Optional file ID for context
            data_source: Optional data source hint
            user_preference: Optional user preference ("sql" or "python")
            
        Returns:
            Recommended service name ("csv_to_sql_converter" or "data_analysis_service")
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
    
    async def route_intelligent_multi_file_analysis(
        self, 
        question: str, 
        file_ids: List[str], 
        context: Optional[AnalysisContext] = None,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Intelligently route multi-file CSV analysis requests.
        
        This method:
        1. Analyzes the question to determine if single-file or multi-file analysis is optimal
        2. Selects only necessary files for the analysis
        3. Chooses between SQL and pandas approaches
        4. Provides detailed routing information
        
        Args:
            question: Natural language question
            file_ids: List of available file IDs
            context: Analysis context information
            
        Returns:
            Dictionary containing routing decision and metadata
        """
        try:
            # Generate request_id if not provided
            if not request_id:
                request_id = str(uuid.uuid4())
            
            self.logger.info(f"AI Agent analyzing multi-file question: '{question}' for {len(file_ids)} files (request: {request_id})")
            
            # Get schema information using working memory to prevent duplicates
            from services.csv_schema_analyzer import csv_schema_analyzer
            from core.redis_service import redis_service
            
            # Get user ID from context
            user_id = getattr(context, 'user_id', None) if context else None
            schemas_info = {}
            routing_recommendations = None
            
            # Check working memory first to prevent duplicate schema analysis
            if working_memory_service.has_request_context(request_id, "schema_analysis", file_ids):
                self.logger.info(f"🧠 Using working memory schema analysis for request {request_id}")
                cached_analysis = working_memory_service.get_schema_analysis(request_id, file_ids)
                if cached_analysis:
                    schemas_info = cached_analysis.get("file_schemas", {})
                    routing_recommendations = cached_analysis.get("routing_recommendations")
                    self.logger.info(f"Schema-based routing recommendation: {routing_recommendations['recommended_service']}")
            else:
                # Perform fresh analysis and store in working memory
                self.logger.info(f"🧠 Performing fresh schema analysis for request {request_id}")
                
                if not user_id:
                    self.logger.warning("No user_id in context, using fallback schema analysis")
                    # Fallback to original method
                    from services.data_analysis_service import data_analysis_service
                    for file_id in file_ids:
                        try:
                            schema_info = await data_analysis_service.analyze_data_schema(file_id)
                            schemas_info[file_id] = schema_info
                        except Exception as e:
                            self.logger.warning(f"Could not get schema for file {file_id}: {e}")
                else:
                    # Check long-term cache first
                    cached_analysis = self._get_cached_schema_analysis(file_ids, user_id)
                    
                    if cached_analysis:
                        # Use cached results
                        schemas_info = cached_analysis.get("file_schemas", {})
                        routing_recommendations = cached_analysis.get("routing_recommendations")
                        self.logger.info(f"Using long-term cached schema analysis for {len(file_ids)} files")
                    else:
                        # Perform fresh analysis and cache results
                        self.logger.info(f"Analyzing cached CSV schemas for user {user_id}")
                        schema_analysis = csv_schema_analyzer.analyze_multiple_files(file_ids, user_id)
                        schemas_info = schema_analysis.get("file_schemas", {})
                        
                        # Get AI routing recommendations based on schema (reuse the analysis)
                        routing_recommendations = csv_schema_analyzer.get_ai_routing_recommendation_from_analysis(
                            schema_analysis, question
                        )
                        
                        # Cache the results in long-term cache
                        cache_data = {
                            "file_schemas": schemas_info,
                            "routing_recommendations": routing_recommendations,
                            "schema_analysis": schema_analysis
                        }
                        self._cache_schema_analysis(file_ids, user_id, cache_data)
                
                # Store in working memory to prevent duplicates within this request
                working_memory_data = {
                    "file_schemas": schemas_info,
                    "routing_recommendations": routing_recommendations,
                    "analysis_timestamp": time.time()
                }
                working_memory_service.store_schema_analysis(request_id, file_ids, working_memory_data)
                
                if routing_recommendations:
                    self.logger.info(f"Schema-based routing recommendation: {routing_recommendations['recommended_service']}")
            
            # Initialize trace_obj outside the context manager to prevent generator issues
            trace_obj = None
            try:
                # Prepare sanitized metadata for LangSmith using working memory
                metadata_key = f"trace_metadata_{request_id}"
                sanitized_metadata = {
                    "endpoint": "ai_multi_file_routing",
                    "question_length": len(question),
                    "file_count": len(file_ids),
                    "has_context": bool(context),
                    "user_preference": str(context.user_preference) if context and context.user_preference else None,
                    "schema_files_analyzed": len(schemas_info),
                    "schema_recommendation": str(routing_recommendations['recommended_service']) if routing_recommendations else 'none',
                    "request_id": str(request_id),
                    "timestamp": str(time.time())
                }
                
                # Store sanitized metadata in working memory
                working_memory_service.store_langsmith_metadata(request_id, metadata_key, sanitized_metadata)
                
                with langsmith_service.create_trace("ai_multi_file_routing") as trace:
                    trace_obj = trace
                    # Use sanitized metadata from working memory
                    trace_obj.metadata = sanitized_metadata
                    
                    # Build enhanced prompt for multi-file analysis with schema information
                    prompt = self._build_multi_file_routing_prompt(question, file_ids, schemas_info, context)
                    
                    # Get AI recommendation with timeout
                    try:
                        response = await self.llm.ainvoke(prompt)
                        
                        # Clean and parse AI response
                        response_content = response.content.strip()
                        self.logger.info(f"Raw AI response: {response_content[:200]}...")
                        
                        # Try to parse JSON response
                        try:
                            result = json.loads(response_content)
                        except json.JSONDecodeError as e:
                            self.logger.error(f"Failed to parse AI response as JSON: {e}")
                            self.logger.error(f"Response content: {response_content}")
                            raise ValueError(f"AI response is not valid JSON: {str(e)}")
                            
                    except Exception as ai_error:
                        self.logger.warning(f"AI LLM call failed: {ai_error}")
                        # Use schema-based recommendation as fallback
                        if routing_recommendations:
                            result = {
                                "required_files": file_ids,
                                "recommended_service": routing_recommendations['recommended_service'],
                                "analysis_type": "pandas" if routing_recommendations['recommended_service'] == "data_analysis_service" else "sql",
                                "reasoning": f"AI LLM failed, using schema-based recommendation: {routing_recommendations['reasoning']}",
                                "confidence": routing_recommendations['confidence'] * 0.8,  # Slightly lower confidence
                                "join_strategy": "none",
                                "optimization_applied": False,
                                "ai_analysis": "schema_based_fallback"
                            }
                        else:
                            raise ai_error
                    
                    # Validate result and fix placeholder file IDs
                    required_files = result.get('required_files', [])
                    
                    # Check if AI returned placeholder file IDs
                    if not required_files or any(f.startswith('file_id') for f in required_files):
                        self.logger.warning(f"AI returned placeholder file IDs: {required_files}, using all available files")
                        required_files = file_ids
                    
                    # Ensure all required files are actually available
                    result['required_files'] = [
                        f for f in required_files 
                        if f in file_ids
                    ]
                    
                    # Final validation - ensure we have at least one file
                    if not result['required_files']:
                        self.logger.warning("No valid files selected, using first available file")
                        result['required_files'] = file_ids[:1]
                    
                    # Add metadata
                    langsmith_service.add_metadata(trace_obj, {
                        "recommended_service": result.get('recommended_service', 'data_analysis_service'),
                        "confidence": result.get('confidence', 0.5),
                        "files_analyzed": len(file_ids),
                        "files_used": len(result['required_files']),
                        "optimization_applied": len(result['required_files']) < len(file_ids),
                        "analysis_type": result.get('analysis_type', 'pandas'),
                        "ai_analysis": result.get('ai_analysis', 'unknown'),
                        "success": True
                    })
                    
                    self.logger.info(f"AI Agent multi-file recommendation: {result['recommended_service']} using {len(result['required_files'])} files")
                    langsmith_service.log_trace_event("ai_multi_file_routing_decision", 
                        f"Successfully routed to {result['recommended_service']} using {len(result['required_files'])} files")
                    
                    return result
                    
            except Exception as trace_error:
                self.logger.warning(f"LangSmith trace creation failed: {trace_error}")
                # Create a dummy trace object to continue processing
                class DummyTrace:
                    def __init__(self):
                        self.metadata = {}
                trace_obj = DummyTrace()
                
                # Continue with the same logic but without LangSmith tracing
                # Schema analysis already done above, no need to repeat
                
                # Build enhanced prompt for multi-file analysis with schema information
                prompt = self._build_multi_file_routing_prompt(question, file_ids, schemas_info, context)
                
                # Get AI recommendation with timeout
                try:
                    response = await self.llm.ainvoke(prompt)
                    
                    # Clean and parse AI response
                    response_content = response.content.strip()
                    self.logger.info(f"Raw AI response: {response_content[:200]}...")
                    
                    # Try to parse JSON response
                    try:
                        result = json.loads(response_content)
                    except json.JSONDecodeError as e:
                        self.logger.error(f"Failed to parse AI response as JSON: {e}")
                        self.logger.error(f"Response content: {response_content}")
                        raise ValueError(f"AI response is not valid JSON: {str(e)}")
                        
                except Exception as ai_error:
                    self.logger.warning(f"AI LLM call failed: {ai_error}")
                    # Use schema-based recommendation as fallback
                    if routing_recommendations:
                        result = {
                            "required_files": file_ids,
                            "recommended_service": routing_recommendations['recommended_service'],
                            "analysis_type": "pandas" if routing_recommendations['recommended_service'] == "data_analysis_service" else "sql",
                            "reasoning": f"AI LLM failed, using schema-based recommendation: {routing_recommendations['reasoning']}",
                            "confidence": routing_recommendations['confidence'] * 0.8,  # Slightly lower confidence
                            "join_strategy": "none",
                            "optimization_applied": False,
                            "ai_analysis": "schema_based_fallback"
                        }
                    else:
                        raise ai_error
                
                # Validate result and fix placeholder file IDs
                required_files = result.get('required_files', [])
                
                # Check if AI returned placeholder file IDs
                if not required_files or any(f.startswith('file_id') for f in required_files):
                    self.logger.warning(f"AI returned placeholder file IDs: {required_files}, using all available files")
                    required_files = file_ids
                
                # Ensure all required files are actually available
                result['required_files'] = [
                    f for f in required_files 
                    if f in file_ids
                ]
                
                # Final validation - ensure we have at least one file
                if not result['required_files']:
                    self.logger.warning("No valid files selected, using first available file")
                    result['required_files'] = file_ids[:1]
                
                # Add metadata (without LangSmith)
                trace_obj.metadata = {
                    "recommended_service": result.get('recommended_service', 'data_analysis_service'),
                    "confidence": result.get('confidence', 0.5),
                    "files_analyzed": len(file_ids),
                    "files_used": len(result['required_files']),
                    "optimization_applied": len(result['required_files']) < len(file_ids),
                    "analysis_type": result.get('analysis_type', 'pandas'),
                    "ai_analysis": result.get('ai_analysis', 'unknown'),
                    "success": True
                }
                
                self.logger.info(f"AI Agent multi-file recommendation: {result['recommended_service']} using {len(result['required_files'])} files")
                langsmith_service.log_trace_event("ai_multi_file_routing_decision", 
                    f"Successfully routed to {result['recommended_service']} using {len(result['required_files'])} files")
                
                return result
                
        except Exception as e:
            self.logger.error(f"Error in AI multi-file routing: {e}")
            
            # Proper cleanup of any partial state
            try:
                # Clean up any partial analysis state
                if hasattr(self, '_current_analysis'):
                    delattr(self, '_current_analysis')
            except Exception as cleanup_error:
                self.logger.warning(f"Error during cleanup: {cleanup_error}")
            
            # Smart fallback for multi-file analysis based on question type
            question_lower = question.lower()
            
            # Analyze question to determine best fallback service
            if any(keyword in question_lower for keyword in ['count', 'total', 'number', 'how many']):
                # Counting questions - prefer SQL for efficiency
                fallback_service = "csv_to_sql_converter"
                fallback_reasoning = "Counting question detected, using SQL service for efficiency"
                confidence = 0.6
            elif any(keyword in question_lower for keyword in ['correlation', 'trend', 'analysis', 'statistical', 'regression']):
                # Complex analysis - prefer pandas
                fallback_service = "data_analysis_service"
                fallback_reasoning = "Complex analysis detected, using pandas service"
                confidence = 0.7
            else:
                # Default to pandas for multi-file scenarios
                fallback_service = "data_analysis_service"
                fallback_reasoning = "Multi-file analysis detected, using pandas service"
                confidence = 0.5
            
            # Use all files for fallback to ensure we don't miss data
            fallback_files = file_ids
            
            self.logger.info(f"AI routing fallback: {fallback_service} with {len(fallback_files)} files")
            
            return {
                "recommended_service": fallback_service,
                "required_files": fallback_files,
                "reasoning": f"AI routing failed: {str(e)}. {fallback_reasoning}.",
                "confidence": confidence,
                "ai_analysis": "Fallback analysis due to routing error",
                "analysis_type": "pandas" if fallback_service == "data_analysis_service" else "sql",
                "context": {
                    "question": question,
                    "file_count": len(file_ids),
                    "data_source": context.data_source if context else None,
                    "fallback_reason": str(e)
                }
            }
    
    def _build_multi_file_routing_prompt(self, question: str, file_ids: List[str], schemas_info: Dict[str, Any], context: Optional[AnalysisContext]) -> str:
        """Build the AI prompt for multi-file routing decisions with schema information."""
        
        context_info = ""
        if context:
            context_info = f"""
CONTEXT INFORMATION:
- File Size: {context.file_size or 'Unknown'}
- File Type: {context.file_type or 'CSV'}
- Data Source: {context.data_source or 'CSV files'}
- User Preference: {context.user_preference or 'None specified'}
"""
        
        # Format schema information for AI (handle both schema formats)
        schema_text = ""
        for file_id, schema in schemas_info.items():
            schema_text += f"\nFILE: {file_id}\n"
            
            # Handle both schema formats: CSV schema analyzer vs data analysis service
            if 'file_info' in schema:
                # Data analysis service format
                row_count = schema['file_info']['row_count']
                col_count = schema['file_info']['column_count']
                columns = schema["columns"]
            else:
                # CSV schema analyzer format
                row_count = schema.get('total_rows', 0)
                col_count = schema.get('total_columns', 0)
                columns = schema.get("columns", [])
            
            schema_text += f"Rows: {row_count}, Columns: {col_count}\n"
            schema_text += "Columns:\n"
            
            for col in columns:
                # Handle different column formats
                col_name = col.get('name', 'unknown')
                col_type = col.get('type', col.get('data_type', 'unknown'))
                sample_values = col.get('sample_values', col.get('sample_data', []))
                null_count = col.get('null_count', 0)
                unique_count = col.get('unique_count', 0)
                
                schema_text += f"  - {col_name} ({col_type}): "
                schema_text += f"Sample: {sample_values[:3]}, "
                schema_text += f"Nulls: {null_count}, "
                schema_text += f"Unique: {unique_count}\n"
            
            schema_text += "\n"
        
        return f"""You are an expert data analyst who determines the optimal approach for analyzing multiple CSV files.

QUESTION: {question}

AVAILABLE FILES AND THEIR SCHEMAS:
{schema_text}

{context_info}

ANALYSIS REQUIREMENTS:
1. Determine if this question can be answered with a single file or requires multiple files
2. Identify which specific files are needed (if not all)
3. Decide between SQL analysis (csv_to_sql_converter) or pandas analysis (data_analysis_service)
4. Consider data relationships and JOIN requirements

DECISION CRITERIA:
- Single file sufficient: Questions about one dataset (e.g., "What's the total sales?", "Show me top products")
- Multiple files needed: Questions requiring data from multiple sources (e.g., "Compare sales between regions", "Customer lifetime value by segment")
- SQL approach: Structured queries, aggregations, JOINs, filtering
- Pandas approach: Complex data manipulation, statistical analysis, custom transformations

OPTIMIZATION GOALS:
- Use only necessary files to minimize memory usage
- Choose the most efficient analysis approach
- Consider user preferences when applicable

IMPORTANT: You must analyze the question carefully and select ONLY the files that are actually needed to answer the question. Do not select all files unless the question explicitly requires data from all of them.

RESPONSE FORMAT (JSON):
{{
    "required_files": ["ACTUAL_FILE_ID_1", "ACTUAL_FILE_ID_2"],
    "recommended_service": "csv_to_sql_converter" or "data_analysis_service",
    "analysis_type": "sql" or "pandas",
    "reasoning": "Detailed explanation of decision",
    "confidence": 0.0-1.0,
    "join_strategy": "inner" or "left" or "right" or "full" or "none",
    "optimization_applied": true/false,
    "ai_analysis": "Brief analysis summary"
}}

CRITICAL REQUIREMENTS:
1. Use ONLY the actual file IDs provided above (e.g., "997ff849-fec3-4f20-bec9-56079818d9a6")
2. Do NOT use placeholder values like "file_id1" or "file_id2"
3. Return ONLY the JSON object above, without any markdown formatting, code blocks, or additional text
4. Do not wrap in ```json``` or any other formatting"""

# Global instance
ai_routing_agent = AIRoutingAgent()