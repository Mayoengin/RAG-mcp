#!/usr/bin/env python3
"""
Network RAG System - Main Entry Point
Demonstrates RAG system with vectorized health knowledge and LLM integration
"""

import asyncio
import os
import sys
from datetime import datetime, UTC
from typing import Dict, Any, Optional
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Core imports
from network_rag.models import Document, DocumentType
from network_rag.controller.query_controller import QueryController
from network_rag.controller.document_controller import DocumentController
from network_rag.inbound.mcp_server_standard import mcp, initialize_controllers, network_query

# Adapters
from network_rag.outbound.mongodb_adapter import MongoDBAdapter
from network_rag.outbound.network_api_adapter import NetworkAPIAdapter


class NetworkRAGDemo:
    """Demo class to showcase the Network RAG system with vectorized health knowledge"""
    
    def __init__(self):
        self.server = None
        self.query_controller: Optional[QueryController] = None
        self.document_controller: Optional[DocumentController] = None
        
    async def initialize(self, use_mock_data: bool = True):
        """Initialize the Network RAG system"""
        print("🚀 Initializing Network RAG System...")
        
        try:
            # Initialize adapters
            if use_mock_data:
                print("📊 Using mock data with real LLM integration")
                mongodb_adapter = await self._create_mock_mongodb()
                network_adapter = await self._create_mock_network_adapter()
                llm_adapter = await self._create_lm_studio_adapter()
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
                llm_adapter = await self._create_lm_studio_adapter()
            
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
            
            # Initialize RAG analyzer 
            self.query_controller.initialize_rag_analyzer(self.document_controller)
            
            # Initialize MCP server
            initialize_controllers(self.query_controller, self.document_controller)
            self.server = mcp
            
            # Initialize knowledge base
            if not use_mock_data:
                await mongodb_adapter.initialize()
                await self._initialize_health_rules_in_mongodb(mongodb_adapter)
            else:
                await self._initialize_health_rules_in_mock(self.document_controller)
            
            print("✅ System initialized successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Initialization failed: {e}")
            return False
    
    async def _create_lm_studio_adapter(self):
        """Create LM Studio adapter with fallback to mock"""
        
        # Test LM Studio connection first
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                test_payload = {
                    "model": os.getenv("LLM_MODEL_NAME", "llama-3.2-8x3b-moe-dark-champion-instruct-uncensored-abliterated-18.4b@q8_0"),
                    "messages": [{"role": "user", "content": "test"}],
                    "max_tokens": 1,
                    "temperature": 0.1
                }
                async with session.post("http://127.0.0.1:1234/v1/chat/completions", 
                                       json=test_payload, 
                                       timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()
                        if 'choices' in data and len(data['choices']) > 0:
                            print("🤖 LM Studio connected successfully")
                            return await self._create_lm_studio_enhanced_adapter()
                        else:
                            print("⚠️  LM Studio responded but no model available")
                    else:
                        raise Exception(f"HTTP {response.status}")
        except Exception as e:
            print(f"⚠️  LM Studio not available ({str(e)}). Using mock LLM...")
        
        return await self._create_mock_llm_adapter()
    
    async def _create_lm_studio_enhanced_adapter(self):
        """Create LM Studio enhanced adapter"""
        
        mock_llm = await self._create_mock_llm_adapter()
        
        async def lm_studio_generate_response(messages):
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
                    "model": os.getenv("LLM_MODEL_NAME", "llama-3.2-8x3b-moe-dark-champion-instruct-uncensored-abliterated-18.4b@q8_0"),
                    "messages": openai_messages,
                    "max_tokens": int(os.getenv("LLM_MAX_TOKENS", "256")),
                    "temperature": float(os.getenv("LLM_TEMPERATURE", "0.3")),
                    "stream": False
                }
                
                async with aiohttp.ClientSession() as session:
                    async with session.post("http://127.0.0.1:1234/v1/chat/completions", 
                                          json=payload, 
                                          timeout=aiohttp.ClientTimeout(total=15)) as response:
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
        
        mock_llm.generate_response = lm_studio_generate_response
        return mock_llm
    
    async def _initialize_health_rules_in_mongodb(self, mongodb_adapter):
        """Initialize health rules in real MongoDB"""
        try:
            from network_rag.services.health_rules_initializer import HealthRulesInitializer
            
            print("🏥 Initializing vectorized health knowledge in MongoDB...")
            initializer = HealthRulesInitializer(mongodb_adapter)
            success = await initializer.initialize_health_rules()
            
            if success:
                print("✅ Vectorized health knowledge loaded successfully")
            else:
                print("⚠️  Health rules initialization completed with warnings")
                
        except Exception as e:
            print(f"⚠️  Could not initialize health rules: {e}")
    
    async def _initialize_health_rules_in_mock(self, document_controller):
        """Initialize vectorized health rules in mock storage"""
        try:
            from network_rag.services.health_rules_initializer import HealthRulesInitializer
            
            print("🏥 Loading vectorized health knowledge into mock storage...")
            
            knowledge_port = document_controller.knowledge_port
            if hasattr(knowledge_port, 'store_health_rule'):
                print("📋 Using vectorized health rules collection")
                initializer = HealthRulesInitializer(knowledge_port)
                success = await initializer.initialize_health_rules()
                
                if success:
                    print("✅ Vectorized health knowledge loaded successfully")
                else:
                    print("⚠️  Health rules initialization completed with warnings")
            else:
                print("⚠️  Mock adapter doesn't support vectorized health rules")
                
        except Exception as e:
            print(f"⚠️  Could not initialize vectorized health rules: {e}")
    
    async def _create_mock_mongodb(self):
        """Create mock MongoDB adapter with vectorized health support"""
        
        class MockMongoDBAdapter:
            def __init__(self):
                self.documents = []
                self.health_rules = []  # Separate vectorized health rules storage
                self.health_vectors = []  # Vector embeddings storage
                self.sample_docs = [
                    {
                        "id": "doc_001",
                        "title": "FTTH OLT Configuration Guide", 
                        "content": "Complete guide for configuring Fiber To The Home Optical Line Terminals. Covers HOBO region deployment, bandwidth allocation, and Inmanta management integration.",
                        "document_type": DocumentType.CONFIGURATION_GUIDE,
                        "keywords": ["FTTH", "OLT", "configuration", "HOBO", "Inmanta"],
                        "usefulness_score": 0.92,
                        "embedding": [0.1] * 384
                    },
                    {
                        "id": "doc_002",
                        "title": "Network Troubleshooting Best Practices",
                        "content": "Best practices for troubleshooting FTTH networks including OLT diagnostics, LAG configuration issues, and mobile modem connectivity problems.",
                        "document_type": DocumentType.TROUBLESHOOTING,
                        "keywords": ["troubleshooting", "FTTH", "diagnostics", "LAG", "mobile"],
                        "usefulness_score": 0.88,
                        "embedding": [0.2] * 384
                    },
                    {
                        "id": "doc_003",
                        "title": "HOBO Region Network Architecture",
                        "content": "Comprehensive overview of HOBO region network architecture including OLT placement, regional connectivity, and capacity planning.",
                        "document_type": DocumentType.API_REFERENCE,
                        "keywords": ["HOBO", "architecture", "network", "regional", "topology"],
                        "usefulness_score": 0.85,
                        "embedding": [0.15] * 384
                    }
                ]
            
            async def search_documents(self, query: str, limit: int = 10):
                query_lower = query.lower()
                results = []
                
                for doc_data in self.sample_docs:
                    content = doc_data["content"].lower()
                    title = doc_data["title"].lower()
                    keywords_text = " ".join(doc_data["keywords"]).lower()
                    
                    if any(word in content or word in title or word in keywords_text 
                           for word in query_lower.split()):
                        doc = Document(**doc_data)
                        results.append(doc)
                
                return results[:limit]
            
            async def similarity_search(self, query_embedding, limit=10, threshold=0.5, document_types=None):
                results = []
                for doc_data in self.sample_docs:
                    similarity = 0.8 + (hash(doc_data["id"]) % 100) / 500
                    if similarity >= threshold:
                        doc = Document(**doc_data)
                        results.append((doc, similarity))
                results.sort(key=lambda x: x[1], reverse=True)
                return results[:limit]
            
            # Vectorized health rules methods
            async def store_health_rule(self, health_rule_data):
                self.health_rules = [r for r in self.health_rules if r.get('id') != health_rule_data['id']]
                self.health_rules.append(health_rule_data)
                return health_rule_data['id']
            
            async def get_health_rule(self, rule_id):
                for rule in self.health_rules:
                    if rule.get('id') == rule_id:
                        return rule
                return None
            
            async def search_health_rules(self, device_type=None, rule_type=None, limit=10):
                results = []
                for rule in self.health_rules:
                    if device_type and rule.get('device_type') != device_type:
                        continue
                    if rule_type and rule.get('rule_type') != rule_type:
                        continue
                    results.append(rule)
                    if len(results) >= limit:
                        break
                return results
            
            async def store_health_rule_embedding(self, rule_id, embedding, model="default"):
                # Remove existing embedding
                self.health_vectors = [v for v in self.health_vectors if not (v.get('rule_id') == rule_id and v.get('embedding_model') == model)]
                
                # Add new embedding
                vector_data = {
                    'rule_id': rule_id,
                    'embedding': embedding,
                    'embedding_model': model,
                    'created_at': datetime.now(UTC)
                }
                self.health_vectors.append(vector_data)
                return True
            
            async def find_similar_health_rules(self, query_embedding, limit=5, device_type=None):
                if not self.health_vectors:
                    return []
                
                similar_rules = []
                for vector in self.health_vectors:
                    rule_embedding = vector.get('embedding', [])
                    if not rule_embedding:
                        continue
                    
                    # Calculate cosine similarity
                    similarity = self._calculate_cosine_similarity(query_embedding, rule_embedding)
                    
                    # Get the actual rule
                    rule_id = vector.get('rule_id')
                    rule = None
                    for health_rule in self.health_rules:
                        if health_rule.get('id') == rule_id:
                            rule = health_rule
                            break
                    
                    if rule and (not device_type or rule.get('device_type') == device_type):
                        similar_rules.append((rule, similarity))
                
                similar_rules.sort(key=lambda x: x[1], reverse=True)
                return similar_rules[:limit]
            
            def _calculate_cosine_similarity(self, vec1, vec2):
                if len(vec1) != len(vec2):
                    return 0.0
                try:
                    dot_product = sum(a * b for a, b in zip(vec1, vec2))
                    magnitude1 = sum(a * a for a in vec1) ** 0.5
                    magnitude2 = sum(a * a for a in vec2) ** 0.5
                    if magnitude1 == 0 or magnitude2 == 0:
                        return 0.0
                    return dot_product / (magnitude1 * magnitude2)
                except:
                    return 0.0
            
            # Stub methods for interface compliance
            async def get_document(self, document_id: str): 
                for doc_data in self.sample_docs:
                    if doc_data["id"] == document_id:
                        return Document(**doc_data)
                return None
            async def store_document(self, document): return document.id
            async def index_document(self, document, embedding): return True
            async def find_similar_documents(self, document_id, limit=10, threshold=0.7): return []
            async def get_document_embedding(self, document_id): return None
            async def remove_document_from_index(self, document_id): return True
            async def update_document_embedding(self, document_id, embedding): return True
            async def get_index_stats(self): return {"document_count": len(self.sample_docs)}
            async def rebuild_index(self, documents=None): return True
            async def batch_similarity_search(self, query_embeddings, limit=10, threshold=0.7): return []
            async def cluster_documents(self, num_clusters=5, document_types=None): return {}
            async def get_embedding_dimension(self): return 384
            async def delete_health_rule(self, rule_id): 
                initial_count = len(self.health_rules)
                self.health_rules = [r for r in self.health_rules if r.get('id') != rule_id]
                self.health_vectors = [v for v in self.health_vectors if v.get('rule_id') != rule_id]
                return len(self.health_rules) < initial_count
            async def get_health_rule_embedding(self, rule_id, model="default"):
                for vector in self.health_vectors:
                    if vector.get('rule_id') == rule_id and vector.get('embedding_model') == model:
                        return vector.get('embedding')
                return None
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
                self.connection_type = "1x10G" if bandwidth_gbps == 10 else "1x100G"
                # Important: Direct attribute for health analysis
                self.complete_config = managed_by_inmanta and service_count > 0
                
            def get_health_summary(self):
                return {
                    "name": self.name,
                    "region": self.region,
                    "environment": self.environment,
                    "bandwidth_gbps": self.bandwidth_gbps,
                    "service_count": self.service_count,
                    "managed_by_inmanta": self.managed_by_inmanta,
                    "esi_name": self.esi_name,
                    "connection_type": self.connection_type,
                    "complete_config": self.complete_config
                }
            
            def is_production(self):
                return self.environment == "PRODUCTION"
            
            def has_complete_config(self):
                return self.complete_config
        
        class MockNetworkAdapter:
            def __init__(self):
                self.sample_olts = [
                    MockFTTHOLT("OLT17PROP01", "HOBO", "PRODUCTION", 10, 200, True),
                    MockFTTHOLT("OLT18PROP02", "HOBO", "PRODUCTION", 10, 150, False),  # Not managed
                    MockFTTHOLT("OLT19PROP03", "HOBO", "PRODUCTION", 100, 0, True),    # No services
                    MockFTTHOLT("OLT20PROP01", "HOBO", "UAT", 10, 50, True),
                    MockFTTHOLT("OLT21GENT01", "GENT", "PRODUCTION", 10, 300, True),
                    MockFTTHOLT("OLT22GENT02", "GENT", "PRODUCTION", 100, 250, True),
                    MockFTTHOLT("OLT23ROES01", "ROES", "PRODUCTION", 10, 180, True),
                ]
            
            async def fetch_ftth_olts(self, filters=None):
                olts = self.sample_olts.copy()
                
                if filters:
                    if "region" in filters:
                        olts = [olt for olt in olts if olt.region == filters["region"]]
                    if "environment" in filters:
                        olts = [olt for olt in olts if olt.environment == filters["environment"]]
                    if "managed_by_inmanta" in filters:
                        olts = [olt for olt in olts if olt.managed_by_inmanta == filters["managed_by_inmanta"]]
                
                return olts
        
        return MockNetworkAdapter()
    
    async def _create_mock_llm_adapter(self):
        """Create mock LLM adapter as fallback"""
        
        class MockLLMAdapter:
            async def generate_embedding(self, text: str):
                import hashlib
                hash_obj = hashlib.md5(text.encode())
                hash_int = int(hash_obj.hexdigest(), 16)
                embedding = []
                for i in range(384):
                    embedding.append(((hash_int >> (i % 32)) & 1) * 0.1 - 0.05)
                return embedding
            
            async def extract_keywords(self, text: str, max_keywords: int = 8):
                common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were'}
                words = text.lower().replace('.', '').replace(',', '').split()
                keywords = [word for word in words if len(word) > 3 and word not in common_words]
                word_count = {}
                for word in keywords:
                    word_count[word] = word_count.get(word, 0) + 1
                sorted_words = sorted(word_count.items(), key=lambda x: x[1], reverse=True)
                return [word for word, count in sorted_words[:max_keywords]]
            
            async def generate_response(self, messages):
                return "Mock LLM unavailable. Please configure a real LLM service (LM Studio, Ollama, etc.) to get intelligent network analysis."
        
        return MockLLMAdapter()
    
    async def run_demo_scenarios(self):
        """Run demo scenarios showcasing vectorized health knowledge"""
        print("\n" + "="*60)
        print("🎯 NETWORK RAG SYSTEM DEMONSTRATION")
        print("="*60)
        
        scenarios = [
            {
                "name": "Regional Device Inventory",
                "query": "How many FTTH OLTs are in HOBO region?",
                "description": "Tests device listing with vectorized health analysis"
            }
        ]
        
        for i, scenario in enumerate(scenarios, 1):
            print(f"\n🔍 Scenario {i}: {scenario['name']}")
            print(f"📝 Description: {scenario['description']}")
            print(f"❓ Query: \"{scenario['query']}\"")
            print("-" * 50)
            
            try:
                response = await network_query(
                    query=scenario["query"],
                    include_recommendations=True
                )
                print("🤖 Response:")
                print(response)
            except Exception as e:
                print(f"❌ Error: {e}")
            
            print("\n" + "-" * 50)
    
    async def interactive_mode(self):
        """Interactive query mode"""
        print("\n" + "="*50)
        print("💬 INTERACTIVE MODE - Vectorized Health Knowledge")
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
                
                print("\n🤖 Processing query with vectorized knowledge...")
                
                response = await network_query(
                    query=query,
                    include_recommendations=True
                )
                
                print(f"\n📋 Response:\n{response}\n")
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"❌ Error: {e}\n")
    
    def print_system_overview(self):
        """Print concise system overview"""
        print("\n" + "="*60)
        print("🏗️  NETWORK RAG SYSTEM - ARCHITECTURE OVERVIEW")
        print("="*60)
        
        print("\\n📊 SYSTEM FEATURES:")
        print("┌─────────────────────────────────────────────────────────┐")
        print("│ ✅ VECTORIZED HEALTH KNOWLEDGE                          │")
        print("│   • 384-dimensional embeddings for health rules        │")
        print("│   • Semantic similarity search for rule matching       │")
        print("│   • Cosine similarity scoring for relevance            │")
        print("│                                                         │")
        print("│ ✅ INTELLIGENT QUERY PROCESSING                         │")
        print("│   • RAG fusion with multi-strategy document search     │")
        print("│   • Pattern analysis for automatic tool selection      │")
        print("│   • Context-aware LLM integration                      │")
        print("│                                                         │")
        print("│ ✅ NETWORK DEVICE INTEGRATION                           │")
        print("│   • Real-time FTTH OLT data retrieval                  │")
        print("│   • Regional filtering (HOBO, GENT, ROES, ASSE)        │")
        print("│   • Health scoring with knowledge-based rules          │")
        print("│                                                         │")
        print("│ ✅ LLM-POWERED ANALYSIS                                 │")
        print("│   • LM Studio integration for intelligent responses    │")
        print("│   • Network engineering insights and recommendations   │")
        print("│   • Context-aware device assessment                    │")
        print("└─────────────────────────────────────────────────────────┘")
        
        print("\\n🔄 QUERY EXECUTION FLOW:")
        print("┌─────────────────────────────────────────────────────────┐")
        print("│ 1. Query Analysis → RAG Fusion Intelligence            │")
        print("│ 2. Tool Selection → Pattern Recognition                │")
        print("│ 3. Data Retrieval → Network Device Fetching            │")
        print("│ 4. Health Analysis → Vectorized Knowledge Search       │")
        print("│ 5. LLM Generation → Intelligent Response Creation      │")
        print("│ 6. Response Assembly → Formatted Output                │")
        print("└─────────────────────────────────────────────────────────┘")
        
        print("\\n🎯 VECTORIZATION ARCHITECTURE:")
        print("┌─────────────────────────────────────────────────────────┐")
        print("│ Knowledge Base → Text Extraction → Embedding           │")
        print("│ 384D Vectors → Similarity Search → Rule Matching       │")
        print("│ Query Embedding → Cosine Distance → Best Rules         │")
        print("└─────────────────────────────────────────────────────────┘")


