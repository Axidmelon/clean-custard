# llm/services.py

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate


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
        self.llm = ChatOpenAI(model="gpt-4-turbo", temperature=0)

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
