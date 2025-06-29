
-- Initialize PostgreSQL database for traffic system
-- CREATE EXTENSION IF NOT EXISTS postgis;  -- Commented out: requires postgis/postgis Docker image
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create application user and database
-- (These are handled by Docker environment variables)
