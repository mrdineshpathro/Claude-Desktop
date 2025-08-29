import json
from typing import Dict, Any, List

def format_output(data: Dict[str, Any]) -> str:
    """Format output data for better readability"""
    return json.dumps(data, indent=2, default=str)

def validate_host(host: str) -> bool:
    """Basic host validation"""
    if not host:
        return False
    
    # Simple IP address validation
    parts = host.split('.')
    if len(parts) == 4:
        try:
            return all(0 <= int(part) <= 255 for part in parts)
        except ValueError:
            return False
    
    return True

def parse_options(options_str: str) -> Dict[str, Any]:
    """Parse options string into dictionary"""
    try:
        return json.loads(options_str)
    except json.JSONDecodeError:
        return {}
