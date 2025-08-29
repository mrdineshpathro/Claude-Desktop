#!/usr/bin/env python3
"""
Metasploit MCP Server
A Model Context Protocol server for Metasploit Framework integration
"""

import os
import sys
import argparse
from src.metasploit_mcp import mcp

def main():
    parser = argparse.ArgumentParser(description="Metasploit MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "http", "sse"],
        default="stdio",
        help="Transport protocol to use"
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind to (HTTP/SSE only)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Port to bind to (HTTP/SSE only)"
    )
    
    args = parser.parse_args()
    
    # Check if Metasploit RPC credentials are set
    if not os.getenv("MSF_RPC_PASSWORD"):
        print("Error: MSF_RPC_PASSWORD environment variable not set", file=sys.stderr)
        sys.exit(1)
    
    print(f"Starting Metasploit MCP Server with {args.transport} transport")
    
    if args.transport == "stdio":
        mcp.run()
    elif args.transport == "http":
        mcp.run(transport="http", host=args.host, port=args.port)
    elif args.transport == "sse":
        mcp.run(transport="sse", host=args.host, port=args.port)

if __name__ == "__main__":
    main()
