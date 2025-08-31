#!/usr/bin/env python3
"""Test scenario 2 specifically"""

import asyncio
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from network_rag.controller.query_controller import QueryController
from network_rag.outbound.network_api_adapter import NetworkAPIAdapter
from network_rag.outbound.llama_adapter import LlamaAdapter

async def test_scenario_2():
    """Test scenario 2: Configuration Issue Analysis in HOBO region"""
    
    print("🔍 Testing Scenario 2: Configuration Issue Analysis")
    print("Query: 'Show me FTTH OLTs in HOBO region with configuration issues'")
    print("-" * 60)
    
    # Initialize components
    network_adapter = NetworkAPIAdapter(base_url="file://", api_key="local_files")
    llm_adapter = LlamaAdapter(base_url="http://localhost:1234")
    
    query_controller = QueryController(
        network_port=network_adapter,
        llm_adapter=llm_adapter,
        document_port=None,
        rag_analyzer=None,
        learning_controller=None
    )
    
    # Execute the query
    query = "Show me FTTH OLTs in HOBO region with configuration issues"
    
    try:
        result = await query_controller.execute_intelligent_network_query({"query": query})
        print("🤖 LLM Response:")
        print("=" * 80)
        print(result)
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_scenario_2())