async def main():
    """Main entry point - streamlined for both interactive and non-interactive use"""
    print("🚀 Network RAG System - Vectorized Health Knowledge Demo")
    print("=" * 60)
    
    demo = NetworkRAGDemo()
    
    # Initialize system
    success = await demo.initialize(use_mock_data=True)
    if not success:
        print("❌ Failed to initialize system. Exiting.")
        return
    
    # Show system overview
    demo.print_system_overview()
    
    # Check if running interactively
    if sys.stdin.isatty():
        # Interactive mode
        print("\n📋 Choose demonstration mode:")
        print("1. 🎯 Run demo scenarios (automated)")
        print("2. 💬 Interactive query mode")
        print("3. 📊 Show architecture overview only")
        
        try:
            choice = input("\nSelect mode (1-3): ").strip()
            
            if choice == "1":
                await demo.run_demo_scenarios()
            elif choice == "2":
                await demo.interactive_mode()
            elif choice == "3":
                print("\n✅ Architecture overview shown above.")
            else:
                print("❌ Invalid choice. Running demo scenarios by default.")
                await demo.run_demo_scenarios()
                
        except (KeyboardInterrupt, EOFError):
            print("\n\n👋 Demo interrupted. Goodbye!")
    else:
        # Non-interactive mode - run demo scenarios automatically
        print("\n🤖 Non-interactive environment detected - running demo scenarios")
        await demo.run_demo_scenarios()
    
    print("\n🎯 Network RAG System demonstration completed!")
    print("📋 System showcases vectorized health knowledge and LLM integration")


if __name__ == "__main__":
    asyncio.run(main())