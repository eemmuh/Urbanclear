# 📚 Urbanclear Examples

This directory contains example scripts and demos for the Urbanclear Traffic Management System.

## 🎮 Available Examples

### `demo_real_data.py` - Real Data Integration Demo
**Interactive demonstration of all real data integration features**

```bash
# Run full demo
python examples/demo_real_data.py

# Test specific features
python examples/demo_real_data.py --test geocoding
python examples/demo_real_data.py --test routing
python examples/demo_real_data.py --test places
```

**Features Demonstrated:**
- ✅ **Geocoding**: Convert addresses to coordinates
- ✅ **Routing**: Calculate routes between points
- ✅ **Places Search**: Find nearby businesses
- ✅ **Traffic Matrix**: Multi-location travel times
- ✅ **Isochrones**: Reachable area calculations
- ✅ **Health Monitoring**: API status and rate limiting

**Sample Output:**
```
✅ Geocoding: 3/3 addresses successfully converted
✅ Routing: 2/2 routes calculated with traffic data
✅ Places: 10 coffee shops + 5 gas stations found
✅ Matrix: 4x4 NYC location matrix calculated
✅ Isochrones: 15 & 30-minute reachable areas generated
```

## 🚀 Getting Started

1. **Ensure API is running:**
   ```bash
   python start_api.py
   ```

2. **Run the demo:**
   ```bash
   python examples/demo_real_data.py
   ```

3. **View results:**
   - Demo shows real-time API responses
   - Demonstrates fallback to mock data when needed
   - Tests all major endpoints

## 🔧 Configuration

The demo uses the same configuration as the main API:
- **API Keys**: Optional (works with mock data)
- **Base URL**: `http://localhost:8000`
- **Timeout**: 30 seconds per request

## 📖 Next Steps

- **Add API Keys**: For enhanced real data (see main README)
- **Custom Endpoints**: Modify demo to test your specific use cases
- **Integration**: Use demo patterns in your own applications

For more information, see the main project [README](../README.md). 