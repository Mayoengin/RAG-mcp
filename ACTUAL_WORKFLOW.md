# ACTUAL NETWORK RAG SYSTEM WORKFLOW
## Complete Function Call Trace for Query: "Show me FTTH OLTs in HOBO region"

```
🌐 USER QUERY: "Show me FTTH OLTs in HOBO region"
```

## 📋 COMPLETE FUNCTION CALL SEQUENCE

### **1. 🎬 DEMO ENTRY POINT**
```python
# File: /RAG/main.py
async def main():
    demo = NetworkRAGDemo()
    await demo.initialize(use_mock_data=False)
    await demo.run_single_demo_scenario()

# Demo scenario executes:
await demo.server._execute_network_query({
    "query": "Show me all the FTTH OLTs in GENT region", 
    "include_recommendations": True
})
```

### **2. 📡 MCP SERVER ADAPTER**
```python
# File: /src/network_rag/inbound/mcp_server.py:36
class MCPServerAdapter:
    async def _execute_network_query(self, arguments: Dict[str, Any]) -> str:
        query = arguments.get("query", "")  # "Show me FTTH OLTs in HOBO region"
        include_recommendations = arguments.get("include_recommendations", True)
        
        # CALLS ⬇️
        response = await self.query_controller.execute_intelligent_network_query({
            "query": query,
            "include_recommendations": include_recommendations
        })
        return response
```

### **3. 🎮 QUERY CONTROLLER - MAIN ORCHESTRATOR**
```python
# File: /src/network_rag/controller/query_controller.py:32
class QueryController:
    async def execute_intelligent_network_query(self, arguments: Dict[str, Any]) -> str:
        query = arguments.get("query", "")  # "Show me FTTH OLTs in HOBO region"
        include_recommendations = arguments.get("include_recommendations", True)
        
        # Step 1: RAG FUSION ANALYSIS ⬇️
        if self.rag_analyzer:
            if hasattr(self.rag_analyzer, 'analyze_query_with_data_awareness'):
                guidance, schema_context = await self.rag_analyzer.analyze_query_with_data_awareness(query)
            else:
                guidance = await self.rag_analyzer.analyze_query_for_tool_selection(query)
                schema_context = None
        else:
            guidance = self._fallback_tool_guidance(query)
            schema_context = None
        
        # Step 2: BUILD RESPONSE STRUCTURE ⬇️
        response_parts = [
            "# Schema-Aware Network Analysis\n",
            f"**Query:** {query}\n\n"
        ]
        
        # Step 3: ADD SCHEMA CONTEXT ⬇️
        if schema_context:
            response_parts.append(self._format_schema_context_summary(schema_context))
        
        # Step 4: EXECUTE STRATEGY BASED ON ANALYSIS ⬇️
        try:
            if guidance['analysis_type'] == 'device_listing':
                result = await self._execute_device_listing_strategy(query, guidance, schema_context)
            elif guidance['analysis_type'] == 'device_details':
                result = await self._execute_device_details_strategy(query, guidance, schema_context)
            else:
                result = await self._execute_complex_analysis_strategy(query, guidance, schema_context)
            
            response_parts.append(result)
        except Exception as e:
            # Error handling...
            
        # Step 5: ADD RECOMMENDATIONS ⬇️
        if include_recommendations and guidance.get('recommendations'):
            response_parts.extend([
                "\n## Knowledge-Based Recommendations\n"
            ])
            for rec in guidance['recommendations']:
                response_parts.append(f"💡 {rec}\n")
        
        return "".join(response_parts)
```

### **4. 🧠 RAG FUSION ANALYZER - INTELLIGENCE ENGINE**
```python
# File: /src/network_rag/services/rag_fusion_analyzer.py:32
class RAGFusionAnalyzer:
    async def analyze_query_with_data_awareness(self, query: str) -> Tuple[Dict[str, Any], SchemaAwareContext]:
        try:
            # Step 1: Standard RAG fusion analysis ⬇️
            guidance = await self.analyze_query_for_tool_selection(query)
            
            # Step 2: Build schema-aware context if available ⬇️
            if self.context_builder:
                schema_context = await self.context_builder.build_context_for_query(query)
                
                # Step 3: Enhance guidance with data awareness ⬇️
                guidance = await self._enhance_guidance_with_data_context(guidance, schema_context)
                
                return guidance, schema_context
            else:
                return guidance, None
        except Exception as e:
            print(f"Data-aware RAG fusion analysis failed: {e}")
            return self._fallback_guidance(query), None
    
    async def analyze_query_for_tool_selection(self, query: str) -> Dict[str, Any]:
        try:
            # Multiple search strategies for higher confidence ⬇️
            documents = await self._perform_fusion_search(query)
            
            if documents:
                return await self._analyze_documents_for_guidance(query, documents)
            else:
                return self._fallback_guidance(query)
        except Exception as e:
            print(f"RAG fusion analysis failed: {e}")
            return self._fallback_guidance(query)
```

