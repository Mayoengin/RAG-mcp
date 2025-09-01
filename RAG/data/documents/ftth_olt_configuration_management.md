# FTTH OLT Configuration Management Guide

## Introduction and Scope

This guide provides comprehensive procedures for managing FTTH OLT configurations using both manual and automated approaches. It emphasizes the use of Inmanta for automated configuration management while providing fallback procedures for manual operations.

## Configuration Management Philosophy

### Inmanta-First Approach
- **Primary Method**: All configuration changes through Inmanta
- **Benefits**: Consistency, version control, rollback capability, compliance checking
- **Manual Override**: Only for emergency situations
- **Documentation**: All changes tracked and auditable

### Configuration Completeness Definition
A configuration is considered **complete** when:
- All required parameters are configured
- Device is managed by Inmanta
- Configuration passes validation checks
- All services are properly provisioned
- Monitoring and alerting are configured

## Inmanta Configuration Management

### Inmanta Architecture Overview
```
[Inmanta Server] → [Inmanta Agent (on OLT)] → [Device Configuration]
       ↑                    ↓
[Git Repository] ← [Configuration Model]
```

### Inmanta Agent Installation

#### Prerequisites
- OLT must have network connectivity to Inmanta server
- Sufficient storage space (minimum 1GB free)
- Python 3.7+ runtime environment

#### Installation Procedure
```bash
# Download and install Inmanta agent
wget https://inmanta-server/agent/inmanta-agent.deb
dpkg -i inmanta-agent.deb

# Configure agent
inmanta-agent config set server-url https://inmanta-server:8888
inmanta-agent config set environment production-olts
inmanta-agent config set agent-name OLT[ID][REGION][NUMBER]

# Start agent service
systemctl enable inmanta-agent
systemctl start inmanta-agent

# Verify installation
inmanta-agent status
```

### Configuration Model Development

#### Service Definition Template
```python
# OLT Service Model Example
entity OLTDevice extends Device:
    """FTTH OLT device configuration model"""
    string hostname
    string region
    string environment
    int bandwidth_gbps
    bool managed_by_inmanta = true
end

entity Service extends ConfigItem:
    """Customer service configuration"""
    string customer_id
    int vlan_id
    int downstream_mbps
    int upstream_mbps
    string qos_profile
end

# Implementation constraints
OLTDevice.hostname regex r"^OLT\d+[A-Z]{4}\d+$"
Service.vlan_id > 0 and Service.vlan_id < 4095
```

#### Configuration Validation Rules
```python
# Health validation rules
implementation healthCheck for OLTDevice:
    # Ensure service count is not zero in production
    if self.environment == "PRODUCTION":
        assert len(self.services) > 0, "Production OLT must have services"
    
    # Ensure Inmanta management
    assert self.managed_by_inmanta == true, "OLT must be managed by Inmanta"
    
    # Ensure complete configuration
    assert self.hostname is defined, "Hostname must be configured"
    assert self.management_ip is defined, "Management IP must be configured"
end
```

### Configuration Deployment Process

#### Standard Deployment Workflow
1. **Model Update**: Developer updates configuration model in Git
2. **Compilation**: Inmanta server compiles the model
3. **Validation**: Configuration passes all validation rules
4. **Deployment**: Agent applies configuration to device
5. **Verification**: System validates successful deployment

#### Deployment Commands
```bash
# Compile configuration
inmanta project compile --environment production-olts

# Deploy to specific OLT
inmanta environment deploy --environment production-olts --agent OLT17PROP01

# Deploy to all OLTs in region
inmanta environment deploy --environment production-olts --filter region=HOBO

# Monitor deployment status
inmanta environment status --environment production-olts
```

### Configuration Rollback Procedures

#### Automatic Rollback
```bash
# Rollback to previous version
inmanta environment rollback --environment production-olts --version -1

# Rollback to specific version
inmanta environment rollback --environment production-olts --version 123

# Emergency rollback (bypass validation)
inmanta environment rollback --environment production-olts --force
```

#### Verification After Rollback
```bash
# Verify system health after rollback
show system health-check
show service summary
show interface brief

# Check Inmanta agent status
inmanta-agent status
inmanta-agent log tail
```

## Manual Configuration Procedures

### When Manual Configuration is Appropriate
- **Emergency situations**: Inmanta server unavailable
- **New device bootstrapping**: Initial configuration before Inmanta setup
- **Troubleshooting**: Temporary configuration for diagnostics
- **Vendor-specific features**: Not yet supported by Inmanta model

