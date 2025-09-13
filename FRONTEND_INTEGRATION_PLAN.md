# Frontend Integration Plan - AI Routing & CSV-to-SQL

## 🎯 **Overview**

This plan outlines the integration of the new AI routing agent and CSV-to-SQL functionality into the frontend, providing users with intelligent service selection and enhanced data analysis capabilities.

## 🔄 **Current vs New Architecture**

### **Current Frontend:**
- Simple data source selection (`database` | `csv`)
- Manual service routing
- Basic query interface

### **New Frontend (After Integration):**
- AI-powered automatic service selection (`auto`)
- Enhanced data source options (`auto` | `database` | `csv` | `csv_sql`)
- Intelligent routing with explanations
- User preference support

## 📋 **Integration Checklist**

### **Phase 1: API Types & Services Update**
- [ ] Update `QueryRequest` interface to support new data sources
- [ ] Add `user_preference` field to request
- [ ] Update `QueryResponse` to include AI routing information
- [ ] Enhance query service with new endpoints

### **Phase 2: UI Components Enhancement**
- [ ] Add AI routing option to data source selector
- [ ] Create service explanation component
- [ ] Add user preference selector
- [ ] Enhance query results display

### **Phase 3: TalkData Page Integration**
- [ ] Update data source selection logic
- [ ] Integrate AI routing functionality
- [ ] Add service explanation display
- [ ] Enhance error handling

### **Phase 4: Testing & Validation**
- [ ] Test AI routing functionality
- [ ] Validate service explanations
- [ ] Test user preference handling
- [ ] End-to-end integration testing

## 🔧 **Detailed Implementation**

### **1. API Types Update (`types/api.ts`)**

```typescript
// Enhanced QueryRequest interface
export interface QueryRequest {
  connection_id?: string;
  file_id?: string;
  question: string;
  data_source: 'auto' | 'database' | 'csv' | 'csv_sql';
  user_preference?: 'sql' | 'python';
}

// Enhanced QueryResponse interface
export interface QueryResponse {
  answer: string;
  sql_query: string;
  data: any[];
  columns: string[];
  row_count: number;
  ai_routing?: {
    service_used: string;
    reasoning: string;
    confidence: number;
  };
}
```

### **2. Query Service Enhancement (`services/queryService.ts`)**

```typescript
// New AI routing query function
const askAIQuestion = async (
  fileId: string, 
  question: string, 
  userPreference?: 'sql' | 'python'
): Promise<QueryResponse> => {
  const queryData: QueryRequest = {
    file_id: fileId,
    question: question,
    data_source: 'auto',
    user_preference: userPreference
  };
  
  return askQuestion(queryData);
};

// CSV SQL query function
const askCSVSQLQuestion = async (fileId: string, question: string): Promise<QueryResponse> => {
  const queryData: QueryRequest = {
    file_id: fileId,
    question: question,
    data_source: 'csv_sql'
  };
  
  return askQuestion(queryData);
};

export const queryService = {
  askQuestion,
  askDataAnalysisQuestion,
  askDatabaseQuestion,
  askAIQuestion,        // NEW
  askCSVSQLQuestion     // NEW
};
```

### **3. UI Components Enhancement**

#### **A. Data Source Selector Component**
```typescript
interface DataSourceSelectorProps {
  value: string;
  onChange: (value: string) => void;
  hasFile: boolean;
  hasConnection: boolean;
}

const DataSourceSelector: React.FC<DataSourceSelectorProps> = ({
  value,
  onChange,
  hasFile,
  hasConnection
}) => {
  const options = [
    { value: 'auto', label: '🤖 AI Auto-Select', description: 'Let AI choose the best service' },
    { value: 'csv', label: '📊 Pandas Analysis', description: 'Advanced data analysis' },
    { value: 'csv_sql', label: '🗃️ SQL Queries', description: 'SQL queries on CSV data' },
    { value: 'database', label: '🗄️ Database', description: 'Real-time database queries' }
  ];

  return (
    <Select value={value} onValueChange={onChange}>
      {options.map(option => (
        <SelectItem key={option.value} value={option.value}>
          <div className="flex flex-col">
            <span className="font-medium">{option.label}</span>
            <span className="text-sm text-muted-foreground">{option.description}</span>
          </div>
        </SelectItem>
      ))}
    </Select>
  );
};
```

