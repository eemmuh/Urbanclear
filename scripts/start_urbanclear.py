#!/usr/bin/env python3
"""
Urbanclear System Startup Script
Comprehensive initialization and startup of all system components.
"""

import asyncio
import sys
import os
import time
import subprocess
import threading
from pathlib import Path
from datetime import datetime
import logging

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from data.metrics_publisher import start_metrics_server
from models.ml_trainer import ModelTrainer
from visualization.web_dashboard import run_dashboard

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class UrbanclearSystem:
    """Main system orchestrator"""
    
    def __init__(self):
        self.processes = {}
        self.metrics_server = None
        
    def check_dependencies(self):
        """Check that all required services are running"""
        logger.info("🔍 Checking system dependencies...")
        
        # Check Docker services
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
        
    def train_ml_models(self):
        """Train all ML models"""
        logger.info("🤖 Training ML models...")
        
        try:
            trainer = ModelTrainer()
            results = trainer.train_all_models(samples=5000)
            
            for model_type, result in results.items():
                if 'error' in result:
                    logger.error(f"❌ {model_type}: {result['error']}")
                else:
                    logger.info(f"✅ {model_type}: Trained successfully")
                    
            logger.info("🎯 ML models training completed!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error training models: {e}")
            return False
            
    def start_metrics_server(self):
        """Start the metrics publisher"""
        logger.info("📊 Starting metrics server...")
        
        try:
            self.metrics_server = start_metrics_server(port=8001)
            logger.info("✅ Metrics server started on port 8001")
            return True
        except Exception as e:
            logger.error(f"❌ Error starting metrics server: {e}")
            return False
            
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
            
    def start_web_dashboard(self):
        """Start the Streamlit web dashboard"""
        logger.info("🌐 Starting web dashboard...")
        
        try:
            # Change back to project root
            os.chdir(Path(__file__).parent.parent)
            
            dashboard_process = subprocess.Popen([
                'streamlit', 'run',
                'src/visualization/web_dashboard.py',
                '--server.port', '8501',
                '--server.address', '0.0.0.0'
            ])
            
            self.processes['dashboard'] = dashboard_process
            logger.info("✅ Web dashboard started on port 8501")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error starting web dashboard: {e}")
            return False
            
    def display_system_info(self):
        """Display system access information"""
        logger.info("\n" + "="*60)
        logger.info("🚦 URBANCLEAR TRAFFIC SYSTEM - READY!")
        logger.info("="*60)
        logger.info("📱 Web Dashboard:     http://localhost:8501")
        logger.info("🔧 API Documentation: http://localhost:8000/docs")
        logger.info("📊 Prometheus:        http://localhost:9090")
        logger.info("📈 Grafana:           http://localhost:3000")
        logger.info("📊 Metrics:           http://localhost:8001/metrics")
        logger.info("🗄️  Kafka UI:          http://localhost:8080")
        logger.info("="*60)
        logger.info("💡 Press Ctrl+C to stop all services")
        logger.info("="*60 + "\n")
        
    def test_api_endpoints(self):
        """Test key API endpoints"""
        logger.info("🧪 Testing API endpoints...")
        
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
                
    def run_system(self):
        """Run the complete Urbanclear system"""
        logger.info("🚀 Starting Urbanclear Traffic System...")
        
        # Check dependencies
        if not self.check_dependencies():
            logger.error("❌ System dependencies not met. Exiting.")
            return False
            
        # Train ML models
        if not self.train_ml_models():
            logger.warning("⚠️  ML models training failed, continuing with existing models...")
            
        # Start metrics server
        if not self.start_metrics_server():
            logger.warning("⚠️  Metrics server failed to start, continuing...")
            
        # Start API server
        if not self.start_api_server():
            logger.error("❌ API server failed to start. Exiting.")
            return False
            
        # Test API endpoints
        self.test_api_endpoints()
        
        # Start web dashboard
        if not self.start_web_dashboard():
            logger.warning("⚠️  Web dashboard failed to start, continuing...")
            
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
                
        # Stop metrics server
        if self.metrics_server:
            try:
                self.metrics_server.stop()
                logger.info("✅ Stopped metrics server")
            except Exception as e:
                logger.error(f"❌ Error stopping metrics server: {e}")
                
        logger.info("🎯 System shutdown complete")

def main():
    """Main entry point"""
    system = UrbanclearSystem()
    
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