import os
import json
import requests
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class MetasploitClient:
    """Client for interacting with Metasploit RPC API"""
    
    def __init__(self):
        self.rpc_url = os.getenv("MSF_RPC_URL", "http://127.0.0.1:55553")
        self.rpc_password = os.getenv("MSF_RPC_PASSWORD", "")
        self.rpc_ssl = os.getenv("MSF_RPC_SSL", "false").lower() == "true"
        self.token = None
        self.session = requests.Session()
        
        if self.rpc_ssl:
            self.session.verify = False
            
    async def connect(self) -> bool:
        """Connect to Metasploit RPC server"""
        try:
            auth_data = {
                "jsonrpc": "2.0",
                "method": "login",
                "params": {
                    "password": self.rpc_password
                },
                "id": 1
            }
            
            response = self.session.post(
                f"{self.rpc_url}/api",
                json=auth_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                if "result" in result and "token" in result["result"]:
                    self.token = result["result"]["token"]
                    return True
                    
        except Exception as e:
            print(f"Connection error: {e}")
            
        return False
    
    async def call_rpc(self, method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make RPC call to Metasploit"""
        if not self.token:
            await self.connect()
            
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {},
            "id": 1
        }
        
        if self.token:
            payload["token"] = self.token
            
        try:
            response = self.session.post(
                f"{self.rpc_url}/api",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            return {"error": str(e)}
    
    async def list_exploits(self, search_term: str = "") -> List[Dict[str, Any]]:
        """List available exploits"""
        result = await self.call_rpc("module.exploits")
        if "result" in result:
            exploits = result["result"]
            if search_term:
                exploits = [e for e in exploits if search_term.lower() in e.lower()]
            return exploits
        return []
    
    async def list_payloads(self, platform: str = "", arch: str = "") -> List[Dict[str, Any]]:
        """List available payloads"""
        result = await self.call_rpc("module.payloads")
        if "result" in result:
            payloads = result["result"]
            if platform:
                payloads = [p for p in payloads if platform.lower() in p.lower()]
            if arch:
                payloads = [p for p in payloads if arch.lower() in p.lower()]
            return payloads
        return []
    
    async def execute_exploit(self, exploit_name: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an exploit"""
        params = {
            "module": exploit_name,
            "options": options
        }
        return await self.call_rpc("module.execute", params)
    
    async def generate_payload(self, payload_name: str, format_type: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a payload"""
        params = {
            "module": payload_name,
            "options": options,
            "datastore": {"Format": format_type}
        }
        return await self.call_rpc("module.execute", params)
    
    async def list_sessions(self) -> List[Dict[str, Any]]:
        """List active sessions"""
        result = await self.call_rpc("session.list")
        if "result" in result:
            return [{"id": k, **v} for k, v in result["result"].items()]
        return []
    
    async def session_command(self, session_id: int, command: str) -> Dict[str, Any]:
        """Send command to session"""
        params = {
            "id": session_id,
            "command": command
        }
        return await self.call_rpc("session.shell_write", params)
    
    async def kill_session(self, session_id: int) -> Dict[str, Any]:
        """Kill a session"""
        params = {"id": session_id}
        return await self.call_rpc("session.stop", params)
