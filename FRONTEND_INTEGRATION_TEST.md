# Frontend-Backend Integration Test

## 🧪 **Test Plan**

This document outlines comprehensive testing procedures to verify the integration between the frontend and backend for the new AI routing and CSV-to-SQL functionality.

## 📋 **Test Checklist**

### **Phase 1: Basic Integration Tests**
- [ ] Frontend builds successfully
- [ ] Backend starts without errors
- [ ] API endpoints are accessible
- [ ] CORS configuration works
- [ ] Authentication flow works

### **Phase 2: AI Routing Tests**
- [ ] AI routing with CSV files
- [ ] AI routing with database connections
- [ ] User preference handling
- [ ] Service explanation display
- [ ] Error handling and fallbacks

### **Phase 3: Data Source Tests**
- [ ] CSV analysis service
- [ ] CSV SQL service
- [ ] Database service
- [ ] Auto routing service

### **Phase 4: End-to-End Tests**
- [ ] Complete user flow with AI routing
- [ ] Service switching
- [ ] Error recovery
- [ ] Performance validation

## 🔧 **Test Setup**

### **1. Environment Setup**
```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py

# Frontend
cd frontend
npm install
npm run dev
```

### **2. Test Data**
- **CSV Files**: Upload test CSV files with various sizes and structures
- **Database**: Set up test database connections
- **User Accounts**: Create test user accounts

## 🧪 **Detailed Test Cases**

### **Test Case 1: AI Routing with CSV File**

**Objective**: Verify AI routing works correctly with CSV files

**Steps**:
1. Start backend and frontend
2. Login to the application
3. Upload a CSV file
4. Select "AI Auto-Select" as data source
5. Set user preference to "SQL"
6. Ask a simple question: "What is the average value in column X?"
7. Verify AI routing information is displayed
8. Check that the correct service was selected

**Expected Results**:
- AI routing explanation appears
- Service selection shows high confidence
- Query executes successfully
- Results are displayed correctly

**Test Data**:
```csv
name,age,salary,department
John,25,50000,Engineering
Jane,30,60000,Marketing
Bob,35,70000,Engineering
```

**Test Questions**:
- "What is the average salary?"
- "How many people are in each department?"
- "Show me all employees over 30"

### **Test Case 2: AI Routing with Database**

**Objective**: Verify AI routing works with database connections

**Steps**:
1. Set up database connection
2. Select "AI Auto-Select" as data source
3. Set user preference to "Python"
4. Ask a complex analytical question
5. Verify AI routing and service selection

**Expected Results**:
- AI routing explanation appears
- Service selection considers user preference
- Complex analysis is performed correctly

### **Test Case 3: Manual Service Selection**

**Objective**: Verify manual service selection works

**Steps**:
1. Upload CSV file
2. Select "CSV SQL" as data source
3. Ask SQL-style question
4. Verify direct routing to CSV SQL service
5. Repeat with "Pandas Analysis" selection

**Expected Results**:
- No AI routing explanation appears
- Direct service execution
- Appropriate service behavior

### **Test Case 4: Error Handling**

**Objective**: Verify error handling and recovery

**Steps**:
1. Test with invalid file selection
2. Test with disconnected database
3. Test with malformed queries
4. Verify error messages and recovery options

**Expected Results**:
- Clear error messages
- Graceful degradation
- Retry options available

### **Test Case 5: User Preference Impact**

**Objective**: Verify user preferences affect AI routing

**Steps**:
1. Upload CSV file
2. Set preference to "SQL"
3. Ask statistical question
4. Change preference to "Python"
5. Ask same question
6. Compare service selections

**Expected Results**:
- SQL preference biases toward CSV SQL service
- Python preference biases toward data analysis service
- AI reasoning reflects preference consideration

## 📊 **Performance Tests**

### **Response Time Tests**
- AI routing decision: < 2 seconds
- CSV SQL conversion: < 5 seconds
- Data analysis: < 10 seconds
- Database queries: < 3 seconds

### **Memory Usage Tests**
- CSV file loading: < 100MB per file
- Total memory usage: < 500MB
- Memory cleanup: Automatic after query completion

### **Concurrent User Tests**
- Multiple users with different data sources
- Concurrent AI routing decisions
- Resource sharing and isolation

## 🔍 **Debugging Guide**

### **Common Issues**

#### **1. AI Routing Not Working**
**Symptoms**: No AI routing explanation appears
**Debug Steps**:
- Check browser console for errors
- Verify backend AI routing agent is running
- Check API response for ai_routing field
- Verify OpenAI API key is configured

#### **2. Service Selection Issues**
**Symptoms**: Wrong service selected or service not available
**Debug Steps**:
- Check data source selection logic
- Verify file/connection availability
- Check AI routing agent logs
- Verify service isolation rules

#### **3. UI Component Issues**
**Symptoms**: Components not rendering or styling issues
**Debug Steps**:
- Check component imports
- Verify TypeScript types
- Check CSS class availability
- Verify component props

#### **4. API Communication Issues**
**Symptoms**: Network errors or CORS issues
**Debug Steps**:
- Check API base URL configuration
- Verify CORS settings
- Check authentication headers
- Verify endpoint availability

### **Debug Commands**

```bash
# Backend logs
tail -f backend/logs/app.log

# Frontend console
# Open browser dev tools and check console

# API testing
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"file_id":"test","question":"test","data_source":"auto"}'
```

## 📈 **Success Criteria**

### **Functional Requirements**
- ✅ AI routing works for all data sources
- ✅ Service explanations are accurate and helpful
- ✅ User preferences are respected
- ✅ Error handling is robust
- ✅ Performance meets requirements

### **User Experience Requirements**
- ✅ Intuitive data source selection
- ✅ Clear service explanations
- ✅ Responsive UI components
- ✅ Helpful error messages
- ✅ Smooth user flow

### **Technical Requirements**
- ✅ Type safety maintained
- ✅ No memory leaks
- ✅ Proper error boundaries
- ✅ Responsive design
- ✅ Cross-browser compatibility

## 🚀 **Deployment Testing**

### **Production Environment Tests**
1. Deploy backend to production
2. Deploy frontend to production
3. Test with production data
4. Verify performance metrics
5. Test error monitoring

### **Rollback Plan**
1. Keep previous version available
2. Monitor error rates
3. Have rollback procedure ready
4. Test rollback process

## 📝 **Test Results Template**

```
Test Case: [Test Name]
Date: [Date]
Tester: [Name]
Environment: [Dev/Staging/Prod]

Steps:
1. [Step 1]
2. [Step 2]
...

Expected Results:
- [Expected result 1]
- [Expected result 2]

Actual Results:
- [Actual result 1]
- [Actual result 2]

Status: [PASS/FAIL]
Notes: [Additional notes]
```

## 🎯 **Next Steps**

After successful testing:
1. Document any issues found
2. Create bug reports for failures
3. Update integration documentation
4. Plan production deployment
5. Set up monitoring and alerts

---

This comprehensive test plan ensures the frontend-backend integration works correctly and provides a smooth user experience with the new AI routing functionality.
