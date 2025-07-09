# 🚦 Urbanclear Traffic Management System

A comprehensive AI-powered traffic management system with **real-time data integration**, **intelligent fallback systems**, and **production-ready APIs** for smart city traffic optimization.

## 🎯 Key Features

### 🌐 **Real Data Integration**
- **Multiple Data Sources**: Geoapify, OpenRouteService, OpenStreetMap integration
- **Smart Fallback System**: Intelligent mock data when APIs are unavailable
- **Geocoding**: Convert addresses to coordinates with high accuracy
- **Routing**: Real-time route calculation with traffic considerations
- **Places Search**: Find nearby businesses and points of interest
- **Traffic Matrix**: Calculate travel times between multiple locations
- **Isochrones**: Determine reachable areas within time limits

### 🤖 **AI-Powered Analytics**
- **Traffic Flow Prediction**: LSTM-based time series forecasting
- **Route Optimization**: Multi-objective pathfinding algorithms
- **Incident Detection**: Real-time anomaly detection
- **Performance Analytics**: Comprehensive traffic pattern analysis

### 🔄 **Real-Time Capabilities**
- **WebSocket Streaming**: Live traffic updates and predictions
- **Background Processing**: Continuous data collection and analysis
- **Health Monitoring**: Real-time API status and performance metrics
- **Caching Layer**: Redis-ready with in-memory fallback

### 🛡️ **Production Ready**
- **CI/CD Pipeline**: Automated testing and deployment
- **Comprehensive Testing**: 49 passing tests across unit and integration
- **API Documentation**: OpenAPI/Swagger auto-generated docs
- **Docker Support**: Containerized deployment with monitoring stack

## 🏗️ Architecture

```
urbanclear/
├── src/
│   ├── api/                 # FastAPI REST endpoints + WebSocket
│   ├── data/                # Real data integration + mock fallbacks
│   │   ├── geoapify_client.py      # Geoapify API integration
│   │   ├── openrouteservice_client.py  # OpenRouteService client
│   │   ├── osm_client.py           # OpenStreetMap client
│   │   ├── real_data_service.py    # Unified data service
│   │   └── real_data_config.py     # Configuration management
│   ├── models/              # ML models and algorithms
│   │   ├── prediction.py           # Traffic prediction models
│   │   ├── optimization.py         # Route optimization
│   │   └── incident_detection.py   # Incident detection
│   └── monitoring/          # Health monitoring and metrics
├── infrastructure/          # Big data processing
│   ├── kafka/               # Real-time streaming
│   └── spark/               # Distributed processing
├── docker/                  # Docker configurations
│   ├── grafana/             # Monitoring dashboards
│   ├── prometheus/          # Metrics collection
│   └── postgres/            # Database setup
├── tests/                   # Comprehensive test suite
│   ├── unit/                # Unit tests
│   ├── integration/         # Integration tests
│   └── api/                 # API endpoint tests
├── scripts/                 # Automation scripts
├── demo_real_data.py        # Interactive demo script
└── start_api.py            # API server launcher
```

## 🚀 Quick Start

### Prerequisites

- **Python 3.9+** (tested with 3.12)
- **Docker & Docker Compose** (optional)
- **API Keys** (optional - system works with mock data)

### Installation

1. **Clone and setup:**
```bash
git clone <repository-url>
cd traffic-system
```

2. **Create virtual environment:**
```bash
python -m venv urbanclear-env
source urbanclear-env/bin/activate  # On Windows: urbanclear-env\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Configure APIs (Optional):**
```bash
cp config/config.example.yaml config/config.yaml
# Edit config.yaml with your API keys:
# - Geoapify: 3,000 free requests/day
# - OpenRouteService: 2,000 free requests/day  
# - OpenStreetMap: Free (no key required)
```

5. **Start the API server:**
```bash
python start_api.py
```

6. **Access the system:**
- **API Documentation**: http://localhost:8000/api/docs
- **Health Check**: http://localhost:8000/health
- **WebSocket Test**: http://localhost:8000/api/docs (try WebSocket endpoints)

## 🎮 Demo & Testing

### Interactive Demo
```bash
# Full demo of all features
python demo_real_data.py

# Test specific features
python demo_real_data.py --test geocoding
python demo_real_data.py --test routing
python demo_real_data.py --test places
```

### Run Tests
```bash
# Run full test suite (49 tests)
pytest

# Run with coverage
pytest --cov=src tests/

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
pytest tests/api/
```

## 📊 API Endpoints

### **Real Data Integration**
- `GET /api/v1/real-data/health` - Data source health status
- `POST /api/v1/real-data/geocode` - Convert addresses to coordinates
- `POST /api/v1/real-data/route` - Calculate routes between points
- `GET /api/v1/real-data/places/search` - Search for nearby places
- `GET /api/v1/real-data/matrix` - Multi-location travel time matrix
- `GET /api/v1/real-data/isochrones` - Reachable area calculations

### **Traffic Analytics**
- `GET /api/v1/traffic/current` - Current traffic conditions
- `GET /api/v1/traffic/predictions` - AI-powered traffic forecasts
- `POST /api/v1/routes/optimize` - Route optimization
- `GET /api/v1/incidents/active` - Active traffic incidents

### **Real-Time Streaming**
- `WebSocket /ws/traffic` - Live traffic updates
- `WebSocket /ws/incidents` - Real-time incident notifications
- `WebSocket /ws/predictions` - Streaming traffic predictions

### **System Health**
- `GET /health` - System health check
- `GET /metrics` - Prometheus metrics
- `GET /api/v1/real-data/health` - Data source status

## 🔧 Configuration

### Data Sources Configuration
```yaml
# config/config.yaml
data_sources:
  geoapify:
    api_key: "your-geoapify-key"  # Optional: 3K free requests/day
    enabled: true
  
  openrouteservice:
    api_key: "your-ors-key"       # Optional: 2K free requests/day
    enabled: true
  
  openstreetmap:
    enabled: true                 # Always free, no key required
