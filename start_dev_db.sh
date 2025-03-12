#!/bin/bash

# Start Qdrant
docker run -p 6333:6333 -p 6334:6334 -v $(pwd)/qdrant_storage:/qdrant/storage:z qdrant/qdrant &

# Start Redis
docker run -p 6379:6379 --name redis-server -d redis &
sleep 1