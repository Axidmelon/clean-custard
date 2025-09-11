# Custard MongoDB Agent

A specialized agent for connecting to MongoDB databases and providing schema discovery and query execution capabilities for the Custard platform.

## Features

- **MongoDB Schema Discovery**: Automatically discovers collections, fields, and data types
- **Safe Query Execution**: Executes read-only MongoDB queries with security validation
- **WebSocket Communication**: Connects to Custard backend via WebSocket
- **Collection Filtering**: Optional collection filtering for focused schema discovery
- **Document Sampling**: Analyzes document structure by sampling data
- **Index Information**: Discovers and reports database indexes

## Supported MongoDB Operations

- `find` - Query documents with filtering, projection, sorting, and pagination
- `aggregate` - Execute aggregation pipelines
- `count` - Count documents matching criteria
- `distinct` - Get distinct values for a field

## Environment Variables

Create a `.env` file with the following variables:

```env
# Backend connection
BACKEND_WEBSOCKET_URI=wss://your-backend.com/api/v1/connections/ws/{agent_id}
CONNECTION_ID=your-connection-uuid
AGENT_ID=your-agent-id

# MongoDB connection
MONGODB_CONNECTION_STRING=mongodb://username:password@host:port/database
MONGODB_DATABASE_NAME=your_database_name

# Optional: Collection filtering
MONGODB_COLLECTION_FILTER=collection1,collection2,collection3
```

## MongoDB Connection String Formats

### Local MongoDB
```
mongodb://localhost:27017/database_name
```

### MongoDB Atlas
```
mongodb+srv://username:password@cluster.mongodb.net/database_name?retryWrites=true&w=majority
```

### MongoDB with Authentication
```
mongodb://username:password@host:port/database_name?authSource=admin
```

## Query Examples

### Find Query
```json
{
  "find": {"status": "active"},
  "projection": {"name": 1, "email": 1},
  "limit": 10,
  "sort": {"created_at": -1}
}
```

### Aggregation Query
```json
{
  "aggregate": [
    {"$match": {"status": "active"}},
    {"$group": {"_id": "$category", "count": {"$sum": 1}}},
    {"$sort": {"count": -1}}
  ]
}
```

### Count Query
```json
{
  "count": {"status": "active"}
}
```

### Distinct Query
```json
{
  "distinct": "category",
  "query": {"status": "active"}
}
```

## Security Features

- **Read-Only Operations**: Only allows safe, read-only MongoDB operations
- **Query Validation**: Blocks dangerous operations and operators
- **Collection Filtering**: Optional collection filtering for security
- **Input Sanitization**: Validates and sanitizes all query inputs

## Installation

1. Clone the repository
2. Navigate to the `agent-mongodb` directory
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Set up environment variables
5. Run the agent:
   ```bash
   python main.py
   ```

## Docker Usage

Build the Docker image:
```bash
docker build -t custard-mongodb-agent .
```

Run the container:
```bash
docker run -d \
  --name custard-mongodb-agent \
  --env-file .env \
  custard-mongodb-agent
```

## Schema Discovery

The agent automatically discovers:
- Collection names and document counts
- Field types and structures
- Index information
- Sample documents
- Database statistics

## Error Handling

The agent includes comprehensive error handling for:
- Connection failures
- Invalid queries
- Security violations
- MongoDB errors
- Network issues

## Logging

The agent provides detailed logging for:
- Connection status
- Query execution
- Schema discovery
- Error conditions
- Performance metrics

## Development

To test the schema discoverer directly:
```bash
python schema_discoverer.py
```

This will connect to your MongoDB instance and output the discovered schema in JSON format.
