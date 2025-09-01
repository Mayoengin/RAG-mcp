# FTTH OLT Comprehensive Knowledge Base

## Overview

Fiber-to-the-Home (FTTH) Optical Line Terminals (OLTs) are critical network infrastructure components that provide high-speed fiber connectivity to residential and business customers. This comprehensive guide covers all aspects of FTTH OLT management, deployment, and operations.

## Table of Contents

1. [Technical Specifications](#technical-specifications)
2. [Device Architecture](#device-architecture)
3. [Regional Deployment Patterns](#regional-deployment-patterns)
4. [Configuration Management](#configuration-management)
5. [Health Monitoring](#health-monitoring)
6. [Troubleshooting Procedures](#troubleshooting-procedures)
7. [Best Practices](#best-practices)
8. [Integration Points](#integration-points)

## Technical Specifications

### Hardware Specifications

#### Bandwidth Capacity
- **Standard Capacity**: 10 Gbps per OLT
- **High Capacity**: 100 Gbps per OLT
- **Connection Types**: 1x10G, 1x100G
- **Uplink Interfaces**: SFP+, QSFP28

#### Service Scaling
- **Low Utilization**: < 50 services per OLT
- **Normal Operation**: 100-300 services per OLT
- **High Utilization**: > 300 services per OLT
- **Maximum Capacity**: Vendor-dependent (typically 1024-4096 services)

#### Power and Environmental
- **Power Consumption**: 200-500W depending on capacity
- **Operating Temperature**: -5°C to +50°C
- **Humidity**: 5-95% non-condensing
- **MTBF**: > 100,000 hours

### Software Features

#### Management Interfaces
- **SNMP v2c/v3**: Network monitoring and management
- **CLI Access**: SSH/Telnet command line interface
- **Web Interface**: HTTP/HTTPS management portal
- **NETCONF/YANG**: Programmatic configuration

#### Supported Standards
- **ITU-T G.984**: GPON standard compliance
- **ITU-T G.987**: XG-PON standard compliance
- **IEEE 802.3**: Ethernet standards
- **ITU-T G.988**: OMCI (ONT Management and Control Interface)

## Device Architecture

### Network Position
```
[Core Network] → [Aggregation Switch] → [OLT] → [ODN] → [ONT/ONU] → [Customer]
```

### Key Components

#### Line Cards
- **PON Ports**: 16-64 PON ports per line card
- **Uplink Ports**: 4-8 uplink ports per line card
- **Processing**: Dedicated CPU and memory per card

#### Control Module
- **Main CPU**: ARM/x86 processor for control functions
- **Memory**: 4-16GB RAM, 32-256GB storage
- **Management**: Dedicated management interfaces

#### Power System
- **Redundant PSU**: Dual power supplies for high availability
- **Battery Backup**: Optional UPS integration
- **Power Monitoring**: Real-time power consumption tracking

### ESI (Ethernet Segment Identifier) Structure
- **Format**: ESI_[OLT_NAME]
- **Example**: ESI_OLT17PROP01
- **Purpose**: Unique identification for network topology mapping

## Regional Deployment Patterns

### HOBO Region
- **Total OLTs**: 4 devices (OLT17PROP01, OLT18PROP02, OLT19PROP03, OLT20PROP01)
- **Environment Mix**: 3 PRODUCTION, 1 UAT
- **Capacity Distribution**: 
  - High capacity: 1 device (100 Gbps)
  - Standard capacity: 3 devices (10 Gbps each)
- **Service Distribution**: 200-400 services per production OLT

### GENT Region
- **Total OLTs**: 2 devices (OLT21GENT01, OLT22GENT02)
- **Environment**: 2 PRODUCTION
- **Capacity Distribution**:
  - High capacity: 1 device (100 Gbps)
  - Standard capacity: 1 device (10 Gbps)
- **Service Distribution**: 250-300 services per OLT

### ROES Region  
- **Total OLTs**: 1 device (OLT23ROES01)
- **Environment**: 1 PRODUCTION
- **Capacity**: Standard (10 Gbps)
- **Service Load**: 180 services

### ASSE Region
- **Status**: Reserved for future expansion
- **Planned Capacity**: 2-4 OLTs
- **Target Environment**: PRODUCTION

## Configuration Management

### Inmanta Integration

#### Managed vs Unmanaged
- **Managed by Inmanta**: Automated configuration deployment
- **Manual Management**: Direct CLI/SNMP configuration
- **Benefits of Inmanta**: 
  - Consistent configuration across fleet
  - Automated compliance checking
  - Rollback capabilities
  - Change tracking and audit

#### Configuration Completeness
- **Complete Config**: All required parameters configured
- **Incomplete Config**: Missing critical configuration elements
- **Impact**: Incomplete configs lead to service disruption risk

### Service Configuration

#### Service Provisioning
- **Service Count**: Number of active customer connections
- **Service Types**: Residential, Business, Wholesale
- **Bandwidth Allocation**: Dynamic bandwidth assignment
- **QoS Profiles**: Service-specific quality parameters

#### VLAN Configuration
- **Management VLAN**: OLT management traffic
- **Service VLANs**: Customer traffic segregation  
- **Uplink VLANs**: Aggregation network connectivity
- **Native VLAN**: Untagged traffic handling

## Health Monitoring

### Health Scoring System

#### Scoring Methodology
- **Base Score**: 100 points (perfect health)
- **Penalty System**: Deduct points for issues
- **Health Categories**:
  - **HEALTHY**: 80-100 points
  - **WARNING**: 50-79 points  
  - **CRITICAL**: 0-49 points

#### Health Criteria

##### Critical Issues (-50 points each)
- **No Services Configured**: service_count = 0
- **Production Without Management**: PRODUCTION + not managed_by_inmanta
- **Configuration Incomplete**: complete_config = false

##### Warning Issues (-20 to -30 points each)
- **Low Service Utilization**: service_count < 50
- **Manual Management**: managed_by_inmanta = false
- **Bandwidth Constraints**: bandwidth_gbps < 10

##### Bonus Points (+10 points each)
- **High Capacity**: bandwidth_gbps >= 100
- **Optimal Utilization**: 100 ≤ service_count ≤ 300

### Monitoring Parameters

#### Performance Metrics
- **Uplink Utilization**: % of uplink capacity used
- **PON Port Utilization**: Services per PON port
- **Error Rates**: FEC errors, BER measurements
- **Latency**: Round-trip time measurements

#### Operational Metrics
- **Uptime**: Device availability percentage
- **Temperature**: Operating temperature monitoring
- **Power Consumption**: Real-time power usage
- **Memory/CPU**: System resource utilization

## Troubleshooting Procedures

### Common Issues

#### No Services Configured
**Symptoms**: 
- service_count = 0
- No customer traffic
- Empty service provisioning tables

**Diagnosis Steps**:
1. Check service provisioning system
2. Verify OMCI communication with ONTs
3. Check VLAN configuration
4. Validate uplink connectivity

**Resolution**:
1. Provision services through management system
2. Configure VLAN mappings
3. Validate ONT registration
4. Test service connectivity

#### Configuration Management Issues
**Symptoms**:
- complete_config = false
- Inconsistent device behavior
- Service provisioning failures

**Diagnosis Steps**:
1. Compare running vs. startup configuration
2. Check Inmanta deployment status
3. Validate configuration syntax
4. Check access permissions

**Resolution**:
1. Deploy complete configuration via Inmanta
2. Manually configure missing parameters
3. Validate configuration consistency
4. Document configuration changes

#### Connectivity Issues
**Symptoms**:
- High error rates
- Service degradation
- Uplink failures

**Diagnosis Steps**:
1. Check physical layer (fiber, connectors)
2. Monitor optical power levels
3. Check uplink status and utilization
4. Validate routing tables

**Resolution**:
1. Clean/replace fiber connections
2. Adjust optical power levels
3. Configure uplink redundancy
4. Update routing configuration

### Diagnostic Commands

#### Basic Health Check
```bash
# Check device status
show system status
show interfaces brief
show pon summary

# Check service status  
show service overview
show vlan brief
show mac-address-table summary
```

#### Performance Monitoring
```bash
# Check utilization
show interface statistics
show pon port utilization
show cpu-utilization
show memory-utilization

# Check errors
show interface errors
show pon errors
show system logs
```

## Best Practices

### Deployment Standards

#### Pre-Deployment
1. **Site Survey**: Physical location assessment
2. **Power Planning**: Adequate power and cooling
3. **Fiber Planning**: Uplink and distribution fiber paths
4. **Configuration Preparation**: Pre-configure device parameters

#### Deployment Process
1. **Physical Installation**: Rack mounting and power connection
2. **Initial Configuration**: Management IP and basic parameters
3. **Inmanta Integration**: Add device to management system
4. **Service Provisioning**: Configure customer services
5. **Testing and Validation**: End-to-end connectivity testing

### Operational Excellence

#### Change Management
1. **Use Inmanta for all configuration changes**
2. **Test changes in UAT environment first**
3. **Schedule changes during maintenance windows**
4. **Document all changes and rollback procedures**

#### Monitoring and Alerting
1. **Monitor all health criteria continuously**
2. **Set up automated alerting for critical issues**
3. **Regular health assessments using scoring system**
4. **Proactive maintenance based on trends**

#### Capacity Management
1. **Monitor service growth trends**
2. **Plan capacity expansion before reaching 80% utilization**
3. **Load balance services across multiple OLTs**
4. **Consider high-capacity upgrades for high-demand areas**

## Integration Points

### Network Architecture

#### Uplink Connectivity
- **BNG Integration**: Broadband Network Gateway connectivity
- **Aggregation Layer**: Connection to aggregation switches
- **Core Network**: Integration with service provider core
- **Redundancy**: Dual-homed uplink configuration

#### Management Systems
- **Network Management System (NMS)**: SNMP-based monitoring
- **Element Management System (EMS)**: Device-specific management
- **Service Provisioning**: Automated service deployment
- **Performance Management**: SLA monitoring and reporting

### Service Integration

#### Customer Services
- **Residential Broadband**: High-speed internet access
- **Business Services**: Dedicated bandwidth and SLA
- **Wholesale Services**: Carrier-to-carrier connectivity
- **Value-Added Services**: IPTV, VoIP, cloud services

#### Service Assurance
- **SLA Monitoring**: Real-time performance tracking
- **Fault Management**: Automated fault detection and resolution
- **Performance Optimization**: Continuous service improvement
- **Customer Communication**: Automated status updates

## Conclusion

FTTH OLTs are critical infrastructure components requiring comprehensive management across technical, operational, and service domains. This knowledge base provides the foundation for effective OLT deployment, management, and troubleshooting, ensuring optimal service delivery and network reliability.

Regular updates to this knowledge base should reflect operational experience, vendor recommendations, and evolving industry standards to maintain its effectiveness as a reference resource.