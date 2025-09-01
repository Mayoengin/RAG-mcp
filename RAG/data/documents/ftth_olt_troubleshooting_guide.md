# FTTH OLT Troubleshooting Guide

## Purpose and Scope

This guide provides comprehensive troubleshooting procedures for FTTH Optical Line Terminal (OLT) devices. It covers common issues, diagnostic procedures, and resolution steps for maintaining optimal network performance and service availability.

## Emergency Contact Information

### Escalation Matrix
- **Level 1 Support**: NOC Team (24/7) - +1-XXX-XXX-XXXX
- **Level 2 Support**: Network Engineering - +1-XXX-XXX-XXXX
- **Level 3 Support**: Vendor TAC - +1-XXX-XXX-XXXX
- **Emergency Escalation**: Network Manager - +1-XXX-XXX-XXXX

## Troubleshooting Framework

### General Approach
1. **Problem Identification**: Clearly define the issue
2. **Information Gathering**: Collect relevant data and logs
3. **Root Cause Analysis**: Identify the underlying cause
4. **Solution Implementation**: Apply appropriate fix
5. **Verification**: Confirm resolution effectiveness
6. **Documentation**: Record findings and actions taken

### Health Scoring Context
When troubleshooting, always consider the device health score:
- **CRITICAL (0-49)**: Immediate action required
- **WARNING (50-79)**: Schedule maintenance
- **HEALTHY (80-100)**: Monitor for trends

## Common Issues and Resolutions

### 1. Service Configuration Issues

#### Issue: No Services Configured (service_count = 0)
**Health Impact**: CRITICAL (-50 points)
**Priority**: HIGH

**Symptoms**:
- No customer traffic flowing
- Empty service tables
- Customer complaints of no connectivity

**Diagnostic Steps**:
```bash
# Check service configuration
show service summary
show service detail all
show pon onu-list

# Verify OMCI communication
show omci onu-list
show omci session

# Check provisioning system status
show provisioning status
```

**Resolution Procedure**:
1. **Check Provisioning System**:
   - Verify connectivity to service provisioning database
   - Check for pending service orders
   - Validate provisioning templates

2. **Service Creation**:
   ```bash
   # Create new service
   service create customer-id [CUSTOMER_ID] service-type [TYPE]
   service [SERVICE_ID] vlan [VLAN_ID]
   service [SERVICE_ID] bandwidth downstream [DL] upstream [UL]
   service [SERVICE_ID] activate
   ```

3. **OMCI Registration**:
   ```bash
   # Force ONU registration
   pon-port [PORT] onu [ONU_ID] register
   omci session [ONU_ID] reset
   ```

4. **Verification**:
   ```bash
   # Confirm service creation
   show service [SERVICE_ID] detail
   ping customer-gateway [IP_ADDRESS]
   ```

#### Issue: Low Service Utilization (service_count < 50)
**Health Impact**: WARNING (-20 points)
**Priority**: MEDIUM

**Analysis Required**:
- Check market penetration in coverage area
- Verify marketing and sales activities
- Analyze competitor impact
- Review pricing strategy

**Technical Actions**:
1. Optimize PON split ratios for better coverage
2. Verify service quality to prevent churn
3. Monitor service performance metrics

### 2. Configuration Management Issues

#### Issue: Incomplete Configuration (complete_config = false)
**Health Impact**: CRITICAL (-40 points)
**Priority**: HIGH

**Symptoms**:
- Inconsistent device behavior
- Service provisioning failures
- Management system alarms

**Diagnostic Steps**:
```bash
# Compare configurations
show configuration running
show configuration startup
show configuration diff

# Check Inmanta status
show inmanta agent-status
show inmanta deployment-log

# Verify configuration completeness
show system configuration-validation
```

**Resolution Procedure**:
1. **Inmanta Deployment**:
   ```bash
   # Force configuration deployment
   inmanta agent deploy --force
   inmanta agent export --environment production
   ```

2. **Manual Configuration Completion**:
   ```bash
   # Configure missing elements
   configure terminal
   [missing configuration commands]
   write memory
   ```

