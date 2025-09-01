# FTTH OLT Health Monitoring Procedures

## Overview and Objectives

This document outlines comprehensive health monitoring procedures for FTTH OLT devices using the vectorized health analysis system. The monitoring framework provides proactive identification of issues, automated health scoring, and intelligent recommendations for maintenance actions.

## Health Scoring Framework

### Scoring Methodology
The health scoring system uses a **vectorized knowledge approach** where health rules are matched to device conditions using 384-dimensional vector similarity search.

#### Base Scoring System
- **Perfect Health**: 100 points
- **Penalty System**: Points deducted for each identified issue
- **Minimum Score**: 0 points (floor)
- **Real-time Calculation**: Updated continuously based on current device state

#### Health Categories
- **🟢 HEALTHY (80-100 points)**: Device operating optimally
- **🟡 WARNING (50-79 points)**: Minor issues requiring attention
- **🔴 CRITICAL (0-49 points)**: Serious problems needing immediate action

### Vector-Based Health Rule Matching

#### Rule Selection Process
1. **Query Generation**: Device condition → "health analysis ftth_olt monitoring diagnostics"
2. **Vector Search**: Generate 384D embedding and search health rule vectors
3. **Similarity Matching**: Cosine similarity calculation (typical: -0.377 for FTTH rules)
4. **Rule Application**: Execute best-matching health rule conditions

#### Health Rule Components
```json
{
  "device_type": "ftth_olt",
  "health_conditions": {
    "CRITICAL": [
      {"field": "service_count", "operator": "==", "value": 0},
      {"field": "complete_config", "operator": "==", "value": false}
    ],
    "WARNING": [
      {"field": "service_count", "operator": "<", "value": 50}
    ]
  },
  "scoring_rules": [
    {"condition": "service_count == 0", "impact": -50, "reason": "No services"},
    {"condition": "not managed_by_inmanta", "impact": -30, "reason": "Manual management"}
  ]
}
```

## Health Criteria and Thresholds

### Critical Health Indicators (-50 points each)

#### Service Configuration Issues
**Condition**: `service_count == 0`
- **Impact**: CRITICAL health status
- **Root Cause**: No customer services configured
- **Symptoms**: Zero revenue-generating traffic
- **Immediate Action**: Investigate service provisioning system
- **Recommendation**: "🚨 URGENT: Configure services for this OLT immediately"

#### Production Management Issues  
**Condition**: `environment == 'PRODUCTION' and not managed_by_inmanta`
- **Impact**: CRITICAL health status
- **Root Cause**: Production device without automated management
- **Symptoms**: Configuration drift, manual errors, compliance issues
- **Immediate Action**: Migration to Inmanta management
- **Recommendation**: "⚠️ Migrate to Inmanta for automated management"

#### Configuration Completeness
**Condition**: `complete_config == false`
- **Impact**: CRITICAL health status
- **Root Cause**: Missing essential configuration parameters
- **Symptoms**: Unpredictable behavior, service failures
- **Immediate Action**: Complete configuration deployment
- **Recommendation**: "⚠️ Complete device configuration to ensure stability"

### Warning Health Indicators (-20 to -30 points each)

#### Low Service Utilization
**Condition**: `service_count < 50 and service_count > 0`
- **Impact**: WARNING health status
- **Root Cause**: Underutilized network resource
- **Analysis**: Market penetration or technical issues
- **Action**: Capacity optimization, market analysis

#### Manual Management
**Condition**: `managed_by_inmanta == false` (non-production)
- **Impact**: WARNING health status
- **Root Cause**: Manual configuration management
- **Risk**: Human error, inconsistent configuration
- **Action**: Plan migration to automated management

### Positive Health Indicators (+10 points each)

#### High Capacity Infrastructure
**Condition**: `bandwidth_gbps >= 100`
- **Impact**: Bonus health points
- **Benefit**: Future-ready infrastructure
- **Value**: Supports service growth

## Monitoring Infrastructure

### Data Collection Architecture
```
[OLT Device] → [SNMP/NETCONF] → [Monitoring System] → [Health Engine] → [Vector Search] → [Health Score]
```

### Real-Time Monitoring Components

#### Device Telemetry Collection
- **SNMP Polling**: Every 5 minutes for critical metrics
- **NETCONF Streaming**: Real-time configuration changes
- **Syslog Analysis**: Event-based monitoring
- **Performance Metrics**: 1-minute intervals

