import os
import json
from typing import Dict, Any, List
from fastmcp import FastMCP, Context
from .client import MetasploitClient

mcp = FastMCP("Metasploit MCP Server")
msf_client = MetasploitClient()

@mcp.tool
async def list_exploits(search_term: str = "") -> str:
    """List available Metasploit exploit modules.
    
    Args:
        search_term: Optional search term to filter exploits
        
    Returns:
        JSON string containing list of exploits
    """
    try:
        exploits = await msf_client.list_exploits(search_term)
        return json.dumps({
            "status": "success",
            "count": len(exploits),
            "exploits": exploits[:50]  # Limit to first 50 for readability
        }, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

@mcp.tool
async def list_payloads(platform: str = "", arch: str = "") -> str:
    """List available Metasploit payload modules.
    
    Args:
        platform: Filter by platform (e.g., windows, linux, etc.)
        arch: Filter by architecture (e.g., x86, x64, etc.)
        
    Returns:
        JSON string containing list of payloads
    """
    try:
        payloads = await msf_client.list_payloads(platform, arch)
        return json.dumps({
            "status": "success",
            "count": len(payloads),
            "payloads": payloads[:50]
        }, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

@mcp.tool
async def run_exploit(
    exploit_name: str,
    rhosts: str,
    payload: str = "",
    lhost: str = "",
    lport: int = 4444,
    additional_options: str = "",
    run_check: bool = True
) -> str:
    """Run a Metasploit exploit against a target.
    
    Args:
        exploit_name: Full exploit module name (e.g., exploit/windows/smb/ms17_010_eternalblue)
        rhosts: Target host(s) (comma-separated for multiple)
        payload: Payload to use (optional)
        lhost: Local host for reverse connections (optional)
        lport: Local port for reverse connections (default: 4444)
        additional_options: Additional options as JSON string (optional)
        run_check: Whether to run exploit check first (default: True)
        
    Returns:
        JSON string containing exploit execution result
    """
    try:
        # Parse additional options
        options = {"RHOSTS": rhosts}
        if payload:
            options["PAYLOAD"] = payload
        if lhost:
            options["LHOST"] = lhost
        if lport:
            options["LPORT"] = str(lport)
            
        if additional_options:
            try:
                extra_opts = json.loads(additional_options)
                options.update(extra_opts)
            except json.JSONDecodeError:
                return json.dumps({
                    "status": "error",
                    "message": "Invalid JSON in additional_options"
                })
        
        # Run exploit check if requested
        if run_check:
            check_result = await msf_client.call_rpc("module.check", {
                "module": exploit_name,
                "options": options
            })
            
            if "result" in check_result and check_result["result"].get("status") != "exploitable":
                return json.dumps({
                    "status": "check_failed",
                    "message": "Target is not vulnerable or check failed",
                    "check_result": check_result
                })
        
        # Execute exploit
        result = await msf_client.execute_exploit(exploit_name, options)
        
        return json.dumps({
            "status": "success",
            "exploit": exploit_name,
            "target": rhosts,
            "result": result
        }, indent=2)
        
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

@mcp.tool
async def generate_payload(
    payload_name: str,
    format_type: str,
    lhost: str = "",
    lport: int = 4444,
    additional_options: str = ""
) -> str:
    """Generate a Metasploit payload file.
    
    Args:
        payload_name: Full payload name (e.g., windows/meterpreter/reverse_tcp)
        format_type: Output format (e.g., exe, raw, python, etc.)
        lhost: Local host for reverse connections (optional)
        lport: Local port for reverse connections (default: 4444)
        additional_options: Additional options as JSON string (optional)
        
    Returns:
        JSON string containing payload generation result
    """
    try:
        options = {}
        if lhost:
            options["LHOST"] = lhost
        if lport:
            options["LPORT"] = str(lport)
            
        if additional_options:
            try:
                extra_opts = json.loads(additional_options)
                options.update(extra_opts)
            except json.JSONDecodeError:
                return json.dumps({
                    "status": "error",
                    "message": "Invalid JSON in additional_options"
                })
        
        result = await msf_client.generate_payload(payload_name, format_type, options)
        
        # Save payload to file if successful
        if "result" in result:
            save_dir = os.getenv("PAYLOAD_SAVE_DIR", "./payloads")
            os.makedirs(save_dir, exist_ok=True)
            
            filename = f"{payload_name.replace('/', '_')}.{format_type}"
            filepath = os.path.join(save_dir, filename)
            
            with open(filepath, "wb") as f:
                f.write(result["result"].get("data", b""))
            
            return json.dumps({
                "status": "success",
                "payload": payload_name,
                "format": format_type,
                "saved_to": filepath,
                "result": result
            }, indent=2)
        
        return json.dumps({
            "status": "error",
            "message": "Payload generation failed",
            "result": result
        })
        
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

@mcp.tool
async def list_sessions() -> str:
    """List active Metasploit sessions.
    
    Returns:
        JSON string containing list of active sessions
    """
    try:
        sessions = await msf_client.list_sessions()
        return json.dumps({
            "status": "success",
            "count": len(sessions),
            "sessions": sessions
        }, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

@mcp.tool
async def send_session_command(session_id: int, command: str) -> str:
    """Send a command to an active Metasploit session.
    
    Args:
        session_id: ID of the session to send command to
        command: Command to execute
        
    Returns:
        JSON string containing command execution result
    """
    try:
        result = await msf_client.session_command(session_id, command)
        return json.dumps({
            "status": "success",
            "session_id": session_id,
            "command": command,
            "result": result
        }, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

@mcp.tool
async def kill_session(session_id: int) -> str:
    """Kill an active Metasploit session.
    
    Args:
        session_id: ID of the session to kill
        
    Returns:
        JSON string containing session termination result
    """
    try:
        result = await msf_client.kill_session(session_id)
        return json.dumps({
            "status": "success",
            "session_id": session_id,
            "result": result
        }, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

@mcp.tool
async def get_module_info(module_name: str) -> str:
    """Get detailed information about a Metasploit module.
    
    Args:
        module_name: Full module name (exploit, payload, auxiliary, etc.)
        
    Returns:
        JSON string containing module information
    """
    try:
        result = await msf_client.call_rpc("module.info", {"module": module_name})
        return json.dumps({
            "status": "success",
            "module": module_name,
            "info": result
        }, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})
