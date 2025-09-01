# src/network_rag/services/health_rules_initializer.py
"""Initialize health rules in MongoDB knowledge base"""

from typing import List, Dict, Any
from datetime import datetime

from ..models import Document, DocumentType
from ..knowledge.health_rules import HealthRulesKnowledge


class HealthRulesInitializer:
    """Initializes health analysis rules in the MongoDB knowledge base"""
    
    def __init__(self, knowledge_port):
        self.knowledge_port = knowledge_port
    
    async def initialize_health_rules(self) -> bool:
        """
        Initialize health rules in MongoDB knowledge base
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            print("📚 Initializing health rules in MongoDB knowledge base...")
            
            # Get all health rules from static definitions
            health_rule_data = HealthRulesKnowledge.get_all_health_rules()
            
            # Check if rules already exist
            existing_rules = await self._check_existing_rules()
            if existing_rules:
                print(f"✅ Health rules already exist in knowledge base ({len(existing_rules)} rules)")
                return True
            
            # Convert to Document objects and store in MongoDB
            documents_created = 0
            
            for rule_data in health_rule_data:
                # Prepare health rule data for separate collection
                health_rule = {
                    "id": rule_data["id"],
                    "title": rule_data["title"],
                    "content": rule_data["content"],
                    "device_type": rule_data.get("executable_rules", {}).get("device_type", "unknown"),
                    "rule_type": "health_analysis",
                    "keywords": rule_data.get("keywords", []),
                    "executable_rules": rule_data.get("executable_rules", {}),
                    "usefulness_score": 0.95,
                    "version": rule_data.get("version", "1.0"),
                    "author": rule_data.get("author", "System"),
                    "created_at": rule_data.get("created_at", datetime.utcnow())
                }
                
                # Store in separate health rules collection
                try:
                    rule_id = await self.knowledge_port.store_health_rule(health_rule)
                    if rule_id:
                        documents_created += 1
                        print(f"  ✅ Created health rule: {health_rule['title']} (device_type: {health_rule['device_type']})")
                        
                        # Generate and store embedding for vector search
                        await self._generate_and_store_health_embedding(rule_id, health_rule)
                    else:
                        print(f"  ❌ Failed to create health rule: {health_rule['title']}")
                except Exception as e:
                    print(f"  ❌ Failed to create health rule {health_rule['title']}: {e}")
            
            print(f"🎉 Successfully initialized {documents_created} health rules in MongoDB!")
            return documents_created > 0
            
        except Exception as e:
            print(f"❌ Failed to initialize health rules: {e}")
            return False
    
    async def _check_existing_rules(self) -> List[Dict[str, Any]]:
        """Check if health rules already exist in the separate health rules collection"""
        try:
            # Check health rules collection directly
            existing = await self.knowledge_port.search_health_rules(rule_type="health_analysis", limit=10)
            return existing
            
        except Exception as e:
            print(f"Warning: Could not check existing rules: {e}")
            return []
    
    async def _store_executable_rules(self, document_id: str, executable_rules: Dict[str, Any]):
        """Store executable rules as separate metadata document"""
        try:
            metadata_doc = Document(
                id=f"{document_id}_executable",
                title=f"Executable Rules for {document_id}",
                content=f"Executable rules metadata for health analysis document {document_id}",
                document_type=DocumentType.CONFIGURATION_GUIDE,
                keywords=["executable_rules", "metadata", "health_analysis"],
                topics=["system_metadata"],
                tags=["executable", "rules", "metadata"],
                usefulness_score=1.0  # Maximum score for executable rules
            )
            
            # Store the executable rules in the document content as JSON
            import json
            metadata_doc.content = json.dumps({
                "parent_document_id": document_id,
                "executable_rules": executable_rules,
                "rule_type": "health_analysis",
                "created_at": datetime.utcnow().isoformat()
            }, indent=2)
            
            await self.knowledge_port.store_document(metadata_doc)
            print(f"    ✅ Stored executable rules for {document_id}")
            
        except Exception as e:
            print(f"    ⚠️  Could not store executable rules for {document_id}: {e}")
    
    async def update_health_rule(
        self, 
        rule_id: str, 
        updated_content: str = None,
        updated_executable_rules: Dict[str, Any] = None
    ) -> bool:
        """
        Update an existing health rule in MongoDB
        
        Args:
            rule_id: ID of the rule to update
            updated_content: New content for the rule
            updated_executable_rules: New executable rules
            
        Returns:
            bool: True if successful
        """
        try:
            # Find the existing document
            documents = await self.knowledge_port.search_documents(
                query=f"id:{rule_id}",
                limit=1
            )
            
            if not documents:
                print(f"❌ Health rule not found: {rule_id}")
                return False
            
            document = documents[0]
            
            # Update content if provided
            if updated_content:
                document.content = updated_content
                document.updated_at = datetime.utcnow()
                
                # Update in MongoDB using store_document (with upsert)
                try:
                    document_id = await self.knowledge_port.store_document(document)
                    if document_id:
                        print(f"✅ Updated health rule content: {rule_id}")
                    else:
                        print(f"❌ Failed to update health rule content: {rule_id}")
                        return False
                except Exception as e:
                    print(f"❌ Failed to update health rule content {rule_id}: {e}")
                    return False
            
            # Update executable rules if provided
            if updated_executable_rules:
                await self._store_executable_rules(rule_id, updated_executable_rules)
                print(f"✅ Updated executable rules: {rule_id}")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to update health rule {rule_id}: {e}")
            return False
    
    async def delete_health_rule(self, rule_id: str) -> bool:
        """
        Delete a health rule from separate health rules collection
        
        Args:
            rule_id: ID of the rule to delete
            
        Returns:
            bool: True if successful
        """
        try:
            # Delete from health rules collection
            success = await self.knowledge_port.delete_health_rule(rule_id)
            
            if success:
                print(f"✅ Deleted health rule: {rule_id}")
                return True
            else:
                print(f"❌ Failed to delete health rule: {rule_id}")
                return False
                
        except Exception as e:
            print(f"❌ Failed to delete health rule {rule_id}: {e}")
            return False
    
    async def list_health_rules(self) -> List[Dict[str, Any]]:
        """List all health rules in the separate health rules collection"""
        try:
            # Get all health rules from separate collection
            health_rules = await self.knowledge_port.search_health_rules(rule_type="health_analysis", limit=50)
            return health_rules
            
        except Exception as e:
            print(f"❌ Failed to list health rules: {e}")
            return []
    
    async def _generate_and_store_health_embedding(self, rule_id: str, health_rule: Dict[str, Any]):
        """Generate and store embedding for health rule for vector search"""
        try:
            # Check if the knowledge port supports embeddings
            if not hasattr(self.knowledge_port, 'store_health_rule_embedding'):
                return  # Skip if no vector support
            
            # Create text for embedding from rule content
            embedding_text = self._create_embedding_text(health_rule)
            
            # Generate embedding using simple word-based approach (mock)
            # In production, use proper embedding model (OpenAI, sentence-transformers, etc.)
            embedding = self._generate_mock_embedding(embedding_text)
            
            # Store the embedding
            success = await self.knowledge_port.store_health_rule_embedding(rule_id, embedding)
            if success:
                print(f"    🔍 Generated vector embedding for {rule_id}")
            else:
                print(f"    ⚠️  Failed to store embedding for {rule_id}")
                
        except Exception as e:
            print(f"    ⚠️  Could not generate embedding for {rule_id}: {e}")
    
    def _create_embedding_text(self, health_rule: Dict[str, Any]) -> str:
        """Create comprehensive text for embedding generation"""
        text_parts = []
        
        # Add title and content
        title = health_rule.get('title', '')
        content = health_rule.get('content', '')
        
        text_parts.append(title)
        text_parts.append(content)
        
        # Add device type and keywords
        device_type = health_rule.get('device_type', '')
        keywords = health_rule.get('keywords', [])
        
        text_parts.append(f"Device type: {device_type}")
        text_parts.append(f"Keywords: {' '.join(keywords)}")
        
        # Add executable rules information
        exec_rules = health_rule.get('executable_rules', {})
        if exec_rules:
            # Add summary fields
            fields = exec_rules.get('summary_fields', [])
            if fields:
                text_parts.append(f"Analyzes fields: {' '.join(fields)}")
            
            # Add health conditions
            conditions = exec_rules.get('health_conditions', {})
            for status, rules in conditions.items():
                text_parts.append(f"Health {status.lower()} conditions")
                for rule in rules:
                    if 'condition' in rule:
                        text_parts.append(rule['condition'])
        
        return ' '.join(text_parts)
    
    def _generate_mock_embedding(self, text: str) -> List[float]:
        """Generate mock embedding based on text content (for demo purposes)"""
        import hashlib
        import struct
        
        # Create deterministic embedding based on text hash
        # In production, use proper embedding models like sentence-transformers
        
        # Create hash of text
        text_hash = hashlib.md5(text.lower().encode()).hexdigest()
        
        # Convert to 384-dimensional vector (common embedding size)
        embedding = []
        for i in range(0, 384):
            # Use parts of hash to generate float values between -1 and 1
            hash_part = text_hash[(i * 2) % len(text_hash):((i * 2) + 2) % len(text_hash)]
            if len(hash_part) < 2:
                hash_part = text_hash[:2]
            
            # Convert hex to float
            int_val = int(hash_part, 16) if hash_part else 0
            float_val = (int_val / 255.0) * 2.0 - 1.0  # Scale to -1 to 1
            embedding.append(float_val)
        
        # Add some semantic meaning based on keywords
        if 'ftth' in text.lower():
            embedding[0] += 0.3
        if 'mobile' in text.lower():
            embedding[1] += 0.3
        if 'critical' in text.lower():
            embedding[2] += 0.4
        if 'bandwidth' in text.lower():
            embedding[3] += 0.2
        
        # Normalize to keep in reasonable range
        max_val = max(abs(x) for x in embedding) or 1.0
        embedding = [x / max_val for x in embedding]
        
        return embedding