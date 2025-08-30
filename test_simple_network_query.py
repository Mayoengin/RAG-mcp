#!/usr/bin/env python3
"""Simple test to debug the network query"""

import asyncio
import sys
sys.path.insert(0, '/Users/mayo.eid/Desktop/RAG/RAG')

from src.network_rag.infrastructure.config import load_config
from src.network_rag.infrastructure.container import initialize_system, get_mcp_server

async def test_simple_query():
    """Test simple network query without LLM"""
    
    print("🧪 Testing Simple Network Query...")
    
    try:
        # Load configuration and initialize system
        config = load_config()
        container = await initialize_system(config)
        mcp_server = await get_mcp_server()
        
        print("✅ System initialized successfully")
        
        # Get network adapter directly
        network_adapter = mcp_server.query_controller.network_port
        
        print("📋 Testing direct data access...")
        
        # Test direct FTTH OLT fetch
        print("Fetching FTTH OLTs...")
        ftth_olts = await network_adapter.fetch_ftth_olts()
        print(f"✅ Found {len(ftth_olts)} FTTH OLTs")
        
        if ftth_olts:
            olt = ftth_olts[0]
            print(f"First OLT: {olt}")
            print(f"Type: {type(olt)}")
            
            # Test health summary
            try:
                health = olt.get_health_summary()
                print(f"Health summary: {health}")
            except Exception as e:
                print(f"❌ Health summary error: {e}")
        
        # Test LAG data
        print("\nFetching LAG data...")
        lag_data = await network_adapter._load_local_json('lag')
        print(f"✅ Found {len(lag_data)} LAG devices")
        if lag_data:
            print(f"First LAG: {lag_data[0]}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_simple_query())