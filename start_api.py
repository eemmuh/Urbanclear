#!/usr/bin/env python3
"""
Simple startup script for the Urbanclear API
This script properly sets up the Python path and starts the server
"""

import os
import sys
import uvicorn

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Set environment variables
os.environ.setdefault("PYTHONPATH", project_root)

if __name__ == "__main__":
    # Import the app after setting up the path
    from src.api.main import app
    
    # Get host from environment variable (secure default)
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", 8000))
    
    print(f"🚀 Starting Urbanclear API on {host}:{port}")
    print(f"📚 API Documentation: http://{host}:{port}/api/docs")
    print(f"❤️ Health Check: http://{host}:{port}/health")
    print(f"📊 Metrics: http://{host}:{port}/metrics")
    print("\n🛑 Press Ctrl+C to stop the server\n")
    
    # Start the server without reload to avoid Prometheus conflicts
    uvicorn.run(
        app,
        host=host,
        port=port,
        reload=False,  # Disable reload to avoid metrics collision
        log_level="info"
    ) 