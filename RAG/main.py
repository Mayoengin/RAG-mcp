#!/usr/bin/env python3
"""
Network RAG System - Main Entry Point
Demonstrates Schema-Aware RAG system with two core scenarios
"""

import asyncio
import os
import sys
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Core imports
from network_rag.models import Document, DocumentType
from network_rag.controller.query_controller import QueryController
from network_rag.controller.document_controller import DocumentController
from network_rag.services.schema_registry import SchemaRegistry
from network_rag.services.data_quality_service import DataQualityService
from network_rag.services.schema_aware_context import SchemaAwareContextBuilder
from network_rag.inbound.mcp_server import MCPServerAdapter

# Adapters
from network_rag.outbound.mongodb_adapter import MongoDBAdapter
from network_rag.outbound.network_api_adapter import NetworkAPIAdapter
from network_rag.outbound.llama_adapter import LlamaAdapter


class NetworkRAGDemo:
    """Demo class to showcase the Schema-Aware RAG system"""
    
    def __init__(self):
        self.server: Optional[MCPServerAdapter] = None
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
                mongodb_adapter = MongoDBAdapter(
                    connection_string=os.getenv("MONGODB_URI", "mongodb://localhost:27017"),
                    database_name="network_rag"
                )
                network_adapter = NetworkAPIAdapter(
                    base_url="file://local",
                    api_key="local_files"
                )
                print("🔍 Checking for LM Studio...")
                try:
                    import aiohttp
                    async with aiohttp.ClientSession() as session:
                        test_payload = {
                            "model": "llama-3.2-8x3b-moe-dark-champion-instruct-uncensored-abliterated-18.4b@q8_0",
                            "messages": [{"role": "user", "content": "Hello"}],
                            "max_tokens": 5,
                            "temperature": 0.1
                        }
                        async with session.post("http://127.0.0.1:1234/v1/chat/completions", 
                                               json=test_payload, 
                                               timeout=aiohttp.ClientTimeout(total=10)) as response:
                            if response.status == 200:
                                data = await response.json()
                                if 'choices' in data and len(data['choices']) > 0:
                                    print("✅ LM Studio is running with your Llama model!")
                                    llm_adapter = await self._create_lm_studio_enhanced_mock()
                                else:
                                    print("⚠️  LM Studio responded but no model available")
                                    llm_adapter = await self._create_mock_llm_adapter()
                            else:
                                raise Exception(f"LM Studio returned {response.status}")
                except Exception as e:
                    print(f"⚠️  LM Studio not available ({str(e)}). Using mock LLM...")
                    llm_adapter = await self._create_mock_llm_adapter()
            
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
                document_controller=self.document_controller
            )
            
            # Initialize RAG analyzer with schema awareness
            self.query_controller.initialize_rag_analyzer(
                self.document_controller, 
                context_builder
            )
            
            # Initialize simplified MCP server
            self.server = MCPServerAdapter(
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
                        "document_type": DocumentType.CONFIGURATION_GUIDE,
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
                        "document_type": DocumentType.API_REFERENCE,
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
            
            # Add stub methods for VectorSearchPort interface
            async def find_similar_documents(self, document_id, limit=10, threshold=0.7): return []
            async def get_document_embedding(self, document_id): return None
            async def remove_document_from_index(self, document_id): return True
            async def update_document_embedding(self, document_id, embedding): return True
            async def get_index_stats(self): return {"document_count": len(self.sample_docs)}
            async def rebuild_index(self, documents=None): return True
            async def batch_similarity_search(self, query_embeddings, limit=10, threshold=0.7): return []
            async def cluster_documents(self, num_clusters=5, document_types=None): return {}
            async def get_embedding_dimension(self): return 384
            async def close(self): pass
        
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
                
                word_count = {}
                for word in keywords:
                    word_count[word] = word_count.get(word, 0) + 1
                
                sorted_words = sorted(word_count.items(), key=lambda x: x[1], reverse=True)
                return [word for word, count in sorted_words[:max_keywords]]
            
            async def generate_response(self, messages):
                """Generate basic mock response"""
                return "Mock LLM unavailable. Please configure a real LLM service (LM Studio, Ollama, etc.) to get intelligent network analysis."
        
        return MockLLMAdapter()
    
    
    async def _create_lm_studio_enhanced_mock(self):
        """Create a mock LLM that uses real LM Studio for generate_response"""
        
        # First create the base mock
        mock_llm = await self._create_mock_llm_adapter()
        
        # Override the generate_response method to use LM Studio
        original_generate_response = mock_llm.generate_response
        
        async def lm_studio_generate_response(messages):
            """Use real LM Studio for response generation"""
            try:
                import aiohttp
                
                # Convert messages to OpenAI format
                openai_messages = []
                for msg in messages:
                    if hasattr(msg, 'role') and hasattr(msg, 'content'):
                        role = "system" if hasattr(msg.role, 'value') and msg.role.value == "system" else "user"
                        openai_messages.append({"role": role, "content": msg.content})
                    elif isinstance(msg, dict) and 'role' in msg and 'content' in msg:
                        openai_messages.append(msg)
                
                payload = {
                    "model": "llama-3.2-8x3b-moe-dark-champion-instruct-uncensored-abliterated-18.4b@q8_0",
                    "messages": openai_messages,
                    "max_tokens": 2048,
                    "temperature": 0.7,
                    "stream": False
                }
                
                async with aiohttp.ClientSession() as session:
                    async with session.post("http://127.0.0.1:1234/v1/chat/completions", 
                                          json=payload, 
                                          timeout=aiohttp.ClientTimeout(total=120)) as response:
                        if response.status == 200:
                            data = await response.json()
                            if 'choices' in data and len(data['choices']) > 0:
                                response_content = data['choices'][0]['message']['content']
                                print(f"🤖 LM Studio response generated ({len(response_content)} chars)")
                                return response_content
                            else:
                                return "LM Studio error: No response choices available. Please check your model is loaded."
                        else:
                            return f"LM Studio API error (HTTP {response.status}). Please check your LM Studio server."
            except Exception as e:
                return f"LM Studio connection error: {str(e)}. Please ensure LM Studio is running on port 1234."
        
        # Replace the generate_response method
        mock_llm.generate_response = lm_studio_generate_response
        
        return mock_llm
    
    async def run_demo_scenarios(self):
        """Run comprehensive demo scenarios"""
        print("\n" + "="*60)
        print("🎯 SCHEMA-AWARE RAG SYSTEM DEMONSTRATION")
        print("="*60)
        
        # Test scenarios - Core functionality demonstration
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
            
            print("\n" + "-" * 50)
    
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
    
    async def run_single_demo_scenario(self):
        """Run a single demo scenario for non-interactive environments"""
        print("\n" + "="*60)
        print("🎯 SINGLE SCENARIO DEMONSTRATION")
        print("="*60)
        
        scenario = {
            "name": "Schema-Aware Regional Analysis",
            "query": "Show me all the FTTH OLTs in GENT region",
            "description": "Demonstrates schema-aware context with live data quality assessment"
        }
        
        print(f"\n🔍 {scenario['name']}")
        print(f"📝 Description: {scenario['description']}")
        print(f"❓ Query: \"{scenario['query']}\"")
        print("-" * 50)
        
        try:
            # Execute the scenario
            response = await self.server._execute_network_query({
                "query": scenario["query"],
                "include_recommendations": True
            })
            
            print("🤖 Response:")
            print(response)
            
            print("\n✅ Demo completed successfully!")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    def print_system_overview(self):
        """Print system architecture overview"""
        print("\n" + "="*70)
        print("🏗️ SCHEMA-AWARE RAG SYSTEM ARCHITECTURE")
        print("="*70)
        
        architecture = """
╔═══════════════════════════════════════════════════════════════════════════════════╗
║                          🎯 SCHEMA-AWARE RAG SYSTEM ARCHITECTURE                  ║
╠═══════════════════════════════════════════════════════════════════════════════════╣
║                                                                                   ║
║  ┌─────────────────┐    ┌──────────────────┐    ┌─────────────────────────────┐  ║
║  │   🌐 USER       │───▶│  📡 MCP SERVER   │───▶│  🎮 QUERY CONTROLLER       │  ║
║  │   INTERFACE     │    │  • Tool routing  │    │  • Business logic          │  ║
║  │   • CLI/API     │    │  • Protocol mgmt │    │  • Multi-source fusion     │  ║
║  └─────────────────┘    └──────────────────┘    └─────────────────────────────┘  ║
║                                                                │                  ║
║                                                                ▼                  ║
║  ┌─────────────────────────────────────────────────────────────────────────────┐  ║
║  │                    🧠 ENHANCED RAG FUSION ANALYZER                         │  ║
║  │  • Query intent analysis     • Schema-aware context building              │  ║
║  │  • Tool selection strategy   • Data quality assessment                    │  ║
║  │  • Document retrieval        • Multi-source data fusion                   │  ║
║  └─────────────────────────────────────────────────────────────────────────────┘  ║
║                              │               │               │                    ║
║        ┌─────────────────────┼───────────────┼───────────────┼─────────────────┐  ║
║        │                     │               │               │                 │  ║
║        ▼                     ▼               ▼               ▼                 ▼  ║
║  ┌──────────┐  ┌──────────────────┐  ┌─────────────┐  ┌─────────────┐  ┌──────────┐ ║
║  │📚 VECTOR │  │🗃️  KNOWLEDGE     │  │🧬 SCHEMA    │  │🌐 NETWORK   │  │💾 DATA   │ ║
║  │EMBEDDINGS│  │   DATABASE       │  │ REGISTRY    │  │   APIS      │  │QUALITY   │ ║
║  │          │  │                  │  │             │  │             │  │SERVICE   │ ║
║  │• Semantic│  │• Config guides   │  │• Data types │  │• FTTH OLTs  │  │• Health  │ ║
║  │  search  │  │• Troubleshooting │  │• Validation │  │• Real-time  │  │  checks  │ ║
║  │• Document│  │• Best practices  │  │• Schemas    │  │  status     │  │• Quality │ ║
║  │  ranking │  │• API references  │  │• Context    │  │• Filtering  │  │  scores  │ ║
║  │• Similarity│ │• Network docs   │  │  builders   │  │• JSON data  │  │• Metrics │ ║
║  └──────────┘  └──────────────────┘  └─────────────┘  └─────────────┘  └──────────┘ ║
║        │                     │               │               │                 │  ║
║        └─────────────────────┼───────────────┼───────────────┼─────────────────┘  ║
║                              │               │               │                    ║
║                              ▼               ▼               ▼                    ║
║  ┌─────────────────────────────────────────────────────────────────────────────┐  ║
║  │                    🎯 INTELLIGENT CONTEXT BUILDER                          │  ║
║  │                                                                             │  ║
║  │  📊 Data Context:           🧠 Schema Context:         📚 Knowledge Context: │  ║
║  │  • Live FTTH OLT data      • Field definitions       • Relevant documents   │  ║
║  │  • Regional filtering      • Data relationships      • Configuration guides │  ║
║  │  • Quality metrics         • Validation rules        • Best practices       │  ║
║  │  • Real-time status        • Type constraints        • Troubleshooting tips │  ║
║  └─────────────────────────────────────────────────────────────────────────────┘  ║
║                                           │                                       ║
║                                           ▼                                       ║
║  ┌─────────────────────────────────────────────────────────────────────────────┐  ║
║  │                      🤖 LARGE LANGUAGE MODEL                               │  ║
║  │                                                                             │  ║
║  │  Input: Rich Context = Live Data + Schema Info + Knowledge Base            │  ║
║  │  ┌─────────────────────────────────────────────────────────────────────┐   │  ║
║  │  │ SYSTEM PROMPT: "You are a network infrastructure analyst..."        │   │  ║
║  │  │ USER CONTEXT:                                                       │   │  ║
║  │  │ • Query: "Show me FTTH OLTs in GENT region"                        │   │  ║
║  │  │ • 5 devices found: OLT17LEUV01, OLT70NIKL01, etc.                 │   │  ║
║  │  │ • Device details: regions, environments, configurations             │   │  ║
║  │  │ • Schema: FTTH OLT data structure and validation rules             │   │  ║
║  │  │ • Knowledge: Network configuration best practices                   │   │  ║
║  │  └─────────────────────────────────────────────────────────────────────┘   │  ║
║  │                                   ▼                                         │  ║
║  │  Output: Intelligent Analysis with Insights & Recommendations              │  ║
║  └─────────────────────────────────────────────────────────────────────────────┘  ║
║                                           │                                       ║
║                                           ▼                                       ║
║  ┌─────────────────────────────────────────────────────────────────────────────┐  ║
║  │                     ✨ INTELLIGENT RESPONSE                                 │  ║
║  │                                                                             │  ║
║  │  🎯 Analysis: "Found 5 FTTH OLTs in GENT region"                          │  ║
║  │  🔍 Insights: "4 production, 1 UAT - mature deployment"                   │  ║
║  │  📊 Details: Device-by-device breakdown with status                        │  ║
║  │  🛠️  Recommendations: "Consider promoting UAT to production"               │  ║
║  │  ⚡ Powered by: Live data + Schema awareness + Domain knowledge           │  ║
║  └─────────────────────────────────────────────────────────────────────────────┘  ║
║                                                                                   ║
╚═══════════════════════════════════════════════════════════════════════════════════╝
        """
        
        print(architecture)
        
        print("\n🎯 KEY INNOVATIONS & CAPABILITIES:")
        print("┌─────────────────────────────────────────────────────────────────────┐")
        print("│  🧠 SCHEMA-AWARE RAG FUSION                                         │")
        print("│  ✅ LLM receives structured data + schema context + domain knowledge│")
        print("│  ✅ Multi-source intelligence: Vector DB + Live APIs + Schemas     │")
        print("│  ✅ Query intent analysis drives intelligent tool selection        │")
        print("│                                                                     │")
        print("│  🌐 REAL-TIME NETWORK INTEGRATION                                  │")
        print("│  ✅ Live FTTH OLT data from network APIs and JSON sources          │")
        print("│  ✅ Regional filtering (GENT, HOBO, ROES, ASSE regions)            │")
        print("│  ✅ Environment-aware (Production, UAT, Test environments)         │")
        print("│  ✅ Inmanta configuration management integration                    │")
        print("│                                                                     │")
        print("│  📊 DATA QUALITY & HEALTH ASSESSMENT                               │")
        print("│  ✅ Automatic data completeness and freshness scoring              │")
        print("│  ✅ Schema validation and constraint checking                       │")
        print("│  ✅ Real-time network device health monitoring                     │")
        print("│                                                                     │")
        print("│  🎯 INTELLIGENT ANALYSIS & RECOMMENDATIONS                         │")
        print("│  ✅ Context-aware insights (production vs UAT analysis)            │")
        print("│  ✅ Network topology understanding and pattern recognition         │")
        print("│  ✅ Actionable recommendations based on operational context        │")
        print("│  ✅ Multi-dimensional analysis: technical + business intelligence  │")
        print("│                                                                     │")
        print("│  🏗️ PRODUCTION-READY ARCHITECTURE                                  │")
        print("│  ✅ Clean separation: Controllers, Services, Adapters, Models      │")
        print("│  ✅ Comprehensive error handling and graceful degradation          │")
        print("│  ✅ MCP protocol integration for tool-based AI interactions       │")
        print("│  ✅ Scalable design supporting multiple data sources & LLM models  │")
        print("└─────────────────────────────────────────────────────────────────────┘")


async def main():
    """Main entry point"""
    print("🚀 Network RAG System - Schema-Aware Demonstration")
    print("=" * 55)
    
    demo = NetworkRAGDemo()
    
    # Initialize system
    success = await demo.initialize(use_mock_data=False)
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
    except EOFError:
        # Handle non-interactive environment by running a demo scenario
        print("\n🎯 Non-interactive environment detected. Running demo scenario...")
        await demo.run_single_demo_scenario()
    except Exception as e:
        print(f"\n❌ Demo error: {e}")
    
    print("\n🎯 Schema-Aware RAG System demonstration completed!")
    print("📋 Review the generated documentation files for full system details.")


if __name__ == "__main__":
    asyncio.run(main())