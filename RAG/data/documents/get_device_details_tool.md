# get_device_details MCP Tool

## Purpose
The `get_device_details` tool provides detailed configuration information for a specific network device. Use this tool when you need deep technical details about one particular device.

## When to Use This Tool

### Question Patterns That Should Use This Tool:
- "Show me the configuration of [specific device name]"
- "What are the details for [device name]?"
- "Get technical information about [device name]"
- "How is [device name] configured?"
- "What are the connections for [device name]?"

### Example Queries:
- "Show me OLT17PROP01 configuration"
- "What are the CIN node details for CINMECHA01 connections?"
- "Get VPN subscriber details for modem LPL2408001DF"
- "Show me LAG configurations on CINAALSA01"
- "What are the contact details for the MOBILE team?"

## Tool Parameters

### Required Parameters:
- **device_name**: Exact name of the device (case-sensitive)

### Optional Parameters:
- **device_type**: 
  - Options: "ftth_olt", "lag", "pxc", "mobile_modem", "team"
  - Default: "ftth_olt"
  - Helps optimize the search

## Device Name Examples by Type

### FTTH OLT Device Names:
- Examples: "OLT17PROP01", "OLT17PROP23", "OLT70AALS01"
- Names follow pattern: OLT[number][REGION][number]

### LAG Device Names:
- Examples: "CINAALSA01", "SRPTRO01", "SRSCHA01" 
- Various device naming conventions

### Mobile Modem Device Names:
- Examples: "LPL2408001DF", "LPL24080006F", "LPL2408001DS"
- Serial number format: LPL[date/batch][sequence]

### Team Names:
- Examples: "MOBILE", "NAS", "IPOPS", "INFRA", "DTV"
- Uppercase team identifiers

## Data Structures You'll Get

### FTTH OLT Device Details:
```
Device Configuration:
- ESI Name (Ethernet Segment Identifier)
- ESI (MAC-based identifier)  
- Environment classification
- Region assignment

BNG Configuration:
- Master Node (name and IP address)
- Slave Node (name and IP address)
- LAG IDs for BNG connections

CIN Node Connections:
- Primary CIN node (name and IP)
- Secondary CIN node (name and IP) 
- Port assignments (slot/port format)
- Count of configured ports
```

### LAG Device Details:
```
LAG Configuration:
- LAG ID (numeric identifier)
- Description (purpose/notes)
- Admin Key (LACP configuration)
- Device association
```

### PXC Device Details:
```
Cross-Connect Configuration:
- PXC ID (port identifier)
- Description (connection purpose)
- Device location/assignment
```

### Mobile Modem Details:
```
Hardware Information:
- Serial Number
- Hardware Type (Nokia 5G26-A)
- Mobile Modem ID (UUID)

Service Configuration:
- VPN Subscriber ID
- FNT Command ID (if configured)
```

### Team Details:
```
Team Information:
- Team Name
- Team ID (UUID)
- Description (if available)
- Contact Information (if available)
```

## Response Format
The tool returns detailed markdown with:
- Device identification header
- Configuration sections organized by type
- Technical parameters and values
- Connection information where applicable

## Typical Use Cases

### FTTH OLT Configuration Analysis
```
Query: "Show me OLT17PROP01 configuration"
Tool Call: get_device_details(device_name="OLT17PROP01", device_type="ftth_olt")
Result: Complete OLT config including CIN, BNG, ESI details
```

### LAG Configuration Details
```
Query: "What LAG configurations exist on CINAALSA01?"
Tool Call: get_device_details(device_name="CINAALSA01", device_type="lag") 
Result: Specific LAG details for that device
```

### Mobile Modem Investigation
```
Query: "Get details for modem LPL2408001DF"
Tool Call: get_device_details(device_name="LPL2408001DF", device_type="mobile_modem")
Result: Hardware type, VPN subscriber, service configuration
```

## What This Tool Does NOT Do
- Does not list multiple devices (use list_network_devices instead)
- Does not show relationships between devices
- Does not provide impact analysis
- Does not give inventory counts

## When to Use Other Tools Instead

### Use `list_network_devices` if:
- User wants to see multiple devices
- User asks for counts or inventory
- User doesn't specify an exact device name

### Use `query_network_resources` if:
- User asks about device relationships
- User wants impact analysis
- User asks what happens if device fails

## Common Error Cases

### Device Not Found:
- Check exact spelling of device name
- Verify device exists in the specified device_type
- Try using list_network_devices with filter to find similar names

### Wrong Device Type:
- Mobile modems use serial numbers, not device names
- Teams use team names like "MOBILE", not device names
- FTTH OLTs use names like "OLT17PROP01"

## Data Interpretation

### Configuration Completeness:
- ✅ indicates complete/operational configuration
- ⚠️ indicates incomplete or missing configuration
- "N/A" indicates field not applicable for this device

### Connection Information:
- CIN nodes are core infrastructure connections
- BNG nodes are broadband network gateways  
- LAG IDs indicate link aggregation groups
- Port numbers follow format "slot/port/subport"

### VPN Subscribers (Mobile):
- Format: "MOBILE-SUB-VPN-[identifier]"
- Multiple modems can share same subscriber ID