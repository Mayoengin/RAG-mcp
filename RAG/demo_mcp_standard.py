#!/usr/bin/env python3
"""
Demo script using the standard MCP-compliant server
This demonstrates how to integrate with the proper MCP SDK
"""

import asyncio
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Import the MCP server and initialize dependencies
from src.network_rag.inbound.mcp_server_standard import mcp, initialize_controllers

# Import the existing demo infrastructure
from main import NetworkRAGDemo

async def test_standard_mcp_server():
    """Test the standard MCP-compliant server"""
    print("🚀 Testing Standard MCP Server Implementation")
    print("=" * 60)
    
    # Initialize the NetworkRAGDemo to get controllers
    demo = NetworkRAGDemo()
    success = await demo.initialize(use_mock_data=False)  # Use real LLM
    
    if not success:
        print("❌ Failed to initialize Network RAG system")
        return False
    
    # Initialize the MCP server controllers
    initialize_controllers(demo.query_controller, demo.document_controller)
    
    print("✅ MCP Server initialized with Network RAG controllers")
    
    # Test each MCP tool directly
    print("\n🧪 Testing MCP Tools:")
    print("-" * 40)
    
    # Test 1: network_query tool
    print("1. Testing network_query tool...")
    try:
        from src.network_rag.inbound.mcp_server_standard import network_query
        
        response = await network_query(
            query="Show me FTTH OLTs in HOBO region",
            include_recommendations=True
        )
        
        print(f"   ✅ Response length: {len(response)} characters")
        if "## LLM Analysis" in response:
            llm_section = response.split("## LLM Analysis")[1].split("##")[0].strip()
            if len(llm_section) > 200:
                print(f"   ✅ LLM Analysis included: {len(llm_section)} chars")
            else:
                print(f"   ⚠️  LLM Analysis short: {llm_section[:100]}...")
        
        # Show preview
        preview = response[:300] + "..." if len(response) > 300 else response
        print(f"   Preview: {preview}")
        
    except Exception as e:
        print(f"   ❌ network_query failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 2: list_network_devices tool  
    print("\n2. Testing list_network_devices tool...")
    try:
        from src.network_rag.inbound.mcp_server_standard import list_network_devices
        
        response = await list_network_devices(
            device_type="ftth_olt",
            region="GENT",
            limit=5
        )
        
        print(f"   ✅ Response length: {len(response)} characters")
        preview = response[:300] + "..." if len(response) > 300 else response
        print(f"   Preview: {preview}")
        
    except Exception as e:
        print(f"   ❌ list_network_devices failed: {e}")
    
    # Test 3: get_device_details tool
    print("\n3. Testing get_device_details tool...")
    try:
        from src.network_rag.inbound.mcp_server_standard import get_device_details
        
        response = await get_device_details(device_name="OLT17PROP01")
        
        print(f"   ✅ Response length: {len(response)} characters")
        preview = response[:300] + "..." if len(response) > 300 else response
        print(f"   Preview: {preview}")
        
    except Exception as e:
        print(f"   ❌ get_device_details failed: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 Standard MCP Server testing completed!")
    
    return True

async def run_mcp_server_demo():
    """Run a comprehensive demo with the standard MCP server"""
    print("🚀 Network RAG System - MCP Standard Demo")
    print("=" * 60)
    
    success = await test_standard_mcp_server()
    
    if success:
        print("\n📋 MCP Server is ready! You can now:")
        print("   • Connect Claude Desktop to this MCP server")
        print("   • Use tools: network_query, list_network_devices, get_device_details")
        print("   • Each tool follows proper MCP protocols")
        print("\n   To run the MCP server:")
        print("   python3 src/network_rag/inbound/mcp_server_standard.py")
    else:
        print("\n❌ MCP Server demo failed")

if __name__ == "__main__":
    asyncio.run(run_mcp_server_demo())