#### **B. User Preference Selector**
```typescript
interface UserPreferenceSelectorProps {
  value?: 'sql' | 'python';
  onChange: (value: 'sql' | 'python' | undefined) => void;
}

const UserPreferenceSelector: React.FC<UserPreferenceSelectorProps> = ({
  value,
  onChange
}) => {
  return (
    <div className="flex gap-2">
      <Button
        variant={value === 'sql' ? 'default' : 'outline'}
        size="sm"
        onClick={() => onChange(value === 'sql' ? undefined : 'sql')}
      >
        SQL
      </Button>
      <Button
        variant={value === 'python' ? 'default' : 'outline'}
        size="sm"
        onClick={() => onChange(value === 'python' ? undefined : 'python')}
      >
        Python
      </Button>
    </div>
  );
};
```

#### **C. Service Explanation Component**
```typescript
interface ServiceExplanationProps {
  aiRouting?: {
    service_used: string;
    reasoning: string;
    confidence: number;
  };
}

const ServiceExplanation: React.FC<ServiceExplanationProps> = ({ aiRouting }) => {
  if (!aiRouting) return null;

  const getServiceIcon = (service: string) => {
    switch (service) {
      case 'csv_to_sql_converter': return '🗃️';
      case 'data_analysis_service': return '📊';
      case 'database': return '🗄️';
      default: return '🤖';
    }
  };

  const getServiceName = (service: string) => {
    switch (service) {
      case 'csv_to_sql_converter': return 'CSV to SQL Converter';
      case 'data_analysis_service': return 'Data Analysis Service';
      case 'database': return 'Database Service';
      default: return 'Unknown Service';
    }
  };

  return (
    <Card className="p-4 bg-blue-50 border-blue-200">
      <div className="flex items-start gap-3">
        <div className="text-2xl">{getServiceIcon(aiRouting.service_used)}</div>
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <span className="font-medium">AI Selected:</span>
            <span className="font-semibold text-blue-700">
              {getServiceName(aiRouting.service_used)}
            </span>
            <Badge variant="secondary" className="text-xs">
              {Math.round(aiRouting.confidence * 100)}% confidence
            </Badge>
          </div>
          <p className="text-sm text-gray-600">{aiRouting.reasoning}</p>
        </div>
      </div>
    </Card>
  );
};
```

### **4. TalkData Page Integration**

#### **A. State Management Updates**
```typescript
interface TalkDataState {
  // Existing state...
  dataSource: 'auto' | 'database' | 'csv' | 'csv_sql';
  userPreference?: 'sql' | 'python';
  aiRouting?: {
    service_used: string;
    reasoning: string;
    confidence: number;
  };
}
```

#### **B. Query Handling Logic**
```typescript
const handleQuery = async (question: string) => {
  try {
    let response: QueryResponse;
    
    switch (dataSource) {
      case 'auto':
        response = await queryService.askAIQuestion(
          selectedFile?.id || '', 
          question, 
          userPreference
        );
        break;
      case 'csv':
        response = await queryService.askDataAnalysisQuestion(
          selectedFile?.id || '', 
          question
        );
        break;
      case 'csv_sql':
        response = await queryService.askCSVSQLQuestion(
          selectedFile?.id || '', 
          question
        );
        break;
      case 'database':
        response = await queryService.askDatabaseQuestion(
          selectedConnection?.id || '', 
          question
        );
        break;
    }
    
    // Store AI routing information
    if (response.ai_routing) {
      setAiRouting(response.ai_routing);
    }
    
    // Process response...
  } catch (error) {
    // Handle error...
  }
};
```

