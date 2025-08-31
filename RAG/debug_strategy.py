#!/usr/bin/env python3
"""Debug which strategy is actually being selected"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from network_rag.services.rag_fusion_analyzer import RAGFusionAnalyzer

# Test with a mock document controller
class MockDocumentController:
    async def search_documents(self, query, limit=10, use_vector_search=True):
        # Return some mock documents to simulate finding 12 documents
        return [
            {"title": "FTTH Guide", "content": "OLT configuration guide"},
            {"title": "Network Troubleshooting", "content": "Troubleshooting steps"},
            {"title": "HOBO Architecture", "content": "Regional network setup"}
        ]

async def test_rag_analysis():
    """Test what the RAG analyzer actually returns"""
    
    analyzer = RAGFusionAnalyzer(MockDocumentController())
    
    query = "How many FTTH OLTs are in HOBO region?"
    
    # This should simulate what happens in the real system
    guidance = await analyzer.analyze_query_for_tool_selection(query)
    
    print(f"Query: {query}")
    print(f"RAG Analysis Result:")
    for key, value in guidance.items():
        print(f"  {key}: {repr(value)}")
    
    # Test the routing logic
    analysis_type = guidance.get('analysis_type', '')
    print(f"\nRouting test:")
    print(f"analysis_type = {repr(analysis_type)}")
    print(f"analysis_type == 'device_listing': {analysis_type == 'device_listing'}")
    print(f"analysis_type == 'device_details': {analysis_type == 'device_details'}")
    
    if analysis_type == 'device_listing':
        print("✅ Should execute: device_listing_strategy")
    elif analysis_type == 'device_details':
        print("❌ Would execute: device_details_strategy")
    else:
        print(f"❌ Would execute: complex_analysis_strategy (default)")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_rag_analysis())