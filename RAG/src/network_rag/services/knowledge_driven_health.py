# src/network_rag/services/knowledge_driven_health.py
"""Knowledge-driven health analysis service using rules from knowledge base"""

from typing import Dict, Any, List, Optional, Tuple
import re
import ast
import operator

from ..controller.document_controller import DocumentController
from ..models import DocumentType


class KnowledgeDrivenHealthAnalyzer:
    """Analyzes device health using knowledge base rules"""
    
    def __init__(self, document_controller: DocumentController):
        self.document_controller = document_controller
        self._rules_cache = {}  # Cache loaded rules for performance
        
        # Operator mapping for rule evaluation
        self.operators = {
            '==': operator.eq,
            '!=': operator.ne,
            '<': operator.lt,
            '<=': operator.le,
            '>': operator.gt,
            '>=': operator.ge,
            'in': lambda x, y: x in y,
            'not_in': lambda x, y: x not in y
        }
    
    def clear_cache(self):
        """Clear the rules cache to force fresh loading"""
        self._rules_cache.clear()
    
    async def analyze_device_health(
        self, 
        device: Any, 
        device_type: str = "ftth_olt"
    ) -> Dict[str, Any]:
        """
        Analyze device health using knowledge-based rules
        
        Args:
            device: The device object to analyze
            device_type: Type of device (ftth_olt, mobile_modem, etc.)
            
        Returns:
            Health summary dictionary with status, score, and recommendations
        """
        
        # Step 1: Get health rules from knowledge base
        rules = await self._get_health_rules(device_type)
        
        if not rules:
            # Fallback to basic extraction if no rules found
            return self._basic_health_extraction(device)
        
        # Step 2: Extract device data based on rules
        device_data = self._extract_device_data(device, rules)
        
        # Step 3: Evaluate health status
        health_status = self._evaluate_health_status(device_data, rules)
        
        # Step 4: Calculate health score
        health_score = self._calculate_health_score(device_data, rules)
        
        # Step 5: Generate recommendations
        recommendations = self._generate_recommendations(device_data, rules)
        
        # Step 6: Apply environment-specific adjustments
        if hasattr(device, 'environment'):
            env_rules = await self._get_environment_rules(device.environment)
            if env_rules:
                health_status = self._adjust_for_environment(
                    health_status, device_data, env_rules
                )
        
        # Build comprehensive health summary
        health_summary = {
            **device_data,  # Include all extracted fields
            'health_status': health_status,
            'health_score': health_score,
            'risk_level': self._determine_risk_level(health_score),
            'recommendations': recommendations
        }
        
        return health_summary
    
    async def _get_health_rules(self, device_type: str) -> Optional[Dict[str, Any]]:
        """Retrieve health rules using vector search or fallback to text search"""
        
        # Check cache first
        cache_key = f"health_rules_{device_type}"
        if cache_key in self._rules_cache:
            return self._rules_cache[cache_key]
        
        # Try vector search first, then fallback to text search
        try:
            mongodb_adapter = self.document_controller.knowledge_port
            
            # Method 1: Vector search (semantic similarity)
            executable_rules = await self._search_health_rules_by_vector(mongodb_adapter, device_type)
            if executable_rules:
                self._rules_cache[cache_key] = executable_rules
                return executable_rules
            
            # Method 2: Fallback to text search
            health_rules = await mongodb_adapter.search_health_rules(device_type=device_type, rule_type="health_analysis", limit=5)
            
            if health_rules:
                best_rule = health_rules[0]
                executable_rules = best_rule.get('executable_rules', {})
                
                if executable_rules:
                    self._rules_cache[cache_key] = executable_rules
                    return executable_rules
                    
        except Exception as e:
            print(f"Warning: Could not access health rules collection: {e}")
        
        return None
    
    async def _search_health_rules_by_vector(self, mongodb_adapter, device_type: str) -> Optional[Dict[str, Any]]:
        """Search health rules using vector similarity"""
        try:
            # Check if vector search is supported
            if not hasattr(mongodb_adapter, 'find_similar_health_rules'):
                return None
            
            # Create query embedding for device type and health analysis
            query_text = f"health analysis rules for {device_type} device monitoring diagnostics"
            query_embedding = self._generate_query_embedding(query_text)
            
            # Search for similar health rules
            similar_rules = await mongodb_adapter.find_similar_health_rules(
                query_embedding, 
                limit=3, 
                device_type=device_type
            )
            
            if similar_rules:
                # Get the most similar rule (highest similarity score)
                best_rule, similarity_score = similar_rules[0]
                print(f"🔍 Found health rule via vector search (similarity: {similarity_score:.3f})")
                
                executable_rules = best_rule.get('executable_rules', {})
                if executable_rules:
                    return executable_rules
                    
        except Exception as e:
            print(f"Warning: Vector search failed, falling back to text search: {e}")
            
        return None
    
    def _generate_query_embedding(self, query_text: str) -> List[float]:
        """Generate embedding for query text (mock implementation)"""
        import hashlib
        
        # Simple mock embedding generation (same logic as initializer)
        text_hash = hashlib.md5(query_text.lower().encode()).hexdigest()
        
        embedding = []
        for i in range(0, 384):
            hash_part = text_hash[(i * 2) % len(text_hash):((i * 2) + 2) % len(text_hash)]
            if len(hash_part) < 2:
                hash_part = text_hash[:2]
            
            int_val = int(hash_part, 16) if hash_part else 0
            float_val = (int_val / 255.0) * 2.0 - 1.0
            embedding.append(float_val)
        
        # Add semantic weighting for health analysis queries
        if 'health' in query_text.lower():
            embedding[0] += 0.4
        if 'analysis' in query_text.lower():
            embedding[1] += 0.3
        if 'ftth' in query_text.lower():
            embedding[2] += 0.3
        if 'mobile' in query_text.lower():
            embedding[3] += 0.3
        
        # Normalize
        max_val = max(abs(x) for x in embedding) or 1.0
        embedding = [x / max_val for x in embedding]
        
        return embedding
    
    async def _get_executable_rules_from_mongodb(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get executable rules metadata from MongoDB"""
        try:
            # Search for executable rules metadata document
            executable_id = f"{document_id}_executable"
            metadata_docs = await self.document_controller.search_documents(
                query=f"executable rules {document_id}",
                limit=3
            )
            
            # Look for the metadata document
            for doc in metadata_docs:
                doc_content = doc.content if hasattr(doc, 'content') else doc.get('content', '')
                doc_title = doc.title if hasattr(doc, 'title') else doc.get('title', '')
                
                if 'executable' in doc_title.lower() or document_id in doc_content:
                    # Parse JSON content
                    import json
                    try:
                        metadata = json.loads(doc_content)
                        if 'executable_rules' in metadata:
                            return metadata['executable_rules']
                    except json.JSONDecodeError:
                        continue
            
            return None
            
        except Exception as e:
            print(f"Warning: Could not fetch executable rules for {document_id}: {e}")
            return None
    
    async def _get_environment_rules(self, environment: str) -> Optional[Dict[str, Any]]:
        """Get environment-specific rule adjustments from health rules collection"""
        
        cache_key = f"env_rules_{environment}"
        if cache_key in self._rules_cache:
            return self._rules_cache[cache_key]
        
        try:
            # Search for environment-specific rules in health rules collection
            mongodb_adapter = self.document_controller.knowledge_port
            health_rules = await mongodb_adapter.search_health_rules(rule_type="health_analysis", limit=10)
            
            for rule in health_rules:
                executable_rules = rule.get('executable_rules', {})
                env_overrides = executable_rules.get('environment_overrides', {})
                if env_overrides and environment.upper() in env_overrides:
                    rules = env_overrides[environment.upper()]
                    self._rules_cache[cache_key] = rules
                    return rules
        except Exception as e:
            print(f"Warning: Could not get environment rules: {e}")
        
        return None
    
    def _extract_device_data(self, device: Any, rules: Dict[str, Any]) -> Dict[str, Any]:
        """Extract relevant fields from device based on rules"""
        
        device_data = {}
        summary_fields = rules.get('summary_fields', [])
        
        for field in summary_fields:
            # Support nested field access (e.g., "config.bandwidth")
            if '.' in field:
                value = self._get_nested_attr(device, field)
            else:
                value = getattr(device, field, None)
            
            # Handle None values with sensible defaults
            if value is None:
                if field in ['service_count', 'bandwidth_gbps']:
                    value = 0
                elif field in ['managed_by_inmanta', 'complete_config']:
                    value = False
                elif field in ['name', 'region', 'environment', 'esi_name', 'connection_type']:
                    value = 'Unknown'
            
            device_data[field] = value
        
        
        return device_data
    
    def _evaluate_health_status(
        self, 
        device_data: Dict[str, Any], 
        rules: Dict[str, Any]
    ) -> str:
        """Evaluate device health status based on rules"""
        
        health_conditions = rules.get('health_conditions', {})
        
        # Check conditions in order of severity
        for status in ['CRITICAL', 'WARNING', 'DEGRADED', 'HEALTHY']:
            if status not in health_conditions:
                continue
                
            conditions = health_conditions[status]
            if self._check_conditions(device_data, conditions):
                return status
        
        return 'UNKNOWN'
    
    def _check_conditions(
        self, 
        device_data: Dict[str, Any], 
        conditions: List[Dict[str, Any]]
    ) -> bool:
        """Check if any condition in the list is met"""
        
        for condition in conditions:
            if 'condition' in condition:
                # Complex condition as string
                if self._evaluate_complex_condition(device_data, condition['condition']):
                    return True
            else:
                # Simple field-operator-value condition
                field = condition.get('field')
                op = condition.get('operator', '==')
                value = condition.get('value')
                
                if field in device_data:
                    device_value = device_data[field]
                    if self._compare_values(device_value, op, value):
                        return True
        
        return False
    
    def _evaluate_complex_condition(
        self, 
        device_data: Dict[str, Any], 
        condition_str: str
    ) -> bool:
        """Evaluate complex condition string"""
        
        try:
            # Replace field names with actual values
            eval_str = condition_str
            for field, value in device_data.items():
                # Handle different value types
                if isinstance(value, str):
                    replacement = f"'{value}'"
                elif value is None:
                    replacement = "None"
                elif isinstance(value, bool):
                    replacement = str(value)
                else:
                    replacement = str(value)
                
                eval_str = eval_str.replace(field, replacement)
            
            # Safe evaluation (only allows basic operations)
            return eval(eval_str, {"__builtins__": {}}, {})
        except:
            return False
    
    def _compare_values(self, device_value: Any, op: str, rule_value: Any) -> bool:
        """Compare device value with rule value using operator"""
        
        # Handle None values
        if device_value is None:
            if op == '==':
                return rule_value is None
            elif op == '!=':
                return rule_value is not None
            else:
                # For numeric comparisons, treat None as 0
                device_value = 0
                
        if op in self.operators:
            try:
                return self.operators[op](device_value, rule_value)
            except (TypeError, AttributeError):
                # Handle comparison errors (like None < int)
                return False
        return False
    
    def _calculate_health_score(
        self, 
        device_data: Dict[str, Any], 
        rules: Dict[str, Any]
    ) -> int:
        """Calculate numeric health score based on scoring rules"""
        
        base_score = 100
        score = base_score
        
        scoring_rules = rules.get('scoring_rules', [])
        
        for rule in scoring_rules:
            condition = rule.get('condition', '')
            impact = rule.get('impact', 0)
            
            if self._evaluate_complex_condition(device_data, condition):
                score += impact
        
        # Ensure score is within bounds and handle None
        if score is None:
            return 50  # Default middle score
        
        try:
            score = int(score)
            return max(0, min(score, 110))
        except (ValueError, TypeError):
            return 50  # Default middle score
    
    def _generate_recommendations(
        self, 
        device_data: Dict[str, Any], 
        rules: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations based on device state"""
        
        recommendations = []
        recommendation_rules = rules.get('recommendations', [])
        
        for rec_rule in recommendation_rules:
            condition = rec_rule.get('condition', '')
            message = rec_rule.get('message', '')
            priority = rec_rule.get('priority', 'LOW')
            
            if self._evaluate_complex_condition(device_data, condition):
                # Add priority indicator to message if high priority
                if priority == 'HIGH':
                    message = f"[HIGH PRIORITY] {message}"
                recommendations.append(message)
        
        return recommendations[:3]  # Limit to top 3 recommendations
    
    def _determine_risk_level(self, health_score: int) -> str:
        """Determine risk level based on health score"""
        
        # Handle None or invalid scores
        if health_score is None:
            return 'UNKNOWN_RISK'
        
        # Ensure score is numeric
        try:
            score = int(health_score)
        except (ValueError, TypeError):
            return 'UNKNOWN_RISK'
            
        if score < 30:
            return 'HIGH_RISK'
        elif score < 70:
            return 'MEDIUM_RISK'
        else:
            return 'LOW_RISK'
    
    def _adjust_for_environment(
        self, 
        health_status: str, 
        device_data: Dict[str, Any], 
        env_rules: Dict[str, Any]
    ) -> str:
        """Adjust health status based on environment-specific rules"""
        
        # Check if device meets environment requirements
        if env_rules:
            min_services = env_rules.get('min_service_count', 0)
            require_inmanta = env_rules.get('require_inmanta', False)
            require_complete = env_rules.get('require_complete_config', False)
            
            service_count = device_data.get('service_count', 0)
            managed_by_inmanta = device_data.get('managed_by_inmanta', False)
            complete_config = device_data.get('complete_config', False)
            
            # Upgrade to CRITICAL if environment requirements not met
            # Handle None values safely
            service_count = service_count if service_count is not None else 0
            min_services = min_services if min_services is not None else 0
            
            if service_count < min_services:
                return 'CRITICAL'
            if require_inmanta and not managed_by_inmanta:
                return 'CRITICAL'
            if require_complete and not complete_config:
                return 'CRITICAL'
        
        return health_status
    
    def _basic_health_extraction(self, device: Any) -> Dict[str, Any]:
        """Fallback basic health extraction when no rules are available"""
        
        return {
            'name': getattr(device, 'name', 'Unknown'),
            'region': getattr(device, 'region', 'Unknown'),
            'environment': getattr(device, 'environment', 'Unknown'),
            'bandwidth_gbps': getattr(device, 'bandwidth_gbps', 0),
            'service_count': getattr(device, 'service_count', 0),
            'managed_by_inmanta': getattr(device, 'managed_by_inmanta', False),
            'complete_config': getattr(device, 'complete_config', False),
            'health_status': 'UNKNOWN',
            'health_score': 50,
            'risk_level': 'UNKNOWN',
            'recommendations': ['No health rules available for analysis']
        }
    
    def _get_nested_attr(self, obj: Any, path: str) -> Any:
        """Get nested attribute using dot notation"""
        
        attrs = path.split('.')
        for attr in attrs:
            if hasattr(obj, attr):
                obj = getattr(obj, attr)
            else:
                return None
        return obj
    
    def _parse_rules_from_content(self, document: Any) -> Dict[str, Any]:
        """Parse rules from document content if not in executable format"""
        
        # This is a fallback parser for text-based rules
        # In production, you'd want more sophisticated parsing
        
        content = getattr(document, 'content', '') if hasattr(document, 'content') else str(document)
        
        rules = {
            'summary_fields': [],
            'health_conditions': {},
            'scoring_rules': [],
            'recommendations': []
        }
        
        # Simple pattern matching to extract rules from content
        # This is a basic implementation - enhance as needed
        
        if 'CRITICAL:' in content:
            # Extract critical conditions
            critical_match = re.search(r'CRITICAL: (.+?)(?:\n|$)', content)
            if critical_match:
                rules['health_conditions']['CRITICAL'] = [
                    {'condition': critical_match.group(1).strip()}
                ]
        
        return rules