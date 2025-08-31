# MCP Server Refactoring Plan

## Current Issues (1,546 lines)
- Single massive class handling everything
- Mixed concerns: protocol, business logic, formatting
- Hardcoded analysis methods
- Duplicate response formatting code

## Proposed Structure

### 1. Core MCP Server (200 lines)
```
MCPServerAdapter
├── Protocol handling only
├── Tool routing
└── Request/response parsing
```

### 2. Tool Executors (300 lines total)
```
NetworkToolExecutor
├── _execute_network_query
├── _execute_list_devices  
└── _execute_get_details

KnowledgeToolExecutor
├── _execute_knowledge_search
└── _execute_olt_validation
```

### 3. RAG System (200 lines)
```
RAGFusionAnalyzer
├── _rag_fusion_search
├── _analyze_rag_results
└── _determine_tool_strategy
```

### 4. Response Formatters (150 lines)
```
ResponseFormatter
├── format_network_analysis
├── format_device_list
└── format_error_response
```

### 5. Network Analyzers (400 lines)
```
NetworkAnalysisService
├── analyze_connectivity
├── analyze_impact
└── analyze_dependencies
```

## Benefits
- Each class ~200 lines max
- Single responsibility principle
- Testable components
- Easier maintenance
- Reusable formatters

## Migration Strategy
1. Extract response formatting first
2. Move RAG fusion to separate class
3. Create tool executor classes
4. Move network analysis logic
5. Slim down core MCP server