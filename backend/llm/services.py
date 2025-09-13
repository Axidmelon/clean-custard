# llm/services.py

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from core.config import settings
from core.langsmith_service import langsmith_service
from typing import Any, Union
import logging

logger = logging.getLogger(__name__)


class ResultFormatter:
    """
    Utility class for detecting and formatting different result types.
    Handles both string and numeric results with appropriate formatting.
    """
    
    @staticmethod
    def detect_result_type(result_value: Any) -> str:
        """
        Detect the type of result value.
        
        Args:
            result_value: The result value to analyze
            
        Returns:
            String indicating the type: 'number', 'string', 'list', 'other'
        """
        if isinstance(result_value, (int, float)):
            return "number"
        elif isinstance(result_value, str):
            return "string"
        elif isinstance(result_value, list):
            return "list"
        else:
            return "other"
    
    @staticmethod
    def format_result_by_type(result_value: Any, question: str) -> str:
        """
        Format result value based on its type and question context.
        
        Args:
            result_value: The result value to format
            question: The original user question for context
            
        Returns:
            Formatted string representation of the result
        """
        result_type = ResultFormatter.detect_result_type(result_value)
        question_lower = question.lower()
        
        if result_type == "number":
            return ResultFormatter._format_number(result_value, question_lower)
        elif result_type == "string":
            return ResultFormatter._format_string(result_value, question_lower)
        elif result_type == "list":
            return ResultFormatter._format_list(result_value, question_lower)
        else:
            return str(result_value)
    
    @staticmethod
    def _format_number(value: Union[int, float], question_lower: str) -> str:
        """Format numeric values with appropriate formatting."""
        if isinstance(value, float):
            if "revenue" in question_lower or "total" in question_lower:
                return f"${value:,.2f}"
            elif "average" in question_lower or "mean" in question_lower:
                return f"${value:.2f}"
            else:
                return f"{value:.2f}"
        else:  # integer
            if "revenue" in question_lower or "total" in question_lower:
                return f"${value:,}"
            elif "count" in question_lower or "number" in question_lower:
                return f"{value:,}"
            else:
                return f"{value:,}"
    
    @staticmethod
    def _format_string(value: str, question_lower: str) -> str:
        """Format string values with appropriate context."""
        # Clean up the string value
        cleaned_value = value.strip()
        
        # Return clean string without quotes for natural language responses
        return cleaned_value
    
    @staticmethod
    def _format_list(value: list, question_lower: str) -> str:
        """Format list values with appropriate context."""
        if len(value) <= 3:
            return f"[{', '.join(map(str, value))}]"
        else:
            return f"[{', '.join(map(str, value[:3]))}, ...] ({len(value)} total)"
    
    @staticmethod
    def generate_contextual_response(question: str, result_value: Any) -> str:
        """
        Generate a contextual response based on question and result type.
        
        Args:
            question: The original user question
            result_value: The result value
            
        Returns:
            Natural language response
        """
        formatted_value = ResultFormatter.format_result_by_type(result_value, question)
        question_lower = question.lower()
        
        # Generate contextual responses based on question patterns
        if "revenue" in question_lower and ("total" in question_lower or "sum" in question_lower):
            return f"The total revenue is {formatted_value}"
        elif "average" in question_lower or "mean" in question_lower:
            return f"The average value is {formatted_value}"
        elif "how many" in question_lower or ("count" in question_lower and "number" in question_lower):
            return f"The count is {formatted_value}"
        elif "which state" in question_lower or "which country" in question_lower:
            return f"The state with the highest consumers is {formatted_value}"
        elif "which product" in question_lower:
            return f"The product with the highest sales is {formatted_value}"
        elif "which customer" in question_lower or "which user" in question_lower:
            return f"The customer with the most orders is {formatted_value}"
        elif "top" in question_lower and "product" in question_lower:
            return f"Here are the top products: {formatted_value}"
        elif "top" in question_lower:
            return f"Here are the top results: {formatted_value}"
        else:
            return f"The result is {formatted_value}"


