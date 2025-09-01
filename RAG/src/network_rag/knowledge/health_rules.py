# src/network_rag/knowledge/health_rules.py
"""Health analysis rules stored as knowledge documents"""

from typing import Dict, List, Any
from datetime import datetime
from ..models import Document, DocumentType

class HealthRulesKnowledge:
    """Health analysis rules stored as searchable knowledge"""
    
    @staticmethod
    def get_ftth_olt_health_rules() -> Dict[str, Any]:
        """FTTH OLT health analysis rules document"""
        return {
            "id": "health_rule_ftth_olt_001",
            "title": "FTTH OLT Health Analysis Framework",
            "document_type": DocumentType.BEST_PRACTICES,
            "content": """
            FTTH OLT Device Health Assessment Rules and Guidelines
            
            PURPOSE: Define health indicators and scoring for FTTH OLT devices
            
            HEALTH INDICATORS:
            
            1. SERVICE CONFIGURATION
               - CRITICAL: service_count = 0 (No services configured)
               - WARNING: service_count < 50 (Low service utilization)
               - HEALTHY: service_count >= 100 (Normal operation)
            
            2. MANAGEMENT STATUS
               - CRITICAL: managed_by_inmanta = false AND environment = PRODUCTION
               - WARNING: managed_by_inmanta = false (Manual management risk)
               - HEALTHY: managed_by_inmanta = true (Automated management)
            
            3. CONFIGURATION COMPLETENESS
               - CRITICAL: complete_config = false (Configuration incomplete)
               - HEALTHY: complete_config = true (Fully configured)
            
            4. BANDWIDTH CAPACITY
               - OPTIMAL: bandwidth_gbps >= 100 (High capacity)
               - NORMAL: bandwidth_gbps >= 10 (Standard capacity)
               - LIMITED: bandwidth_gbps < 10 (Constrained capacity)
            
            HEALTH SCORE CALCULATION:
            - Base score: 100 points
            - Deduct 50 points: if service_count = 0
            - Deduct 30 points: if not managed_by_inmanta
            - Deduct 40 points: if complete_config = false
            - Deduct 20 points: if service_count < 50
            - Add 10 points: if bandwidth_gbps >= 100
            - Minimum score: 0, Maximum score: 110
            
            RISK LEVELS:
            - HIGH RISK (Score < 30): Immediate attention required
            - MEDIUM RISK (Score 30-70): Monitoring needed
            - LOW RISK (Score > 70): Operating normally
            
            AUTOMATED RECOMMENDATIONS:
            - If service_count = 0: "URGENT: Configure services for this OLT"
            - If not managed_by_inmanta: "Migrate to Inmanta for automated management"
            - If not complete_config: "Complete device configuration to ensure stability"
            - If bandwidth_gbps < 10: "Consider bandwidth upgrade for better performance"
            """,
            "keywords": [
                "health", "assessment", "FTTH", "OLT", "scoring",
                "inmanta", "configuration", "services", "bandwidth"
            ],
            "executable_rules": {
                "device_type": "ftth_olt",
                "summary_fields": [
                    "name", "region", "environment", "bandwidth_gbps",
                    "service_count", "managed_by_inmanta", "complete_config",
                    "esi_name", "connection_type"
                ],
                "health_conditions": {
                    "CRITICAL": [
                        {"field": "service_count", "operator": "==", "value": 0},
                        {"field": "complete_config", "operator": "==", "value": False},
                        {"condition": "environment == 'PRODUCTION' and not managed_by_inmanta"}
                    ],
                    "WARNING": [
                        {"field": "service_count", "operator": "<", "value": 50},
                        {"field": "managed_by_inmanta", "operator": "==", "value": False}
                    ],
                    "HEALTHY": [
                        {"condition": "service_count >= 50 and managed_by_inmanta and complete_config"}
                    ]
                },
                "scoring_rules": [
                    {"condition": "service_count == 0", "impact": -50, "reason": "No services"},
                    {"condition": "not managed_by_inmanta", "impact": -30, "reason": "Manual management"},
                    {"condition": "not complete_config", "impact": -40, "reason": "Incomplete config"},
                    {"condition": "service_count < 50", "impact": -20, "reason": "Low utilization"},
                    {"condition": "bandwidth_gbps >= 100", "impact": 10, "reason": "High capacity"}
                ],
                "recommendations": [
                    {
                        "condition": "service_count == 0",
                        "message": "🚨 URGENT: Configure services for this OLT immediately",
                        "priority": "HIGH"
                    },
                    {
                        "condition": "not managed_by_inmanta",
                        "message": "⚠️ Migrate to Inmanta for automated management",
                        "priority": "MEDIUM"
                    },
                    {
                        "condition": "not complete_config",
                        "message": "⚠️ Complete device configuration to ensure stability",
                        "priority": "HIGH"
                    },
                    {
                        "condition": "bandwidth_gbps < 10",
                        "message": "📊 Consider bandwidth upgrade for better performance",
                        "priority": "LOW"
                    }
                ]
            },
            "version": "1.0",
            "author": "Network Engineering Team",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
    
    @staticmethod
    def get_mobile_modem_health_rules() -> Dict[str, Any]:
        """Mobile modem health analysis rules document"""
        return {
            "id": "health_rule_mobile_modem_001",
            "title": "Mobile Modem Health Analysis Framework",
            "document_type": DocumentType.BEST_PRACTICES,
            "content": """
            Mobile Modem (4G/5G) Health Assessment Rules
            
            HEALTH INDICATORS:
            
            1. SIGNAL STRENGTH
               - CRITICAL: signal_strength < -110 dBm (Very poor signal)
               - WARNING: signal_strength < -90 dBm (Weak signal)
               - HEALTHY: signal_strength >= -90 dBm (Good signal)
            
            2. CONNECTION STATUS
               - CRITICAL: status = 'DISCONNECTED' or 'ERROR'
               - WARNING: status = 'CONNECTING' (Unstable)
               - HEALTHY: status = 'CONNECTED' (Stable connection)
            
            3. DATA THROUGHPUT
               - WARNING: throughput_mbps < 10 (Low throughput)
               - HEALTHY: throughput_mbps >= 50 (Good throughput)
            
            4. TEMPERATURE
               - CRITICAL: temperature_celsius > 70 (Overheating)
               - WARNING: temperature_celsius > 60 (High temperature)
               - HEALTHY: temperature_celsius <= 60 (Normal temperature)
            """,
            "keywords": ["health", "mobile", "modem", "4G", "5G", "signal", "temperature"],
            "executable_rules": {
                "device_type": "mobile_modem",
                "summary_fields": [
                    "name", "model", "status", "signal_strength",
                    "throughput_mbps", "temperature_celsius", "network_type"
                ],
                "health_conditions": {
                    "CRITICAL": [
                        {"field": "signal_strength", "operator": "<", "value": -110},
                        {"field": "status", "operator": "in", "value": ["DISCONNECTED", "ERROR"]},
                        {"field": "temperature_celsius", "operator": ">", "value": 70}
                    ],
                    "WARNING": [
                        {"field": "signal_strength", "operator": "<", "value": -90},
                        {"field": "throughput_mbps", "operator": "<", "value": 10},
                        {"field": "temperature_celsius", "operator": ">", "value": 60}
                    ]
                }
            }
        }
    
    @staticmethod
    def get_environment_specific_rules() -> Dict[str, Any]:
        """Environment-specific health rules"""
        return {
            "id": "health_rule_env_specific_001",
            "title": "Environment-Specific Health Thresholds",
            "document_type": DocumentType.CONFIGURATION_GUIDE,
            "content": """
            Environment-Specific Health Assessment Adjustments
            
            PRODUCTION ENVIRONMENT:
            - Stricter thresholds for all metrics
            - service_count minimum: 100
            - complete_config: MUST be true
            - managed_by_inmanta: MUST be true
            
            UAT ENVIRONMENT:
            - Relaxed thresholds for testing
            - service_count minimum: 10
            - complete_config: SHOULD be true
            - managed_by_inmanta: RECOMMENDED
            
            TEST ENVIRONMENT:
            - Minimal requirements
            - service_count minimum: 1
            - complete_config: OPTIONAL
            - managed_by_inmanta: OPTIONAL
            """,
            "keywords": ["environment", "production", "UAT", "test", "thresholds"],
            "executable_rules": {
                "environment_overrides": {
                    "PRODUCTION": {
                        "min_service_count": 100,
                        "require_inmanta": True,
                        "require_complete_config": True
                    },
                    "UAT": {
                        "min_service_count": 10,
                        "require_inmanta": False,
                        "require_complete_config": False
                    },
                    "TEST": {
                        "min_service_count": 1,
                        "require_inmanta": False,
                        "require_complete_config": False
                    }
                }
            }
        }
    
    @staticmethod
    def get_all_health_rules() -> List[Dict[str, Any]]:
        """Get all health rule documents"""
        return [
            HealthRulesKnowledge.get_ftth_olt_health_rules(),
            HealthRulesKnowledge.get_mobile_modem_health_rules(),
            HealthRulesKnowledge.get_environment_specific_rules()
        ]