### **5. 🔍 DOCUMENT SEARCH & ANALYSIS**
```python
# File: /src/network_rag/services/rag_fusion_analyzer.py:55
async def _perform_fusion_search(self, query: str) -> List[Any]:
    search_strategies = [
        f"tool selection for: {query}",
        f"how to handle query: {query}",  
        f"MCP tool for {query}",
        f"network analysis approach for: {query}"
    ]
    
    all_documents = []
    
    for search_query in search_strategies:
        try:
            # CALLS ⬇️ DOCUMENT CONTROLLER
            documents = await self.document_controller.search_documents(
                query=search_query,
                limit=3,
                use_vector_search=True
            )
            all_documents.extend(documents)
        except Exception as e:
            print(f"Search failed for '{search_query}': {e}")
            continue
    
    return all_documents

# File: /src/network_rag/services/rag_fusion_analyzer.py:81
async def _analyze_documents_for_guidance(self, query: str, documents: List[Any]) -> Dict[str, Any]:
    # Tool mention analysis
    tool_scores = {
        'list_network_devices': 0,
        'get_device_details': 0, 
        'query_network_resources': 0
    }
    
    # Analysis type patterns
    analysis_patterns = {
        'device_listing': 0,
        'device_details': 0,
        'complex_analysis': 0
    }
    
    # PRIORITY: Score based on query content first
    query_lower = query.lower()
    
    # Device listing patterns - queries asking for multiple devices
    if any(word in query_lower for word in ['how many', 'count', 'list all', 'show all', 'inventory']):
        analysis_patterns['device_listing'] += 3
    if 'show me' in query_lower and any(word in query_lower for word in ['ftth olts', 'devices', 'olts']):
        analysis_patterns['device_listing'] += 3  # "Show me FTTH OLTs..." = listing
    if any(word in query_lower for word in ['olts in', 'devices in', 'ftth olts']) and any(word in query_lower for word in ['region', 'hobo', 'gent', 'asse']):
        analysis_patterns['device_listing'] += 4  # Regional device queries = listing
        
    # [More pattern analysis...]
    
    # Determine best matches
    best_tool = max(tool_scores.items(), key=lambda x: x[1])
    best_analysis = max(analysis_patterns.items(), key=lambda x: x[1])
    
    return {
        'confidence': confidence_level,
        'tool_recommendation': best_tool[0] if best_tool[1] > 0 else None,
        'analysis_type': best_analysis[0],  # 'device_listing' for our query
        'approach': self._determine_approach(query, best_analysis[0]),
        'reasoning': self._generate_reasoning(best_tool[0], best_analysis[0]),
        'recommendations': recommendations[:3],
        'docs_analyzed': len(documents)
    }
```

### **6. 📊 SCHEMA CONTEXT BUILDING**
```python
# File: /src/network_rag/services/schema_aware_context.py:29
class SchemaAwareContextBuilder:
    async def build_context_for_query(self, query: str) -> SchemaAwareContext:
        # Step 1: Identify relevant schemas based on query ⬇️
        relevant_schemas = self.schema_registry.get_schemas_for_query_intent(query)
        schema_names = [schema.name for schema in relevant_schemas]
        
        # Step 2: Get basic data samples for identified schemas ⬇️
        data_samples = self._get_basic_data_samples(schema_names)
        
        # Step 3: Build schema summary for LLM ⬇️
        schema_summary = self._build_schema_summary(relevant_schemas, data_samples)
        
        # Step 4: Extract business context ⬇️
        business_context = self._build_business_context(relevant_schemas)
        
        # Step 5: Generate contextual recommendations ⬇️
        recommendations = self._generate_context_recommendations(data_samples)
        
        return SchemaAwareContext(
            query=query,
            relevant_schemas=relevant_schemas,
            data_samples=data_samples,
            schema_summary=schema_summary,
            business_context=business_context,
            recommendations=recommendations,
            generated_at=datetime.utcnow()
        )
```

