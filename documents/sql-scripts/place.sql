-- Enable PostGIS if not already installed
CREATE EXTENSION IF NOT EXISTS postgis;

-- Create places table with Plus Code support
CREATE TABLE places (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    category TEXT,
    tags TEXT[],

    -- Google's Open Location Code (Plus Code)
    pluscode TEXT UNIQUE,

    -- Geometry: store lat/lon as POINT with SRID 4326 (WGS 84)
    geom GEOMETRY(Point, 4326) NOT NULL,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Optional: keep updated_at in sync
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_places_timestamp
BEFORE UPDATE ON places
FOR EACH ROW
EXECUTE PROCEDURE update_timestamp();

-- Index for fast geospatial queries
CREATE INDEX idx_places_geom ON places USING GIST (geom);

-- Index for quick lookup by Plus Code
CREATE INDEX idx_places_pluscode ON places (pluscode);
