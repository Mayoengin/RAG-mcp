#!/usr/bin/env python3
"""Test LLM integration with MCP tools"""

import asyncio
import json
import sys
sys.path.insert(0, '/Users/mayo.eid/Desktop/RAG/RAG')

from src.network_rag.infrastructure.config import load_config
from src.network_rag.infrastructure.container import initialize_system, get_mcp_server

async def test_llm_integration():
    """Test the full LLM integration"""
    
    print("🧪 Testing LLM Integration...")
    
    try:
        # Load configuration and initialize system
        config = load_config()
        container = await initialize_system(config)
        mcp_server = await get_mcp_server()
        
        print("✅ System initialized successfully")
        print(f"🤖 LLM Config: {config.llm.base_url} - {config.llm.model_name}")
        
        # Test the query_network_resources tool (this uses the LLM)
        print("\n📋 Testing query_network_resources with LLM")
        request = {
            "jsonrpc": "2.0",
            "id": "llm_test",
            "method": "tools/call",
            "params": {
                "name": "query_network_resources",
                "arguments": {
                    "query": "Show me all FTTH OLT devices and their status",
                    "include_recommendations": True,
                    "session_id": "test_session"
                }
            }
        }
        
        print("🔄 Sending query to LLM-powered tool...")
        response = await mcp_server.handle_mcp_request(request)
        
        if "result" in response:
            content = response["result"]["content"][0]["text"]
            print("✅ LLM-powered query successful:")
            print("="*60)
            print(content)
            print("="*60)
        else:
            error = response.get("error", {})
            print(f"❌ Error: {error.get('message', 'Unknown error')}")
            print(f"Full error: {error}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_llm_integration())