### **7. 🧬 SCHEMA REGISTRY - INTENT MAPPING**
```python
# File: /src/network_rag/services/schema_registry.py:285
class SchemaRegistry:
    def get_schemas_for_query_intent(self, query: str) -> List[DataSchema]:
        query_lower = query.lower()  # "show me ftth olts in hobo region"
        relevant_schemas = []
        
        # Map query terms to schema names
        schema_mappings = {
            'ftth_olt': ['ftth', 'olt', 'fiber', 'optical'],  # MATCHES! 🎯
            'lag': ['lag', 'link', 'aggregation', 'lacp'],
            'mobile_modem': ['mobile', 'modem', 'nokia', '5g'],
            'team': ['team', 'responsible', 'contact', 'escalation'],
            'pxc': ['pxc', 'cross', 'connect', 'integration']
        }
        
        for schema_name, keywords in schema_mappings.items():
            if any(keyword in query_lower for keyword in keywords):
                schema = self.get_schema(schema_name)
                if schema:
                    relevant_schemas.append(schema)  # Adds 'ftth_olt' schema
        
        return relevant_schemas  # Returns [ftth_olt_schema]
```

### **8. 🌐 NETWORK DATA EXECUTION - DEVICE LISTING**
```python
# File: /src/network_rag/controller/query_controller.py:180
async def _execute_device_listing_strategy(self, query: str, guidance: Dict[str, Any], schema_context=None) -> str:
    return await self._execute_original_device_listing_strategy(query, guidance)

# File: /src/network_rag/controller/query_controller.py:180
async def _execute_original_device_listing_strategy(self, query: str, guidance: Dict[str, Any]) -> str:
    try:
        # Extract region filter from query ⬇️
        region_filter = self._extract_region_from_query(query)  # Returns "HOBO"
        filters = {"region": region_filter} if region_filter else {}
        
        # Fetch FTTH OLT devices ⬇️
        devices = await self.network_port.fetch_ftth_olts(filters)
        
        if not devices:
            return self.response_formatter.format_error_response(...)
        
        # Build context for LLM ⬇️
        device_summaries = []
        for device in devices:
            summary = device.get_health_summary()
            device_summaries.append({
                "name": summary["name"],
                "region": summary["region"], 
                "environment": summary["environment"],
                "bandwidth_gbps": summary["bandwidth_gbps"],
                "service_count": summary["service_count"],
                "managed_by_inmanta": summary["managed_by_inmanta"],
                "esi_name": summary.get("esi_name", "ESI_" + summary['name']),
                "connection_type": summary.get("connection_type", "N/A"),
                "complete_config": summary.get("complete_config", False)
            })
        
        # Generate LLM analysis ⬇️
        messages = [
            {
                "role": "system", 
                "content": "You are a network infrastructure analyst..."
            },
            {
                "role": "user",
                "content": f"Query: {query}\n\nFTTH OLT Devices Found: {len(device_summaries)}\n\n..."
            }
        ]
        
        llm_response = await self.llm_port.generate_response(messages)
        return llm_response
        
    except Exception as e:
        return self.response_formatter.format_error_response(...)
```

### **9. 🔧 REGION EXTRACTION UTILITY**
```python
# File: /src/network_rag/controller/query_controller.py:394
def _extract_region_from_query(self, query: str) -> Optional[str]:
    query_lower = query.lower()  # "show me ftth olts in hobo region"
    regions = ["hobo", "gent", "roes", "asse"]
    
    for region in regions:
        if region in query_lower:  # "hobo" found! 🎯
            return region.upper()  # Returns "HOBO"
    return None
```

### **10. 🌐 NETWORK API ADAPTER - DATA RETRIEVAL**
```python
# File: /RAG/main.py:275 (Mock Implementation)
class MockNetworkAdapter:
    async def fetch_ftth_olts(self, filters=None):
        olts = self.sample_olts.copy()  # All 7 mock OLTs
        
        if filters:
            if "region" in filters:  # filters = {"region": "HOBO"}
                olts = [olt for olt in olts if olt.region == filters["region"]]
                # Filters to HOBO devices only: OLT17PROP01, OLT18PROP02, OLT19PROP03, OLT20PROP01
        
        return olts  # Returns 4 HOBO OLTs

# Mock FTTH OLT devices:
self.sample_olts = [
    MockFTTHOLT("OLT17PROP01", "HOBO", "PRODUCTION", 10, 200, True),    # ✅ HOBO
    MockFTTHOLT("OLT18PROP02", "HOBO", "PRODUCTION", 10, 150, False),   # ✅ HOBO
    MockFTTHOLT("OLT19PROP03", "HOBO", "PRODUCTION", 100, 0, True),     # ✅ HOBO
    MockFTTHOLT("OLT20PROP01", "HOBO", "UAT", 10, 50, True),           # ✅ HOBO
    MockFTTHOLT("OLT21GENT01", "GENT", "PRODUCTION", 10, 300, True),    # ❌ GENT
    MockFTTHOLT("OLT22GENT02", "GENT", "PRODUCTION", 100, 250, True),   # ❌ GENT
    MockFTTHOLT("OLT23ROES01", "ROES", "PRODUCTION", 10, 180, True),    # ❌ ROES
]
```