3. **Validation**:
   ```bash
   # Verify configuration completeness
   show system health-check
   show configuration validate
   ```

#### Issue: Manual Management (managed_by_inmanta = false)
**Health Impact**: WARNING (-30 points)
**Priority**: MEDIUM

**Migration Procedure**:
1. **Preparation**:
   - Export current configuration
   - Create Inmanta service model
   - Test in UAT environment

2. **Migration**:
   ```bash
   # Enable Inmanta management
   inmanta agent install
   inmanta agent configure --server [INMANTA_SERVER]
   inmanta agent enable
   ```

3. **Validation**:
   - Verify configuration consistency
   - Test service provisioning
   - Monitor for configuration drift

### 3. Physical Layer Issues

#### Issue: High Optical Power Loss
**Symptoms**:
- High bit error rates
- Service degradation
- ONT registration failures

**Diagnostic Steps**:
```bash
# Check optical power levels
show pon port [PORT] optical-power
show pon port [PORT] statistics

# Check ONT power levels
show pon onu [ONU_ID] optical-power
show pon onu [ONU_ID] performance
```

**Resolution Procedure**:
1. **Connector Cleaning**:
   - Clean all fiber connectors with isopropyl alcohol
   - Use lint-free wipes and appropriate cleaning tools
   - Inspect with fiber scope

2. **Fiber Path Verification**:
   - Check for fiber bends (radius > 30mm)
   - Verify splice quality at patch panels
   - Test with OTDR if necessary

3. **Power Level Optimization**:
   ```bash
   # Adjust OLT TX power if supported
   pon-port [PORT] tx-power [LEVEL]
   
   # Configure optical protection thresholds
   pon-port [PORT] optical-threshold high [HIGH] low [LOW]
   ```

#### Issue: Uplink Connectivity Problems
**Symptoms**:
- No upstream connectivity
- High latency to core network
- Upstream interface down

**Diagnostic Steps**:
```bash
# Check uplink status
show interface uplink brief
show interface uplink [INTERFACE] detail

# Check routing
show ip route
show arp table

# Test connectivity
ping [GATEWAY_IP]
traceroute [DESTINATION]
```

**Resolution Procedure**:
1. **Physical Layer Check**:
   - Verify fiber/copper connections
   - Check SFP/SFP+ module status
   - Test with known good transceiver

2. **Configuration Verification**:
   ```bash
   # Check interface configuration
   show running-config interface [INTERFACE]
   
   # Verify VLAN configuration
   show vlan [UPLINK_VLAN]
   show spanning-tree [INTERFACE]
   ```

3. **Protocol Troubleshooting**:
   ```bash
   # Check LACP if using LAG
   show lacp [LAG_ID] detail
   
   # Verify routing protocols
   show ospf neighbors
   show bgp summary
   ```

### 4. Performance Issues

#### Issue: High CPU Utilization
**Symptoms**:
- Slow response to management commands
- Service provisioning delays
- Increased error rates

**Diagnostic Steps**:
```bash
# Check system resources
show system cpu-utilization
show system memory-utilization
show system processes top

# Check for high-traffic flows
show interface statistics rate
show service top-talkers
```

**Resolution Procedure**:
1. **Identify CPU-intensive processes**:
   ```bash
   show processes cpu sorted
   show processes memory sorted
   ```

2. **Traffic Analysis**:
   - Identify high-bandwidth services
   - Check for broadcast storms
   - Analyze traffic patterns

3. **Load Balancing**:
   - Redistribute services across PON ports
   - Implement traffic shaping
   - Consider hardware upgrade

#### Issue: High Error Rates
**Symptoms**:
- Increased FEC corrections
- CRC errors on interfaces
- Service quality degradation

**Diagnostic Steps**:
```bash
# Check error statistics
show interface errors
show pon errors
show service [SERVICE_ID] errors

# Check environmental conditions
show system temperature
show system power-supply
```

**Resolution Procedure**:
1. **Error Pattern Analysis**:
   - Identify error types and patterns
   - Correlate with environmental conditions
   - Check for external interference

2. **Optical Path Optimization**:
   - Clean connectors
   - Adjust power levels
   - Check fiber path integrity

