# llm/mongo_services.py

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate


class TextToMongoService:
    """
    A service that uses an LLM to convert natural language questions into MongoDB queries.
    """

    def __init__(self):
        """
        Initialize the TextToMongoService with LLM and prompt template.
        """
        print("Initializing TextToMongoService...")

        # 1. Define the AI Model
        self.llm = ChatOpenAI(model="gpt-4-turbo", temperature=0)

        # 2. Define the Prompt Template for MongoDB
        prompt_template = """
You are an expert, world-class MongoDB query writer.
Your job is to take a user's question and a MongoDB database schema, and write a perfect,
syntactically correct MongoDB query to answer the question.

RULES:
- You MUST only respond with a valid JSON object containing the MongoDB query.
- Do not add any extra text, explanations, or markdown formatting.
- The response must be a valid JSON object that can be parsed directly.
- Use the collection and field names exactly as they are provided in the schema.
- For queries that need to find documents, use the "find" operation.
- For aggregation queries, use the "aggregate" operation.
- For counting documents, use the "count" operation.
- For getting distinct values, use the "distinct" operation.

QUERY FORMATS:
- Find query: {{"find": {{"field": "value"}}, "projection": {{"field1": 1, "field2": 1}}, "limit": 10, "sort": {{"field": -1}}}}
- Aggregation: {{"aggregate": [{{"$match": {{"field": "value"}}}}, {{"$group": {{"_id": "$field", "count": {{"$sum": 1}}}}}}]}}
- Count: {{"count": {{"field": "value"}}}}
- Distinct: {{"distinct": "field", "query": {{"field": "value"}}}}

Here is the MongoDB database schema:
{schema}

Here is the user's question:
{question}

MongoDB Query (JSON):
"""
        self.prompt = ChatPromptTemplate.from_template(prompt_template)

        # 3. Create the LangChain "Chain"
        self.chain = self.prompt | self.llm
        print("TextToMongoService initialized successfully.")

    def generate_mongo_query(self, question: str, schema: str, collection_name: str = None) -> dict:
        """
        Takes a user's question and a MongoDB schema, and returns a MongoDB query.

        Args:
            question: The user's question in plain English.
            schema: A string representation of the MongoDB database schema.
            collection_name: Optional collection name to target.

        Returns:
            A dictionary containing the generated MongoDB query.
        """
        print(f"Generating MongoDB query for question: '{question}'")

        # We "invoke" the chain, passing in the specific data for this request.
        response = self.chain.invoke({"schema": schema, "question": question})

        generated_query = response.content.strip()
        print(f"Generated MongoDB query: {generated_query}")

        try:
            import json
            query_dict = json.loads(generated_query)
            
            # If collection_name is provided and not in the query, add it
            if collection_name and "collection_name" not in query_dict:
                query_dict["collection_name"] = collection_name
                
            return query_dict
        except json.JSONDecodeError as e:
            print(f"Failed to parse generated query as JSON: {e}")
            # Fallback: create a simple find query
            return {
                "find": {},
                "collection_name": collection_name or "unknown"
            }

    def suggest_collection(self, question: str, schema: str) -> str:
        """
        Suggest the most appropriate collection for a given question.

        Args:
            question: The user's question in plain English.
            schema: A string representation of the MongoDB database schema.

        Returns:
            The suggested collection name.
        """
        print(f"Suggesting collection for question: '{question}'")

        # Simple collection suggestion based on question keywords
        # This could be enhanced with more sophisticated logic
        question_lower = question.lower()
        
        # Extract collection names from schema
        import json
        try:
            schema_dict = json.loads(schema)
            collections = list(schema_dict.get("collections", {}).keys())
            
            # Simple keyword matching
            for collection in collections:
                if any(keyword in question_lower for keyword in collection.lower().split('_')):
                    return collection
                    
            # If no match, return the first collection
            return collections[0] if collections else "unknown"
            
        except (json.JSONDecodeError, KeyError):
            return "unknown"
