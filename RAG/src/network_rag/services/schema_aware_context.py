# src/network_rag/services/schema_aware_context.py
"""Schema-aware context builder for providing rich context to LLM"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass

from .schema_registry import SchemaRegistry, DataSchema
from .data_quality_service import DataQualityService, DataQualityMetrics, DataSample


@dataclass
class SchemaAwareContext:
    """Rich context combining data, schema, and quality metrics for LLM"""
    query: str
    relevant_schemas: List[DataSchema]
    data_samples: Dict[str, DataSample]
    quality_metrics: Dict[str, DataQualityMetrics]
    schema_summary: Dict[str, Any]
    business_context: Dict[str, Any]
    recommendations: List[str]
    generated_at: datetime


class SchemaAwareContextBuilder:
    """Builder for creating schema-aware contexts for LLM consumption"""
    
    def __init__(
        self, 
        schema_registry: SchemaRegistry,
        data_quality_service: DataQualityService
    ):
        self.schema_registry = schema_registry
        self.data_quality_service = data_quality_service
    
    async def build_context_for_query(self, query: str) -> SchemaAwareContext:
        """Build comprehensive schema-aware context for a query"""
        
        # Step 1: Identify relevant schemas based on query
        relevant_schemas = self.schema_registry.get_schemas_for_query_intent(query)
        schema_names = [schema.name for schema in relevant_schemas]
        
        # Step 2: Get live data samples for identified schemas
        data_samples = await self._get_data_samples(schema_names)
        
        # Step 3: Assess data quality for each schema
        quality_metrics = await self.data_quality_service.get_all_quality_metrics(schema_names)
        
        # Step 4: Build schema summary for LLM
        schema_summary = self._build_schema_summary(relevant_schemas, data_samples, quality_metrics)
        
        # Step 5: Extract business context
        business_context = self._build_business_context(relevant_schemas, query)
        
        # Step 6: Generate contextual recommendations
        recommendations = self._generate_context_recommendations(query, quality_metrics, data_samples)
        
        return SchemaAwareContext(
            query=query,
            relevant_schemas=relevant_schemas,
            data_samples=data_samples,
            quality_metrics=quality_metrics,
            schema_summary=schema_summary,
            business_context=business_context,
            recommendations=recommendations,
            generated_at=datetime.utcnow()
        )
    
    async def _get_data_samples(self, schema_names: List[str]) -> Dict[str, DataSample]:
        """Get data samples for specified schemas"""
        
        data_samples = {}
        
        for schema_name in schema_names:
            sample = await self.data_quality_service.get_live_data_sample(schema_name)
            if sample:
                data_samples[schema_name] = sample
        
        return data_samples
    
    def _build_schema_summary(
        self, 
        schemas: List[DataSchema], 
        data_samples: Dict[str, DataSample],
        quality_metrics: Dict[str, DataQualityMetrics]
    ) -> Dict[str, Any]:
        """Build schema summary optimized for LLM understanding"""
        
        summary = {
            "available_data_types": [],
            "data_structures": {},
            "data_quality_overview": {},
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
                "record_count": data_samples.get(schema_name, DataSample("", [], 0, 0, False)).total_count
            })
            
            # Extract data structure info
            props = schema.schema.get("properties", {})
            summary["data_structures"][schema_name] = {
                "required_fields": schema.schema.get("required", []),
                "key_fields": {
                    field: {
                        "type": field_info.get("type", "unknown"),
                        "description": field_info.get("description", ""),
                        "examples": field_info.get("examples", [])[:2]  # Limit examples
                    }
                    for field, field_info in list(props.items())[:5]  # Top 5 fields
                },
                "total_fields": len(props)
            }
            
            # Add quality overview
            if schema_name in quality_metrics:
                metrics = quality_metrics[schema_name]
                summary["data_quality_overview"][schema_name] = {
                    "overall_score": f"{metrics.overall_score:.1%}",
                    "status": self._quality_to_status(metrics.overall_score),
                    "key_issues": metrics.issues[:2],  # Top 2 issues
                    "record_count": metrics.record_count,
                    "last_assessed": metrics.last_updated.strftime("%H:%M")
                }
            
            # Add sample data for LLM to understand structure
            if schema_name in data_samples:
                sample = data_samples[schema_name]
                if sample.sample_records:
                    # Take first record as structure example
                    example_record = sample.sample_records[0]
                    summary["sample_data"][schema_name] = {
                        "structure_example": {
                            k: f"<{type(v).__name__}>" if v is not None else "<null>"
                            for k, v in example_record.items()
                        },
                        "actual_sample": example_record,  # First real record
                        "total_available": sample.total_count
                    }
            
            # Add relationships
            if schema.relationships:
                summary["relationships"][schema_name] = schema.relationships
            
            # Add business constraints
            if schema.constraints:
                summary["constraints"][schema_name] = schema.constraints[:3]  # Top 3 constraints
        
        return summary
    
    def _build_business_context(self, schemas: List[DataSchema], query: str) -> Dict[str, Any]:
        """Build business context relevant to the query"""
        
        context = {
            "operational_context": {},
            "criticality_info": {},
            "service_impact": {},
            "maintenance_considerations": {}
        }
        
        for schema in schemas:
            if not schema.business_context:
                continue
            
            schema_name = schema.name
            biz_ctx = schema.business_context
            
            # Extract operational context
            context["operational_context"][schema_name] = {
                "criticality": biz_ctx.get("criticality", "medium"),
                "service_type": biz_ctx.get("service_impact", "internal"),
                "availability_req": biz_ctx.get("availability_requirement", "standard")
            }
            
            # Criticality mapping
            if biz_ctx.get("criticality") == "high":
                context["criticality_info"][schema_name] = "Changes require careful planning and approval"
            
            # Service impact
            if "customer" in str(biz_ctx.get("service_impact", "")):
                context["service_impact"][schema_name] = "Customer-facing service - high impact"
            
            # Maintenance windows
            if "maintenance_window" in biz_ctx:
                context["maintenance_considerations"][schema_name] = biz_ctx["maintenance_window"]
        
        return context
    
    def _generate_context_recommendations(
        self, 
        query: str, 
        quality_metrics: Dict[str, DataQualityMetrics],
        data_samples: Dict[str, DataSample]
    ) -> List[str]:
        """Generate contextual recommendations based on data state"""
        
        recommendations = []
        query_lower = query.lower()
        
        # Data quality based recommendations
        poor_quality_sources = [
            name for name, metrics in quality_metrics.items() 
            if metrics.overall_score < 0.6
        ]
        
        if poor_quality_sources:
            recommendations.append(
                f"Data quality concerns in {', '.join(poor_quality_sources)}. "
                f"Consider validating results or requesting data refresh."
            )
        
        # Data availability recommendations
        empty_sources = [
            name for name, sample in data_samples.items()
            if sample.total_count == 0
        ]
        
        if empty_sources:
            recommendations.append(
                f"No data available for {', '.join(empty_sources)}. "
                f"Check data collection processes."
            )
        
        # Query-specific recommendations
        if "count" in query_lower or "how many" in query_lower:
            high_count_sources = [
                name for name, sample in data_samples.items()
                if sample.total_count > 1000
            ]
            if high_count_sources:
                recommendations.append(
                    f"Large datasets detected in {', '.join(high_count_sources)}. "
                    f"Consider using filters or aggregation for better performance."
                )
        
        if "production" in query_lower:
            recommendations.append(
                "Production environment query detected. "
                "Ensure changes are properly tested and approved."
            )
        
        # Default recommendations
        if not recommendations:
            recommendations.append("Data appears healthy. Proceed with analysis.")
        
        return recommendations[:3]  # Limit to top 3 recommendations
    
    def _quality_to_status(self, score: float) -> str:
        """Convert quality score to human-readable status"""
        if score >= 0.9:
            return "excellent"
        elif score >= 0.7:
            return "good"
        elif score >= 0.5:
            return "fair"
        else:
            return "poor"
    
    def to_llm_context(self, context: SchemaAwareContext) -> Dict[str, Any]:
        """Convert schema-aware context to LLM-optimized format"""
        
        return {
            "query_analysis": {
                "original_query": context.query,
                "detected_data_types": [schema.name for schema in context.relevant_schemas],
                "analysis_timestamp": context.generated_at.strftime("%Y-%m-%d %H:%M:%S")
            },
            
            "available_data": {
                "data_sources": context.schema_summary.get("available_data_types", []),
                "data_quality": context.schema_summary.get("data_quality_overview", {}),
                "total_records_available": sum(
                    sample.total_count for sample in context.data_samples.values()
                )
            },
            
            "data_structures": {
                "schemas": context.schema_summary.get("data_structures", {}),
                "relationships": context.schema_summary.get("relationships", {}),
                "constraints": context.schema_summary.get("constraints", {}),
                "sample_data": context.schema_summary.get("sample_data", {})
            },
            
            "business_context": {
                "operational_info": context.business_context.get("operational_context", {}),
                "criticality_alerts": context.business_context.get("criticality_info", {}),
                "service_impact": context.business_context.get("service_impact", {})
            },
            
            "recommendations": {
                "data_recommendations": context.recommendations,
                "analysis_guidance": self._generate_analysis_guidance(context)
            },
            
            "metadata": {
                "context_generated_at": context.generated_at.isoformat(),
                "schemas_analyzed": len(context.relevant_schemas),
                "data_sources_available": len(context.data_samples),
                "overall_data_health": self._assess_overall_health(context.quality_metrics)
            }
        }
    
    def _generate_analysis_guidance(self, context: SchemaAwareContext) -> List[str]:
        """Generate analysis guidance for the LLM"""
        
        guidance = []
        
        # Schema-specific guidance
        schema_names = [schema.name for schema in context.relevant_schemas]
        
        if "ftth_olt" in schema_names:
            guidance.append("For FTTH OLT analysis, consider region distribution and production/test environments")
        
        if "lag" in schema_names:
            guidance.append("For LAG analysis, check device associations and admin key configurations")
        
        if "mobile_modem" in schema_names:
            guidance.append("For mobile modem analysis, focus on subscriber mappings and hardware types")
        
        # Data quality guidance
        poor_quality = [
            name for name, metrics in context.quality_metrics.items()
            if metrics.overall_score < 0.7
        ]
        
        if poor_quality:
            guidance.append(f"Exercise caution with {', '.join(poor_quality)} data due to quality concerns")
        
        return guidance
    
    def _assess_overall_health(self, quality_metrics: Dict[str, DataQualityMetrics]) -> str:
        """Assess overall data health across all sources"""
        
        if not quality_metrics:
            return "unknown"
        
        avg_score = sum(m.overall_score for m in quality_metrics.values()) / len(quality_metrics)
        
        if avg_score >= 0.8:
            return "excellent"
        elif avg_score >= 0.6:
            return "good"
        elif avg_score >= 0.4:
            return "fair"
        else:
            return "poor"