# Urbanclear Grafana Dashboards 📊

This directory contains comprehensive monitoring dashboards for the Urbanclear traffic optimization system. The dashboards provide real-time insights into traffic flow, incidents, system performance, and predictive analytics.

## 🗂️ Dashboard Overview

### 1. System Overview (`overview-dashboard.json`)
**Main landing dashboard with system-wide metrics**
- System health status (API, Database, Cache)
- Real-time traffic overview
- API performance metrics
- Key system metrics
- Resource usage monitoring
- Quick links to other dashboards

**Best for**: Executive overview, system health checks, quick navigation

### 2. Traffic Flow Dashboard (`traffic-flow-dashboard.json`)
**Real-time traffic monitoring and analysis**
- Traffic flow rates by location and direction
- Congestion level distribution
- API request patterns
- Response time heatmaps
- Traffic patterns over time

**Best for**: Traffic operations teams, real-time monitoring

### 3. Incident Management Dashboard (`incident-management-dashboard.json`)
**Comprehensive incident tracking and response monitoring**
- Active incidents by severity
- Incident response times (95th percentile)
- Daily incident resolution counts
- Incident trends over 24 hours
- Severity distribution
- Average resolution times
- Recent incident logs

**Best for**: Emergency response teams, incident managers

### 4. System Performance Dashboard (`system-performance-dashboard.json`)
**Infrastructure monitoring and performance metrics**
- API response times and request rates
- Database connection monitoring
- Query performance metrics
- Redis cache hit rates
- Memory usage tracking
- System health indicators
- Error rate monitoring

**Best for**: DevOps teams, system administrators

### 5. Geographic Traffic Map (`geographic-traffic-map.json`)
**Interactive geographic visualization**
- Traffic conditions map with color-coded flow rates
- Active incident markers with severity indicators
- Traffic sensor location mapping
- Traffic density heatmaps
- Geographic clustering analysis

**Best for**: City planners, traffic control centers

### 6. Predictive Analytics Dashboard (`predictive-analytics-dashboard.json`)
**Machine learning model performance and predictions**
- Model accuracy gauges (Traffic, Incident, Route models)
- Predicted vs actual traffic comparisons
- Route optimization performance metrics
- Signal optimization efficiency
- Prediction error distributions
- 24-hour traffic forecasts
- Model training metrics
- Feature importance analysis

**Best for**: Data scientists, ML engineers, strategic planning

## 🚀 Getting Started

### Prerequisites
1. Docker and Docker Compose installed
2. Urbanclear system running with all services
3. Prometheus metrics enabled in the API

### Quick Start
1. **Start the system**:
   ```bash
   make start
   ```

2. **Access Grafana**:
   - URL: http://localhost:3000
   - Username: `admin`
   - Password: `grafana_password`

3. **Navigate to dashboards**:
   - Go to "Dashboards" → "Browse"
   - Look for dashboards tagged with "urbanclear"
   - Start with "System Overview" for the main dashboard

### Configuration
- **Prometheus datasource**: Pre-configured to connect to `http://prometheus:9090`
- **Refresh intervals**: Set from 30s to 5m depending on dashboard purpose
- **Time ranges**: Default to 1-24 hours with option to customize

## 📈 Key Metrics Explained

### Traffic Metrics
- **Traffic Flow Rate**: Percentage of road capacity being used (0-100%)
- **Congestion Level**: Classification of traffic density (Free, Light, Heavy, Gridlock)
- **Sensor Coverage**: Number and location of active traffic sensors

### Incident Metrics
- **Active Incidents**: Current unresolved traffic incidents
- **Severity Levels**: Critical, High, Medium, Low
- **Response Time**: Time from incident detection to first response
- **Resolution Time**: Average time to fully resolve incidents

### System Metrics
- **API Performance**: Request rate, response times, error rates
- **Database Health**: Connection count, query performance, size
- **Cache Efficiency**: Redis hit rates, memory usage
- **Service Uptime**: Availability of critical system components

### Prediction Metrics
- **Model Accuracy**: Percentage accuracy of ML predictions
- **Prediction Error**: Difference between predicted and actual values
- **Feature Importance**: Which factors most influence predictions
- **Optimization Impact**: Improvements from route/signal optimization

## 🔧 Customization

### Adding New Panels
1. Edit dashboard JSON files or use Grafana UI
2. Use existing Prometheus metrics or add new ones
3. Follow naming convention: `urbanclear_[metric_name]`

### Creating Alerts
1. Set up alert rules in Grafana
2. Configure notification channels (Slack, email, etc.)
3. Use thresholds based on your operational requirements

### Custom Metrics
Add new metrics to the FastAPI application:
```python
from prometheus_client import Counter, Gauge, Histogram

# Example: Custom traffic metric
CUSTOM_METRIC = Gauge('urbanclear_custom_metric', 'Description', ['label'])
CUSTOM_METRIC.labels('value').set(123)
```

## 🎨 Visual Features

### Color Coding
- **Green**: Normal/Healthy (0-50%)
- **Yellow**: Warning/Moderate (50-70%)
- **Orange**: High/Concerning (70-90%)
- **Red**: Critical/Severe (90-100%)

### Chart Types
- **Time Series**: Trends over time
- **Gauges**: Current status indicators  
- **Bar Charts**: Comparative analysis
- **Pie Charts**: Distribution visualization
- **Heatmaps**: Pattern identification
- **Geographic Maps**: Spatial visualization
- **Tables**: Detailed data views

## 🔍 Troubleshooting

### Common Issues

1. **No Data Showing**
   - Check Prometheus is running and accessible
   - Verify API is exposing `/metrics` endpoint
   - Ensure time range includes data points

2. **Dashboard Import Errors**
   - Validate JSON syntax
   - Check Grafana version compatibility
   - Verify datasource configuration

3. **Performance Issues**
   - Reduce time ranges for heavy queries
   - Optimize Prometheus query intervals
   - Check system resource usage

### Log Locations
- Grafana logs: `/var/log/grafana/`
- Prometheus logs: Check Docker container logs
- API metrics: `/metrics` endpoint

## 📊 Dashboard Usage Tips

### For Traffic Operations
1. Start with System Overview
2. Monitor Traffic Flow Dashboard during peak hours
3. Use Geographic Map for spatial analysis
4. Set up alerts for high incident counts

### For System Administration
1. Focus on System Performance Dashboard
2. Monitor resource usage trends
3. Set up alerting for service downtime
4. Track API performance metrics

### For Strategic Planning
1. Use Predictive Analytics for forecasting
2. Analyze incident patterns over time
3. Monitor model accuracy trends
4. Review optimization effectiveness

## 🔐 Security Considerations

- Change default Grafana admin password
- Configure authentication (LDAP, OAuth, etc.)
- Restrict dashboard editing permissions
- Use HTTPS in production
- Regular backup of dashboard configurations

## 📝 Contributing

When adding new dashboards:
1. Follow naming convention: `urbanclear-[purpose]-dashboard.json`
2. Add appropriate tags: `["urbanclear", "category"]`
3. Include description and documentation
4. Test with sample data
5. Update this README

## 📞 Support

For issues or questions:
- Check logs first
- Review Prometheus metrics availability
- Verify system connectivity
- Consult Grafana documentation for panel-specific issues

---

**Last Updated**: 2024
**Version**: 1.0.0
**Grafana Version**: Latest (Docker) 