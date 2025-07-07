#!/usr/bin/env python3
"""
Enhanced API Test Suite for Urbanclear Traffic System
Tests all endpoints with comprehensive validation and reporting
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any
import sys
from colorama import Fore, Style, init

# Initialize colorama for cross-platform colored output
init(autoreset=True)

class UrbanClearAPITester:
    """Comprehensive API tester for Urbanclear system"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.test_results = []
        self.failed_tests = []
        
    async def run_all_tests(self):
        """Run all API tests"""
        print(f"{Fore.CYAN}🚦 URBANCLEAR API COMPREHENSIVE TEST SUITE{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        print(f"Base URL: {self.base_url}")
        print(f"Test started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        async with aiohttp.ClientSession() as session:
            # Core API tests
            await self._test_health_endpoints(session)
            await self._test_traffic_endpoints(session)
            await self._test_prediction_endpoints(session)
            await self._test_route_endpoints(session)
            await self._test_incident_endpoints(session)
            await self._test_analytics_endpoints(session)
            await self._test_signal_endpoints(session)
            await self._test_admin_endpoints(session)
            
            # Demo endpoints tests
            await self._test_demo_endpoints(session)
            
            # WebSocket test (basic connectivity)
            await self._test_websocket_status(session)
        
        # Print summary
        self._print_test_summary()
    
    async def _make_request(self, session: aiohttp.ClientSession, method: str, 
                          endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request with error handling"""
        url = f"{self.base_url}{endpoint}"
        start_time = time.time()
        
        try:
            async with session.request(method, url, **kwargs) as response:
                response_time = time.time() - start_time
                content = await response.text()
                
                try:
                    data = json.loads(content) if content else {}
                except json.JSONDecodeError:
                    data = {"raw_content": content}
                
                return {
                    "status_code": response.status,
                    "data": data,
                    "response_time": response_time,
                    "url": url
                }
        except Exception as e:
            return {
                "status_code": 0,
                "data": {"error": str(e)},
                "response_time": time.time() - start_time,
                "url": url
            }
    
    async def _test_endpoint(self, session: aiohttp.ClientSession, name: str, 
                           method: str, endpoint: str, expected_status: int = 200,
                           **kwargs) -> bool:
        """Test a single endpoint"""
        result = await self._make_request(session, method, endpoint, **kwargs)
        
        success = result["status_code"] == expected_status
        status_color = Fore.GREEN if success else Fore.RED
        status_symbol = "✅" if success else "❌"
        
        print(f"  {status_symbol} {name:<40} {status_color}{result['status_code']}{Style.RESET_ALL} "
              f"({result['response_time']:.3f}s)")
        
        if not success:
            print(f"    {Fore.RED}Error: {result['data']}{Style.RESET_ALL}")
            self.failed_tests.append({
                "name": name,
                "endpoint": endpoint,
                "expected": expected_status,
                "actual": result["status_code"],
                "error": result["data"]
            })
        
        self.test_results.append({
            "name": name,
            "success": success,
            "response_time": result["response_time"],
            "status_code": result["status_code"],
            "data_size": len(str(result["data"]))
        })
        
        return success
    
    async def _test_health_endpoints(self, session: aiohttp.ClientSession):
        """Test health and system endpoints"""
        print(f"\n{Fore.YELLOW}🏥 HEALTH & SYSTEM ENDPOINTS{Style.RESET_ALL}")
        
        await self._test_endpoint(session, "Root endpoint", "GET", "/")
        await self._test_endpoint(session, "Health check", "GET", "/health")
        await self._test_endpoint(session, "Metrics endpoint", "GET", "/metrics")
        await self._test_endpoint(session, "API documentation", "GET", "/api/docs")
    
    async def _test_traffic_endpoints(self, session: aiohttp.ClientSession):
        """Test traffic data endpoints"""
        print(f"\n{Fore.YELLOW}🚗 TRAFFIC DATA ENDPOINTS{Style.RESET_ALL}")
        
        await self._test_endpoint(session, "Current traffic", "GET", "/api/v1/traffic/current")
        await self._test_endpoint(session, "Traffic with location filter", "GET", 
                                "/api/v1/traffic/current?location=Central Park")
        await self._test_endpoint(session, "Traffic with radius", "GET", 
                                "/api/v1/traffic/current?radius=5.0")
        await self._test_endpoint(session, "Traffic predictions", "GET", 
                                "/api/v1/traffic/predict?location=Times Square")
        await self._test_endpoint(session, "Extended predictions", "GET", 
                                "/api/v1/traffic/predict?location=Brooklyn Bridge&hours_ahead=6")
        
        # Historical data test
        start_date = (datetime.now() - timedelta(days=1)).isoformat()
        end_date = datetime.now().isoformat()
        await self._test_endpoint(session, "Historical traffic", "GET", 
                                f"/api/v1/traffic/historical?location=Manhattan&start_date={start_date}&end_date={end_date}")
    
    async def _test_prediction_endpoints(self, session: aiohttp.ClientSession):
        """Test prediction endpoints"""
        print(f"\n{Fore.YELLOW}🔮 PREDICTION ENDPOINTS{Style.RESET_ALL}")
        
        await self._test_endpoint(session, "Traffic prediction default", "GET", 
                                "/api/v1/traffic/predict?location=Central Park")
        await self._test_endpoint(session, "Multi-hour prediction", "GET", 
                                "/api/v1/traffic/predict?location=Times Square&hours_ahead=12")
    
    async def _test_route_endpoints(self, session: aiohttp.ClientSession):
        """Test route optimization endpoints"""
        print(f"\n{Fore.YELLOW}🛣️  ROUTE OPTIMIZATION ENDPOINTS{Style.RESET_ALL}")
        
        # Route optimization POST request
        route_data = {
            "origin": {
                "latitude": 40.7831,
                "longitude": -73.9712,
                "address": "Central Park"
            },
            "destination": {
                "latitude": 40.7505,
                "longitude": -73.9934,
                "address": "Times Square"
            },
            "departure_time": datetime.now().isoformat(),
            "preferences": {
                "avoid_tolls": False,
                "avoid_highways": False,
                "optimize_for": "time"
            }
        }
        
        await self._test_endpoint(session, "Route optimization", "POST", 
                                "/api/v1/routes/optimize",
                                json=route_data)
        
        await self._test_endpoint(session, "Route alternatives", "GET", 
                                "/api/v1/routes/alternatives?origin=JFK Airport&destination=Manhattan&max_alternatives=3")
    
    async def _test_incident_endpoints(self, session: aiohttp.ClientSession):
        """Test incident management endpoints"""
        print(f"\n{Fore.YELLOW}🚨 INCIDENT MANAGEMENT ENDPOINTS{Style.RESET_ALL}")
        
        await self._test_endpoint(session, "Active incidents", "GET", "/api/v1/incidents/active")
        await self._test_endpoint(session, "Incidents by location", "GET", 
                                "/api/v1/incidents/active?location=Brooklyn")
        await self._test_endpoint(session, "Incidents by severity", "GET", 
                                "/api/v1/incidents/active?severity=high")
        
        # Test incident reporting
        incident_data = {
            "type": "accident",
            "location": {
                "latitude": 40.7589,
                "longitude": -73.9851,
                "address": "West Side Highway"
            },
            "severity": "moderate",
            "description": "Test incident report",
            "lanes_affected": 1
        }
        
        await self._test_endpoint(session, "Report incident", "POST", 
                                "/api/v1/incidents/report",
                                json=incident_data)
    
    async def _test_analytics_endpoints(self, session: aiohttp.ClientSession):
        """Test analytics endpoints"""
        print(f"\n{Fore.YELLOW}📊 ANALYTICS ENDPOINTS{Style.RESET_ALL}")
        
        periods = ["1h", "24h", "7d", "30d"]
        for period in periods:
            await self._test_endpoint(session, f"Analytics summary ({period})", "GET", 
                                    f"/api/v1/analytics/summary?period={period}")
        
        metrics = ["congestion", "throughput", "emissions", "efficiency"]
        for metric in metrics:
            await self._test_endpoint(session, f"Performance metrics ({metric})", "GET", 
                                    f"/api/v1/analytics/performance?metric_type={metric}")
    
    async def _test_signal_endpoints(self, session: aiohttp.ClientSession):
        """Test signal optimization endpoints"""
        print(f"\n{Fore.YELLOW}🚦 SIGNAL OPTIMIZATION ENDPOINTS{Style.RESET_ALL}")
        
        await self._test_endpoint(session, "Signal status", "GET", "/api/v1/signals/status")
        await self._test_endpoint(session, "Specific signal status", "GET", 
                                "/api/v1/signals/status?intersection_id=INT001")
        
        # Signal optimization request
        signal_data = {
            "intersection_id": "INT001",
            "optimization_period": 60,
            "consider_pedestrians": True
        }
        
        await self._test_endpoint(session, "Signal optimization", "POST", 
                                "/api/v1/signals/optimize",
                                json=signal_data)
    
    async def _test_admin_endpoints(self, session: aiohttp.ClientSession):
        """Test admin endpoints"""
        print(f"\n{Fore.YELLOW}⚙️  ADMIN ENDPOINTS{Style.RESET_ALL}")
        
        await self._test_endpoint(session, "System stats", "GET", "/api/v1/admin/system/stats")
        
        # Model retraining (commented out to avoid triggering actual retraining)
        # await self._test_endpoint(session, "Retrain model", "POST", 
        #                         "/api/v1/admin/models/retrain?model_type=traffic_prediction")
    
    async def _test_demo_endpoints(self, session: aiohttp.ClientSession):
        """Test demonstration endpoints"""
        print(f"\n{Fore.YELLOW}🎯 DEMO ENDPOINTS{Style.RESET_ALL}")
        
        await self._test_endpoint(session, "Rush hour simulation", "GET", 
                                "/api/v1/demo/rush-hour-simulation")
        await self._test_endpoint(session, "Real-time dashboard", "GET", 
                                "/api/v1/demo/real-time-dashboard")
        await self._test_endpoint(session, "ML showcase", "GET", 
                                "/api/v1/demo/ml-showcase")
        await self._test_endpoint(session, "Performance metrics demo", "GET", 
                                "/api/v1/demo/performance-metrics")
        await self._test_endpoint(session, "Geographic heatmap", "GET", 
                                "/api/v1/demo/geographic-heatmap")
        await self._test_endpoint(session, "Incident timeline", "GET", 
                                "/api/v1/demo/incident-timeline")
    
    async def _test_websocket_status(self, session: aiohttp.ClientSession):
        """Test WebSocket status endpoint"""
        print(f"\n{Fore.YELLOW}🔌 WEBSOCKET ENDPOINTS{Style.RESET_ALL}")
        
        await self._test_endpoint(session, "WebSocket status", "GET", 
                                "/api/v1/websocket/status")
    
    def _print_test_summary(self):
        """Print comprehensive test summary"""
        print(f"\n{Fore.CYAN}📋 TEST SUMMARY{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        avg_response_time = sum(result["response_time"] for result in self.test_results) / total_tests if total_tests > 0 else 0
        
        print(f"Total tests: {total_tests}")
        print(f"{Fore.GREEN}Passed: {passed_tests}{Style.RESET_ALL}")
        if failed_tests > 0:
            print(f"{Fore.RED}Failed: {failed_tests}{Style.RESET_ALL}")
        print(f"Success rate: {success_rate:.1f}%")
        print(f"Average response time: {avg_response_time:.3f}s")
        
        if self.failed_tests:
            print(f"\n{Fore.RED}❌ FAILED TESTS:{Style.RESET_ALL}")
            for test in self.failed_tests:
                print(f"  • {test['name']}: Expected {test['expected']}, got {test['actual']}")
                if "error" in test and test["error"]:
                    print(f"    Error: {test['error']}")
        
        # Performance analysis
        print(f"\n{Fore.CYAN}⚡ PERFORMANCE ANALYSIS{Style.RESET_ALL}")
        slow_tests = [result for result in self.test_results if result["response_time"] > 1.0]
        if slow_tests:
            print(f"{Fore.YELLOW}Slow endpoints (>1s):{Style.RESET_ALL}")
            for test in sorted(slow_tests, key=lambda x: x["response_time"], reverse=True):
                print(f"  • {test['name']}: {test['response_time']:.3f}s")
        else:
            print(f"{Fore.GREEN}All endpoints respond quickly (<1s){Style.RESET_ALL}")
        
        # Overall status
        if success_rate >= 95:
            print(f"\n{Fore.GREEN}🎉 EXCELLENT: API is working perfectly!{Style.RESET_ALL}")
        elif success_rate >= 80:
            print(f"\n{Fore.YELLOW}⚠️  GOOD: API is mostly functional with minor issues{Style.RESET_ALL}")
        else:
            print(f"\n{Fore.RED}🚨 ISSUES: API has significant problems that need attention{Style.RESET_ALL}")
        
        print(f"\nTest completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


async def main():
    """Main test function"""
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = "http://localhost:8000"
    
    tester = UrbanClearAPITester(base_url)
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main()) 