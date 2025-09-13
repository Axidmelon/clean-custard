# Postman Test Commands

## Quick curl Commands for Testing

### 1. Health Check
```bash
curl -X GET "http://localhost:8000/health"
```

### 2. Upload CSV File (Replace YOUR_TOKEN)
```bash
curl -X POST "http://localhost:8000/api/v1/files/upload" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@test_employees.csv"
```

### 3. Test Current CSV System
```bash
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "file_id": "YOUR_FILE_ID",
    "question": "What is the average salary by department?",
    "data_source": "csv"
  }'
```

### 4. Test New CSV SQL System
```bash
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "file_id": "YOUR_FILE_ID",
    "question": "What is the average salary by department?",
    "data_source": "csv_sql"
  }'
```

### 5. Test Different Query Types
```bash
# Count query
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "file_id": "YOUR_FILE_ID",
    "question": "How many employees are there?",
    "data_source": "csv_sql"
  }'

# Filter query
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "file_id": "YOUR_FILE_ID",
    "question": "Show me employees with salary greater than 60000",
    "data_source": "csv_sql"
  }'

# Complex query
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "file_id": "YOUR_FILE_ID",
    "question": "What are the top 3 highest paid employees?",
    "data_source": "csv_sql"
  }'
```

## Postman Collection JSON

```json
{
  "info": {
    "name": "Clean-Custard CSV-to-SQL Testing",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "variable": [
    {
      "key": "base_url",
      "value": "http://localhost:8000"
    },
    {
      "key": "auth_token",
      "value": "YOUR_JWT_TOKEN"
    }
  ],
  "item": [
    {
      "name": "Health Check",
      "request": {
        "method": "GET",
        "header": [],
        "url": {
          "raw": "{{base_url}}/health",
          "host": ["{{base_url}}"],
          "path": ["health"]
        }
      }
    },
    {
      "name": "Upload CSV File",
      "request": {
        "method": "POST",
        "header": [
          {
            "key": "Authorization",
            "value": "Bearer {{auth_token}}"
          }
        ],
        "body": {
          "mode": "formdata",
          "formdata": [
            {
              "key": "file",
              "type": "file",
              "src": "test_employees.csv"
            }
          ]
        },
        "url": {
          "raw": "{{base_url}}/api/v1/files/upload",
          "host": ["{{base_url}}"],
          "path": ["api", "v1", "files", "upload"]
        }
      }
    },
    {
      "name": "CSV Query (Current System)",
      "request": {
        "method": "POST",
        "header": [
          {
            "key": "Content-Type",
            "value": "application/json"
          },
          {
            "key": "Authorization",
            "value": "Bearer {{auth_token}}"
          }
        ],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"file_id\": \"YOUR_FILE_ID\",\n  \"question\": \"What is the average salary by department?\",\n  \"data_source\": \"csv\"\n}"
        },
        "url": {
          "raw": "{{base_url}}/api/v1/query",
          "host": ["{{base_url}}"],
          "path": ["api", "v1", "query"]
        }
      }
    },
    {
      "name": "CSV SQL Query (New System)",
      "request": {
        "method": "POST",
        "header": [
          {
            "key": "Content-Type",
            "value": "application/json"
          },
          {
            "key": "Authorization",
            "value": "Bearer {{auth_token}}"
          }
        ],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"file_id\": \"YOUR_FILE_ID\",\n  \"question\": \"What is the average salary by department?\",\n  \"data_source\": \"csv_sql\"\n}"
        },
        "url": {
          "raw": "{{base_url}}/api/v1/query",
          "host": ["{{base_url}}"],
          "path": ["api", "v1", "query"]
        }
      }
    }
  ]
}
```
