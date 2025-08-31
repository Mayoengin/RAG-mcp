#!/usr/bin/env python3
"""Test harder network questions"""

import asyncio
import sys
sys.path.insert(0, '/Users/mayo.eid/Desktop/RAG/RAG')

from src.network_rag.infrastructure.config import load_config
from src.network_rag.infrastructure.container import initialize_system, get_mcp_server

async def test_hard_questions():
    """Test complex network questions"""
    
    print("🧪 Testing Hard Network Questions...")
    
    try:
        # Load configuration and initialize system
        config = load_config()
        container = await initialize_system(config)
        mcp_server = await get_mcp_server()
        
        print("✅ System initialized successfully")
        
        # Hard questions to test
        hard_questions = [
            {
                "question": "Which FTTH OLTs in HOBO region are connected to CINMECHA01 and what are their redundancy configurations? Cross-reference with BNG nodes and identify any single points of failure.",
                "expected": "Should analyze FTTH data, find HOBO region devices, check CIN node connections, analyze BNG master/slave configs"
            },
            {
                "question": "Show me all LAG configurations on CINAALSA01 device and correlate them with any FTTH OLTs that might be using these LAGs for uplink connectivity. What teams should be notified if this device fails?",
                "expected": "Should cross-reference LAG data with FTTH data, identify dependencies, check team assignments"
            },
            {
                "question": "Identify all Nokia mobile modems and their subscriber mappings. Which teams manage mobile infrastructure vs FTTH infrastructure and what are the potential integration points?",
                "expected": "Should filter mobile modems by hardware type, find team assignments, identify integration architectures"
            },
            {
                "question": "Map the complete network path from OLT17PROP01 to its BNG nodes, including all intermediate LAG connections and PXC cross-connects. What would be the blast radius if CINMECHA01 goes down?",
                "expected": "Should trace end-to-end connectivity, identify dependencies, calculate failure impact"
            },
            {
                "question": "Which devices have incomplete configurations and what specific configuration elements are missing? Prioritize by production impact and suggest a remediation timeline.",
                "expected": "Should analyze config completeness, assess production impact, provide prioritized recommendations"
            }
        ]
        
        for i, test_case in enumerate(hard_questions, 1):
            print(f"\n{'='*80}")
            print(f"🔥 HARD QUESTION {i}/5")
            print(f"{'='*80}")
            print(f"Question: {test_case['question']}")
            print(f"Expected: {test_case['expected']}")
            print(f"{'='*80}")
            
            request = {
                "jsonrpc": "2.0",
                "id": f"hard_test_{i}",
                "method": "tools/call",
                "params": {
                    "name": "query_network_resources",
                    "arguments": {
                        "query": test_case['question'],
                        "include_recommendations": True,
                        "session_id": f"hard_test_session_{i}"
                    }
                }
            }
            
            print("🔄 Processing complex query...")
            response = await mcp_server.handle_mcp_request(request)
            
            if "result" in response:
                content = response["result"]["content"][0]["text"]
                print("✅ Response generated:")
                print("-" * 80)
                print(content)
                print("-" * 80)
                
                # Simple analysis of response quality
                word_count = len(content.split())
                has_device_names = any(device in content for device in ["OLT17PROP01", "CINAALSA01", "CINMECHA01"])
                has_analysis = any(keyword in content.lower() for keyword in ["analysis", "impact", "recommendation", "configuration"])
                
                print(f"📊 Response Analysis:")
                print(f"   - Word count: {word_count}")
                print(f"   - Contains real device names: {'✅' if has_device_names else '❌'}")
                print(f"   - Contains analysis keywords: {'✅' if has_analysis else '❌'}")
                
            else:
                error = response.get("error", {})
                print(f"❌ Error: {error.get('message', 'Unknown error')}")
            
            print(f"\n{'='*80}\n")
        
        print("🎉 Hard questions test completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_hard_questions())