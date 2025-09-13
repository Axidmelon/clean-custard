# AI Routing Agent - Visual Flow Diagram

## 🤖 **Complete AI Routing Flow**

```
                    ┌─────────────────────────────────┐
                    │        USER ASKS QUESTION       │
                    │                                 │
                    │  "What is the average salary?"  │
                    │  "Calculate correlation..."     │
                    │  "Show me real-time data..."    │
                    └─────────────┬───────────────────┘
                                  │
                                  ▼
                    ┌─────────────────────────────────┐
                    │      API ENDPOINT               │
                    │    /api/v1/query                │
                    │                                 │
                    │  Request: {                     │
                    │    "question": "...",          │
                    │    "data_source": "auto",      │
                    │    "file_id": "...",           │
                    │    "user_preference": "sql"    │
                    │  }                             │
                    └─────────────┬───────────────────┘
                                  │
                                  ▼
                    ┌─────────────────────────────────┐
                    │     ROUTING DECISION            │
                    │                                 │
                    │  if data_source == "auto":      │
                    │    → 🤖 AI Agent Routing        │
                    │  else:                          │
                    │    → Direct Service Routing     │
                    └─────────────┬───────────────────┘
                                  │
                                  ▼
                    ┌─────────────────────────────────┐
                    │      AI AGENT ACTIVATED         │
                    │                                 │
                    │  🤖 AI Routing Agent           │
                    │  ┌─────────────────────────┐   │
                    │  │     LLM Analysis        │   │
                    │  │                         │   │
                    │  │  📝 Question: "..."     │   │
                    │  │  📊 Context: File size,│   │
                    │  │      Data source,       │   │
                    │  │      User preference    │   │
                    │  │                         │   │
                    │  │  🧠 AI Prompt:          │   │
                    │  │  "You are an expert..." │   │
                    │  │                         │   │
                    │  │  🤖 OpenAI GPT:         │   │
                    │  │  {                      │   │
                    │  │    "recommended_service"│   │
                    │  │    "reasoning": "..."   │   │
                    │  │    "confidence": 0.90   │   │
                    │  │  }                      │   │
                    │  └─────────────────────────┘   │
                    └─────────────┬───────────────────┘
                                  │
                                  ▼
                    ┌─────────────────────────────────┐
                    │      SERVICE ROUTING             │
                    │                                 │
                    │  Based on AI Recommendation:    │
                    │                                 │
                    │  if "csv_sql": → CSV SQL        │
                    │  if "csv": → CSV Pandas         │
                    │  if "database": → Database      │
                    └─────────────┬───────────────────┘
                                  │
                                  ▼
                    ┌─────────────────────────────────┐
                    │     SERVICE EXECUTION           │
                    │                                 │
                    │  ┌─────────┐ ┌─────────┐ ┌─────┐│
                    │  │CSV SQL │ │CSV Pandas│ │DB   ││
                    │  │Handler │ │ Handler  │ │Handler││
                    │  │        │ │          │ │     ││
                    │  │1. Load │ │1. Load   │ │1.   ││
                    │  │2. SQL  │ │2. Pandas │ │Connect││
                    │  │3. Exec │ │3. Exec   │ │2.   ││
                    │  │4. Ret  │ │4. Ret    │ │Query ││
                    │  └─────────┘ └─────────┘ └─────┘│
                    └─────────────┬───────────────────┘
                                  │
                                  ▼
                    ┌─────────────────────────────────┐
                    │     RESPONSE FORMATTING          │
                    │                                 │
                    │  {                              │
                    │    "answer": "...",             │
                    │    "sql_query": "...",          │
                    │    "data": [...],               │
                    │    "ai_routing_info": {         │
                    │      "recommended_service": "...",│
                    │      "reasoning": "...",        │
                    │      "confidence": 0.90         │
                    │    }                            │
                    │  }                              │
                    └─────────────┬───────────────────┘
                                  │
                                  ▼
                    ┌─────────────────────────────────┐
                    │   USER RECEIVES RESULTS          │
                    │                                 │
                    │  ✅ Answer: "The average..."    │
                    │  📊 Data: Table with results    │
                    │  🤖 AI Info: "Used CSV SQL      │
                    │      because: Simple query..."   │
                    │  🎯 Confidence: 90%             │
                    └─────────────────────────────────┘
```

## 🔄 **AI Decision Process Detail**

