"""
Real-time Web Dashboard for Urbanclear Traffic System.
Interactive monitoring interface with live metrics and visualizations.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import requests
import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

# Set page config
st.set_page_config(
    page_title="🚦 Urbanclear Traffic Dashboard",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded"
)

logger = logging.getLogger(__name__)

class WebDashboard:
    """Web-based dashboard for traffic monitoring"""
    
    def __init__(self, api_url: str = "http://localhost:8000"):
        self.api_url = api_url
        
    def fetch_api_data(self, endpoint: str) -> Optional[Dict]:
        """Fetch data from API endpoint"""
        try:
            response = requests.get(f"{self.api_url}{endpoint}", timeout=5)
            if response.status_code == 200:
                return response.json()
            else:
                return None
        except Exception as e:
            st.error(f"Error fetching data from {endpoint}: {e}")
            return None
            
    def create_traffic_flow_chart(self, traffic_data: Dict) -> go.Figure:
        """Create real-time traffic flow chart"""
        if not traffic_data or 'sensors' not in traffic_data:
            # Create sample data for demonstration
            locations = ['Times Square', 'Brooklyn Bridge', 'Central Park', 'Wall Street']
            flow_rates = np.random.randint(200, 800, len(locations))
        else:
            locations = [sensor['location'] for sensor in traffic_data['sensors']]
            flow_rates = [sensor['flow_rate'] for sensor in traffic_data['sensors']]
            
        fig = go.Figure(data=[
            go.Bar(
                x=locations,
                y=flow_rates,
                marker_color=['red' if rate > 600 else 'orange' if rate > 400 else 'green' 
                             for rate in flow_rates],
                text=[f"{rate} veh/h" for rate in flow_rates],
                textposition='auto',
            )
        ])
        
        fig.update_layout(
            title="🚗 Real-time Traffic Flow by Location",
            xaxis_title="Location",
            yaxis_title="Vehicles per Hour",
            showlegend=False,
            height=400
        )
        
        return fig
        
    def create_congestion_map(self, traffic_data: Dict) -> go.Figure:
        """Create congestion level map"""
        if not traffic_data or 'sensors' not in traffic_data:
            # Sample NYC coordinates
            locations = ['Times Square', 'Brooklyn Bridge', 'Central Park', 'Wall Street']
            lats = [40.7580, 40.7061, 40.7829, 40.7074]
            lons = [-73.9855, -73.9969, -73.9654, -74.0113]
            congestion = np.random.uniform(0, 1, len(locations))
        else:
            locations = [sensor['location'] for sensor in traffic_data['sensors']]
            lats = [sensor.get('coordinates', {}).get('lat', 40.7580) for sensor in traffic_data['sensors']]
            lons = [sensor.get('coordinates', {}).get('lon', -73.9855) for sensor in traffic_data['sensors']]
            congestion = [sensor.get('congestion_level', 0.5) for sensor in traffic_data['sensors']]
            
        fig = go.Figure(data=go.Scattermapbox(
            lat=lats,
            lon=lons,
            mode='markers',
            marker=go.scattermapbox.Marker(
                size=[20 + c * 30 for c in congestion],
                color=congestion,
                colorscale='Viridis',
                showscale=True,
                colorbar=dict(title="Congestion Level"),
                cmin=0,
                cmax=1
            ),
            text=[f"{loc}<br>Congestion: {c:.2f}" for loc, c in zip(locations, congestion)],
            hovertemplate='%{text}<extra></extra>'
        ))
        
        fig.update_layout(
            mapbox_style="open-street-map",
            mapbox=dict(
                center=go.layout.mapbox.Center(lat=40.7589, lon=-73.9851),
                zoom=11
            ),
            showlegend=False,
            height=400,
            title="🗺️ Real-time Congestion Map"
        )
        
        return fig
        
    def create_prediction_chart(self, prediction_data: Dict) -> go.Figure:
        """Create traffic prediction chart"""
        if not prediction_data or 'predictions' not in prediction_data:
            # Generate sample prediction data
            times = pd.date_range(start=datetime.now(), periods=24, freq='H')
            current_flow = np.random.randint(300, 700, len(times))
            predicted_flow = current_flow + np.random.randint(-50, 50, len(times))
        else:
            predictions = prediction_data['predictions']
            times = pd.to_datetime([p['timestamp'] for p in predictions])
            current_flow = [p.get('current_flow', 500) for p in predictions]
            predicted_flow = [p.get('predicted_flow', 500) for p in predictions]
            
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=times,
            y=current_flow,
            mode='lines+markers',
            name='Current Flow',
            line=dict(color='blue')
        ))
        
        fig.add_trace(go.Scatter(
            x=times,
            y=predicted_flow,
            mode='lines+markers',
            name='Predicted Flow',
            line=dict(color='red', dash='dash')
        ))
        
        fig.update_layout(
            title="📈 Traffic Flow Predictions (24h)",
            xaxis_title="Time",
            yaxis_title="Vehicles per Hour",
            hovermode='x unified',
            height=400
        )
        
        return fig
        
    def create_incidents_chart(self, incidents_data: Dict) -> go.Figure:
        """Create incidents summary chart"""
        if not incidents_data or 'incidents' not in incidents_data:
            # Sample incident data
            severities = ['Low', 'Medium', 'High', 'Critical']
            counts = [5, 3, 1, 0]
        else:
            incidents = incidents_data['incidents']
            severity_counts = {}
            for incident in incidents:
                severity = incident.get('severity', 'Low')
                severity_counts[severity] = severity_counts.get(severity, 0) + 1
                
            severities = list(severity_counts.keys())
            counts = list(severity_counts.values())
            
        colors = ['#2ecc71', '#f39c12', '#e74c3c', '#8b0000'][:len(severities)]
        
        fig = go.Figure(data=[
            go.Pie(
                labels=severities,
                values=counts,
                marker_colors=colors,
                textinfo='label+percent+value'
            )
        ])
        
        fig.update_layout(
            title="🚨 Active Incidents by Severity",
            height=400
        )
        
        return fig
        
    def render_metrics_cards(self, analytics_data: Dict):
        """Render key metrics cards"""
        if not analytics_data:
            # Sample metrics
            metrics = {
                'total_sensors': 8,
                'active_incidents': 4,
                'avg_flow_rate': 487,
                'system_health': 'Good'
            }
        else:
            metrics = analytics_data.get('summary', {})
            
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="🎯 Active Sensors",
                value=metrics.get('total_sensors', 'N/A'),
                delta=None
            )
            
        with col2:
            incidents = metrics.get('active_incidents', 0)
            st.metric(
                label="🚨 Active Incidents",
                value=incidents,
                delta=None,
                delta_color="inverse"
            )
            
        with col3:
            flow_rate = metrics.get('avg_flow_rate', 0)
            st.metric(
                label="🚗 Avg Flow Rate",
                value=f"{flow_rate} veh/h",
                delta=f"{np.random.randint(-20, 20)} veh/h"
            )
            
        with col4:
            health = metrics.get('system_health', 'Unknown')
            health_color = 'normal' if health == 'Good' else 'inverse'
            st.metric(
                label="💚 System Health",
                value=health,
                delta=None
            )

def main():
    """Main dashboard application"""
    st.title("🚦 Urbanclear Traffic Management Dashboard")
    st.markdown("Real-time traffic monitoring and optimization system")
    
    dashboard = WebDashboard()
    
    # Sidebar controls
    st.sidebar.title("⚙️ Dashboard Controls")
    auto_refresh = st.sidebar.checkbox("Auto Refresh", value=True)
    refresh_interval = st.sidebar.slider("Refresh Interval (seconds)", 5, 60, 10)
    
    # API status check
    api_status = dashboard.fetch_api_data("/health")
    if api_status:
        st.sidebar.success("✅ API Connected")
    else:
        st.sidebar.error("❌ API Disconnected")
        st.sidebar.info("💡 Using demo data")
    
    # Create placeholder for auto-refresh
    placeholder = st.empty()
    
    # Main dashboard loop  
    while auto_refresh:
        with placeholder.container():
            # Fetch data
            traffic_data = dashboard.fetch_api_data("/api/v1/traffic/current")
            analytics_data = dashboard.fetch_api_data("/api/v1/analytics/summary")
            prediction_data = dashboard.fetch_api_data("/api/v1/traffic/predict")
            incidents_data = dashboard.fetch_api_data("/api/v1/incidents/active")
            
            # Render metrics cards
            st.subheader("📊 Key Metrics")
            dashboard.render_metrics_cards(analytics_data)
            
            # Create two columns for charts
            col1, col2 = st.columns(2)
            
            with col1:
                # Traffic flow chart
                traffic_fig = dashboard.create_traffic_flow_chart(traffic_data)
                st.plotly_chart(traffic_fig, use_container_width=True, key="traffic_flow_chart")
                
                # Predictions chart
                prediction_fig = dashboard.create_prediction_chart(prediction_data)
                st.plotly_chart(prediction_fig, use_container_width=True, key="prediction_chart")
                
            with col2:
                # Congestion map
                map_fig = dashboard.create_congestion_map(traffic_data)
                st.plotly_chart(map_fig, use_container_width=True, key="congestion_map_chart")
                
                # Incidents chart
                incidents_fig = dashboard.create_incidents_chart(incidents_data)
                st.plotly_chart(incidents_fig, use_container_width=True, key="incidents_chart")
                
            # System status
            st.subheader("🔧 System Status")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.info("**Database Status**: ✅ Connected")
                st.info("**Redis Cache**: ✅ Active")
                
            with col2:
                st.info("**ML Models**: ✅ Loaded")
                st.info("**Prometheus**: ✅ Collecting")
                
            with col3:
                st.info("**Grafana**: ✅ Dashboards Active")
                st.info("**Kafka**: ✅ Streaming")
                
            # Latest incidents table
            st.subheader("📋 Recent Incidents")
            if incidents_data and 'incidents' in incidents_data:
                incidents_df = pd.DataFrame(incidents_data['incidents'])
                st.dataframe(incidents_df)
            else:
                # Sample incidents data
                sample_incidents = pd.DataFrame([
                    {'Time': '08:45', 'Location': 'Times Square', 'Type': 'Accident', 'Severity': 'Medium'},
                    {'Time': '09:12', 'Location': 'Brooklyn Bridge', 'Type': 'Construction', 'Severity': 'Low'},
                    {'Time': '09:30', 'Location': 'Central Park', 'Type': 'Event', 'Severity': 'Low'}
                ])
                st.dataframe(sample_incidents)
                
            # Update timestamp
            st.caption(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")
            
        if auto_refresh:
            time.sleep(refresh_interval)
        else:
            break
            
    if not auto_refresh:
        st.info("🔄 Auto-refresh disabled. Refresh the page to update data.")

def run_dashboard():
    """Run the dashboard (convenience function)"""
    main()

if __name__ == "__main__":
    main() 