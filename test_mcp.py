#!/usr/bin/env python3
"""Test script for MCP server tools"""

import asyncio
import json
import sys
sys.path.insert(0, '/Users/mayo.eid/Desktop/RAG/RAG')

from src.network_rag.infrastructure.config import load_config
from src.network_rag.infrastructure.container import initialize_system, get_mcp_server

async def test_mcp_tools():
    """Test the MCP tools"""
    
    print("🧪 Testing MCP Tools...")
    
    try:
        # Load configuration and initialize system
        config = load_config()
        container = await initialize_system(config)
        mcp_server = await get_mcp_server()
        
        print("✅ System initialized successfully")
        
        # Test 1: List available tools
        print("\n📋 Test 1: Listing available tools")
        request = {
            "jsonrpc": "2.0",
            "id": "test1",
            "method": "tools/list"
        }
        
        response = await mcp_server.handle_mcp_request(request)
        if "result" in response:
            tools = response["result"]["tools"]
            print(f"✅ Found {len(tools)} tools:")
            for tool in tools:
                print(f"  - {tool['name']}: {tool['description']}")
        else:
            print(f"❌ Error: {response.get('error', 'Unknown error')}")
        
        # Test 2: List network devices
        print("\n📋 Test 2: List network devices")
        request = {
            "jsonrpc": "2.0",
            "id": "test2",
            "method": "tools/call",
            "params": {
                "name": "list_network_devices",
                "arguments": {
                    "device_type": "all",
                    "limit": 3
                }
            }
        }
        
        response = await mcp_server.handle_mcp_request(request)
        if "result" in response:
            content = response["result"]["content"][0]["text"]
            print("✅ Network devices listed:")
            print(content[:500] + "..." if len(content) > 500 else content)
        else:
            print(f"❌ Error: {response.get('error', 'Unknown error')}")
        
        # Test 3: Get device details (try first FTTH OLT from JSON data)
        print("\n📋 Test 3: Get device details")
        
        # First, check what device names are available
        import json
        with open('/Users/mayo.eid/Desktop/RAG/ftth_olt.json', 'r') as f:
            data = json.load(f)
            if data['data']:
                device_name = data['data'][0].get('name', 'Unknown')
                print(f"Trying to get details for device: {device_name}")
                
                request = {
                    "jsonrpc": "2.0",
                    "id": "test3",
                    "method": "tools/call",
                    "params": {
                        "name": "get_device_details",
                        "arguments": {
                            "device_name": device_name,
                            "device_type": "ftth_olt"
                        }
                    }
                }
                
                response = await mcp_server.handle_mcp_request(request)
                if "result" in response:
                    content = response["result"]["content"][0]["text"]
                    print("✅ Device details retrieved:")
                    print(content[:500] + "..." if len(content) > 500 else content)
                else:
                    print(f"❌ Error: {response.get('error', 'Unknown error')}")
            else:
                print("❌ No FTTH OLT devices found in data")
        
        print("\n🎉 MCP Tools test completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_mcp_tools())