### Manual Configuration Best Practices
1. **Document all manual changes**
2. **Create Inmanta model update ticket**
3. **Test in UAT environment first**
4. **Plan migration back to Inmanta management**

### Basic System Configuration

#### Initial Device Setup
```bash
# Enter configuration mode
configure terminal

# Basic system configuration
hostname OLT[ID][REGION][NUMBER]
domain-name network.internal

# Management interface
interface management
  ip address [MGMT_IP] [NETMASK]
  gateway [GATEWAY_IP]
  vlan [MGMT_VLAN]

# Time synchronization
ntp server [NTP_SERVER_1]
ntp server [NTP_SERVER_2]

# SNMP configuration
snmp-server community [READONLY_COMMUNITY] ro
snmp-server community [READWRITE_COMMUNITY] rw
snmp-server contact "NOC Team <noc@company.com>"
snmp-server location "[DATA_CENTER] - Rack [RACK_ID]"

# Save configuration
write memory
```

#### User Management
```bash
# Create user accounts
username admin privilege 15 password [ADMIN_PASSWORD]
username operator privilege 10 password [OPERATOR_PASSWORD]
username readonly privilege 5 password [READONLY_PASSWORD]

# Configure authentication
aaa authentication login default local
aaa authorization exec default local

# SSH configuration
ip ssh version 2
ip ssh timeout 300
crypto key generate rsa modulus 2048
```

### Service Configuration

#### Customer Service Provisioning
```bash
# Create customer service
service [SERVICE_ID]
  description "Customer [CUSTOMER_ID] - [SERVICE_TYPE]"
  customer-id [CUSTOMER_ID]
  service-type residential
  
  # VLAN configuration
  vlan [CUSTOMER_VLAN]
  inner-vlan [INNER_VLAN] # if QinQ required
  
  # Bandwidth configuration
  bandwidth downstream [DOWNSTREAM_MBPS] mbps
  bandwidth upstream [UPSTREAM_MBPS] mbps
  
  # QoS configuration
  qos-profile [QOS_PROFILE]
  
  # Activate service
  no shutdown

# Bind service to PON port and ONU
pon-port [PON_PORT]
  onu [ONU_ID]
    service [SERVICE_ID] vlan [VLAN_ID]
```

#### Bulk Service Configuration
```bash
# Template for multiple services
for customer in [CUSTOMER_LIST]:
  service [BASE_SERVICE_ID + INCREMENT]
    description "Customer [CUSTOMER_ID] - Residential"
    vlan [BASE_VLAN + INCREMENT]
    bandwidth downstream 100 mbps upstream 20 mbps
    qos-profile residential
    no shutdown
```

### Network Configuration

#### Uplink Configuration
```bash
# Configure uplink interface
interface uplink [INTERFACE_ID]
  description "Uplink to [UPSTREAM_DEVICE]"
  mtu 9000
  
  # LACP configuration for redundancy
  channel-group [LAG_ID] mode active
  
  # Enable interface
  no shutdown

# Configure LAG
interface lag [LAG_ID]
  description "LAG to [UPSTREAM_DEVICE]"
  lacp timeout short
  lacp priority [PRIORITY]
```

#### VLAN Configuration
```bash
# Create VLANs
vlan [CUSTOMER_VLAN_RANGE]
  name "Customer Services"
  
vlan [MGMT_VLAN]
  name "Management"
  
vlan [UPLINK_VLAN]
  name "Uplink Transport"

# Configure VLAN interfaces if required
interface vlan [VLAN_ID]
  ip address [IP_ADDRESS] [NETMASK]
  description "[VLAN_DESCRIPTION]"
```

## Configuration Templates and Standards

### Naming Conventions

#### Device Naming
- **Format**: OLT[2-digit ID][4-letter REGION][2-digit NUMBER]
- **Examples**: OLT17HOBO01, OLT22GENT02, OLT23ROES01
- **Regional Codes**: HOBO, GENT, ROES, ASSE

#### Service Naming
- **Format**: SVC_[CUSTOMER_ID]_[SERVICE_TYPE]_[INCREMENT]
- **Examples**: SVC_12345_RES_001, SVC_67890_BUS_001

#### VLAN Allocation
- **Management**: 10-99
- **Customer Residential**: 100-2999
- **Customer Business**: 3000-3999
- **Uplink Transport**: 4000-4094

### Configuration Templates