### **11. 📊 DEVICE HEALTH SUMMARY**
```python
# File: /RAG/main.py:241
class MockFTTHOLT:
    def get_health_summary(self):
        return {
            "name": self.name,                    # "OLT17PROP01"
            "region": self.region,                # "HOBO"
            "environment": self.environment,      # "PRODUCTION"
            "bandwidth_gbps": self.bandwidth_gbps, # 10
            "service_count": self.service_count,   # 200
            "managed_by_inmanta": self.managed_by_inmanta, # True
            "esi_name": self.esi_name,            # "ESI_OLT17PROP01"
            "connection_type": "1x10G" if self.bandwidth_gbps == 10 else "1x100G",
            "complete_config": self.managed_by_inmanta and self.service_count > 0  # True
        }
```

### **12. 🤖 LLM GENERATION**
```python
# File: /RAG/main.py:353
async def lm_studio_generate_response(messages):
    try:
        import aiohttp
        
        # Convert messages to OpenAI format
        openai_messages = []
        for msg in messages:
            # Handle different message formats...
            openai_messages.append(msg)  # Simplified
        
        payload = {
            "model": "llama-3.2-8x3b-moe-dark-champion-instruct-uncensored-abliterated-18.4b@q8_0",
            "messages": openai_messages,
            "max_tokens": 2048,
            "temperature": 0.7,
            "stream": False
        }
        
        # CALLS ⬇️ LM STUDIO HTTP API
        async with aiohttp.ClientSession() as session:
            async with session.post("http://127.0.0.1:1234/v1/chat/completions", 
                                  json=payload, 
                                  timeout=aiohttp.ClientTimeout(total=120)) as response:
                if response.status == 200:
                    data = await response.json()
                    if 'choices' in data and len(data['choices']) > 0:
                        response_content = data['choices'][0]['message']['content']
                        print(f"🤖 LM Studio response generated ({len(response_content)} chars)")
                        return response_content  # ✨ INTELLIGENT NETWORK ANALYSIS
                else:
                    return f"LM Studio API error (HTTP {response.status})"
    except Exception as e:
        return f"LM Studio connection error: {str(e)}"
```

## 📋 **ACTUAL DATA FLOW SUMMARY**

```
📥 INPUT:  "Show me FTTH OLTs in HOBO region"
📤 OUTPUT: "# Schema-Aware Network Analysis
           **Query:** Show me FTTH OLTs in HOBO region
           
           ## 📊 Data Context
           **Available Data:** 4 records across 1 data sources
           **Data Quality:** ftth_olt: 🟢 Good (0.8%)
           **Relevant Schemas:** ftth_olt
           
           [LLM GENERATED INTELLIGENT ANALYSIS OF 4 HOBO DEVICES]
           
           ## Knowledge-Based Recommendations
           💡 Use list_network_devices for inventory queries
           💡 Data appears healthy. Proceed with analysis.
           💡 FTTH OLT data available for network analysis."
```

## 🔄 **ACTUAL FUNCTION CALL CHAIN**

```
main.py:async main()
├── demo.initialize()
├── demo.run_single_demo_scenario()
│   └── demo.server._execute_network_query()
│       └── MCPServerAdapter._execute_network_query()
│           └── QueryController.execute_intelligent_network_query()
│               ├── RAGFusionAnalyzer.analyze_query_with_data_awareness()
│               │   ├── RAGFusionAnalyzer.analyze_query_for_tool_selection()
│               │   │   ├── RAGFusionAnalyzer._perform_fusion_search()
│               │   │   │   └── DocumentController.search_documents() [MOCK]
│               │   │   └── RAGFusionAnalyzer._analyze_documents_for_guidance()
│               │   └── SchemaAwareContextBuilder.build_context_for_query()
│               │       ├── SchemaRegistry.get_schemas_for_query_intent()
│               │       ├── SchemaAwareContextBuilder._get_basic_data_samples()
│               │       ├── SchemaAwareContextBuilder._build_schema_summary()
│               │       ├── SchemaAwareContextBuilder._build_business_context()
│               │       └── SchemaAwareContextBuilder._generate_context_recommendations()
│               ├── QueryController._format_schema_context_summary()
│               └── QueryController._execute_device_listing_strategy()
│                   └── QueryController._execute_original_device_listing_strategy()
│                       ├── QueryController._extract_region_from_query()
│                       ├── MockNetworkAdapter.fetch_ftth_olts()
│                       ├── MockFTTHOLT.get_health_summary() [×4 devices]
│                       └── LLMAdapter.generate_response() [LM Studio HTTP call]
```

**🎯 Result:** The system correctly identifies the query intent, extracts the HOBO region filter, retrieves 4 matching devices, and generates an intelligent analysis using the LLM with full context.