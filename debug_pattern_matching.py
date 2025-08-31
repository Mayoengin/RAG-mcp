#!/usr/bin/env python3
"""Debug pattern matching for scenario 2"""

def test_pattern_matching():
    """Test the exact pattern matching logic from RAG analyzer"""
    
    query = "Show me FTTH OLTs in HOBO region with configuration issues"
    query_lower = query.lower()
    
    print(f"Testing query: {query}")
    print(f"Query lower: {query_lower}")
    print()
    
    # Test the patterns from the code
    analysis_patterns = {
        'device_listing': 0,
        'device_details': 0,
        'complex_analysis': 0
    }
    
    # Device listing patterns
    if any(word in query_lower for word in ['how many', 'count', 'list all', 'show all', 'inventory']):
        analysis_patterns['device_listing'] += 3
        print("✅ Matched: general listing patterns (+3)")
    
    if 'show me' in query_lower and any(word in query_lower for word in ['ftth olts', 'devices', 'olts']):
        analysis_patterns['device_listing'] += 3
        print("✅ Matched: 'show me' + device type (+3)")
    
    if any(word in query_lower for word in ['olts in', 'devices in', 'ftth olts']) and any(word in query_lower for word in ['region', 'hobo', 'gent', 'asse']):
        analysis_patterns['device_listing'] += 4
        print("✅ Matched: regional device queries (+4)")
    
    # Device details patterns
    if any(word in query_lower for word in ['specific', 'details for', 'configuration of']):
        analysis_patterns['device_details'] += 3
        print("✅ Matched: device details patterns (+3)")
    
    if 'show me' in query_lower and any(word in query_lower for word in ['olt17prop01', 'specific device']):
        analysis_patterns['device_details'] += 3
        print("✅ Matched: specific device details (+3)")
    
    # Complex analysis patterns
    if any(word in query_lower for word in ['impact', 'analysis', 'relationships', 'depends on']):
        analysis_patterns['complex_analysis'] += 3
        print("✅ Matched: complex analysis patterns (+3)")
    
    print()
    print("Final scores:")
    for pattern, score in analysis_patterns.items():
        print(f"  {pattern}: {score}")
    
    best_match = max(analysis_patterns.items(), key=lambda x: x[1])
    print(f"\nBest match: {best_match[0]} (score: {best_match[1]})")

if __name__ == "__main__":
    test_pattern_matching()