#### Base OLT Configuration Template
```bash
# System identification
hostname ${HOSTNAME}
domain-name ${DOMAIN_NAME}

# Management
interface management
  ip address ${MGMT_IP} ${MGMT_MASK}
  gateway ${MGMT_GW}
  vlan ${MGMT_VLAN}

# Time synchronization
ntp server ${NTP_PRIMARY}
ntp server ${NTP_SECONDARY}

# Logging
logging server ${SYSLOG_SERVER}
logging level info
logging timestamp

# SNMP
snmp-server community ${RO_COMMUNITY} ro
snmp-server host ${NMS_SERVER} ${RW_COMMUNITY}

# Security
ip ssh version 2
no telnet server
service password-encryption
```

#### Service Configuration Template
```bash
# Service template
service ${SERVICE_ID}
  description "${CUSTOMER_ID} - ${SERVICE_TYPE} Service"
  customer-id ${CUSTOMER_ID}
  vlan ${SERVICE_VLAN}
  bandwidth downstream ${DL_SPEED} upstream ${UL_SPEED}
  qos-profile ${QOS_PROFILE}
  no shutdown
```

## Configuration Validation and Testing

### Pre-Deployment Validation

#### Configuration Syntax Check
```bash
# Inmanta model validation
inmanta project compile --environment uat-olts --verify-only

# Manual configuration check
configure terminal
[configuration commands]
validate configuration

# Exit without saving if errors found
exit discard
```

#### UAT Testing Procedure
1. **Deploy to UAT environment**
2. **Test basic connectivity**
3. **Provision test services**  
4. **Validate service functionality**
5. **Performance testing**
6. **Rollback testing**

### Post-Deployment Verification

#### Health Check Commands
```bash
# System health
show system health
show system resources
show environment all

# Network connectivity
show interface brief
show vlan brief
show service summary

# Service functionality
ping [TEST_IP]
show service [SERVICE_ID] statistics
show pon onu-list
```

#### Automated Testing
```bash
# Inmanta automated testing
inmanta environment test --environment production-olts --test-suite health-check

# Custom health check script
#!/bin/bash
# health_check.sh
echo "Checking OLT health..."
show system alarms | grep -i critical
show interface brief | grep -i down
show service summary | grep -i error
```

## Change Management Process

### Change Approval Workflow
1. **Change Request**: Submit RFC with technical details
2. **Impact Assessment**: Review affected services and customers
3. **Approval**: CAB approval for production changes
4. **Scheduling**: Schedule during maintenance window
5. **Implementation**: Execute change with rollback plan
6. **Verification**: Confirm successful implementation
7. **Documentation**: Update records and knowledge base

### Emergency Change Procedure
1. **Emergency Declaration**: Justify emergency status
2. **Minimal Approval**: Emergency approver authorization
3. **Implementation**: Execute with extensive monitoring
4. **Communication**: Notify stakeholders immediately
5. **Post-Implementation Review**: Full review within 24 hours

### Documentation Requirements

#### Change Documentation
- **Change ID**: Unique identifier
- **Description**: Detailed change description
- **Justification**: Business/technical rationale
- **Impact**: Risk assessment and affected services
- **Procedure**: Step-by-step implementation
- **Rollback Plan**: Detailed rollback procedure
- **Verification**: Success criteria and testing

#### Configuration Backup
```bash
# Automated backup before changes
backup configuration startup-config backup-[DATE]-[TIME].cfg
backup configuration running-config running-[DATE]-[TIME].cfg

# Archive to central repository
scp backup-*.cfg backup-server:/backups/olt-configs/
```

## Compliance and Auditing

### Configuration Compliance Monitoring
```bash
# Inmanta compliance checking
inmanta environment compliance --environment production-olts

# Generate compliance report
inmanta environment report --environment production-olts --format pdf
```

### Audit Requirements
- **Configuration Changes**: All changes logged and tracked
- **Access Control**: User access regularly reviewed
- **Backup Verification**: Regular restore testing
- **Compliance Reporting**: Monthly compliance reports

### Security Hardening
```bash
# Disable unused services
no http server
no telnet server
no snmp server

# Configure access control
access-list 10 permit [MGMT_NETWORK]
access-list 10 deny any

# Enable logging
logging audit enable
logging security enable
```

## Disaster Recovery

### Configuration Backup Strategy
- **Frequency**: Daily automated backups
- **Retention**: 30 days local, 1 year archived
- **Locations**: Local storage + remote backup site
- **Encryption**: All backups encrypted in transit and at rest

### Recovery Procedures
```bash
# Emergency configuration restore
configure replace backup-[DATE]-[TIME].cfg

# Inmanta-based recovery
inmanta environment restore --environment production-olts --backup [BACKUP_ID]

# Verify recovery
show system health
inmanta-agent status
```

This configuration management guide should be regularly updated to reflect operational experience, new Inmanta features, and changing business requirements.