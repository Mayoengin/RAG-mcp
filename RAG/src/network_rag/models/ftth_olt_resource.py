# src/network_rag/models/ftth_olt_resource.py
"""FTTH OLT Resource - Network equipment domain model"""

from datetime import datetime
from typing import Dict, Any, List, Optional
from enum import Enum
from pydantic import BaseModel, Field


class Environment(str, Enum):
    """Network environment types"""
    PRODUCTION = "PRD"
    UAT = "UAT" 
    TEST = "TEST"


class ConnectionType(str, Enum):
    """Network connection types for FTTH OLT equipment"""
    SINGLE_10G = "1x10G"
    QUAD_10G = "4x10G"
    SINGLE_100G = "1x100G"


class FTTHOLTResource(BaseModel):
    """FTTH OLT network equipment domain model"""
    
    # Core identification
    name: str = Field(..., description="OLT name/identifier")
    ftth_olt_id: str = Field(..., description="FTTH OLT unique identifier")
    region: str = Field(..., description="Geographic region")
    
    # Environment and management
    environment: Environment = Field(..., description="Deployment environment")
    managed_by_inmanta: bool = Field(False, description="Managed by Inmanta system")
    
    # Network configuration
    connection_type: Optional[ConnectionType] = Field(None, description="Connection type")
    host_address: Optional[str] = Field(None, description="OAM host address")
    service_configs: Dict[str, Any] = Field(default_factory=dict, description="Service configurations")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        use_enum_values = True
        validate_assignment = True
    
    # Domain methods
    def is_production(self) -> bool:
        """Check if this is a production OLT"""
        return self.environment == Environment.PRODUCTION
    
    def has_complete_config(self) -> bool:
        """Check if OLT has minimum required configuration"""
        return bool(self.connection_type and self.host_address)
    
    def calculate_bandwidth_gbps(self) -> int:
        """Calculate total bandwidth capacity based on connection type"""
        if not self.connection_type:
            return 0
        
        bandwidth_map = {
            ConnectionType.SINGLE_10G: 10,
            ConnectionType.QUAD_10G: 40,
            ConnectionType.SINGLE_100G: 100
        }
        return bandwidth_map[self.connection_type]
    
    def get_configuration_completeness_score(self) -> float:
        """Calculate configuration completeness score (0.0 to 1.0)"""
        score = 0.0
        total_checks = 5
        
        # Core configuration checks
        if self.connection_type:
            score += 1
        if self.host_address:
            score += 1
        if self.service_configs:
            score += 1
        if self.managed_by_inmanta and self.is_production():
            score += 1
        if len(self.service_configs) >= 3:  # Multiple services configured
            score += 1
        
        return score / total_checks
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get comprehensive health and configuration summary"""
        return {
            "name": self.name,
            "region": self.region,
            "environment": self.environment.value if hasattr(self.environment, 'value') else str(self.environment),
            "is_production": self.is_production(),
            "complete_config": self.has_complete_config(),
            "bandwidth_gbps": self.calculate_bandwidth_gbps(),
            "completeness_score": self.get_configuration_completeness_score(),
            "managed_by_inmanta": self.managed_by_inmanta,
            "service_count": len(self.service_configs)
        }