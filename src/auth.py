import os
from starlette.responses import JSONResponse
from starlette.types import Receive, Scope, Send

def load_env_from_file(file_path: str = ".env") -> None:
    try:
        with open(file_path, "r") as env_file:
            for raw_line in env_file:
                line = raw_line.strip()
                if not line or line.startswith("#"):
                    continue
                if line.lower().startswith("export "):
                    line = line[7:].lstrip()
                if "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                # Do not override existing environment variables
                if key and key not in os.environ:
                    os.environ[key] = value
    except FileNotFoundError:
        # Silently ignore if .env is not present
        pass


def require_bearer_token(app, header_name: str, expected_token: str):
    async def auth_app(scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            return await app(scope, receive, send)
        
        # Only protect the MCP endpoint
        path = scope.get("path", "")
        if not path.startswith("/mcp"):
            return await app(scope, receive, send)
        
        if not expected_token:
            response = JSONResponse({
                "detail": "Server misconfigured: API_AUTH_TOKEN not set"
            }, status_code=500,)
            
            return await response(scope, receive, send)
        
        header_value = None
        for k, v in scope.get("headers", []):
            if k.decode().lower() == header_name.lower():
                header_value = v.decode()
                break
            
        if not header_value or not header_value.lower().startswith("bearer "):
            response = JSONResponse({
                "detail": "Missing bearer token"
            }, status_code=401, headers={"WWW-Authenticate": "Bearer"})
            
            return await response(scope, receive, send)
        
        token = header_value.split(" ", 1)[1]
        if token != expected_token:
            response = JSONResponse({
                "detail": "Invalid token"
            }, status_code=401, headers={"WWW-Authenticate": "Bearer"})
            
            return await response(scope, receive, send)
        
        return await app(scope, receive, send)
    
    return auth_app