#### Health Assessment Engine
```python
async def analyze_device_health(device_data):
    """Vector-based health analysis"""
    # 1. Generate query embedding
    query_text = f"health analysis {device_type} monitoring diagnostics"
    query_embedding = generate_embedding(query_text)
    
    # 2. Vector similarity search
    health_rules = await find_similar_health_rules(query_embedding)
    
    # 3. Apply best matching rule
    best_rule = health_rules[0]  # Highest similarity
    health_score = await execute_health_rule(device_data, best_rule)
    
    return health_score
```

### Monitoring Metrics

#### System Performance Metrics
- **CPU Utilization**: Current and historical trends
- **Memory Usage**: Available memory and swap usage  
- **Temperature**: Operating temperature monitoring
- **Power Consumption**: Real-time power draw

#### Optical Performance Metrics
- **Optical Power Levels**: TX/RX power per PON port
- **Error Rates**: FEC errors, BER measurements
- **ONT Registration**: Active/inactive ONT counts
- **Service Quality**: Latency, jitter, packet loss

#### Network Performance Metrics
- **Uplink Utilization**: Bandwidth usage trends
- **Service Throughput**: Per-service performance
- **Error Statistics**: Interface errors and drops
- **Route Table Size**: Routing information base size

## Automated Monitoring Procedures

### Continuous Health Assessment

#### Real-Time Health Calculation
```python
def calculate_health_score(device):
    """Real-time health scoring"""
    base_score = 100
    penalties = []
    
    # Critical conditions
    if device.service_count == 0:
        penalties.append((-50, "No services configured"))
    
    if not device.managed_by_inmanta and device.environment == "PRODUCTION":
        penalties.append((-30, "Production without Inmanta"))
    
    if not device.complete_config:
        penalties.append((-40, "Incomplete configuration"))
    
    # Warning conditions  
    if 0 < device.service_count < 50:
        penalties.append((-20, "Low service utilization"))
    
    # Calculate final score
    total_penalty = sum(penalty for penalty, reason in penalties)
    final_score = max(0, base_score + total_penalty)
    
    # Determine health status
    if final_score >= 80:
        status = "HEALTHY"
    elif final_score >= 50:
        status = "WARNING"
    else:
        status = "CRITICAL"
    
    return {
        "score": final_score,
        "status": status,
        "penalties": penalties
    }
```

#### Health Trend Analysis
- **Historical Scoring**: Track health scores over time
- **Degradation Detection**: Identify declining health patterns
- **Predictive Analytics**: Forecast potential issues
- **Correlation Analysis**: Link health changes to network events

### Alerting and Notification System

#### Alert Severity Levels
- **CRITICAL**: Health score < 50, immediate response required
- **WARNING**: Health score 50-79, scheduled maintenance needed
- **INFORMATIONAL**: Health score changes, trend monitoring

#### Alert Routing Matrix
```yaml
alert_routing:
  CRITICAL:
    - NOC Team (immediate)
    - Network Engineering (escalation after 15 min)
    - Management (escalation after 1 hour)
  WARNING:
    - Network Engineering (within 4 hours)
    - Daily summary to management
  INFORMATIONAL:
    - Dashboard updates
    - Weekly trend reports
```

#### Notification Channels
- **Real-time**: Slack/Teams integration
- **Email**: Structured alert emails with context
- **SMS**: Critical alerts for on-call staff
- **Dashboard**: Visual health status displays
- **API**: Integration with external ticketing systems

## Proactive Monitoring Workflows

### Daily Health Assessment

#### Morning Health Check (8:00 AM)
```bash
#!/bin/bash
# daily_health_check.sh

echo "=== Daily OLT Health Assessment ==="
echo "Date: $(date)"
echo

# Get health summary for all OLTs
for region in HOBO GENT ROES ASSE; do
    echo "--- $region Region ---"
    query_health_by_region $region
    echo
done

# Generate daily health report
generate_daily_health_report
send_health_summary_email
```

#### Health Check Components
1. **Overall Fleet Health**: Summary of all devices
2. **Critical Issues**: Immediate attention required
3. **Warning Trends**: Developing problems
4. **Capacity Utilization**: Resource usage analysis
5. **Maintenance Recommendations**: Proactive actions

### Weekly Health Analysis

#### Weekly Health Review (Monday 9:00 AM)
- **Trend Analysis**: Week-over-week health changes
- **Root Cause Analysis**: Recurring issues investigation
- **Capacity Planning**: Growth trend assessment
- **Maintenance Planning**: Preventive maintenance scheduling

#### Health Metrics Dashboard
```json
{
  "fleet_summary": {
    "total_olts": 7,
    "healthy": 4,
    "warning": 1,
    "critical": 2,
    "average_health_score": 72.3
  },
  "regional_breakdown": {
    "HOBO": {"total": 4, "avg_score": 65.0},
    "GENT": {"total": 2, "avg_score": 95.0},
    "ROES": {"total": 1, "avg_score": 90.0}
  }
}
```

