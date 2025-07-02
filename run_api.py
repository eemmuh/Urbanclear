#!/usr/bin/env python3
"""
Quick API runner for Urbanclear
"""
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

# Change to src directory
os.chdir(Path(__file__).parent / 'src')

if __name__ == "__main__":
    import uvicorn
    from api.main import app
    
    print("🚀 Starting Urbanclear API on http://localhost:8000")
    print("📖 API docs: http://localhost:8000/docs")
    
    uvicorn.run(
        "api.main:app", 
        host='0.0.0.0', 
        port=8000,
        reload=True
    ) 