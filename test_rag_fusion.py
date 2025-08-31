#!/usr/bin/env python3
"""Test RAG fusion functionality"""

import asyncio
import sys
from pathlib import Path
sys.path.insert(0, '/Users/mayo.eid/Desktop/RAG/RAG')

from src.network_rag.infrastructure.config import load_config
from src.network_rag.infrastructure.container import initialize_system

async def test_rag_fusion():
    """Test the RAG fusion functionality"""
    
    print("🧪 Testing RAG Fusion System...")
    
    try:
        # Load configuration and initialize system
        config = load_config()
        container = await initialize_system(config)
        
        # Get MCP server
        mcp_server = await container.get_service("mcp_server")
        
        print("✅ System initialized successfully")
        
        # Test queries that should trigger different tools
        test_queries = [
            {
                "query": "How many FTTH OLTs do we have?",
                "expected_tool": "list_network_devices",
                "expected_type": "device_listing"
            },
            {
                "query": "Show me OLT17PROP01 configuration details",
                "expected_tool": "get_device_details", 
                "expected_type": "device_details"
            },
            {
                "query": "What happens if CINMECHA01 fails?",
                "expected_tool": "query_network_resources",
                "expected_type": "complex_analysis"
            }
        ]
        
        # First check document controller search
        document_controller = await container.get_service("document_controller")
        test_search = await document_controller.search_documents("tool", limit=5, use_vector_search=True)
        print(f"📄 Document search test: {len(test_search)} results found")
        
        print(f"\n🔍 Testing {len(test_queries)} queries with RAG fusion...\n")
        
        for i, test in enumerate(test_queries, 1):
            print(f"Test {i}: {test['query']}")
            
            try:
                # Test RAG fusion search
                guidance = await mcp_server._rag_fusion_search(test["query"])
                
                print(f"   ✅ RAG Guidance Generated")
                print(f"   - Confidence: {guidance.get('confidence', 'N/A')}")
                print(f"   - Tool Recommendation: {guidance.get('tool_recommendation', 'N/A')}")
                print(f"   - Analysis Type: {guidance.get('analysis_type', 'N/A')}")
                print(f"   - Approach: {guidance.get('approach', 'N/A')}")
                print(f"   - Documents Analyzed: {guidance.get('docs_analyzed', 0)}")
                
                # Check if tool recommendation matches expected
                expected_tool = test["expected_tool"]
                actual_tool = guidance.get('tool_recommendation')
                
                if actual_tool == expected_tool:
                    print(f"   ✅ Tool Selection: Correct ({actual_tool})")
                else:
                    print(f"   ⚠️  Tool Selection: Expected {expected_tool}, got {actual_tool}")
                
                # Test full query execution
                print(f"   🔄 Testing full query execution...")
                
                result = await mcp_server._execute_network_query({
                    "query": test["query"],
                    "include_recommendations": True
                })
                
                if result and len(result) > 100:  # Basic check for meaningful response
                    print(f"   ✅ Query Execution: Success ({len(result)} chars)")
                else:
                    print(f"   ❌ Query Execution: Failed or short response")
                    
            except Exception as e:
                print(f"   ❌ Test Failed: {e}")
            
            print()  # Empty line between tests
        
        print("🎉 RAG fusion testing completed!")
        
    except Exception as e:
        print(f"❌ RAG fusion test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_rag_fusion())