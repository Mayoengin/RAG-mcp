#!/usr/bin/env python3
"""Debug script to test GENT region filtering specifically"""

import asyncio
import json
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "RAG" / "src"))

from network_rag.outbound.network_api_adapter import NetworkAPIAdapter

async def debug_gent_filtering():
    """Test GENT region filtering step by step"""
    
    # Initialize adapter with local files
    adapter = NetworkAPIAdapter(
        base_url="file://",
        api_key="local_files"
    )
    
    print("🔍 Testing GENT region filtering...")
    
    # Test 1: No filters (should get all devices)
    print("\n1. Fetching all devices (no filters):")
    all_devices = await adapter.fetch_ftth_olts()
    print(f"   Found {len(all_devices)} total devices")
    
    # Show region distribution
    regions = {}
    for device in all_devices:
        region = device.region or "Unknown"
        regions[region] = regions.get(region, 0) + 1
    
    print("   Region distribution:")
    for region, count in sorted(regions.items()):
        print(f"     {region}: {count} devices")
    
    # Test 2: GENT region filter
    print("\n2. Fetching GENT region devices:")
    gent_filters = {"region": "GENT"}
    gent_devices = await adapter.fetch_ftth_olts(gent_filters)
    print(f"   Found {len(gent_devices)} GENT devices")
    
    for device in gent_devices:
        print(f"     - {device.name}: {device.region} region, {device.environment.value} env, Inmanta: {device.managed_by_inmanta}")
    
    # Test 3: Raw JSON data for comparison
    print("\n3. Raw JSON GENT devices:")
    with open('/Users/mayo.eid/Desktop/RAG/ftth_olt.json', 'r') as f:
        data = json.load(f)
        
    gent_raw = [d for d in data['data'] if d.get('region') == 'GENT']
    print(f"   Raw JSON has {len(gent_raw)} GENT devices:")
    
    for device in gent_raw:
        print(f"     - {device.get('name')}: {device.get('region')} region, {device.get('olt_environment')} env, Inmanta: {device.get('managed_by_inmanta')}")

if __name__ == "__main__":
    asyncio.run(debug_gent_filtering())