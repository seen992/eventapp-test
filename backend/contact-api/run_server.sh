#!/usr/bin/env bash

echo Starting Uvicorn.

exec uvicorn app.main:app --host 0.0.0.0 --port 8080 --workers 1 --log-level info
