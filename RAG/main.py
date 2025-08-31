#!/usr/bin/env python3
"""
Network RAG System - Main Entry Point
Demonstrates Schema-Aware RAG system with comprehensive testing scenarios
"""

import asyncio
import os
import sys
from datetime import datetime
from typing import Dict, Any, Optional
import json
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Core imports
from network_rag.models import Document, DocumentType
from network_rag.controller.query_controller import QueryController
from network_rag.controller.document_controller import DocumentController
from network_rag.services.rag_fusion_analyzer import RAGFusionAnalyzer
from network_rag.services.schema_registry import SchemaRegistry
from network_rag.services.data_quality_service import DataQualityService
from network_rag.services.schema_aware_context import SchemaAwareContextBuilder
from network_rag.inbound.mcp_server import NetworkRAGServer

# Mock implementations for testing
from network_rag.outbound.mongodb_adapter import MongoDBAdapter
from network_rag.outbound.network_api_adapter import NetworkAPIAdapter
from network_rag.outbound.llm_adapter import LLMAdapter


class NetworkRAGDemo:
    """Demo class to showcase the Schema-Aware RAG system"""
    
    def __init__(self):
        self.server: Optional[NetworkRAGServer] = None
        self.query_controller: Optional[QueryController] = None
        self.document_controller: Optional[DocumentController] = None
        
    async def initialize(self, use_mock_data: bool = True):
        """Initialize the complete RAG system"""
        print("🚀 Initializing Schema-Aware Network RAG System...")
        
        try:
            # Initialize adapters
            if use_mock_data:
                print("📊 Using mock data for demonstration")
                mongodb_adapter = await self._create_mock_mongodb()
                network_adapter = await self._create_mock_network_adapter()
                llm_adapter = await self._create_mock_llm_adapter()
            else:
                print("🔗 Connecting to real services...")
                # Use real adapters (would need proper configuration)
                mongodb_adapter = MongoDBAdapter(
                    connection_string=os.getenv("MONGODB_URI", "mongodb://localhost:27017"),
                    database_name="network_rag"
                )
                network_adapter = NetworkAPIAdapter()
                llm_adapter = LLMAdapter()
            
            # Initialize core services
            schema_registry = SchemaRegistry()
            data_quality_service = DataQualityService(network_adapter)
            context_builder = SchemaAwareContextBuilder(schema_registry, data_quality_service)
            
            # Initialize controllers
            self.document_controller = DocumentController(
                knowledge_port=mongodb_adapter,
                vector_search_port=mongodb_adapter,
                llm_port=llm_adapter
            )
            
            self.query_controller = QueryController(
                network_port=network_adapter,
                vector_search_port=mongodb_adapter,
                llm_port=llm_adapter,
                conversation_port=mongodb_adapter,
                document_controller=self.document_controller
            )
            
            # Initialize RAG analyzer with schema awareness
            self.query_controller.initialize_rag_analyzer(
                self.document_controller, 
                context_builder
            )
            
            # Initialize MCP server
            self.server = NetworkRAGServer(
                query_controller=self.query_controller,
                document_controller=self.document_controller
            )
            
            # Initialize database if using real MongoDB
            if not use_mock_data:
                await mongodb_adapter.initialize()
            
            print("✅ System initialized successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Initialization failed: {e}")
            return False
    
    async def _create_mock_mongodb(self):
        """Create mock MongoDB adapter with sample data"""
        
        class MockMongoDBAdapter:
            def __init__(self):
                self.documents = []
                self.vector_index = []
                self.sample_docs = [
                    {
                        "id": "doc_001",
                        "title": "FTTH OLT Configuration Guide",
                        "content": "Complete guide for configuring Fiber To The Home Optical Line Terminals. Covers HOBO region deployment, bandwidth allocation, and Inmanta management integration. Essential for production OLT setup.",
                        "document_type": DocumentType.GUIDE,
                        "keywords": ["FTTH", "OLT", "configuration", "HOBO", "Inmanta"],
                        "usefulness_score": 0.92,
                        "embedding": [0.1] * 384  # Mock embedding
                    },
                    {
                        "id": "doc_002", 
                        "title": "Network Troubleshooting Best Practices",
                        "content": "Best practices for troubleshooting FTTH networks including OLT diagnostics, LAG configuration issues, and mobile modem connectivity problems. Includes step-by-step procedures for HOBO region.",
                        "document_type": DocumentType.TROUBLESHOOTING,
                        "keywords": ["troubleshooting", "FTTH", "diagnostics", "LAG", "mobile"],
                        "usefulness_score": 0.88,
                        "embedding": [0.2] * 384  # Mock embedding
                    },
                    {
                        "id": "doc_003",
                        "title": "HOBO Region Network Architecture",
                        "content": "Comprehensive overview of HOBO region network architecture including OLT placement, regional connectivity, and capacity planning. Critical for understanding regional network topology.",
                        "document_type": DocumentType.REFERENCE,
                        "keywords": ["HOBO", "architecture", "network", "regional", "topology"],
                        "usefulness_score": 0.85,
                        "embedding": [0.15] * 384  # Mock embedding
                    }
                ]
            
            async def search_documents(self, query: str, limit: int = 10):
                """Mock document search"""
                query_lower = query.lower()
                results = []
                
                for doc_data in self.sample_docs:
                    # Simple keyword matching
                    content = doc_data["content"].lower()
                    title = doc_data["title"].lower()
                    keywords_text = " ".join(doc_data["keywords"]).lower()
                    
                    if any(word in content or word in title or word in keywords_text 
                           for word in query_lower.split()):
                        doc = Document(**doc_data)
                        results.append(doc)
                
                return results[:limit]
            
            async def similarity_search(self, query_embedding, limit=10, threshold=0.5, document_types=None):
                """Mock vector similarity search"""
                results = []
                
                for doc_data in self.sample_docs:
                    # Mock similarity calculation
                    similarity = 0.8 + (hash(doc_data["id"]) % 100) / 500  # Mock similarity 0.6-0.8
                    
                    if similarity >= threshold:
                        doc = Document(**doc_data)
                        results.append((doc, similarity))
                
                # Sort by similarity
                results.sort(key=lambda x: x[1], reverse=True)
                return results[:limit]
            
            async def get_document(self, document_id: str):
                """Get document by ID"""
                for doc_data in self.sample_docs:
                    if doc_data["id"] == document_id:
                        return Document(**doc_data)
                return None
                
            async def store_document(self, document):
                """Store document (mock)"""
                return document.id
                
            async def index_document(self, document, embedding):
                """Index document (mock)"""
                return True
            
            # Add other required methods as no-ops for demo
            async def update_document(self, document): return True
            async def create_conversation(self, session_id, user_context, conversation_id=None): return "conv_001"
            async def get_conversation(self, conversation_id): return None
            async def add_message(self, conversation_id, message): return True
        
        return MockMongoDBAdapter()
    
    async def _create_mock_network_adapter(self):
        """Create mock network adapter with sample FTTH OLT data"""
        
        class MockFTTHOLT:
            def __init__(self, name, region, environment, bandwidth_gbps=10, service_count=150, managed_by_inmanta=True):
                self.name = name
                self.region = region
                self.environment = environment
                self.bandwidth_gbps = bandwidth_gbps
                self.service_count = service_count
                self.managed_by_inmanta = managed_by_inmanta
                self.esi_name = f"ESI_{name}"
                
            def get_health_summary(self):
                return {
                    "name": self.name,
                    "region": self.region,
                    "environment": self.environment,
                    "bandwidth_gbps": self.bandwidth_gbps,
                    "service_count": self.service_count,
                    "managed_by_inmanta": self.managed_by_inmanta,
                    "esi_name": self.esi_name,
                    "connection_type": "1x10G" if self.bandwidth_gbps == 10 else "1x100G",
                    "complete_config": self.managed_by_inmanta and self.service_count > 0
                }
            
            def is_production(self):
                return self.environment == "PRODUCTION"
            
            def has_complete_config(self):
                return self.managed_by_inmanta and self.service_count > 0
                
            def calculate_bandwidth_gbps(self):
                return self.bandwidth_gbps
        
        class MockNetworkAdapter:
            def __init__(self):
                self.sample_olts = [
                    MockFTTHOLT("OLT17PROP01", "HOBO", "PRODUCTION", 10, 200, True),
                    MockFTTHOLT("OLT18PROP02", "HOBO", "PRODUCTION", 10, 150, False),  # Issue: not managed
                    MockFTTHOLT("OLT19PROP03", "HOBO", "PRODUCTION", 100, 0, True),    # Issue: no services
                    MockFTTHOLT("OLT20PROP01", "HOBO", "UAT", 10, 50, True),
                    MockFTTHOLT("OLT21GENT01", "GENT", "PRODUCTION", 10, 300, True),
                    MockFTTHOLT("OLT22GENT02", "GENT", "PRODUCTION", 100, 250, True),
                    MockFTTHOLT("OLT23ROES01", "ROES", "PRODUCTION", 10, 180, True),
                ]
            
            async def fetch_ftth_olts(self, filters=None):
                """Fetch FTTH OLTs with optional filtering"""
                olts = self.sample_olts.copy()
                
                if filters:
                    if "region" in filters:
                        olts = [olt for olt in olts if olt.region == filters["region"]]
                    if "environment" in filters:
                        olts = [olt for olt in olts if olt.environment == filters["environment"]]
                    if "managed_by_inmanta" in filters:
                        olts = [olt for olt in olts if olt.managed_by_inmanta == filters["managed_by_inmanta"]]
                
                return olts
            
            async def _load_local_json(self, data_type: str):
                """Mock JSON data loading"""
                if data_type == "lag":
                    return [
                        {"device_name": "CINAALSA01", "lag_id": "lag1", "admin_key": 1001, "status": "active"},
                        {"device_name": "SRPTRO01", "lag_id": "lag2", "admin_key": 1002, "status": "active"}
                    ]
                elif data_type == "mobile_modem":
                    return [
                        {"serial_number": "LPL2408001DF", "hardware_type": "Nokia 5G26-A", "mobile_subscriber_id": "MOBILE-SUB-VPN-001"},
                        {"serial_number": "LPL24080006F", "hardware_type": "Nokia 5G26-A", "mobile_subscriber_id": "MOBILE-SUB-VPN-002"}
                    ]
                return []
        
        return MockNetworkAdapter()
    
    async def _create_mock_llm_adapter(self):
        """Create mock LLM adapter"""
        
        class MockLLMAdapter:
            async def generate_embedding(self, text: str):
                """Generate mock embedding"""
                # Simple hash-based mock embedding
                import hashlib
                hash_obj = hashlib.md5(text.encode())
                hash_int = int(hash_obj.hexdigest(), 16)
                
                # Generate 384-dimensional mock embedding
                embedding = []
                for i in range(384):
                    embedding.append(((hash_int >> (i % 32)) & 1) * 0.1 - 0.05)
                
                return embedding
            
            async def extract_keywords(self, text: str, max_keywords: int = 8):
                """Extract keywords from text (mock)"""
                # Simple keyword extraction
                common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were'}
                words = text.lower().replace('.', '').replace(',', '').split()
                keywords = [word for word in words if len(word) > 3 and word not in common_words]
                
                # Get most frequent words
                word_count = {}
                for word in keywords:
                    word_count[word] = word_count.get(word, 0) + 1
                
                sorted_words = sorted(word_count.items(), key=lambda x: x[1], reverse=True)
                return [word for word, count in sorted_words[:max_keywords]]
            
            async def generate_response(self, messages):
                """Generate mock LLM response"""
                # Extract the user query from the last message
                if messages and messages[-1].content:
                    content = messages[-1].content
                    
                    if "data context" in content.lower():
                        return """Based on the current network data and quality metrics provided:

## Analysis Results

**HOBO Region FTTH OLTs:** Found 4 devices total
- **Production:** 3 OLTs (75% of regional capacity)
- **UAT:** 1 OLT (testing environment)

**Data Quality Assessment:** 🟢 Excellent (87% overall score)
- Completeness: 95% ✅
- Freshness: 90% ✅  
- Consistency: 82% ✅

**Issues Detected:** 2 devices require attention
1. **OLT18PROP02:** Not managed by Inmanta (production risk)
2. **OLT19PROP03:** Zero active services (capacity unused)

**Recommendations:**
💡 Prioritize OLT18PROP02 for Inmanta integration
💡 Investigate OLT19PROP03 service allocation
💡 Regional capacity utilization at 72% - within normal range

**Documentation References:** 
- FTTH OLT Configuration Guide (92% relevance)
- Network Troubleshooting Best Practices (88% relevance)"""
                    
                    elif "how many" in content.lower() and "hobo" in content.lower():
                        return """# HOBO Region FTTH OLT Analysis

**Total FTTH OLTs in HOBO Region:** 4 devices

## Distribution:
- **Production Environment:** 3 OLTs
  - OLT17PROP01: ✅ Operational (200 services)
  - OLT18PROP02: ⚠️ Needs Inmanta management
  - OLT19PROP03: ⚠️ No active services
  
- **UAT Environment:** 1 OLT
  - OLT20PROP01: ✅ Testing (50 services)

## Health Summary:
- **Bandwidth Capacity:** 140 Gbps total
- **Active Services:** 400 services across region
- **Management Status:** 75% Inmanta managed
- **Configuration Health:** 3/4 fully configured

**Next Actions:** Review OLT18PROP02 and OLT19PROP03 configurations."""
                
                return "I can help analyze your network infrastructure. Please provide a specific query about FTTH OLTs, network devices, or configuration issues."
        
        return MockLLMAdapter()
    
    async def run_demo_scenarios(self):
        """Run comprehensive demo scenarios"""
        print("\n" + "="*60)
        print("🎯 SCHEMA-AWARE RAG SYSTEM DEMONSTRATION")
        print("="*60)
        
        # Test scenarios
        scenarios = [
            {
                "name": "Regional Device Inventory",
                "query": "How many FTTH OLTs are in HOBO region?",
                "description": "Tests schema-aware device listing with regional filtering"
            },
            {
                "name": "Configuration Issue Analysis", 
                "query": "Show me FTTH OLTs in HOBO region with configuration issues",
                "description": "Tests data quality assessment and issue detection"
            },
            {
                "name": "Knowledge Base Integration",
                "query": "How to troubleshoot FTTH OLT connectivity problems?",
                "description": "Tests knowledge base search and document retrieval"
            },
            {
                "name": "Complex Analysis Query",
                "query": "What is the total bandwidth capacity in HOBO region and are there any performance concerns?",
                "description": "Tests complex analysis with multiple data points"
            }
        ]
        
        for i, scenario in enumerate(scenarios, 1):
            print(f"\n🔍 Scenario {i}: {scenario['name']}")
            print(f"📝 Description: {scenario['description']}")
            print(f"❓ Query: \"{scenario['query']}\"")
            print("-" * 50)
            
            try:
                # Execute via MCP server (simulating real usage)
                response = await self.server._execute_network_query({
                    "query": scenario["query"],
                    "include_recommendations": True
                })
                
                print("🤖 Response:")
                print(response)
                
            except Exception as e:
                print(f"❌ Error: {e}")
            
            print("\n" + "⏱️ " + "Press Enter to continue...")
            input()
    
    async def interactive_mode(self):
        """Interactive query mode"""
        print("\n" + "="*50)
        print("💬 INTERACTIVE MODE")
        print("="*50)
        print("Enter queries about your network infrastructure.")
        print("Examples:")
        print("- 'Show me all FTTH OLTs in production'")
        print("- 'How many devices need configuration updates?'")
        print("- 'What are the troubleshooting steps for OLT issues?'")
        print("Type 'quit' to exit.\n")
        
        while True:
            try:
                query = input("🔍 Query: ").strip()
                
                if query.lower() in ['quit', 'exit', 'q']:
                    break
                
                if not query:
                    continue
                
                print("\n🤖 Processing query...")
                
                response = await self.server._execute_network_query({
                    "query": query,
                    "include_recommendations": True
                })
                
                print(f"\n📋 Response:\n{response}\n")
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"❌ Error: {e}\n")
    
    def print_system_overview(self):
        """Print system architecture overview"""
        print("\n" + "="*70)
        print("🏗️ SCHEMA-AWARE RAG SYSTEM ARCHITECTURE")
        print("="*70)
        
        architecture = """
┌─────────────────────────────────────────────────────────────────┐
│                     🎯 QUERY PROCESSING LAYER                   │
├─────────────────────────────────────────────────────────────────┤
│  MCP Server → Query Controller → Enhanced RAG Fusion Analyzer  │
└─────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
┌─────────────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│   📚 KNOWLEDGE BASE     │ │  🧠 SCHEMA      │ │  🌐 LIVE DATA   │
│                         │ │     ANALYSIS    │ │                 │  
│ • Vector embeddings     │ │                 │ │ • FTTH OLTs     │
│ • Document search       │ │ • Schema registry│ │ • Network APIs  │
│ • Similarity matching   │ │ • Quality service│ │ • Real-time     │
│ • Business ranking      │ │ • Context builder│ │   health data   │
└─────────────────────────┘ └─────────────────┘ └─────────────────┘
                    │               │               │
                    └───────────────┼───────────────┘
                                    │
┌─────────────────────────────────────────────────────────────────┐
│                   ⚡ INTELLIGENT RESPONSE GENERATION            │
├─────────────────────────────────────────────────────────────────┤
│  Rich Context = Documents + Schema + Data + Quality Metrics    │
│             │                                                   │
│             ▼                                                   │
│  LLM receives comprehensive context for intelligent analysis    │
└─────────────────────────────────────────────────────────────────┘
        """
        
        print(architecture)
        
        print("\n🎯 KEY INNOVATIONS:")
        print("✅ Schema-Aware Context: LLM sees data structure + content")
        print("✅ Quality-Driven Decisions: Automatic data health assessment") 
        print("✅ Real-Time Integration: Live network data + knowledge base")
        print("✅ Business Intelligence: Operational context in responses")
        print("✅ Production Ready: Clean architecture + error handling")


async def main():
    """Main entry point"""
    print("🚀 Network RAG System - Schema-Aware Demonstration")
    print("=" * 55)
    
    demo = NetworkRAGDemo()
    
    # Initialize system
    success = await demo.initialize(use_mock_data=True)
    if not success:
        print("❌ Failed to initialize system. Exiting.")
        return
    
    # Show system overview
    demo.print_system_overview()
    
    print("\n📋 Choose demonstration mode:")
    print("1. 🎯 Run demo scenarios (automated)")
    print("2. 💬 Interactive query mode")
    print("3. 📊 Show system architecture only")
    
    try:
        choice = input("\nSelect mode (1-3): ").strip()
        
        if choice == "1":
            await demo.run_demo_scenarios()
        elif choice == "2":
            await demo.interactive_mode()
        elif choice == "3":
            print("\n✅ Architecture overview shown above.")
        else:
            print("❌ Invalid choice. Exiting.")
            
    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted. Goodbye!")
    except Exception as e:
        print(f"\n❌ Demo error: {e}")
    
    print("\n🎯 Schema-Aware RAG System demonstration completed!")
    print("📋 Review the generated documentation files for full system details.")


if __name__ == "__main__":
    asyncio.run(main())