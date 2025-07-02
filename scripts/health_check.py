#!/usr/bin/env python3
"""
Urbanclear System Health Check Script
Monitors all components and identifies issues automatically.
"""

import requests
import subprocess
import sys
import json
from datetime import datetime
import psutil
import time

class UrbanclearHealthChecker:
    """Comprehensive health checker for all system components"""
    
    def __init__(self):
        self.issues = []
        self.services = {
            'api': 'http://localhost:8000/health',
            'streamlit': 'http://localhost:8501',
            'grafana': 'http://localhost:3000',
            'prometheus': 'http://localhost:9090',
            'kafka_ui': 'http://localhost:8080'
        }
        
    def check_service(self, name, url, timeout=5):
        """Check if a service is responding"""
        try:
            response = requests.get(url, timeout=timeout)
            if response.status_code == 200:
                print(f"✅ {name}: Running")
                return True
            else:
                print(f"⚠️  {name}: Status {response.status_code}")
                self.issues.append(f"{name} returned status {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            print(f"❌ {name}: Not accessible")
            self.issues.append(f"{name} not accessible at {url}")
            return False
        except requests.exceptions.Timeout:
            print(f"⏳ {name}: Timeout")
            self.issues.append(f"{name} timed out")
            return False
        except Exception as e:
            print(f"❌ {name}: Error - {e}")
            self.issues.append(f"{name} error: {e}")
            return False
            
    def check_docker_services(self):
        """Check Docker container status"""
        try:
            result = subprocess.run(['docker', 'ps'], capture_output=True, text=True)
            if result.returncode == 0:
                containers = result.stdout.count('urbanclear_')
                print(f"✅ Docker: {containers} containers running")
                return True
            else:
                print("❌ Docker: Not running")
                self.issues.append("Docker services not running")
                return False
        except FileNotFoundError:
            print("❌ Docker: Not installed")
            self.issues.append("Docker not found")
            return False
            
    def check_python_processes(self):
        """Check Python processes for API and Streamlit"""
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['name'] == 'python' and proc.info['cmdline']:
                    cmdline = ' '.join(proc.info['cmdline'])
                    if 'uvicorn' in cmdline:
                        processes.append(f"API Server (PID: {proc.info['pid']})")
                    elif 'streamlit' in cmdline:
                        processes.append(f"Streamlit (PID: {proc.info['pid']})")
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
                
        if processes:
            print(f"✅ Python Processes: {', '.join(processes)}")
            return True
        else:
            print("⚠️  Python Processes: None found")
            self.issues.append("No API/Streamlit processes running")
            return False
            
    def check_virtual_env(self):
        """Check virtual environment status"""
        venv_path = sys.prefix
        if 'urbanclear-env' in venv_path:
            print(f"✅ Virtual Env: Active ({venv_path})")
            return True
        else:
            print("⚠️  Virtual Env: Not activated")
            self.issues.append("Virtual environment not activated")
            return False
            
    def check_api_endpoints(self):
        """Test key API endpoints"""
        endpoints = [
            '/health',
            '/api/v1/traffic/current',
            '/api/v1/demo/rush-hour-simulation'
        ]
        
        working_endpoints = 0
        for endpoint in endpoints:
            try:
                response = requests.get(f'http://localhost:8000{endpoint}', timeout=3)
                if response.status_code == 200:
                    working_endpoints += 1
                    print(f"  ✅ {endpoint}")
                else:
                    print(f"  ❌ {endpoint}: {response.status_code}")
                    self.issues.append(f"API endpoint {endpoint} not working")
            except Exception as e:
                print(f"  ❌ {endpoint}: {e}")
                self.issues.append(f"API endpoint {endpoint} error: {e}")
                
        print(f"📊 API Endpoints: {working_endpoints}/{len(endpoints)} working")
        return working_endpoints == len(endpoints)
        
    def generate_fixes(self):
        """Generate fix recommendations"""
        fixes = []
        
        if any('not accessible' in issue for issue in self.issues):
            fixes.append("🔧 Restart services: python run_api.py &")
            
        if any('Docker' in issue for issue in self.issues):
            fixes.append("🐳 Start Docker: make start")
            
        if any('Virtual environment' in issue for issue in self.issues):
            fixes.append("🐍 Activate venv: source urbanclear-env/bin/activate")
            
        if any('Streamlit' in issue for issue in self.issues):
            fixes.append("📊 Restart dashboard: streamlit run src/visualization/web_dashboard.py")
            
        return fixes
        
    def run_full_check(self):
        """Run comprehensive health check"""
        print("🔍 URBANCLEAR SYSTEM HEALTH CHECK")
        print("=" * 40)
        print(f"📅 Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Check virtual environment
        self.check_virtual_env()
        print()
        
        # Check Docker services
        self.check_docker_services()
        print()
        
        # Check Python processes
        self.check_python_processes()
        print()
        
        # Check web services
        print("🌐 WEB SERVICES:")
        for name, url in self.services.items():
            self.check_service(name, url)
        print()
        
        # Check API endpoints
        print("🔗 API ENDPOINTS:")
        self.check_api_endpoints()
        print()
        
        # Summary
        if self.issues:
            print("⚠️  ISSUES FOUND:")
            for i, issue in enumerate(self.issues, 1):
                print(f"  {i}. {issue}")
            print()
            
            print("🛠️  RECOMMENDED FIXES:")
            fixes = self.generate_fixes()
            for i, fix in enumerate(fixes, 1):
                print(f"  {i}. {fix}")
        else:
            print("🎉 ALL SYSTEMS OPERATIONAL!")
            
        print()
        print("=" * 40)
        
        return len(self.issues) == 0

def main():
    """Main entry point"""
    checker = UrbanclearHealthChecker()
    all_healthy = checker.run_full_check()
    
    sys.exit(0 if all_healthy else 1)

if __name__ == "__main__":
    main() 