#!/usr/bin/env bash

echo Starting Test Deploy API...

exec uvicorn app.main:app --host 0.0.0.0 --port 8080 --workers 1 --log-level info