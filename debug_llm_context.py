#!/usr/bin/env python3
"""Debug what context is actually sent to the LLM"""

import asyncio
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "RAG" / "src"))

from network_rag.outbound.network_api_adapter import NetworkAPIAdapter

async def debug_llm_context():
    """Debug what gets sent to LLM for GENT query"""
    
    # Initialize adapter with local files
    adapter = NetworkAPIAdapter(
        base_url="file://",
        api_key="local_files"
    )
    
    print("🔍 Testing what context gets sent to LLM for GENT region query...")
    
    # Simulate the GENT region filter from query controller
    gent_filters = {"region": "GENT"}
    gent_devices = await adapter.fetch_ftth_olts(gent_filters)
    print(f"✅ Found {len(gent_devices)} GENT devices")
    
    # Convert to device_dicts as done in query_controller.py
    device_dicts = []
    for device in gent_devices:
        if hasattr(device, 'get_health_summary'):
            health_summary = device.get_health_summary()
            device_dicts.append(health_summary)
            print(f"✅ Device {device.name} health summary:")
            print(f"   {health_summary}")
        else:
            device_dict = device.__dict__ if hasattr(device, '__dict__') else device
            device_dicts.append(device_dict)
            print(f"✅ Device {device.name} dict:")
            print(f"   {device_dict}")
    
    print(f"\n🤖 This is what would be sent to LLM:")
    print(f"📊 Query: 'Show me all the FTTH OLTs in GENT region'")
    print(f"📊 Device Count: {len(device_dicts)}")
    print(f"📊 Filters Applied: {gent_filters}")
    
    # Simulate the context building from _generate_llm_response_with_device_data
    context_parts = [
        f"USER QUERY: Show me all the FTTH OLTs in GENT region",
        f"DEVICE TYPE: FTTH OLT",
        f"TOTAL DEVICES FOUND: {len(device_dicts)}",
    ]
    
    if gent_filters:
        filter_desc = ", ".join([f"{k}={v}" for k, v in gent_filters.items() if v])
        context_parts.append(f"FILTERS APPLIED: {filter_desc}")
    
    context_parts.append("\nDEVICE DATA:")
    for i, device in enumerate(device_dicts, 1):
        context_parts.append(f"\n{i}. Device: {device.get('name', 'Unknown')}")
        context_parts.append(f"   - Region: {device.get('region', 'N/A')}")
        context_parts.append(f"   - Environment: {device.get('environment', 'N/A')}")
        context_parts.append(f"   - Managed by Inmanta: {device.get('managed_by_inmanta', False)}")
        
        if device.get('connection_type'):
            context_parts.append(f"   - Connection: {device.get('connection_type')}")
        if device.get('bandwidth_gbps'):
            context_parts.append(f"   - Bandwidth: {device.get('bandwidth_gbps')} Gbps")
    
    llm_context = "\n".join(context_parts)
    
    print(f"\n📝 FULL LLM CONTEXT:")
    print("=" * 80)
    print(llm_context)
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(debug_llm_context())