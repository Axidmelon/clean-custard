# File: agent/schema_discoverer.py

import os
import psycopg2
from dotenv import load_dotenv
from typing import Dict, Any


class SchemaDiscoverer:
    """
    A tool to connect to a PostgreSQL database and discover its schema.
    """

    def __init__(self, host, port, dbname, user, password,
                 schema_name="public", table_filter=None):
        """Initializes the discoverer with database connection details."""
        self.db_params = {
            "host": host,
            "port": port,
            "dbname": dbname,
            "user": user,
            "password": password
        }
        self.schema_name = schema_name
        self.table_filter = table_filter

    def _build_schema_query(self) -> str:
        """
        Build the schema discovery query based on configuration.

        Returns:
            SQL query string for schema discovery
        """
        # Base query
        query = """
        SELECT table_name, column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = %s
        """

        # Add table filter if specified
        if self.table_filter:
            query += " AND table_name IN %s"
            return query + " ORDER BY table_name, ordinal_position;"
        else:
            return query + " ORDER BY table_name, ordinal_position;"

    def discover_schema(self) -> Dict[str, Any]:  # <-- CHANGE 1: Return type is now a dictionary
        """
        Connects to the database and returns a structured dictionary of the schema.
        """
        # Build the query dynamically based on configuration
        query = self._build_schema_query()

        try:
            print("Connecting to the database to discover schema...")
            with psycopg2.connect(**self.db_params) as conn:
                with conn.cursor() as cursor:
                    # Execute query with parameters
                    if self.table_filter:
                        cursor.execute(query, (self.schema_name, tuple(self.table_filter)))
                    else:
                        cursor.execute(query, (self.schema_name,))
                    results = cursor.fetchall()
            print("Successfully fetched schema information.")
            # <-- CHANGE 2: Call the new formatting function
            return self._format_schema_as_dict(results)
        except psycopg2.Error as e:
            print(f"ERROR: Could not connect to the database. {e}")
            # Raise an exception so the caller can handle it
            raise ConnectionError(f"Could not connect to the database: {e}")

    def _format_schema_as_dict(self, results: list) -> Dict[str, Any]:  # <-- CHANGE 3: New function
        """
        Private helper method to format the raw schema into a dictionary.
        This is perfect for converting to JSON.
        """
        tables = {}
        for table_name, column_name, data_type in results:
            if table_name not in tables:
                tables[table_name] = {"columns": []}
            tables[table_name]["columns"].append({
                "name": column_name,
                "type": data_type.upper()
            })
        return tables


# --- This block is for direct testing of this file ---
if __name__ == '__main__':
    load_dotenv()

    # Get configuration from environment variables
    schema_name = os.getenv("SCHEMA_NAME", "public")
    table_filter = os.getenv("TABLE_FILTER")
    if table_filter:
        table_filter = [table.strip() for table in table_filter.split(",")]

    discoverer = SchemaDiscoverer(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        schema_name=schema_name,
        table_filter=table_filter
    )
    schema_dict = discoverer.discover_schema()
    import json
    print("\n--- DISCOVERED SCHEMA (JSON) ---")
    print(json.dumps(schema_dict, indent=2))
