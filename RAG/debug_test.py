#!/usr/bin/env python3
"""Debug test to verify RAG routing logic"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_query_routing():
    """Test the query routing logic"""
    
    query = "How many FTTH OLTs are in HOBO region?"
    query_lower = query.lower()
    
    print(f"Query: {query}")
    print(f"Query lower: {query_lower}")
    
    # Test the pattern matching
    listing_words = ['how many', 'list', 'count', 'all']
    matches = [word for word in listing_words if word in query_lower]
    
    print(f"Listing words found: {matches}")
    
    # Test the device detection
    device_words = ['olt17prop01', 'cinaalsa01', 'specific']
    device_matches = [device for device in device_words if device in query_lower]
    
    print(f"Device words found: {device_matches}")
    
    # Expected routing
    if matches:
        print("✅ Should route to: device_listing")
        expected_guidance = {
            'confidence': 'MEDIUM',
            'tool_recommendation': 'list_network_devices',
            'analysis_type': 'device_listing',
            'approach': 'Device inventory approach (fallback)',
            'reasoning': 'Query pattern suggests device listing',
            'recommendations': ['Use list_network_devices for inventory queries'],
            'docs_analyzed': 0
        }
        print(f"Expected guidance: {expected_guidance}")
    else:
        print("❌ Should NOT route to device_listing")

if __name__ == "__main__":
    test_query_routing()