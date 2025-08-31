#!/usr/bin/env python3
"""
Standalone runner for the MCP-compliant Network RAG server
This script can be used with Claude Desktop or other MCP clients
"""

import asyncio
import sys
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Import the main demo for initialization
from main import NetworkRAGDemo

# Import the MCP server components
from src.network_rag.inbound.mcp_server_standard import mcp, initialize_controllers

async def initialize_and_run():
    """Initialize the Network RAG system and run the MCP server"""
    print("🚀 Starting MCP-Compliant Network RAG Server")
    print("=" * 50)
    
    # Initialize the Network RAG system
    demo = NetworkRAGDemo()
    success = await demo.initialize(use_mock_data=False)  # Use real LLM
    
    if not success:
        print("❌ Failed to initialize Network RAG system")
        sys.exit(1)
    
    # Initialize MCP server with controllers
    initialize_controllers(demo.query_controller, demo.document_controller)
    print("✅ MCP Server initialized with Network RAG capabilities")
    
    print("\n📋 Available MCP Tools:")
    print("   • network_query - Intelligent network analysis with RAG+LLM")
    print("   • list_network_devices - Filter and list network devices")
    print("   • get_device_details - Detailed device configuration")
    
    print(f"\n🌐 MCP Server ready on stdio transport")
    print("   Connect Claude Desktop or other MCP clients to use these tools")
    
    # Run the MCP server
    return mcp

if __name__ == "__main__":
    # For Claude Desktop integration, we need to run the server
    server = asyncio.run(initialize_and_run())
    server.run()