```

### Smart Fallback System
The system automatically uses mock data when real APIs are unavailable:
- **Geocoding**: 20+ famous locations with real coordinates
- **Routing**: Distance-based travel time calculations
- **Places**: Categorized business database with realistic locations
- **Matrix**: Multi-point travel time calculations
- **Isochrones**: Speed-based reachable area polygons

## 🎯 Data Sources

### **Supported APIs**
| Provider | Free Tier | Features | Status |
|----------|-----------|----------|---------|
| **Geoapify** | 3,000 requests/day | Geocoding, Routing, Places, Isochrones | ✅ Integrated |
| **OpenRouteService** | 2,000 requests/day | Routing, Matrix, Isochrones | ✅ Integrated |
| **OpenStreetMap** | Unlimited (rate limited) | Places, Roads, Geographic data | ✅ Integrated |
| **Mock Fallback** | Unlimited | All features with simulated data | ✅ Always Available |

### **Mock Data Features**
- **Realistic Geocoding**: Famous landmarks with accurate coordinates
- **Intelligent Places**: Categorized businesses (coffee shops, restaurants, gas stations, etc.)
- **Traffic Simulation**: Distance-based travel times with traffic factors
- **Geographic Accuracy**: Proper coordinate calculations and realistic distances

## 🚦 Traffic Models

### **Prediction Models**
- **LSTM Networks**: Time-series traffic volume prediction
- **Seasonal Analysis**: Daily/weekly traffic pattern recognition
- **Anomaly Detection**: Incident and congestion detection

### **Optimization Algorithms**
- **Multi-objective Routing**: Distance, time, and traffic optimization
- **Dynamic Rerouting**: Real-time path adjustment
- **Signal Timing**: Adaptive traffic light optimization

## 📈 Monitoring & Analytics

### **Grafana Dashboards**
- **Traffic Flow Dashboard**: Real-time traffic visualization
- **System Performance**: API response times and throughput
- **Geographic Traffic Map**: Location-based traffic analysis
- **Predictive Analytics**: AI model performance metrics

### **Health Monitoring**
- **API Status**: Real-time data source availability
- **Rate Limiting**: Request quota monitoring
- **Performance Metrics**: Response times and error rates
- **Cache Performance**: Hit rates and efficiency

## 🧪 Testing & Quality

### **Test Coverage**
- **49 Passing Tests**: Unit, integration, and API tests
- **Coverage**: 20% code coverage (configurable threshold)
- **CI/CD Pipeline**: Automated testing on Python 3.9, 3.10, 3.11

### **Code Quality**
- **Black**: Code formatting
- **Type Hints**: MyPy type checking
- **Linting**: Flake8 compliance
- **Security**: Bandit security scanning

## 🐳 Docker Deployment

### **Start Full Stack**
```bash
# Start all services (API, Grafana, Prometheus, etc.)
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### **Production Deployment**
```bash
# Build production image
docker build -t urbanclear-api .

# Run with environment variables
docker run -p 8000:8000 \
  -e GEOAPIFY_API_KEY=your-key \
  -e OPENROUTESERVICE_API_KEY=your-key \
  urbanclear-api
```

## 🔄 Recent Updates

### **v1.2.0 - Real Data Integration**
- ✅ **Multi-API Support**: Geoapify, OpenRouteService, OpenStreetMap
- ✅ **Smart Fallbacks**: Intelligent mock data when APIs unavailable
- ✅ **Health Monitoring**: Real-time API status and rate limiting
- ✅ **Caching Layer**: Redis-ready with in-memory fallback

### **v1.1.0 - Production Ready**
- ✅ **CI/CD Pipeline**: Fixed all test failures (49 tests passing)
- ✅ **FastAPI Migration**: Modern async API with lifespan handlers
- ✅ **WebSocket Streaming**: Real-time traffic updates
- ✅ **Comprehensive Testing**: Unit, integration, and API tests

## 🤝 Contributing

### **Development Setup**
```bash
# Install development dependencies
pip install -r requirements-ci.txt

# Run tests
make test

# Format code
make format

# Run CI checks locally
make ci
```

### **Pre-commit Hooks**
```bash
# Install hooks
pre-commit install

# Run all hooks
pre-commit run --all-files
```

## 📚 Documentation

- **API Docs**: http://localhost:8000/api/docs (Interactive Swagger UI)
- **Health Check**: http://localhost:8000/health
- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090

## 🎊 Demo Results

```bash
📊 Recent Demo Results:
✅ Geocoding: 3/3 addresses successfully converted
✅ Routing: 2/2 routes calculated with traffic data
✅ Places: 10 coffee shops + 5 gas stations found
✅ Matrix: 4x4 NYC location matrix calculated
✅ Isochrones: 15 & 30-minute reachable areas generated
✅ Health: All endpoints responding with proper fallbacks
```

## 🛠️ System Requirements

- **Python**: 3.9+ (tested with 3.12)
- **Memory**: 2GB+ RAM
- **Storage**: 1GB+ free space
- **Network**: Internet connection for real APIs (optional)

## 🎯 Next Steps

1. **Add API Keys**: Configure Geoapify/OpenRouteService for enhanced data
2. **Redis Setup**: Enable Redis for better caching performance
3. **Frontend Integration**: Connect to web dashboard
4. **Monitoring**: Set up Grafana dashboards
5. **Scaling**: Deploy with Docker Swarm or Kubernetes

---

**🚦 Urbanclear - Production-Ready Traffic Intelligence** 

Built with ❤️ for smarter cities • Real Data • Smart Fallbacks • Always Available 