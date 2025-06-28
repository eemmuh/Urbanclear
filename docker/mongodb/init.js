
// Initialize MongoDB database for traffic system
db = db.getSiblingDB('traffic_logs');

// Create collections
db.createCollection('sensor_logs');
db.createCollection('incident_logs');
db.createCollection('api_logs');
db.createCollection('system_logs');

// Create indexes
db.sensor_logs.createIndex({"timestamp": 1});
db.sensor_logs.createIndex({"sensor_id": 1, "timestamp": 1});
db.incident_logs.createIndex({"timestamp": 1});
db.api_logs.createIndex({"timestamp": 1, "endpoint": 1});

print("MongoDB initialized successfully");