### Monthly Health Assessment

#### Comprehensive Monthly Review
1. **Health Score Trends**: 30-day trend analysis
2. **Issue Pattern Analysis**: Recurring problem identification
3. **Performance Benchmarking**: Compare against SLAs
4. **Capacity Assessment**: Current and projected usage
5. **Maintenance Effectiveness**: Review of performed maintenance

## Predictive Health Analytics

### Machine Learning Integration

#### Health Trend Prediction
```python
class HealthTrendPredictor:
    """Predict health degradation using historical data"""
    
    def predict_health_degradation(self, device_id, days_ahead=30):
        # Load historical health scores
        historical_data = load_health_history(device_id, days=90)
        
        # Train predictive model
        model = train_health_prediction_model(historical_data)
        
        # Generate predictions
        predictions = model.predict(days_ahead)
        
        return {
            "device_id": device_id,
            "current_score": historical_data[-1].score,
            "predicted_score": predictions[-1],
            "risk_level": calculate_risk_level(predictions),
            "recommended_actions": generate_recommendations(predictions)
        }
```

#### Anomaly Detection
- **Baseline Establishment**: Normal operating patterns
- **Deviation Detection**: Significant changes from baseline
- **Correlation Analysis**: Link anomalies to external factors
- **Early Warning**: Alert before critical thresholds reached

### Environmental Correlation

#### External Factor Analysis
- **Weather Impact**: Temperature effects on performance
- **Power Quality**: Voltage fluctuation correlation
- **Network Events**: Upstream changes affecting health
- **Maintenance Windows**: Post-maintenance health tracking

## Health Improvement Procedures

### Critical Health Recovery

#### Immediate Response Protocol (Score < 30)
1. **Emergency Assessment**: Determine service impact
2. **Immediate Mitigation**: Restore basic functionality
3. **Root Cause Analysis**: Identify underlying issue
4. **Corrective Action**: Implement permanent fix
5. **Recovery Validation**: Confirm health improvement

#### Service Recovery Procedure
```bash
# Emergency service configuration
service emergency-restore customer-id EMERGENCY
  vlan 999
  bandwidth downstream 100 mbps upstream 20 mbps
  priority high
  activate immediate

# Validate emergency service
ping customer-gateway 192.168.1.1
show service EMERGENCY statistics
```

### Warning Health Enhancement

#### Proactive Improvement Process (Score 50-79)
1. **Issue Prioritization**: Rank improvement opportunities
2. **Resource Allocation**: Assign appropriate resources
3. **Implementation Planning**: Schedule improvement work
4. **Change Execution**: Implement improvements
5. **Effectiveness Measurement**: Track health score improvement

### Health Maintenance Optimization

#### Preventive Maintenance Scheduling
- **Health Score Triggers**: Schedule maintenance based on scores
- **Trend Analysis**: Predict optimal maintenance timing
- **Resource Optimization**: Batch maintenance for efficiency
- **Impact Minimization**: Schedule during low-traffic periods

## Integration with Network Operations

### NOC Dashboard Integration
```javascript
// Real-time health dashboard component
const OLTHealthDashboard = () => {
  return (
    <div className="health-dashboard">
      <HealthSummaryWidget />
      <RegionalHealthMap />
      <CriticalAlertsList />
      <HealthTrendChart />
      <MaintenanceSchedule />
    </div>
  );
};
```

### Ticketing System Integration
- **Automatic Ticket Creation**: Critical health issues
- **Priority Assignment**: Based on health score and impact
- **Escalation Rules**: Time-based escalation procedures
- **Resolution Tracking**: Link tickets to health improvements

### Capacity Management Integration
- **Health-Based Capacity Planning**: Use health scores for expansion planning
- **Service Migration**: Move services from unhealthy to healthy devices
- **Load Balancing**: Optimize service distribution based on health

## Performance and Scalability

### Monitoring System Performance
- **Health Calculation Time**: < 200ms per device
- **Vector Search Performance**: < 150ms per health rule query
- **Alert Processing**: < 5 seconds from detection to notification
- **Dashboard Update Rate**: Real-time (< 30 seconds)

### Scalability Considerations
- **Device Scaling**: Support for 1000+ OLT devices
- **Metric Volume**: Handle 10M+ metrics per hour
- **Historical Storage**: 2+ years of health data retention
- **Query Performance**: Sub-second health queries at scale

This health monitoring framework provides comprehensive, intelligent, and proactive oversight of FTTH OLT infrastructure, enabling optimal network performance and service delivery.