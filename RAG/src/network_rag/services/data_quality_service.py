# src/network_rag/services/data_quality_service.py
"""Data quality assessment and monitoring service"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import asyncio


@dataclass
class DataQualityMetrics:
    """Data quality metrics for a dataset"""
    schema_name: str
    record_count: int
    completeness_score: float  # 0.0 to 1.0
    freshness_score: float     # 0.0 to 1.0  
    consistency_score: float   # 0.0 to 1.0
    accuracy_score: float      # 0.0 to 1.0
    overall_score: float       # 0.0 to 1.0
    last_updated: datetime
    issues: List[str]
    recommendations: List[str]


@dataclass
class DataSample:
    """Sample of data for LLM context"""
    schema_name: str
    sample_records: List[Dict[str, Any]]
    total_count: int
    sample_size: int
    representative: bool  # Whether sample is representative of full dataset


class DataQualityService:
    """Service for assessing and monitoring data quality"""
    
    def __init__(self, network_port=None):
        self.network_port = network_port
        self._quality_cache: Dict[str, DataQualityMetrics] = {}
        self._cache_ttl = timedelta(minutes=30)  # Cache TTL
    
    async def assess_data_quality(self, schema_name: str, data: List[Dict[str, Any]]) -> DataQualityMetrics:
        """Assess quality of data against schema"""
        
        if not data:
            return DataQualityMetrics(
                schema_name=schema_name,
                record_count=0,
                completeness_score=0.0,
                freshness_score=0.0,
                consistency_score=0.0,
                accuracy_score=0.0,
                overall_score=0.0,
                last_updated=datetime.utcnow(),
                issues=["No data available"],
                recommendations=["Check data source connectivity", "Verify data collection processes"]
            )
        
        # Calculate individual quality metrics
        completeness = await self._assess_completeness(schema_name, data)
        freshness = await self._assess_freshness(schema_name, data)
        consistency = await self._assess_consistency(schema_name, data)
        accuracy = await self._assess_accuracy(schema_name, data)
        
        # Calculate overall score (weighted average)
        overall_score = (
            completeness * 0.3 +   # 30% weight on completeness
            freshness * 0.25 +     # 25% weight on freshness
            consistency * 0.25 +   # 25% weight on consistency  
            accuracy * 0.20        # 20% weight on accuracy
        )
        
        # Collect issues and recommendations
        issues = []
        recommendations = []
        
        if completeness < 0.7:
            issues.append(f"Low data completeness ({completeness:.1%})")
            recommendations.append("Review data collection processes for missing fields")
        
        if freshness < 0.5:
            issues.append(f"Stale data detected (freshness: {freshness:.1%})")
            recommendations.append("Increase data refresh frequency")
        
        if consistency < 0.8:
            issues.append(f"Data consistency issues ({consistency:.1%})")
            recommendations.append("Implement data validation rules")
        
        if accuracy < 0.8:
            issues.append(f"Potential accuracy issues ({accuracy:.1%})")
            recommendations.append("Verify data source reliability")
        
        metrics = DataQualityMetrics(
            schema_name=schema_name,
            record_count=len(data),
            completeness_score=completeness,
            freshness_score=freshness,
            consistency_score=consistency,
            accuracy_score=accuracy,
            overall_score=overall_score,
            last_updated=datetime.utcnow(),
            issues=issues,
            recommendations=recommendations
        )
        
        # Cache the metrics
        self._quality_cache[schema_name] = metrics
        
        return metrics
    
    async def get_cached_quality_metrics(self, schema_name: str) -> Optional[DataQualityMetrics]:
        """Get cached quality metrics if not expired"""
        
        cached = self._quality_cache.get(schema_name)
        if cached and (datetime.utcnow() - cached.last_updated) < self._cache_ttl:
            return cached
        
        return None
    
    async def get_live_data_sample(self, schema_name: str, sample_size: int = 5) -> Optional[DataSample]:
        """Get live sample of data for LLM context"""
        
        if not self.network_port:
            return None
        
        try:
            # Get data based on schema type
            if schema_name == "ftth_olt":
                data = await self.network_port.fetch_ftth_olts()
                # Convert domain objects to dicts
                raw_data = [olt.get_health_summary() for olt in data]
            else:
                # For other types, load from JSON files
                raw_data = await self.network_port._load_local_json(schema_name)
            
            if not raw_data:
                return None
            
            # Take sample
            sample_records = raw_data[:sample_size] if len(raw_data) >= sample_size else raw_data
            
            return DataSample(
                schema_name=schema_name,
                sample_records=sample_records,
                total_count=len(raw_data),
                sample_size=len(sample_records),
                representative=len(raw_data) <= sample_size * 2  # Sample is representative if dataset is small
            )
            
        except Exception as e:
            print(f"Failed to get data sample for {schema_name}: {e}")
            return None
    
    async def get_all_quality_metrics(self, schema_names: List[str]) -> Dict[str, DataQualityMetrics]:
        """Get quality metrics for multiple schemas"""
        
        metrics = {}
        
        for schema_name in schema_names:
            # Try cache first
            cached = await self.get_cached_quality_metrics(schema_name)
            if cached:
                metrics[schema_name] = cached
                continue
            
            # Get fresh data and assess quality
            sample = await self.get_live_data_sample(schema_name)
            if sample:
                quality = await self.assess_data_quality(schema_name, sample.sample_records)
                metrics[schema_name] = quality
        
        return metrics
    
    async def _assess_completeness(self, schema_name: str, data: List[Dict[str, Any]]) -> float:
        """Assess data completeness (percentage of non-null values)"""
        
        if not data:
            return 0.0
        
        # Define critical fields per schema
        critical_fields = {
            "ftth_olt": ["name", "region", "environment"],
            "lag": ["device_name", "lag_id"], 
            "mobile_modem": ["serial_number", "hardware_type"],
            "team": ["team_name", "team_id"],
            "pxc": ["device_name", "pxc_id"]
        }
        
        required_fields = critical_fields.get(schema_name, [])
        if not required_fields:
            return 1.0  # No requirements defined
        
        # Calculate completeness
        total_checks = len(data) * len(required_fields)
        complete_checks = 0
        
        for record in data:
            for field in required_fields:
                if field in record and record[field] is not None and str(record[field]).strip():
                    complete_checks += 1
        
        return complete_checks / total_checks if total_checks > 0 else 0.0
    
    async def _assess_freshness(self, schema_name: str, data: List[Dict[str, Any]]) -> float:
        """Assess data freshness (how recently data was updated)"""
        
        # For this implementation, assume data is fresh if we can retrieve it
        # In real implementation, check last_updated timestamps
        
        if not data:
            return 0.0
        
        # Simple heuristic: if we have data, it's reasonably fresh
        # Real implementation would check timestamps in the data
        now = datetime.utcnow()
        
        # Simulate freshness based on schema type
        freshness_assumptions = {
            "ftth_olt": 0.9,      # Network devices change infrequently
            "lag": 0.8,           # Link aggregation configs are stable
            "mobile_modem": 0.7,  # Mobile devices can change more often
            "team": 0.95,         # Team info very stable
            "pxc": 0.85           # Cross-connects stable
        }
        
        return freshness_assumptions.get(schema_name, 0.8)
    
    async def _assess_consistency(self, schema_name: str, data: List[Dict[str, Any]]) -> float:
        """Assess data consistency (format consistency, no duplicates)"""
        
        if not data:
            return 0.0
        
        consistency_score = 1.0
        
        # Check for duplicates based on key field
        key_fields = {
            "ftth_olt": "name",
            "lag": "lag_id", 
            "mobile_modem": "serial_number",
            "team": "team_name",
            "pxc": "pxc_id"
        }
        
        key_field = key_fields.get(schema_name)
        if key_field:
            key_values = []
            for record in data:
                if key_field in record:
                    key_values.append(record[key_field])
            
            # Check for duplicates
            unique_values = set(key_values)
            if len(unique_values) != len(key_values):
                duplicate_rate = (len(key_values) - len(unique_values)) / len(key_values)
                consistency_score -= duplicate_rate * 0.5  # Reduce score by duplicate rate
        
        # Check format consistency (basic)
        if schema_name == "ftth_olt":
            # Check OLT name format consistency
            name_format_errors = 0
            for record in data:
                name = record.get("name", "")
                if name and not (name.startswith("OLT") and len(name) > 6):
                    name_format_errors += 1
            
            if name_format_errors > 0:
                format_error_rate = name_format_errors / len(data)
                consistency_score -= format_error_rate * 0.3
        
        return max(0.0, min(1.0, consistency_score))
    
    async def _assess_accuracy(self, schema_name: str, data: List[Dict[str, Any]]) -> float:
        """Assess data accuracy (logical validation)"""
        
        if not data:
            return 0.0
        
        accuracy_score = 1.0
        errors = 0
        
        # Schema-specific accuracy checks
        for record in data:
            if schema_name == "ftth_olt":
                # Logical validation for FTTH OLT
                bandwidth = record.get("bandwidth_gbps", 0)
                service_count = record.get("service_count", 0)
                
                # Bandwidth should be positive for production OLTs
                if record.get("environment") == "PRODUCTION" and bandwidth <= 0:
                    errors += 1
                
                # Service count should be reasonable
                if service_count < 0 or service_count > 10000:  # Reasonable bounds
                    errors += 1
                    
            elif schema_name == "mobile_modem":
                # Mobile modem validations
                serial = record.get("serial_number", "")
                if serial and not serial.startswith("LPL"):
                    errors += 1
        
        if errors > 0:
            error_rate = errors / (len(data) * 2)  # Assuming 2 checks per record on average
            accuracy_score = max(0.0, 1.0 - error_rate)
        
        return accuracy_score
    
    def get_quality_summary_for_llm(self, metrics: Dict[str, DataQualityMetrics]) -> Dict[str, Any]:
        """Generate quality summary optimized for LLM consumption"""
        
        summary = {
            "overall_status": "good",  # good, fair, poor
            "data_sources": {},
            "recommendations": [],
            "alerts": []
        }
        
        total_score = 0
        source_count = 0
        
        for schema_name, metric in metrics.items():
            source_count += 1
            total_score += metric.overall_score
            
            # Categorize quality
            if metric.overall_score >= 0.8:
                status = "excellent"
            elif metric.overall_score >= 0.6:
                status = "good"
            elif metric.overall_score >= 0.4:
                status = "fair"  
            else:
                status = "poor"
            
            summary["data_sources"][schema_name] = {
                "status": status,
                "quality_score": f"{metric.overall_score:.1%}",
                "record_count": metric.record_count,
                "key_issues": metric.issues[:2],  # Top 2 issues
                "data_age": "current"  # Simplified for now
            }
            
            # Collect recommendations
            summary["recommendations"].extend(metric.recommendations[:1])  # Top recommendation per source
            
            # Collect alerts for poor quality
            if metric.overall_score < 0.5:
                summary["alerts"].append(f"{schema_name} data quality is poor ({metric.overall_score:.1%})")
        
        # Overall status
        if source_count > 0:
            avg_score = total_score / source_count
            if avg_score >= 0.8:
                summary["overall_status"] = "excellent"
            elif avg_score >= 0.6:
                summary["overall_status"] = "good"
            elif avg_score >= 0.4:
                summary["overall_status"] = "fair"
            else:
                summary["overall_status"] = "poor"
        
        return summary