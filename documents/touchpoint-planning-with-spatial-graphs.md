# Travel Touchpoint Planning with Spatial Graphs

## Overview

This feature powers smart travel planning and contextual retail recommendations using a graph database with geographic awareness. It models destinations, retail stores, and transit hubs as touchpoints in a spatial graph. Powered by PostgreSQL 16, PostGIS, and pgRouting, this solution supports:

- Personalized trip routing
- Nearest retail store search
- Multi-modal travel planning
- Location-aware heuristics (e.g., priority scores, travel types)

## Tech Stack

- PostgreSQL 16 – Core relational engine
- PostGIS – Spatial extension for geolocation, distance, and geometry
- pgRouting – Graph extension for shortest path and travel network analysis

## Data Model

### touchpoint_nodes
Represents touchpoints like landmarks, retail stores, hotels, or transit hubs.

| Column     | Type               | Description                               |
|------------|--------------------|-------------------------------------------|
| node_id    | SERIAL PRIMARY KEY | Unique node ID                            |
| name       | VARCHAR(255)       | Human-readable name                       |
| type       | VARCHAR(50)        | e.g. landmark, retail, transit            |
| lat, lon   | DOUBLE PRECISION   | GPS coordinates                           |
| geom       | GEOGRAPHY(POINT)   | Spatial geometry for fast queries         |
| priority   | INTEGER            | Travel relevance or recommendation rank   |

### touchpoint_paths
Represents possible travel between two touchpoints.

| Column        | Type               | Description                                      |
|---------------|--------------------|--------------------------------------------------|
| path_id       | SERIAL PRIMARY KEY | Unique path ID                                  |
| source_id     | INTEGER            | FK → touchpoint_nodes(node_id) (start)          |
| target_id     | INTEGER            | FK → touchpoint_nodes(node_id) (end)            |
| travel_type   | VARCHAR(50)        | e.g. walk, bike, subway                         |
| cost          | NUMERIC            | Cost in time, energy, or preference units       |
| length        | NUMERIC            | Distance in meters                              |
| reverse_cost  | NUMERIC            | Optional reverse direction cost                 |

## Spatial Indexes & Extensions

```sql
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pgrouting;

CREATE INDEX IF NOT EXISTS idx_touchpoint_geom ON touchpoint_nodes USING GIST (geom);
```

## Sample Data

### Nodes

```sql
INSERT INTO touchpoint_nodes (name, type, lat, lon, geom, priority) VALUES
('Central Park', 'landmark', 40.785091, -73.968285, ST_SetSRID(ST_MakePoint(-73.968285, 40.785091), 4326)::GEOGRAPHY, 5),
('5th Ave Retail', 'retail', 40.762421, -73.974103, ST_SetSRID(ST_MakePoint(-73.974103, 40.762421), 4326)::GEOGRAPHY, 4),
('Times Square', 'landmark', 40.758896, -73.985130, ST_SetSRID(ST_MakePoint(-73.985130, 40.758896), 4326)::GEOGRAPHY, 5),
('Midtown Transit Hub', 'transit', 40.754932, -73.984016, ST_SetSRID(ST_MakePoint(-73.984016, 40.754932), 4326)::GEOGRAPHY, 3);
```

### Paths

```sql
INSERT INTO touchpoint_paths (source_id, target_id, travel_type, cost, length, reverse_cost) VALUES
(1, 2, 'walk', 5, 1800, 5),
(2, 3, 'walk', 4, 1300, 4),
(1, 3, 'bike', 2, 2000, 2.5),
(3, 4, 'subway', 3, 1000, NULL),
(2, 4, 'walk', 6, 1500, 6);
```

## Shortest Path Query

```sql
SELECT
  p.seq,
  sn.name AS start_node,
  tn.name AS end_node,
  tp.travel_type,
  tp.length,
  p.cost AS total_cost
FROM pgr_dijkstra(
  'SELECT path_id AS id, source_id AS source, target_id AS target, cost FROM touchpoint_paths',
  (SELECT node_id FROM touchpoint_nodes WHERE name = 'Central Park'),
  (SELECT node_id FROM touchpoint_nodes WHERE name = 'Midtown Transit Hub'),
  directed := true
) AS p
JOIN touchpoint_paths tp ON p.edge = tp.path_id
JOIN touchpoint_nodes sn ON tp.source_id = sn.node_id
JOIN touchpoint_nodes tn ON tp.target_id = tn.node_id
ORDER BY p.seq;
```

## Nearest Retail Store Query

```sql
SELECT name, ST_Distance(geom, ST_MakePoint(-73.970000, 40.760000)::GEOGRAPHY) AS distance_m
FROM touchpoint_nodes
WHERE type = 'retail'
ORDER BY distance_m
LIMIT 1;
```

## Extensibility Ideas

- Add `opening_hours`, `brand`, or `tags` for smarter recommendations
- Use `ST_DWithin` for proximity filtering
- Add a `popularity` or `user_rating` score
- Integrate time-based traffic to affect `cost`
- Hook to a map UI (Leaflet / Mapbox / React Native Maps)

## Roadmap

- ✅ Travel path planner via pgRouting
- ✅ Nearest POI via spatial indexing
- 🔜 Multi-criteria path planning (preferences, budget, time)
- 🔜 Realtime POI filters based on user location
- 🔜 AI itinerary assistant (Python/Node backend)

## License

MIT License – Build boldly. Deploy freely.

