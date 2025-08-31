# src/network_rag/services/schema_registry.py
"""Schema registry for network data structures and metadata"""

from typing import Dict, Any, List, Optional, Set
from datetime import datetime
from dataclasses import dataclass
import json
from pathlib import Path


@dataclass
class DataSchema:
    """Represents a data schema with metadata"""
    name: str
    version: str
    schema: Dict[str, Any]  # JSON Schema format
    sample_data: Optional[Dict[str, Any]] = None
    relationships: Optional[Dict[str, List[str]]] = None
    business_context: Optional[Dict[str, Any]] = None
    constraints: Optional[List[str]] = None
    last_updated: Optional[datetime] = None


class SchemaRegistry:
    """Registry for data schemas and their metadata"""
    
    def __init__(self):
        self.schemas: Dict[str, DataSchema] = {}
        self._initialize_network_schemas()
    
    def _initialize_network_schemas(self):
        """Initialize schemas for network data types"""
        
        # FTTH OLT Schema
        self.register_schema(DataSchema(
            name="ftth_olt",
            version="1.0",
            schema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string", 
                        "description": "Unique OLT identifier",
                        "pattern": "^OLT\\d+[A-Z]+\\d+$",
                        "examples": ["OLT17PROP01", "OLT70AALS01"]
                    },
                    "region": {
                        "type": "string",
                        "enum": ["HOBO", "GENT", "ROES", "ASSE"],
                        "description": "Geographic region"
                    },
                    "environment": {
                        "type": "string", 
                        "enum": ["PRODUCTION", "TEST", "STAGING"],
                        "description": "Deployment environment"
                    },
                    "esi_name": {
                        "type": "string",
                        "description": "Ethernet Segment Identifier name"
                    },
                    "bandwidth_gbps": {
                        "type": "number",
                        "minimum": 0,
                        "description": "Bandwidth capacity in Gbps"
                    },
                    "service_count": {
                        "type": "integer",
                        "minimum": 0,
                        "description": "Number of active services"
                    },
                    "managed_by_inmanta": {
                        "type": "boolean",
                        "description": "Whether managed by Inmanta system"
                    }
                },
                "required": ["name", "region", "environment"]
            },
            relationships={
                "connects_to": ["cin_node", "bng_node"],
                "serves": ["subscribers", "services"],
                "managed_by": ["teams"]
            },
            business_context={
                "criticality": "high",
                "service_impact": "customer_facing",
                "availability_requirement": "99.9%",
                "maintenance_window": "02:00-06:00"
            },
            constraints=[
                "production_olts_require_redundancy",
                "bandwidth_must_match_subscribers",
                "region_must_match_physical_location"
            ]
        ))
        
        # LAG Configuration Schema
        self.register_schema(DataSchema(
            name="lag",
            version="1.0",
            schema={
                "type": "object",
                "properties": {
                    "device_name": {
                        "type": "string",
                        "description": "Device hosting the LAG",
                        "examples": ["CINAALSA01", "SRPTRO01"]
                    },
                    "lag_id": {
                        "type": ["integer", "string"],
                        "description": "LAG identifier"
                    },
                    "description": {
                        "type": "string",
                        "description": "Human-readable LAG description"
                    },
                    "admin_key": {
                        "type": ["integer", "string"],
                        "description": "LACP administrative key"
                    },
                    "status": {
                        "type": "string",
                        "enum": ["active", "inactive", "degraded"],
                        "description": "Current LAG status"
                    }
                },
                "required": ["device_name", "lag_id"]
            },
            relationships={
                "aggregates": ["physical_ports"],
                "connects": ["ftth_olt", "bng_node"],
                "managed_by": ["teams"]
            },
            business_context={
                "criticality": "high",
                "service_impact": "multiple_services",
                "redundancy": "required"
            },
            constraints=[
                "lag_members_same_device",
                "admin_key_must_be_unique",
                "minimum_two_members_for_redundancy"
            ]
        ))
        
        # Mobile Modem Schema  
        self.register_schema(DataSchema(
            name="mobile_modem",
            version="1.0",
            schema={
                "type": "object",
                "properties": {
                    "serial_number": {
                        "type": "string",
                        "pattern": "^LPL\\d+[A-F]+$",
                        "description": "Device serial number",
                        "examples": ["LPL2408001DF", "LPL24080006F"]
                    },
                    "hardware_type": {
                        "type": "string",
                        "description": "Hardware model/type",
                        "examples": ["Nokia 5G26-A"]
                    },
                    "mobile_subscriber_id": {
                        "type": "string",
                        "description": "VPN subscriber identifier",
                        "pattern": "^MOBILE-SUB-VPN-"
                    },
                    "mobile_modem_id": {
                        "type": "string",
                        "format": "uuid",
                        "description": "Unique modem identifier"
                    },
                    "fnt_command_id": {
                        "type": ["string", "null"],
                        "description": "FNT command identifier if configured"
                    }
                },
                "required": ["serial_number", "hardware_type"]
            },
            relationships={
                "connects_to": ["mobile_network"],
                "has_subscriber": ["vpn_subscriber"],
                "managed_by": ["mobile_team"]
            },
            business_context={
                "criticality": "medium",
                "service_type": "mobile_connectivity",
                "customer_type": "mobile_subscribers"
            }
        ))
        
        # Team Schema
        self.register_schema(DataSchema(
            name="team",
            version="1.0", 
            schema={
                "type": "object",
                "properties": {
                    "team_name": {
                        "type": "string",
                        "enum": ["MOBILE", "NAS", "IPOPS", "INFRA", "DTV"],
                        "description": "Team identifier"
                    },
                    "team_id": {
                        "type": "string",
                        "format": "uuid",
                        "description": "Unique team identifier"
                    },
                    "description": {
                        "type": "string",
                        "description": "Team responsibilities description"
                    },
                    "contact_info": {
                        "type": "object",
                        "properties": {
                            "email": {"type": "string", "format": "email"},
                            "phone": {"type": "string"},
                            "escalation_path": {"type": "array", "items": {"type": "string"}}
                        }
                    }
                },
                "required": ["team_name", "team_id"]
            },
            relationships={
                "manages": ["network_devices", "services"],
                "escalates_to": ["management"],
                "collaborates_with": ["other_teams"]
            },
            business_context={
                "availability": "24x7_support",
                "responsibilities": "network_operations"
            }
        ))
        
        # PXC Cross-Connect Schema
        self.register_schema(DataSchema(
            name="pxc", 
            version="1.0",
            schema={
                "type": "object",
                "properties": {
                    "device_name": {
                        "type": "string",
                        "description": "Device hosting PXC"
                    },
                    "pxc_id": {
                        "type": ["string", "integer"],
                        "description": "Cross-connect port identifier"
                    },
                    "description": {
                        "type": "string",
                        "description": "Cross-connect purpose/description"
                    },
                    "status": {
                        "type": "string",
                        "enum": ["active", "inactive", "maintenance"],
                        "description": "Current status"
                    }
                },
                "required": ["device_name", "pxc_id"]
            },
            relationships={
                "connects": ["network_segments"],
                "enables": ["service_provisioning"]
            },
            business_context={
                "criticality": "medium",
                "purpose": "network_integration"
            }
        ))
    
    def register_schema(self, schema: DataSchema):
        """Register a new schema"""
        schema.last_updated = datetime.utcnow()
        self.schemas[schema.name] = schema
    
    def get_schema(self, schema_name: str) -> Optional[DataSchema]:
        """Get schema by name"""
        return self.schemas.get(schema_name)
    
    def get_all_schemas(self) -> Dict[str, DataSchema]:
        """Get all registered schemas"""
        return self.schemas.copy()
    
    def get_schemas_for_query_intent(self, query: str) -> List[DataSchema]:
        """Get relevant schemas based on query intent"""
        query_lower = query.lower()
        relevant_schemas = []
        
        # Map query terms to schema names
        schema_mappings = {
            'ftth_olt': ['ftth', 'olt', 'fiber', 'optical'],
            'lag': ['lag', 'link', 'aggregation', 'lacp'],
            'mobile_modem': ['mobile', 'modem', 'nokia', '5g'],
            'team': ['team', 'responsible', 'contact', 'escalation'],
            'pxc': ['pxc', 'cross', 'connect', 'integration']
        }
        
        for schema_name, keywords in schema_mappings.items():
            if any(keyword in query_lower for keyword in keywords):
                schema = self.get_schema(schema_name)
                if schema:
                    relevant_schemas.append(schema)
        
        # If no specific schemas found, return most commonly used ones
        if not relevant_schemas:
            for schema_name in ['ftth_olt', 'team']:  # Default relevant schemas
                schema = self.get_schema(schema_name)
                if schema:
                    relevant_schemas.append(schema)
        
        return relevant_schemas
    
    def get_schema_relationships(self, schema_name: str) -> Dict[str, List[str]]:
        """Get relationships for a schema"""
        schema = self.get_schema(schema_name)
        return schema.relationships if schema and schema.relationships else {}
    
    def get_business_context(self, schema_name: str) -> Dict[str, Any]:
        """Get business context for a schema"""
        schema = self.get_schema(schema_name)
        return schema.business_context if schema and schema.business_context else {}
    
    def validate_data_against_schema(self, schema_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data against schema (basic validation)"""
        schema = self.get_schema(schema_name)
        if not schema:
            return {"valid": False, "error": f"Schema {schema_name} not found"}
        
        # Basic validation - in production, use jsonschema library
        schema_props = schema.schema.get("properties", {})
        required_fields = schema.schema.get("required", [])
        
        errors = []
        
        # Check required fields
        for field in required_fields:
            if field not in data:
                errors.append(f"Missing required field: {field}")
        
        # Check data types (basic)
        for field, value in data.items():
            if field in schema_props:
                expected_type = schema_props[field].get("type")
                if expected_type and not self._check_type(value, expected_type):
                    errors.append(f"Field {field}: expected {expected_type}, got {type(value).__name__}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "schema_name": schema_name
        }
    
    def _check_type(self, value: Any, expected_type: Any) -> bool:
        """Basic type checking"""
        if isinstance(expected_type, list):
            return any(self._check_type(value, t) for t in expected_type)
        
        type_map = {
            "string": str,
            "integer": int,
            "number": (int, float),
            "boolean": bool,
            "array": list,
            "object": dict
        }
        
        expected_python_type = type_map.get(expected_type)
        if expected_python_type:
            return isinstance(value, expected_python_type)
        
        return True  # Unknown type, assume valid
    
    def export_schema_summary(self) -> Dict[str, Any]:
        """Export summary of all schemas for LLM context"""
        summary = {
            "total_schemas": len(self.schemas),
            "schemas": {},
            "relationships_map": {},
            "business_contexts": {}
        }
        
        for name, schema in self.schemas.items():
            # Extract key information for LLM
            props = schema.schema.get("properties", {})
            summary["schemas"][name] = {
                "description": f"Schema for {name} data",
                "key_fields": list(props.keys())[:5],  # Top 5 fields
                "required_fields": schema.schema.get("required", []),
                "sample_structure": {k: v.get("type", "unknown") for k, v in list(props.items())[:3]}
            }
            
            if schema.relationships:
                summary["relationships_map"][name] = schema.relationships
            
            if schema.business_context:
                summary["business_contexts"][name] = schema.business_context
        
        return summary