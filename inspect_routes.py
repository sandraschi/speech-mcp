from speech_mcp.server import app

for route in app.routes:
    print(f"{route.path} - {route.name}")
