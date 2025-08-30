#!/usr/bin/env python3
"""Test script for specific device types"""

import asyncio
import json
import sys
sys.path.insert(0, '/Users/mayo.eid/Desktop/RAG/RAG')

from src.network_rag.infrastructure.config import load_config
from src.network_rag.infrastructure.container import initialize_system, get_mcp_server

async def test_specific_devices():
    """Test different device types"""
    
    print("🧪 Testing Different Device Types...")
    
    try:
        # Load configuration and initialize system
        config = load_config()
        container = await initialize_system(config)
        mcp_server = await get_mcp_server()
        
        print("✅ System initialized successfully")
        
        # Test 1: List only LAG devices
        print("\n📋 Test 1: List LAG devices")
        request = {
            "jsonrpc": "2.0",
            "id": "lag_test",
            "method": "tools/call",
            "params": {
                "name": "list_network_devices",
                "arguments": {
                    "device_type": "lag",
                    "limit": 5
                }
            }
        }
        
        response = await mcp_server.handle_mcp_request(request)
        if "result" in response:
            content = response["result"]["content"][0]["text"]
            print("✅ LAG devices listed:")
            print(content)
        else:
            print(f"❌ Error: {response.get('error', 'Unknown error')}")
        
        # Test 2: Get LAG device details
        print("\n📋 Test 2: Get LAG device details")
        request = {
            "jsonrpc": "2.0",
            "id": "lag_detail_test",
            "method": "tools/call",
            "params": {
                "name": "get_device_details",
                "arguments": {
                    "device_name": "CINAALSA01",
                    "device_type": "lag"
                }
            }
        }
        
        response = await mcp_server.handle_mcp_request(request)
        if "result" in response:
            content = response["result"]["content"][0]["text"]
            print("✅ LAG device details:")
            print(content)
        else:
            print(f"❌ Error: {response.get('error', 'Unknown error')}")
        
        # Test 3: List teams
        print("\n📋 Test 3: List teams")
        request = {
            "jsonrpc": "2.0",
            "id": "team_test",
            "method": "tools/call",
            "params": {
                "name": "list_network_devices",
                "arguments": {
                    "device_type": "team",
                    "limit": 10
                }
            }
        }
        
        response = await mcp_server.handle_mcp_request(request)
        if "result" in response:
            content = response["result"]["content"][0]["text"]
            print("✅ Teams listed:")
            print(content)
        else:
            print(f"❌ Error: {response.get('error', 'Unknown error')}")
            
        print("\n🎉 Device type tests completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_specific_devices())