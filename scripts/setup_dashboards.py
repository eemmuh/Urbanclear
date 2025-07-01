#!/usr/bin/env python3
"""
Urbanclear Dashboard Setup Script

This script helps set up and verify the Grafana dashboard system.
"""

import requests
import time
import json
import sys
from pathlib import Path

def check_service_health(service_name, url, timeout=30):
    """Check if a service is healthy"""
    print(f"Checking {service_name}...")
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ {service_name} is healthy")
                return True
        except requests.exceptions.RequestException:
            pass
        
        print(f"⏳ Waiting for {service_name}...")
        time.sleep(5)
    
    print(f"❌ {service_name} is not responding after {timeout}s")
    return False

def check_prometheus_targets():
    """Check Prometheus targets"""
    try:
        response = requests.get("http://localhost:9090/api/v1/targets")
        if response.status_code == 200:
            targets = response.json()
            active_targets = [t for t in targets['data']['activeTargets'] if t['health'] == 'up']
            print(f"✅ Prometheus has {len(active_targets)} active targets")
            
            for target in active_targets:
                job = target['labels']['job']
                instance = target['labels']['instance']
                print(f"   - {job} ({instance})")
            
            return len(active_targets) > 0
        else:
            print("❌ Failed to fetch Prometheus targets")
            return False
    except Exception as e:
        print(f"❌ Error checking Prometheus targets: {e}")
        return False

def verify_grafana_datasource():
    """Verify Grafana datasource configuration"""
    try:
        # Grafana API endpoint
        auth = ('admin', 'grafana_password')
        response = requests.get("http://localhost:3000/api/datasources", auth=auth)
        
        if response.status_code == 200:
            datasources = response.json()
            prometheus_ds = [ds for ds in datasources if ds['type'] == 'prometheus']
            
            if prometheus_ds:
                print("✅ Prometheus datasource configured in Grafana")
                return True
            else:
                print("❌ No Prometheus datasource found in Grafana")
                return False
        else:
            print(f"❌ Failed to check Grafana datasources: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error checking Grafana datasource: {e}")
        return False

def check_dashboard_files():
    """Check if dashboard files exist"""
    dashboard_dir = Path("docker/grafana/dashboards")
    
    expected_dashboards = [
        "overview-dashboard.json",
        "traffic-flow-dashboard.json", 
        "incident-management-dashboard.json",
        "system-performance-dashboard.json",
        "geographic-traffic-map.json",
        "predictive-analytics-dashboard.json"
    ]
    
    print("Checking dashboard files...")
    all_exist = True
    
    for dashboard in expected_dashboards:
        file_path = dashboard_dir / dashboard
        if file_path.exists():
            print(f"✅ {dashboard}")
        else:
            print(f"❌ {dashboard} - File not found")
            all_exist = False
    
    return all_exist

def check_metrics_endpoint():
    """Check if API metrics endpoint is working"""
    try:
        response = requests.get("http://localhost:8000/metrics")
        if response.status_code == 200:
            metrics_count = len([line for line in response.text.split('\n') if line and not line.startswith('#')])
            print(f"✅ API metrics endpoint active with {metrics_count} metrics")
            return True
        else:
            print(f"❌ API metrics endpoint returned {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error checking API metrics: {e}")
        return False

def display_dashboard_info():
    """Display dashboard access information"""
    print("\n🎯 Dashboard Access Information")
    print("=" * 50)
    print("Grafana Dashboards: http://localhost:3000")
    print("Username: admin")
    print("Password: grafana_password")
    print()
    print("Available Dashboards:")
    print("1. System Overview - Main dashboard with key metrics")
    print("2. Traffic Flow - Real-time traffic monitoring")
    print("3. Incident Management - Incident tracking and response")
    print("4. System Performance - Infrastructure monitoring")
    print("5. Geographic Map - Interactive traffic maps")
    print("6. Predictive Analytics - ML model performance")
    print()
    print("Prometheus: http://localhost:9090")
    print("API Metrics: http://localhost:8000/metrics")

def main():
    """Main setup function"""
    print("🚀 Urbanclear Dashboard Setup")
    print("=" * 40)
    
    # Check dashboard files
    if not check_dashboard_files():
        print("\n❌ Some dashboard files are missing!")
        sys.exit(1)
    
    print("\n📊 Checking Services...")
    
    # Check core services
    services_healthy = True
    
    services = [
        ("Grafana", "http://localhost:3000/api/health"),
        ("Prometheus", "http://localhost:9090/-/healthy"),
        ("API", "http://localhost:8000/health"),
    ]
    
    for name, url in services:
        if not check_service_health(name, url):
            services_healthy = False
    
    if not services_healthy:
        print("\n❌ Some services are not healthy!")
        print("Please ensure all services are running with: make start")
        sys.exit(1)
    
    # Check Prometheus targets
    print("\n🎯 Checking Prometheus Configuration...")
    if not check_prometheus_targets():
        print("⚠️  Warning: Some Prometheus targets may not be configured correctly")
    
    # Check metrics endpoint
    print("\n📈 Checking Metrics...")
    if not check_metrics_endpoint():
        print("⚠️  Warning: API metrics endpoint is not working")
    
    # Check Grafana datasource
    print("\n🔗 Checking Grafana Configuration...")
    if not verify_grafana_datasource():
        print("⚠️  Warning: Grafana datasource may not be configured correctly")
    
    print("\n✅ Dashboard setup verification complete!")
    display_dashboard_info()

if __name__ == "__main__":
    main() 