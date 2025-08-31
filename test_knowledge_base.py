#!/usr/bin/env python3
"""Test what's in the RAG knowledge base"""

import asyncio
import sys
sys.path.insert(0, '/Users/mayo.eid/Desktop/RAG/RAG')

from src.network_rag.infrastructure.config import load_config
from src.network_rag.infrastructure.container import initialize_system, get_mcp_server

async def explore_knowledge_base():
    """Explore the RAG knowledge base contents"""
    
    print("🔍 Exploring RAG Knowledge Base...")
    
    try:
        # Load configuration and initialize system
        config = load_config()
        container = await initialize_system(config)
        mcp_server = await get_mcp_server()
        
        print("✅ System initialized successfully")
        
        # 1. Test the search_knowledge_base tool
        print("\n" + "="*60)
        print("📚 TESTING KNOWLEDGE BASE SEARCH")
        print("="*60)
        
        search_queries = [
            "FTTH configuration",
            "network troubleshooting", 
            "OLT management",
            "BNG setup",
            "LAG configuration",
            "mobile modem",
            "team procedures"
        ]
        
        for query in search_queries:
            print(f"\n🔍 Searching for: '{query}'")
            
            request = {
                "jsonrpc": "2.0",
                "id": f"search_{query.replace(' ', '_')}",
                "method": "tools/call",
                "params": {
                    "name": "search_knowledge_base",
                    "arguments": {
                        "query": query,
                        "limit": 3
                    }
                }
            }
            
            response = await mcp_server.handle_mcp_request(request)
            
            if "result" in response:
                content = response["result"]["content"][0]["text"]
                print(f"📄 Results:")
                print(content[:300] + "..." if len(content) > 300 else content)
            else:
                error = response.get("error", {})
                print(f"❌ Error: {error.get('message', 'Unknown error')}")
        
        # 2. Check document controller directly
        print("\n" + "="*60)
        print("📋 DIRECT DOCUMENT CONTROLLER ACCESS")
        print("="*60)
        
        document_controller = mcp_server.document_controller
        print(f"Document controller type: {type(document_controller)}")
        
        # Try to search documents directly
        try:
            print("\n🔍 Direct document search...")
            documents = await document_controller.search_documents(
                query="network configuration",
                limit=5,
                use_vector_search=True
            )
            print(f"📊 Documents found: {len(documents)}")
            
            if documents:
                for i, doc in enumerate(documents[:3], 1):
                    print(f"\n📄 Document {i}:")
                    print(f"   Title: {getattr(doc, 'title', 'No title')}")
                    print(f"   Type: {getattr(doc, 'document_type', 'Unknown')}")
                    print(f"   Content preview: {str(doc)[:200]}...")
            else:
                print("❌ No documents found in knowledge base")
                
        except Exception as e:
            print(f"❌ Direct search failed: {e}")
        
        # 3. Check if there are any stored documents
        print("\n" + "="*60)
        print("🗄️ CHECKING DOCUMENT STORAGE")
        print("="*60)
        
        try:
            # Check if we can access the document storage directly
            if hasattr(document_controller, 'document_store'):
                print("Document store available")
            else:
                print("No direct document store access")
            
            # Try different search approaches
            searches_to_try = [
                {"query": "", "limit": 10},  # Empty query to get all
                {"query": "configuration", "limit": 10},
                {"query": "network", "limit": 10}
            ]
            
            for search_params in searches_to_try:
                try:
                    docs = await document_controller.search_documents(**search_params)
                    print(f"Search '{search_params['query']}': {len(docs)} documents")
                except Exception as e:
                    print(f"Search '{search_params['query']}' failed: {e}")
                    
        except Exception as e:
            print(f"❌ Document storage check failed: {e}")
        
        # 4. Check configuration for document paths
        print("\n" + "="*60)
        print("⚙️ CONFIGURATION ANALYSIS")
        print("="*60)
        
        print(f"Data directory: {config.data_dir}")
        print(f"Cache directory: {config.cache_dir}")
        print(f"Environment: {config.environment}")
        
        # Check if data directories exist and what's in them
        from pathlib import Path
        
        data_path = Path(config.data_dir)
        if data_path.exists():
            print(f"\n📁 Data directory contents:")
            for item in data_path.iterdir():
                if item.is_file():
                    print(f"   📄 {item.name} ({item.stat().st_size} bytes)")
                elif item.is_dir():
                    print(f"   📁 {item.name}/ ({len(list(item.iterdir()))} items)")
        else:
            print(f"❌ Data directory does not exist: {data_path}")
        
        cache_path = Path(config.cache_dir) 
        if cache_path.exists():
            print(f"\n💾 Cache directory contents:")
            for item in cache_path.iterdir():
                if item.is_file():
                    print(f"   📄 {item.name} ({item.stat().st_size} bytes)")
                elif item.is_dir():
                    print(f"   📁 {item.name}/ ({len(list(item.iterdir()))} items)")
        else:
            print(f"❌ Cache directory does not exist: {cache_path}")
            
    except Exception as e:
        print(f"❌ Exploration failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(explore_knowledge_base())