3. **System Health Check**:
   - Verify cooling system operation
   - Check power supply stability
   - Monitor for hardware alarms

### 5. Environmental Issues

#### Issue: High Operating Temperature
**Symptoms**:
- Temperature alarms
- Performance degradation
- Potential hardware damage

**Immediate Actions**:
1. Check cooling system operation
2. Verify airflow paths are clear
3. Reduce system load if possible
4. Consider emergency shutdown if temperature exceeds limits

**Resolution Procedure**:
```bash
# Monitor temperature trends
show system temperature history
show environment cooling
show system alarms temperature

# Check fan status
show system fans
show system power-consumption
```

#### Issue: Power Supply Problems
**Symptoms**:
- Power supply alarms
- System instability
- Unexpected reboots

**Diagnostic Steps**:
```bash
# Check power status
show system power-supply detail
show system voltage-levels
show system power-consumption

# Check power history
show system power-events
show system ups-status
```

**Resolution Procedure**:
1. **Power Supply Verification**:
   - Check input power quality
   - Verify power cable connections
   - Test with backup power supply

2. **Load Analysis**:
   - Calculate total power consumption
   - Check for power spikes during provisioning
   - Consider load balancing across power supplies

## Advanced Diagnostics

### BERT (Bit Error Rate Testing)
```bash
# Start BERT on uplink interface
bert interface [INTERFACE] pattern [PATTERN] duration [TIME]

# Monitor BERT results
show bert interface [INTERFACE] results
show bert interface [INTERFACE] statistics
```

### Optical Time Domain Reflectometry (OTDR)
```bash
# Perform OTDR test (if supported)
otdr pon-port [PORT] start
show otdr pon-port [PORT] results
otdr pon-port [PORT] trace-save [FILENAME]
```

### Traffic Analysis
```bash
# Enable flow monitoring
flow-monitor interface [INTERFACE] enable
show flow-monitor interface [INTERFACE] top-flows

# Packet capture
packet-capture interface [INTERFACE] filter [FILTER] file [FILENAME]
```

## Preventive Maintenance

### Daily Checks
- Monitor system alarms
- Check environmental conditions
- Review error rate trends
- Verify backup system status

### Weekly Checks
- Clean optical connectors
- Review service performance metrics
- Check software update availability
- Validate backup configurations

### Monthly Checks
- Perform comprehensive system health check
- Review capacity utilization trends
- Test failover procedures
- Update documentation

### Quarterly Checks
- Perform OTDR testing on critical fibers
- Conduct disaster recovery testing
- Review vendor support contracts
- Evaluate system upgrade requirements

## Documentation Requirements

### Incident Documentation
For each troubleshooting incident, document:
1. **Problem Description**: Detailed symptom description
2. **Impact Assessment**: Affected services and customers
3. **Root Cause**: Identified underlying cause
4. **Resolution Steps**: Actions taken to resolve issue
5. **Prevention Measures**: Steps to prevent recurrence

### Knowledge Base Updates
- Update troubleshooting procedures based on new issues
- Add vendor-specific procedures as discovered
- Include lessons learned from major incidents
- Maintain FAQ section for common issues

## Vendor-Specific Procedures

### Nokia OLTs
- Specific CLI commands and procedures
- Vendor TAC escalation procedures
- Firmware update procedures
- Hardware replacement procedures

### Huawei OLTs
- Vendor-specific diagnostic commands
- GPON/EPON specific troubleshooting
- Element management system integration
- Performance monitoring procedures

### ZTE OLTs
- Specific troubleshooting workflows
- Vendor support portal access
- Hardware diagnostic procedures
- Software upgrade procedures

## Training and Certification

### Required Skills
- FTTH/GPON technology fundamentals
- OLT-specific CLI and management
- Optical network troubleshooting
- Network protocol analysis

### Recommended Certifications
- Vendor-specific certifications (Nokia, Huawei, ZTE)
- Fiber optic technician certification
- Network troubleshooting certifications
- ITIL service management certification

This troubleshooting guide should be regularly updated based on operational experience and vendor recommendations to maintain its effectiveness as a primary reference resource.