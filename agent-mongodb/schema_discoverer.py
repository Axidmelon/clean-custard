# File: agent-mongodb/schema_discoverer.py

import os
import pymongo
from pymongo import MongoClient
from dotenv import load_dotenv
from typing import Dict, Any, List, Optional
import json
from bson import ObjectId


class MongoSchemaDiscoverer:
    """
    A tool to connect to a MongoDB database and discover its schema.
    """

    def __init__(self, connection_string: str, database_name: str, collection_filter: Optional[List[str]] = None):
        """Initializes the discoverer with MongoDB connection details."""
        self.connection_string = connection_string
        self.database_name = database_name
        self.collection_filter = collection_filter

    def _is_safe_query(self, query: Dict[str, Any]) -> bool:
        """
        Check if a MongoDB query is safe and read-only.
        
        Args:
            query: MongoDB query dictionary
            
        Returns:
            True if query is safe and read-only, False otherwise
        """
        # Block dangerous operations
        dangerous_operations = [
            'insert', 'update', 'delete', 'remove', 'drop', 'createIndex',
            'dropIndex', 'createCollection', 'dropCollection', 'renameCollection'
        ]
        
        # Check if query contains any dangerous operations
        query_str = str(query).lower()
        for operation in dangerous_operations:
            if operation in query_str:
                return False
                
        return True

    def _get_collection_schema(self, collection_name: str, sample_size: int = 100) -> Dict[str, Any]:
        """
        Analyze a collection to determine its schema by sampling documents.
        
        Args:
            collection_name: Name of the collection to analyze
            sample_size: Number of documents to sample for schema analysis
            
        Returns:
            Dictionary containing schema information for the collection
        """
        try:
            client = MongoClient(self.connection_string)
            db = client[self.database_name]
            collection = db[collection_name]
            
            # Get collection stats
            stats = db.command("collStats", collection_name)
            
            # Sample documents to determine schema
            sample_docs = list(collection.aggregate([
                {"$sample": {"size": sample_size}}
            ]))
            
            # Analyze field types and structure
            field_types = {}
            field_examples = {}
            
            for doc in sample_docs:
                self._analyze_document(doc, field_types, field_examples)
            
            # Get index information
            indexes = list(collection.list_indexes())
            index_info = []
            for idx in indexes:
                index_info.append({
                    "name": idx.get("name", "unknown"),
                    "keys": idx.get("key", {}),
                    "unique": idx.get("unique", False),
                    "sparse": idx.get("sparse", False)
                })
            
            return {
                "name": collection_name,
                "document_count": stats.get("count", 0),
                "size_bytes": stats.get("size", 0),
                "avg_document_size": stats.get("avgObjSize", 0),
                "indexes": index_info,
                "fields": field_types,
                "field_examples": field_examples,
                "sample_documents": sample_docs[:5]  # Include a few sample documents
            }
            
        except Exception as e:
            print(f"ERROR: Could not analyze collection {collection_name}. {e}")
            return {
                "name": collection_name,
                "error": str(e),
                "fields": {},
                "indexes": []
            }

    def _analyze_document(self, doc: Dict[str, Any], field_types: Dict[str, Any], field_examples: Dict[str, Any], prefix: str = ""):
        """
        Recursively analyze a document to determine field types and examples.
        
        Args:
            doc: Document to analyze
            field_types: Dictionary to store field type information
            field_examples: Dictionary to store field examples
            prefix: Current field path prefix
        """
        for key, value in doc.items():
            field_path = f"{prefix}.{key}" if prefix else key
            
            # Determine field type
            if isinstance(value, bool):
                field_type = "boolean"
            elif isinstance(value, int):
                field_type = "integer"
            elif isinstance(value, float):
                field_type = "double"
            elif isinstance(value, str):
                field_type = "string"
            elif isinstance(value, ObjectId):
                field_type = "objectId"
            elif isinstance(value, list):
                field_type = "array"
                # Analyze array elements
                if value and isinstance(value[0], dict):
                    field_type = "array<object>"
            elif isinstance(value, dict):
                field_type = "object"
                # Recursively analyze nested object
                self._analyze_document(value, field_types, field_examples, field_path)
            else:
                field_type = "unknown"
            
            # Store field type information
            if field_path not in field_types:
                field_types[field_path] = {
                    "type": field_type,
                    "count": 0,
                    "nullable": True
                }
            
            field_types[field_path]["count"] += 1
            if value is not None:
                field_types[field_path]["nullable"] = False
            
            # Store field examples (limit to 3 examples per field)
            if field_path not in field_examples:
                field_examples[field_path] = []
            
            if len(field_examples[field_path]) < 3:
                # Convert ObjectId to string for JSON serialization
                if isinstance(value, ObjectId):
                    field_examples[field_path].append(str(value))
                else:
                    field_examples[field_path].append(value)

    def discover_schema(self) -> Dict[str, Any]:
        """
        Connect to the database and return a structured dictionary of the schema.
        
        Returns:
            Dictionary containing database schema information
        """
        try:
            print("Connecting to MongoDB to discover schema...")
            client = MongoClient(self.connection_string)
            db = client[self.database_name]
            
            # Get list of collections
            collection_names = db.list_collection_names()
            
            # Apply collection filter if specified
            if self.collection_filter:
                collection_names = [name for name in collection_names if name in self.collection_filter]
            
            print(f"Found {len(collection_names)} collections: {collection_names}")
            
            # Analyze each collection
            collections = {}
            for collection_name in collection_names:
                print(f"Analyzing collection: {collection_name}")
                collections[collection_name] = self._get_collection_schema(collection_name)
            
            # Get database stats
            db_stats = db.command("dbStats")
            
            schema = {
                "database_name": self.database_name,
                "collections": collections,
                "database_stats": {
                    "collections": db_stats.get("collections", 0),
                    "data_size": db_stats.get("dataSize", 0),
                    "storage_size": db_stats.get("storageSize", 0),
                    "indexes": db_stats.get("indexes", 0),
                    "index_size": db_stats.get("indexSize", 0)
                }
            }
            
            print("Successfully discovered MongoDB schema.")
            return schema
            
        except Exception as e:
            print(f"ERROR: Could not connect to MongoDB. {e}")
            raise ConnectionError(f"Could not connect to MongoDB: {e}")

    def discover_schema_with_connection(self, client) -> Dict[str, Any]:
        """
        Uses an existing MongoDB connection to discover schema.
        
        Args:
            client: Existing MongoDB client connection
            
        Returns:
            Dictionary containing database schema information
        """
        try:
            print("Discovering schema using existing MongoDB connection...")
            db = client[self.database_name]
            
            # Get list of collections
            collection_names = db.list_collection_names()
            
            # Apply collection filter if specified
            if self.collection_filter:
                collection_names = [name for name in collection_names if name in self.collection_filter]
            
            print(f"Found {len(collection_names)} collections: {collection_names}")
            
            # Analyze each collection
            collections = {}
            for collection_name in collection_names:
                print(f"Analyzing collection: {collection_name}")
                collections[collection_name] = self._get_collection_schema(collection_name)
            
            # Get database stats
            db_stats = db.command("dbStats")
            
            schema = {
                "database_name": self.database_name,
                "collections": collections,
                "database_stats": {
                    "collections": db_stats.get("collections", 0),
                    "data_size": db_stats.get("dataSize", 0),
                    "storage_size": db_stats.get("storageSize", 0),
                    "indexes": db_stats.get("indexes", 0),
                    "index_size": db_stats.get("indexSize", 0)
                }
            }
            
            print("Successfully discovered MongoDB schema.")
            return schema
            
        except Exception as e:
            print(f"ERROR: Could not discover MongoDB schema. {e}")
            raise ConnectionError(f"Could not discover MongoDB schema: {e}")


# --- This block is for direct testing of this file ---
if __name__ == '__main__':
    load_dotenv()

    # Get configuration from environment variables
    connection_string = os.getenv("MONGODB_CONNECTION_STRING")
    database_name = os.getenv("MONGODB_DATABASE_NAME")
    collection_filter = os.getenv("MONGODB_COLLECTION_FILTER")
    
    if collection_filter:
        collection_filter = [name.strip() for name in collection_filter.split(",")]

    if not connection_string or not database_name:
        print("ERROR: MONGODB_CONNECTION_STRING and MONGODB_DATABASE_NAME must be set")
        exit(1)

    discoverer = MongoSchemaDiscoverer(
        connection_string=connection_string,
        database_name=database_name,
        collection_filter=collection_filter
    )
    
    schema_dict = discoverer.discover_schema()
    print("\n--- DISCOVERED MONGODB SCHEMA (JSON) ---")
    print(json.dumps(schema_dict, indent=2, default=str))
