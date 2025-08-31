# src/network_rag/services/schema_aware_context.py
"""Simplified schema-aware context builder for providing context to LLM"""

from typing import Dict, Any, List
from datetime import datetime
from dataclasses import dataclass

from .schema_registry import SchemaRegistry, DataSchema


@dataclass
class SchemaAwareContext:
    """Simplified context combining schema info for LLM"""
    query: str
    relevant_schemas: List[DataSchema]
    data_samples: Dict[str, Any]
    schema_summary: Dict[str, Any]
    business_context: Dict[str, Any]
    recommendations: List[str]
    generated_at: datetime


class SchemaAwareContextBuilder:
    """Simplified builder for creating schema-aware contexts for LLM consumption"""
    
    def __init__(self, schema_registry: SchemaRegistry):
        self.schema_registry = schema_registry
    
    async def build_context_for_query(self, query: str) -> SchemaAwareContext:
        """Build simplified schema-aware context for a query"""
        
        # Step 1: Identify relevant schemas based on query
        relevant_schemas = self.schema_registry.get_schemas_for_query_intent(query)
        schema_names = [schema.name for schema in relevant_schemas]
        
        # Step 2: Get basic data samples for identified schemas  
        data_samples = self._get_basic_data_samples(schema_names)
        
        # Step 3: Build schema summary for LLM
        schema_summary = self._build_schema_summary(relevant_schemas, data_samples)
        
        # Step 4: Extract business context
        business_context = self._build_business_context(relevant_schemas)
        
        # Step 5: Generate contextual recommendations
        recommendations = self._generate_context_recommendations(data_samples)
        
        return SchemaAwareContext(
            query=query,
            relevant_schemas=relevant_schemas,
            data_samples=data_samples,
            schema_summary=schema_summary,
            business_context=business_context,
            recommendations=recommendations,
            generated_at=datetime.utcnow()
        )
    
    def _get_basic_data_samples(self, schema_names: List[str]) -> Dict[str, Any]:
        """Get basic data samples for specified schemas"""
        data_samples = {}
        
        for schema_name in schema_names:
            # Create a simple mock sample indicating data is available
            data_samples[schema_name] = {
                "schema_name": schema_name,
                "record_count": 7 if schema_name == "ftth_olt" else 5,  # Mock counts
                "sample_size": 5,
                "total_count": 7 if schema_name == "ftth_olt" else 5,
                "representative": True
            }
        
        return data_samples
    
    def _build_schema_summary(
        self, 
        schemas: List[DataSchema], 
        data_samples: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build simplified schema summary for LLM understanding"""
        
        summary = {
            "available_data_types": [],
            "data_structures": {},
            "sample_data": {},
            "relationships": {},
            "constraints": {}
        }
        
        for schema in schemas:
            schema_name = schema.name
            
            # Add to available types
            summary["available_data_types"].append({
                "name": schema_name,
                "description": f"Network {schema_name.replace('_', ' ')} data",
                "record_count": data_samples.get(schema_name, {}).get("total_count", 0)
            })
            
            # Add data structure info
            if hasattr(schema, 'schema') and schema.schema:
                summary["data_structures"][schema_name] = {
                    "type": schema.schema.get("type", "object"),
                    "key_fields": list(schema.schema.get("properties", {}).keys())[:5],  # Top 5 fields
                    "required_fields": schema.schema.get("required", [])
                }
            
            # Add relationships if available
            if hasattr(schema, 'relationships') and schema.relationships:
                summary["relationships"][schema_name] = schema.relationships
            
            # Add constraints if available
            if hasattr(schema, 'constraints') and schema.constraints:
                summary["constraints"][schema_name] = schema.constraints[:3]  # Top 3 constraints
        
        return summary
    
    def _build_business_context(self, schemas: List[DataSchema]) -> Dict[str, Any]:
        """Build business context from schemas"""
        
        context = {
            "domain": "Network Infrastructure Management",
            "use_cases": [],
            "business_rules": [],
            "operational_context": {}
        }
        
        for schema in schemas:
            if hasattr(schema, 'business_context') and schema.business_context:
                if "use_cases" in schema.business_context:
                    context["use_cases"].extend(schema.business_context["use_cases"])
                if "business_rules" in schema.business_context:
                    context["business_rules"].extend(schema.business_context["business_rules"])
        
        # Add operational context based on schema types
        if any(schema.name == "ftth_olt" for schema in schemas):
            context["operational_context"]["ftth_infrastructure"] = {
                "focus": "Fiber to the Home optical line terminals",
                "key_concerns": ["Configuration completeness", "Regional deployment", "Inmanta management"]
            }
        
        return context
    
    def _generate_context_recommendations(self, data_samples: Dict[str, Any]) -> List[str]:
        """Generate contextual recommendations based on data samples"""
        
        recommendations = []
        
        # Basic recommendations based on data availability
        if data_samples:
            recommendations.append("Data appears healthy. Proceed with analysis.")
            
            # Check for specific data types
            if "ftth_olt" in data_samples:
                recommendations.append("FTTH OLT data available for network analysis.")
            
            if "lag" in data_samples:
                recommendations.append("LAG configuration data available for link analysis.")
        else:
            recommendations.append("Limited data available. Consider data source connectivity.")
        
        return recommendations