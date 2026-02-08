@echo off
echo [Foundry] Launching Microservices on Local Ports...

:: Activate Env
call mcp-servers\.venv\Scripts\activate

:: Start Master Gateway (8001)
start "Foundry: Master" python -m mcp.server.fastmcp run mcp-servers\master-gateway\server.py --port 8001 --transport sse

:: Start Continuity (8002)
start "Foundry: Continuity" python -m mcp.server.fastmcp run mcp-servers\continuity-archivist\server.py --port 8002 --transport sse

:: Start Syntax (8003)
start "Foundry: Syntax" python -m mcp.server.fastmcp run mcp-servers\syntax-architect\server.py --port 8003 --transport sse

:: Start Logic (8004)
start "Foundry: Logic" python -m mcp.server.fastmcp run mcp-servers\logic-validator\server.py --port 8004 --transport sse

:: Start Lexical (8005)
start "Foundry: Lexical" python -m mcp.server.fastmcp run mcp-servers\lexical-curator\server.py --port 8005 --transport sse

echo Services Launched.
echo Run 'orchestrator\run.bat' to execute the compiler.
pause
