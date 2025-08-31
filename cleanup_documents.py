#!/usr/bin/env python3
"""Clean up duplicate and legacy documents from MongoDB"""

import asyncio
from pymongo import MongoClient
import sys
from pathlib import Path
sys.path.insert(0, '/Users/mayo.eid/Desktop/RAG/RAG')

async def cleanup_documents():
    """Remove duplicate and legacy documents, keep only latest vectorized ones"""
    
    print("🧹 Starting Document Cleanup...")
    
    try:
        client = MongoClient('mongodb://localhost:27017/')
        db = client['network_rag']
        
        # Get all documents sorted by creation time (newest first)
        all_docs = list(db.documents.find().sort('created_at', -1))
        vector_docs = list(db.vector_index.find())
        
        print(f"📊 Current state:")
        print(f"   - Documents: {len(all_docs)}")
        print(f"   - Vector indexes: {len(vector_docs)}")
        
        # Get the IDs of the 3 most recent MCP tool docs (the ones that are vectorized)
        vectorized_doc_ids = {vec['document_id'] for vec in vector_docs}
        print(f"   - Vectorized document IDs: {vectorized_doc_ids}")
        
        # Find documents to keep (the 3 most recent MCP tool docs)
        docs_to_keep = []
        docs_to_remove = []
        
        for doc in all_docs:
            doc_id = doc.get('id')
            if doc_id in vectorized_doc_ids:
                docs_to_keep.append(doc)
            else:
                docs_to_remove.append(doc)
        
        print(f"\n🎯 Cleanup Plan:")
        print(f"   - Keep: {len(docs_to_keep)} documents (vectorized MCP tool docs)")
        print(f"   - Remove: {len(docs_to_remove)} documents (duplicates + legacy)")
        
        if docs_to_keep:
            print("\n✅ Documents to KEEP:")
            for doc in docs_to_keep:
                print(f"   - {doc.get('title', 'Untitled')} (ID: {doc.get('id')})")
        
        if docs_to_remove:
            print("\n❌ Documents to REMOVE:")
            for doc in docs_to_remove:
                print(f"   - {doc.get('title', 'Untitled')} (ID: {doc.get('id')})")
        
        # Confirm cleanup
        if docs_to_remove:
            print(f"\n🗑️  Removing {len(docs_to_remove)} documents...")
            
            # Remove from documents collection
            remove_ids = [doc['id'] for doc in docs_to_remove]
            result = db.documents.delete_many({'id': {'$in': remove_ids}})
            print(f"   - Removed {result.deleted_count} documents from main collection")
            
            # Remove any stray vector indexes for removed documents
            vector_result = db.vector_index.delete_many({'document_id': {'$in': remove_ids}})
            print(f"   - Removed {vector_result.deleted_count} stray vector indexes")
            
            print("✅ Cleanup completed!")
        else:
            print("✅ No cleanup needed - database is already clean!")
        
        # Final verification
        final_docs = db.documents.count_documents({})
        final_vectors = db.vector_index.count_documents({})
        
        print(f"\n📊 Final state:")
        print(f"   - Documents: {final_docs}")
        print(f"   - Vector indexes: {final_vectors}")
        
        if final_docs == 3 and final_vectors == 3:
            print("🎉 Perfect! Database now contains exactly 3 vectorized MCP tool documents")
        
        client.close()
        
    except Exception as e:
        print(f"❌ Cleanup failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(cleanup_documents())