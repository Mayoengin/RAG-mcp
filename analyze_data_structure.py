#!/usr/bin/env python3
"""Analyze actual JSON data structure to create data-driven documentation"""

import json
from pathlib import Path
from collections import Counter, defaultdict

def analyze_json_structure():
    """Analyze the actual JSON data to understand structure"""
    
    json_files = {
        'ftth_olt': '/Users/mayo.eid/Desktop/RAG/ftth_olt.json',
        'lag': '/Users/mayo.eid/Desktop/RAG/lag.json',
        'pxc': '/Users/mayo.eid/Desktop/RAG/pxc.json', 
        'mobile_modem': '/Users/mayo.eid/Desktop/RAG/mobile_modem.json',
        'team': '/Users/mayo.eid/Desktop/RAG/team.json',
        'circuit': '/Users/mayo.eid/Desktop/RAG/circuit.json'
    }
    
    analysis = {}
    
    for name, file_path in json_files.items():
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            print(f"\n{'='*60}")
            print(f"ANALYZING: {name.upper()}")
            print(f"{'='*60}")
            
            # Get the data array
            if isinstance(data, dict) and 'data' in data:
                items = data['data']
            elif isinstance(data, list):
                items = data
            else:
                items = [data]
            
            print(f"Total items: {len(items)}")
            
            if items:
                # Analyze first few items for structure
                sample_item = items[0]
                print(f"\nSample item structure:")
                print_structure(sample_item, indent=2)
                
                # Count unique values for key fields
                analyze_key_fields(items, name)
                
                analysis[name] = {
                    'count': len(items),
                    'sample_structure': get_structure_dict(sample_item),
                    'key_fields': get_key_field_analysis(items, name)
                }
            
        except Exception as e:
            print(f"Error analyzing {name}: {e}")
            analysis[name] = {'error': str(e)}
    
    return analysis

def print_structure(obj, indent=0, max_depth=3):
    """Print object structure with indentation"""
    if indent > max_depth * 2:
        print(" " * indent + "...")
        return
        
    if isinstance(obj, dict):
        for key, value in list(obj.items())[:10]:  # Limit to first 10 keys
            print(" " * indent + f"{key}: ", end="")
            if isinstance(value, (dict, list)):
                print(f"{type(value).__name__}")
                if isinstance(value, dict) and len(value) > 0:
                    print_structure(value, indent + 2, max_depth)
                elif isinstance(value, list) and len(value) > 0:
                    print(" " * (indent + 2) + f"[{len(value)} items]")
                    if value:
                        print_structure(value[0], indent + 4, max_depth)
            else:
                print(f"{type(value).__name__} = {str(value)[:50]}")
    elif isinstance(obj, list):
        print(" " * indent + f"List with {len(obj)} items")
        if obj:
            print_structure(obj[0], indent + 2, max_depth)

def get_structure_dict(obj, max_depth=2):
    """Get structure as dictionary"""
    if max_depth <= 0:
        return type(obj).__name__
        
    if isinstance(obj, dict):
        return {k: get_structure_dict(v, max_depth-1) for k, v in list(obj.items())[:5]}
    elif isinstance(obj, list):
        return f"list[{len(obj)}]" + (f" of {get_structure_dict(obj[0], max_depth-1)}" if obj else "")
    else:
        return type(obj).__name__

def get_key_field_analysis(items, data_type):
    """Analyze key fields for patterns"""
    analysis = {}
    
    if data_type == 'ftth_olt':
        names = [item.get('name', 'Unknown') for item in items]
        regions = [item.get('region', 'Unknown') for item in items]
        environments = [item.get('environment', 'Unknown') for item in items]
        
        analysis = {
            'device_names': Counter(names).most_common(10),
            'regions': Counter(regions).most_common(),
            'environments': Counter(environments).most_common(),
            'total_devices': len(items)
        }
        
    elif data_type == 'lag':
        devices = [item.get('device_name', 'Unknown') for item in items]
        lag_ids = [item.get('lag_id', 'Unknown') for item in items]
        
        analysis = {
            'devices': Counter(devices).most_common(10),
            'lag_id_range': f"{min(lag_ids) if lag_ids else 'N/A'} - {max(lag_ids) if lag_ids else 'N/A'}",
            'total_lags': len(items)
        }
        
    elif data_type == 'mobile_modem':
        hardware_types = [item.get('hardware_type', 'Unknown') for item in items]
        subscribers = [item.get('mobile_subscriber_id', 'Unknown') for item in items]
        
        analysis = {
            'hardware_types': Counter(hardware_types).most_common(),
            'subscriber_patterns': Counter(subscribers).most_common(10),
            'total_modems': len(items)
        }
        
    elif data_type == 'team':
        team_names = [item.get('team_name', 'Unknown') for item in items]
        
        analysis = {
            'teams': Counter(team_names).most_common(),
            'total_teams': len(items)
        }
    
    return analysis

def analyze_key_fields(items, data_type):
    """Print analysis of key fields"""
    analysis = get_key_field_analysis(items, data_type)
    
    print(f"\nKey field analysis:")
    for field, data in analysis.items():
        print(f"  {field}: {data}")

if __name__ == "__main__":
    analyze_json_structure()