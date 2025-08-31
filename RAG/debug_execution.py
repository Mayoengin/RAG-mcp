#!/usr/bin/env python3
"""Debug the actual execution path"""

# Mock guidance that should be returned for "How many FTTH OLTs in HOBO region?"
guidance = {
    'confidence': 'MEDIUM',
    'tool_recommendation': None,  # This is the issue - should be 'list_network_devices' 
    'analysis_type': 'device_listing',
    'approach': 'Device inventory and listing approach',
    'reasoning': 'Query requests device inventory or counts - best served by listing tool',
    'recommendations': ['Use list_network_devices for inventory queries'],
    'docs_analyzed': 12
}

print("Current guidance from demo:")
for key, value in guidance.items():
    print(f"  {key}: {value}")

print(f"\nExecution path:")
print(f"guidance['analysis_type'] = '{guidance['analysis_type']}'")

if guidance['analysis_type'] == 'device_listing':
    print("✅ Should execute: _execute_device_listing_strategy")
elif guidance['analysis_type'] == 'device_details':
    print("❌ Would execute: _execute_device_details_strategy")
else:
    print("❌ Would execute: _execute_complex_analysis_strategy")

# The problem might be that analysis_type is not 'device_listing'
print(f"\nActual comparison:")
print(f"'{guidance['analysis_type']}' == 'device_listing': {guidance['analysis_type'] == 'device_listing'}")