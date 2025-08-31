# Proper RAG Fusion Architecture

## Current (Wrong) Architecture
```
MCP Server
├── Protocol Handling  
├── RAG Fusion Logic ❌ (Wrong layer!)
├── Tool Execution
└── Response Formatting
```

## Correct Architecture

### 1. Protocol Layer
```python
# mcp_server.py - ONLY protocol concerns
class MCPServerAdapter:
    async def _handle_tools_call(self, request_id, params):
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        # Delegate to controller (no RAG logic here!)
        result = await self.query_controller.execute_query(arguments)
        
        return {"jsonrpc": "2.0", "id": request_id, "result": result}
```

### 2. Business Logic Layer  
```python
# query_controller.py - RAG fusion belongs HERE
class QueryController:
    def __init__(self, rag_analyzer, tool_executor):
        self.rag_analyzer = rag_analyzer
        self.tool_executor = tool_executor
    
    async def execute_query(self, arguments):
        query = arguments.get("query")
        
        # RAG fusion for tool selection
        guidance = await self.rag_analyzer.analyze_query(query)
        
        # Execute appropriate tool based on RAG guidance
        return await self.tool_executor.execute(
            tool=guidance['tool_recommendation'], 
            query=query,
            guidance=guidance
        )
```

### 3. RAG Service Layer
```python
# rag_fusion_analyzer.py - Pure RAG logic
class RAGFusionAnalyzer:
    async def analyze_query(self, query):
        # Multi-search strategy
        documents = await self._fusion_search(query)
        
        # Analyze for tool recommendation
        return await self._analyze_for_guidance(query, documents)
```

## Benefits of Proper Architecture

### 🎯 Single Responsibility
- **MCP Server**: Only MCP protocol translation
- **QueryController**: Business logic orchestration  
- **RAG Analyzer**: Pure knowledge base analysis
- **Tool Executor**: Tool execution logic

### 🧪 Testability
```python
# Test RAG fusion independently
def test_rag_analyzer():
    analyzer = RAGFusionAnalyzer(mock_document_controller)
    guidance = await analyzer.analyze_query("How many OLTs?")
    assert guidance['tool_recommendation'] == 'list_network_devices'

# Test query controller with mocked RAG
def test_query_controller():
    controller = QueryController(mock_rag_analyzer, mock_tool_executor)
    result = await controller.execute_query({"query": "test"})
    # Verify orchestration logic
```

### 🔄 Flexibility
- Switch RAG strategies without touching MCP server
- Add new tools without changing RAG logic
- Replace MCP protocol without affecting business logic

### 📈 Reusability
- RAG analyzer can be used by CLI, API, or other interfaces
- Query controller can work with different protocols
- Clean separation enables microservices later

## Migration Plan

1. **Move RAG logic to QueryController**
2. **Create dedicated RAGFusionAnalyzer service**
3. **Update MCP server to delegate to QueryController**
4. **Remove RAG methods from MCP server**
5. **Update dependency injection**

## File Structure After Migration
```
src/network_rag/
├── inbound/
│   └── mcp_server.py          # 200 lines - Protocol only
├── controller/  
│   └── query_controller.py    # 300 lines - Business logic + RAG
├── services/
│   ├── rag_fusion_analyzer.py # 150 lines - Pure RAG
│   └── tool_executor.py       # 250 lines - Tool execution
└── outbound/
    └── [adapters]
```

## Why This Matters

### 🏗️ Clean Architecture Principles
- **Dependency Rule**: Inner layers don't depend on outer layers
- **MCP Server** (outer) → **QueryController** (inner) → **RAG Service** (inner)

### 🚀 Scalability
- RAG logic can evolve independently
- Multiple protocol adapters can share same business logic
- Services can be split into microservices later

### 👥 Team Development
- Frontend team: MCP protocol changes
- Backend team: RAG algorithm improvements  
- DevOps team: Service deployment strategies