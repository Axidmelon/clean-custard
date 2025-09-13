# llm/services.py

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from core.config import settings
from typing import Any, Union


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
        print("Initializing TextToSQLService...")

        # 1. Define the AI Model
        # This is the same as before. We're setting up our "brain".
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=settings.openai_temperature,
            max_tokens=settings.openai_max_tokens
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
        print("TextToSQLService initialized successfully.")

    def generate_sql(self, question: str, schema: str) -> str:
        """
        Takes a user's question and a database schema, and returns a SQL query.

        Args:
            question: The user's question in plain English.
            schema: A string representation of the database schema.

        Returns:
            A string containing the generated SQL query.
        """
        print(f"Generating SQL for question: '{question}'")

        # We "invoke" the chain, passing in the specific data for this request.
        # The .content attribute contains the AI's final text response.
        response = self.chain.invoke({"schema": schema, "question": question})

        generated_sql = response.content
        print(f"Generated SQL: {generated_sql}")

        return generated_sql
    
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
        print(f"Generating natural response for question: '{question}'")
        
        # Handle empty results
        if not query_result or not query_result[0]:
            return "The query returned no results."
        
        # Extract the result value
        result_value = query_result[0][0]
        
        # Use ResultFormatter for type-safe formatting
        try:
            # First try using the ResultFormatter for immediate contextual response
            contextual_response = ResultFormatter.generate_contextual_response(question, result_value)
            
            # If we have a simple single-value result, use the contextual response
            if len(query_result) == 1 and len(query_result[0]) == 1:
                print(f"Generated contextual response: {contextual_response}")
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
            
            print(f"Generated natural response: {natural_response}")
            return natural_response
            
        except Exception as e:
            print(f"Error generating natural response: {e}")
            # Fallback to contextual response
            try:
                return ResultFormatter.generate_contextual_response(question, result_value)
            except Exception as fallback_error:
                print(f"Fallback error: {fallback_error}")
                return f"The result is: {result_value}"