#### **C. UI Layout Updates**
```typescript
return (
  <div className="flex flex-col h-full">
    {/* Data Source Selector */}
    <div className="p-4 border-b">
      <div className="flex items-center gap-4">
        <DataSourceSelector
          value={dataSource}
          onChange={setDataSource}
          hasFile={!!selectedFile}
          hasConnection={!!selectedConnection}
        />
        
        {dataSource === 'auto' && (
          <UserPreferenceSelector
            value={userPreference}
            onChange={setUserPreference}
          />
        )}
      </div>
    </div>
    
    {/* Service Explanation */}
    {aiRouting && (
      <div className="p-4">
        <ServiceExplanation aiRouting={aiRouting} />
      </div>
    )}
    
    {/* Chat Interface */}
    <div className="flex-1">
      {/* Existing chat interface */}
    </div>
  </div>
);
```

## 🎨 **UI/UX Enhancements**

### **1. Visual Indicators**
- **AI Auto-Select**: 🤖 icon with "AI Auto-Select" label
- **Service Explanations**: Blue-tinted cards with confidence badges
- **User Preferences**: Toggle buttons for SQL/Python preference
- **Loading States**: Enhanced loading indicators for AI routing

### **2. User Experience Flow**
1. **File Upload**: User uploads CSV file
2. **Data Source Selection**: User chooses "AI Auto-Select" or specific service
3. **Preference Setting**: If AI mode, user can set SQL/Python preference
4. **Query Input**: User asks question
5. **AI Analysis**: System shows AI reasoning and service selection
6. **Results Display**: Results with service explanation

### **3. Error Handling**
- **AI Routing Failures**: Fallback to CSV to SQL converter
- **Service Unavailable**: Clear error messages with retry options
- **Network Issues**: Graceful degradation with offline indicators

## 🧪 **Testing Strategy**

### **1. Unit Tests**
- Test new API types and interfaces
- Test query service functions
- Test UI components in isolation

### **2. Integration Tests**
- Test AI routing functionality
- Test service explanation display
- Test user preference handling

### **3. End-to-End Tests**
- Complete user flow testing
- Cross-browser compatibility
- Performance testing

## 📊 **Performance Considerations**

### **1. AI Routing Optimization**
- Cache AI routing decisions for similar queries
- Debounce user input to reduce API calls
- Show loading states during AI analysis

### **2. UI Performance**
- Lazy load service explanation components
- Optimize re-renders with proper state management
- Use React.memo for expensive components

## 🚀 **Deployment Strategy**

### **1. Feature Flags**
- Enable AI routing as optional feature initially
- Gradual rollout to user segments
- A/B testing for user experience optimization

### **2. Backward Compatibility**
- Maintain existing API endpoints
- Support both old and new data source formats
- Graceful degradation for older clients

## 📈 **Success Metrics**

### **1. User Engagement**
- AI routing adoption rate
- User preference usage
- Query success rate improvement

### **2. Performance Metrics**
- AI routing response time
- Service selection accuracy
- User satisfaction scores

## 🔮 **Future Enhancements**

### **1. Advanced AI Features**
- Query suggestion based on data analysis
- Automatic data visualization recommendations
- Smart query optimization

### **2. User Experience**
- Query history with service explanations
- Favorite service preferences
- Advanced user preference profiles

---

## 🎯 **Implementation Priority**

1. **High Priority**: API types and service updates
2. **High Priority**: Basic AI routing integration
3. **Medium Priority**: Enhanced UI components
4. **Medium Priority**: User preference handling
5. **Low Priority**: Advanced features and optimizations

This integration plan provides a comprehensive roadmap for adding AI routing and CSV-to-SQL functionality to the frontend while maintaining a smooth user experience and robust error handling.
