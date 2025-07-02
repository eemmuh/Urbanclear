#!/usr/bin/env python3
"""
Simplified Urbanclear System Startup Script
Focuses on core API and dashboard functionality.
"""

import sys
import os
import time
import subprocess
import threading
from pathlib import Path
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class SimpleUrbanclearSystem:
    """Simplified system orchestrator"""
    
    def __init__(self):
        self.processes = {}
        
    def check_dependencies(self):
        """Check that Docker services are running"""
        logger.info("🔍 Checking Docker services...")
        
        services_to_check = [
            'urbanclear_postgres',
            'urbanclear_redis', 
            'urbanclear_prometheus',
            'urbanclear_grafana'
        ]
        
        for service in services_to_check:
            result = subprocess.run(
                ['docker', 'ps', '--filter', f'name={service}', '--format', '{{.Names}}'],
                capture_output=True, text=True
            )
            
            if service not in result.stdout:
                logger.error(f"❌ Service {service} is not running")
                logger.info("💡 Run 'make start' to start Docker services")
                return False
            else:
                logger.info(f"✅ {service} is running")
                
        return True
        
    def start_api_server(self):
        """Start the FastAPI server"""
        logger.info("🚀 Starting API server...")
        
        try:
            # Change to src directory for proper imports
            os.chdir(Path(__file__).parent.parent / 'src')
            
            # Start API server in background
            api_process = subprocess.Popen([
                sys.executable, '-m', 'uvicorn',
                'api.main:app',
                '--host', '0.0.0.0',
                '--port', '8000',
                '--reload'
            ])
            
            self.processes['api'] = api_process
            
            # Wait a moment and check if it started
            time.sleep(3)
            
            if api_process.poll() is None:
                logger.info("✅ API server started successfully on port 8000")
                return True
            else:
                logger.error("❌ API server failed to start")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error starting API server: {e}")
            return False
            
    def test_api_endpoints(self):
        """Test key API endpoints"""
        logger.info("🧪 Testing API endpoints...")
        
        try:
            import requests
            
            endpoints_to_test = [
                '/health',
                '/api/v1/traffic/current',
                '/api/v1/analytics/summary',
                '/api/v1/demo/rush-hour-simulation'
            ]
            
            for endpoint in endpoints_to_test:
                try:
                    response = requests.get(f'http://localhost:8000{endpoint}', timeout=5)
                    if response.status_code == 200:
                        logger.info(f"✅ {endpoint}: OK")
                    else:
                        logger.warning(f"⚠️  {endpoint}: Status {response.status_code}")
                except Exception as e:
                    logger.warning(f"⚠️  {endpoint}: {e}")
                    
        except ImportError:
            logger.warning("⚠️  requests not available for testing")
            
    def display_system_info(self):
        """Display system access information"""
        logger.info("\n" + "="*60)
        logger.info("🚦 URBANCLEAR TRAFFIC SYSTEM - READY!")
        logger.info("="*60)
        logger.info("🔧 API Documentation: http://localhost:8000/docs")
        logger.info("💡 API Health Check:  http://localhost:8000/health")
        logger.info("📊 Prometheus:        http://localhost:9090")
        logger.info("📈 Grafana:           http://localhost:3000")
        logger.info("🗄️  Kafka UI:          http://localhost:8080")
        logger.info("="*60)
        logger.info("💡 Test the API with:")
        logger.info("   curl http://localhost:8000/api/v1/traffic/current")
        logger.info("   curl http://localhost:8000/api/v1/demo/rush-hour-simulation")
        logger.info("="*60)
        logger.info("💡 Press Ctrl+C to stop all services")
        logger.info("="*60 + "\n")
        
    def run_system(self):
        """Run the simplified Urbanclear system"""
        logger.info("🚀 Starting Simplified Urbanclear System...")
        
        # Check dependencies
        if not self.check_dependencies():
            logger.error("❌ System dependencies not met. Exiting.")
            return False
            
        # Start API server
        if not self.start_api_server():
            logger.error("❌ API server failed to start. Exiting.")
            return False
            
        # Test API endpoints
        self.test_api_endpoints()
        
        # Display system info
        self.display_system_info()
        
        return True
        
    def stop_system(self):
        """Stop all system processes"""
        logger.info("🛑 Stopping Urbanclear system...")
        
        # Stop processes
        for name, process in self.processes.items():
            try:
                process.terminate()
                logger.info(f"✅ Stopped {name}")
            except Exception as e:
                logger.error(f"❌ Error stopping {name}: {e}")
                
        logger.info("🎯 System shutdown complete")

def main():
    """Main entry point"""
    system = SimpleUrbanclearSystem()
    
    try:
        if system.run_system():
            # Keep running until interrupted
            while True:
                time.sleep(1)
        else:
            logger.error("❌ System failed to start completely")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("\n🛑 Received shutdown signal...")
        system.stop_system()
        
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        system.stop_system()
        sys.exit(1)

if __name__ == "__main__":
    main() 