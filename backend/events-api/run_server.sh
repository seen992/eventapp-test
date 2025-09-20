#!/bin/bash

# Set environment variables
export POSTGRES_DB_HOST=localhost
export POSTGRES_DB_PORT=5432
export POSTGRES_DB_USER=postgres
export POSTGRES_DB_PASSWORD=postgres
export POSTGRES_DB_SCHEMA=public

# Run the server
uvicorn app.main:app --host 0.0.0.0 --port 8081 --reload