# We are creating a 'class' here. Think of it as a blueprint
# for a specialized "Text-to-SQL Converter" tool.
class TextToSQLService:
    """
    A service that uses an LLM to convert natural language questions into SQL queries.
    """

    def __init__(self):
        """
        This is the constructor. It runs when we first create an instance of our service.
        It sets up the AI model and the prompt template, so we don't have to do it every time.
        """
        logger.info("Initializing TextToSQLService...")

        # 1. Define the AI Model with LangSmith tracing
        # This is the same as before. We're setting up our "brain".
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=settings.openai_temperature,
            max_tokens=settings.openai_max_tokens,
            callbacks=[langsmith_service.get_tracer()] if langsmith_service.is_enabled else None
        )

        # 2. Define the Prompt Template
        # This is our detailed instruction manual for the AI.
        prompt_template = """
You are an expert, world-class PostgreSQL query writer.
Your job is to take a user's question and a database schema, and write a perfect,
syntactically correct PostgreSQL query to answer the question.

RULES:
- You MUST only respond with the SQL query itself. Do not add any extra text,
  explanations, or markdown formatting like ```sql. Just the query.
- Always use the table and column names exactly as they are provided in the schema.
- If a question is not related to the database, inform the user that the question is not related to the database.

Here is the database schema:
{schema}

Here is the user's question:
{question}

SQL Query:
"""
        self.prompt = ChatPromptTemplate.from_template(prompt_template)

        # 3. Create the LangChain "Chain"
        # We pre-build the chain that connects the prompt and the LLM.
        self.chain = self.prompt | self.llm
        logger.info("TextToSQLService initialized successfully.")

    def generate_sql(self, question: str, schema: str) -> str:
        """
        Takes a user's question and a database schema, and returns a SQL query.

        Args:
            question: The user's question in plain English.
            schema: A string representation of the database schema.

        Returns:
            A string containing the generated SQL query.
        """
        logger.info(f"Generating SQL for question: '{question}'")

        with langsmith_service.create_trace("sql_generation") as trace_obj:
            # Add initial metadata
            trace_obj.metadata = {
                "question_type": "sql_generation",
                "schema_complexity": len(schema),
                "question_length": len(question),
                "model": settings.openai_model,
                "temperature": settings.openai_temperature
            }

            try:
                # We "invoke" the chain, passing in the specific data for this request.
                # The .content attribute contains the AI's final text response.
                response = self.chain.invoke({"schema": schema, "question": question})

                generated_sql = response.content
                
                # Add success metadata
                langsmith_service.add_metadata(trace_obj, {
                    "sql_length": len(generated_sql),
                    "success": True,
                    "response_time_ms": "calculated_by_langsmith"
                })
                
                logger.info(f"Generated SQL: {generated_sql}")
                langsmith_service.log_trace_event("sql_generation", f"Successfully generated SQL for question: {question[:100]}...")
                
                return generated_sql
                
            except Exception as e:
                # Add error metadata
                langsmith_service.add_metadata(trace_obj, {
                    "success": False,
                    "error": str(e),
                    "error_type": type(e).__name__
                })
                
                logger.error(f"Error generating SQL: {e}")
                langsmith_service.log_trace_event("sql_generation_error", f"Failed to generate SQL: {str(e)}")
                raise
    
    def generate_natural_response(self, question: str, sql_query: str, query_result: list) -> str:
        """
        Generate a natural language response from the SQL query result.
        
        Args:
            question: The original user question
            sql_query: The SQL query that was executed
            query_result: The result from executing the SQL query
            
        Returns:
            A natural language response explaining the result
        """
        logger.info(f"Generating natural response for question: '{question}'")
        
        with langsmith_service.create_trace("natural_response_generation") as trace_obj:
            # Add initial metadata
            trace_obj.metadata = {
                "question_type": "natural_response",
                "question_length": len(question),
                "sql_query_length": len(sql_query),
                "result_type": type(query_result).__name__,
                "result_size": len(query_result) if query_result else 0,
                "model": settings.openai_model
            }

            try:
                # Handle empty results
                if not query_result or not query_result[0]:
                    langsmith_service.add_metadata(trace_obj, {
                        "response_type": "empty_result",
                        "success": True
                    })
                    return "The query returned no results."
                
                # Extract the result value
                result_value = query_result[0][0]
                
                # Use ResultFormatter for type-safe formatting
                try:
                    # First try using the ResultFormatter for immediate contextual response
                    contextual_response = ResultFormatter.generate_contextual_response(question, result_value)
                    
                    # If we have a simple single-value result, use the contextual response
                    if len(query_result) == 1 and len(query_result[0]) == 1:
                        langsmith_service.add_metadata(trace_obj, {
                            "response_type": "contextual_formatter",
                            "result_value_type": ResultFormatter.detect_result_type(result_value),
                            "success": True
                        })
                        logger.info(f"Generated contextual response: {contextual_response}")
                        return contextual_response
                    
                    # For complex results, use LLM with proper formatting
                    formatted_value = ResultFormatter.format_result_by_type(result_value, question)
                    
                    response_prompt = f"""
You are an expert data analyst who explains query results in natural, conversational language.

User's Question: {question}
SQL Query Executed: {sql_query}
Query Result: {formatted_value}
Result Type: {ResultFormatter.detect_result_type(result_value)}

Generate a natural, contextual response that directly answers the user's question using the result.
Make it sound conversational and informative.

Examples:
- "What is the total revenue?" with result $1,234,567 → "The total revenue is $1,234,567"
- "How many customers do we have?" with result 42 → "We have 42 customers"
- "What's the average order value?" with result $99.99 → "The average order value is $99.99"
- "Which state has the highest consumers?" with result "California" → "The state with the highest consumers is California"

Response:"""
                    
                    # Use the LLM to generate a natural response
                    response = self.llm.invoke(response_prompt)
                    natural_response = response.content.strip()
                    
                    # Add success metadata
                    langsmith_service.add_metadata(trace_obj, {
                        "response_type": "llm_generated",
                        "response_length": len(natural_response),
                        "result_value_type": ResultFormatter.detect_result_type(result_value),
                        "success": True
                    })
                    
                    logger.info(f"Generated natural response: {natural_response}")
                    langsmith_service.log_trace_event("natural_response_generation", f"Successfully generated natural response for question: {question[:100]}...")
                    
                    return natural_response
                    
                except Exception as e:
                    logger.error(f"Error generating natural response: {e}")
                    # Fallback to contextual response
                    try:
                        fallback_response = ResultFormatter.generate_contextual_response(question, result_value)
                        langsmith_service.add_metadata(trace_obj, {
                            "response_type": "fallback_contextual",
                            "success": True,
                            "fallback_reason": str(e)
                        })
                        return fallback_response
                    except Exception as fallback_error:
                        logger.error(f"Fallback error: {fallback_error}")
                        langsmith_service.add_metadata(trace_obj, {
                            "response_type": "simple_fallback",
                            "success": True,
                            "fallback_reason": f"LLM error: {str(e)}, Formatter error: {str(fallback_error)}"
                        })
                        return f"The result is: {result_value}"
                        
            except Exception as e:
                # Add error metadata
                langsmith_service.add_metadata(trace_obj, {
                    "success": False,
                    "error": str(e),
                    "error_type": type(e).__name__
                })
                
                logger.error(f"Error in natural response generation: {e}")
                langsmith_service.log_trace_event("natural_response_error", f"Failed to generate natural response: {str(e)}")
                raise