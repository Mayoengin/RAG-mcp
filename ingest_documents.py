#!/usr/bin/env python3
"""Document ingestion system for RAG knowledge base"""

import asyncio
import sys
from pathlib import Path
sys.path.insert(0, '/Users/mayo.eid/Desktop/RAG/RAG')

from src.network_rag.infrastructure.config import load_config
from src.network_rag.infrastructure.container import initialize_system
from src.network_rag.models import Document, DocumentType
from datetime import datetime
import uuid

async def ingest_documents():
    """Ingest technical documents into the knowledge base"""
    
    print("📚 Starting Document Ingestion...")
    
    try:
        # Load configuration and initialize system
        config = load_config()
        container = await initialize_system(config)
        
        # Get document controller
        document_controller = await container.get_service("document_controller")
        
        print("✅ System initialized successfully")
        
        # Define documents to ingest
        documents_dir = Path("/Users/mayo.eid/Desktop/RAG/RAG/data/documents")
        
        documents_to_ingest = [
            {
                "file": "list_network_devices_tool.md",
                "title": "list_network_devices MCP Tool Documentation",
                "type": DocumentType.API_REFERENCE,
                "keywords": ["list_network_devices", "MCP", "tool", "inventory", "devices"]
            },
            {
                "file": "get_device_details_tool.md", 
                "title": "get_device_details MCP Tool Documentation",
                "type": DocumentType.API_REFERENCE,
                "keywords": ["get_device_details", "MCP", "tool", "configuration", "specific device"]
            },
            {
                "file": "query_network_resources_tool.md",
                "title": "query_network_resources MCP Tool Documentation", 
                "type": DocumentType.API_REFERENCE,
                "keywords": ["query_network_resources", "MCP", "tool", "analysis", "intelligence"]
            }
        ]
        
        ingested_count = 0
        
        for doc_info in documents_to_ingest:
            try:
                file_path = documents_dir / doc_info["file"]
                
                if not file_path.exists():
                    print(f"❌ File not found: {file_path}")
                    continue
                
                # Read document content
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                print(f"\n📄 Processing: {doc_info['title']}")
                print(f"   File: {doc_info['file']}")
                print(f"   Size: {len(content)} characters")
                print(f"   Type: {doc_info['type'].value}")
                
                # Store document using create_document method
                document_id = await document_controller.create_document(
                    title=doc_info["title"],
                    content=content,
                    document_type=doc_info["type"],
                    source=f"file://{file_path}"
                )
                
                if document_id:
                    print(f"✅ Successfully ingested: {doc_info['title']}")
                    print(f"   Document ID: {document_id}")
                    ingested_count += 1
                else:
                    print(f"❌ Failed to ingest: {doc_info['title']}")
                    print(f"   Error: No document ID returned")
                
            except Exception as e:
                print(f"❌ Error processing {doc_info['file']}: {e}")
        
        print(f"\n🎉 Document ingestion completed!")
        print(f"📊 Successfully ingested: {ingested_count} documents")
        
        # Test the knowledge base
        print(f"\n🔍 Testing knowledge base search...")
        
        test_queries = [
            "FTTH OLT configuration",
            "CINMECHA01 troubleshooting",
            "Nokia mobile modems",
            "team responsibilities"
        ]
        
        for query in test_queries:
            try:
                documents = await document_controller.search_documents(
                    query=query,
                    limit=2,
                    use_vector_search=True
                )
                print(f"   Query: '{query}' → {len(documents)} results")
                if documents:
                    print(f"     Top result: {documents[0].title}")
            except Exception as e:
                print(f"   Query: '{query}' → Error: {e}")
        
        print(f"\n✅ Knowledge base ingestion and testing completed!")
        
    except Exception as e:
        print(f"❌ Document ingestion failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(ingest_documents())