```
                    ┌─────────────────────────────────┐
                    │     AI AGENT INTERNAL FLOW      │
                    └─────────────────────────────────┘

┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Question   │───▶│  Context    │───▶│  AI Prompt │
│  Analysis   │    │  Evaluation │    │ Generation │
└─────────────┘    └─────────────┘    └─────────────┘
       │                   │                   │
       ▼                   ▼                   ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│• Intent     │    │• File Size │    │• Service   │
│• Complexity│    │• Data Src  │    │  Options   │
│• Keywords   │    │• User Pref │    │• Guidelines│
│• Analysis   │    │• Performance│   │• Examples  │
└─────────────┘    └─────────────┘    └─────────────┘
       │                   │                   │
       └───────────────────┼───────────────────┘
                           ▼
                ┌─────────────────────┐
                │   OpenAI GPT Model  │
                │                     │
                │  🤖 LLM Analysis    │
                │  🧠 Pattern Recog   │
                │  💭 Context Underst │
                │  🎯 Decision Making │
                └─────────────────────┘
                           │
                           ▼
                ┌─────────────────────┐
                │ AI Response Parsing │
                │                     │
                │• Validate JSON      │
                │• Extract Service    │
                │• Extract Reasoning  │
                │• Calculate Confid   │
                │• Handle Errors      │
                └─────────────────────┘
                           │
                           ▼
                ┌─────────────────────┐
                │  Routing Decision   │
                │                     │
                │ ✅ csv_sql          │
                │ ✅ csv (pandas)     │
                │ ✅ database         │
                │ ❌ Fallback         │
                └─────────────────────┘
```

## 📊 **Example Scenarios**

### **Scenario 1: Simple Query**
```
User: "What is the average salary?"
     │
     ▼
AI Analysis: Simple aggregation query
     │
     ▼
Context: Small file (10MB), CSV source, SQL preference
     │
     ▼
AI Decision: csv_sql
     │
     ▼
Reasoning: "Simple aggregation query. SQL is optimal."
     │
     ▼
Confidence: 90%
```

### **Scenario 2: Complex Statistical**
```
User: "Calculate correlation between price and sales"
     │
     ▼
AI Analysis: Complex statistical analysis
     │
     ▼
Context: Medium file (50MB), CSV source, no preference
     │
     ▼
AI Decision: csv (pandas)
     │
     ▼
Reasoning: "Complex statistical analysis. Pandas provides rich functions."
     │
     ▼
Confidence: 90%
```

### **Scenario 3: Real-time Data**
```
User: "Show me real-time inventory levels"
     │
     ▼
AI Analysis: Real-time data query
     │
     ▼
Context: Database source, no file
     │
     ▼
AI Decision: database
     │
     ▼
Reasoning: "Real-time data analysis needed. Database provides live data."
     │
     ▼
Confidence: 95%
```

## 🎯 **AI Intelligence Levels**

```
┌─────────────────────────────────────────────────┐
│            AI INTELLIGENCE SPECTRUM             │
└─────────────────────────────────────────────────┘

Level 1: Keyword Matching (Rule-Based)
├── "correlation" → csv (pandas)
├── "pivot" → csv (pandas)
├── "real-time" → database
└── Default → csv_sql

Level 2: Pattern Recognition (AI Agent)
├── "Calculate correlation between price and sales" → csv (pandas)
├── "What is the average salary by department?" → csv_sql
├── "Show me real-time inventory levels" → database
└── "Merge sales data with customer data" → csv (pandas)

Level 3: Context Understanding (Advanced AI)
├── Considers file size, user preferences, data source
├── Handles ambiguous cases intelligently
├── Provides detailed reasoning and confidence scores
└── Adapts to new question types automatically
```

## 🛡️ **Error Handling Flow**

```
                    ┌─────────────────────────────────┐
                    │        ERROR HANDLING           │
                    └─────────────────────────────────┘

AI API Failure
├── Log error
├── Fallback to csv_sql
└── Return with error message

Invalid AI Response
├── Parse error detected
├── Use safe default (csv_sql)
└── Log parsing failure

Timeout
├── LLM call timeout
├── Use cached decision or default
└── Return with timeout message

Rate Limiting
├── OpenAI rate limit hit
├── Queue request or use fallback
└── Retry with backoff
```

---

**This visual diagram shows how the AI routing agent intelligently processes user questions and routes them to the optimal service using LLM-powered decision making!** 🤖✨
